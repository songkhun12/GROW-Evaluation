#!/usr/bin/env python3
"""Regenerate referral evaluation outputs from the June 15, 2026 XLSX files.

The analysis mirrors the evaluation specification: a propensity-score model is used to
construct overlap weights, then referral counts are estimated with overlap-weighted,
covariate-adjusted Poisson models. Logistic robustness models use the same overlap
weights and covariates for any-referral outcomes.
"""
from __future__ import annotations

from zipfile import ZipFile
import csv
import math
import os
import statistics
import xml.etree.ElementTree as ET

BASE = os.path.dirname(__file__)
JES = os.path.join(BASE, "JES At Risk Report_Updated 6.15.26 (PW_ #JES2026).xlsx")
JMTES = os.path.join(BASE, "JMTES At Risk Report_Updated 6.15.26 (PW_ #MTE2026).xlsx")
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def colidx(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def read_xlsx(path: str):
    with ZipFile(path) as z:
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", NS):
                shared_strings.append("".join(t.text or "" for t in si.findall(".//a:t", NS)))
        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in root.findall(".//a:sheetData/a:row", NS):
        vals = {}
        for cell in row.findall("a:c", NS):
            value = cell.find("a:v", NS)
            value = "" if value is None else value.text
            if cell.get("t") == "s" and value != "":
                value = shared_strings[int(value)]
            vals[colidx(cell.get("r", "A1"))] = value
        if vals:
            rows.append([vals.get(i, "") for i in range(max(vals) + 1)])
    title = rows[0][0]
    header = rows[1]
    return title, [dict(zip(header, row + [""] * (len(header) - len(row)))) for row in rows[2:]]


def clean(x) -> str:
    return str(x).strip()


def num(x) -> float:
    try:
        s = clean(x)
        return 0.0 if s == "" else float(s)
    except Exception:
        return 0.0


def load_school(path: str, school: str, jmtes: int):
    out = []
    title, records = read_xlsx(path)
    for raw in records:
        if not clean(raw.get("Student Id", "")):
            continue
        l1, l2, l3, l4 = [num(raw.get(c, 0)) for c in ["L-1", "L-2", "L-3", "L-4"]]
        local, bus1, bus2, bus3 = [num(raw.get(c, 0)) for c in ["Local", "Transportation 1", "Transportation 2", "Transportation 3"]]
        row = {
            "school": school,
            "source_file": os.path.basename(path),
            "source_title": title,
            "source_report_date": "2026-06-15",
            "jmtes": float(jmtes),
            "student_id": clean(raw.get("Student Id", "")),
            "grade": clean(raw.get("Student Grade", "")),
            "female": 1.0 if clean(raw.get("Gender", "")).lower() == "female" else 0.0,
            "black": 1.0 if clean(raw.get("Ethnic Name", "")).lower() == "black" else 0.0,
            "age": num(raw.get("Student Age", 0)),
            "meal_status": clean(raw.get("Meal Status Code", "")),
            "entry_code": clean(raw.get("Entry Code - E/W", "")),
            # The updated files do not include Report School Days. Use a common
            # 170-day exposure, which keeps outcomes on the report's per-170-day scale.
            "enrollment_days": 170.0,
            "classroom_l1": l1,
            "classroom_l2": l2,
            "classroom_l3": l3,
            "classroom_l4": l4,
            "bus_l1": local + bus1,
            "bus_l2": bus2,
            "bus_l3": bus3,
        }
        row["classroom_total"] = l1 + l2 + l3 + l4
        row["classroom_severity_points"] = l1 + 2 * l2 + 3 * l3 + 4 * l4
        row["bus_total"] = local + bus1 + bus2 + bus3
        row["bus_severity_points"] = local + bus1 + 2 * bus2 + 3 * bus3
        row["any_school_referral"] = 1.0 if row["classroom_total"] > 0 else 0.0
        row["any_bus_referral"] = 1.0 if row["bus_total"] > 0 else 0.0
        row["any_referral"] = 1.0 if row["classroom_total"] > 0 or row["bus_total"] > 0 else 0.0
        out.append(row)
    return out


def design_matrix(data, include_treatment=True):
    cat_terms = []
    for var in ["grade", "meal_status", "entry_code"]:
        levels = sorted({d[var] for d in data})
        cat_terms.extend((var, level) for level in levels[1:])
    base_names = ["Intercept", "female", "black", "age"]
    if include_treatment:
        base_names.insert(1, "jmtes")
    names = base_names + [f"{v}:{l}" for v, l in cat_terms]
    x = []
    for d in data:
        base = [1.0, d["female"], d["black"], d["age"]]
        if include_treatment:
            base.insert(1, d["jmtes"])
        x.append(base + [1.0 if d[v] == level else 0.0 for v, level in cat_terms])
    return names, x


def invert(a):
    n = len(a)
    m = [list(map(float, a[i])) + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[pivot] = m[pivot], m[i]
        if abs(m[i][i]) < 1e-12:
            m[i][i] = 1e-12
        div = m[i][i]
        m[i] = [v / div for v in m[i]]
        for r in range(n):
            if r == i:
                continue
            factor = m[r][i]
            if factor:
                m[r] = [m[r][c] - factor * m[i][c] for c in range(2 * n)]
    return [row[n:] for row in m]


def grouped_records(data, x, yvar, weights, family):
    groups = {}
    for i, d in enumerate(data):
        offset = math.log(d["enrollment_days"]) if family == "poisson" else 0.0
        key = (tuple(x[i]), offset)
        g = groups.setdefault(key, {"x": x[i], "offset": offset, "w": 0.0, "wy": 0.0, "w2_y2": 0.0, "w2_y": 0.0, "w2": 0.0, "n": 0})
        y = d[yvar]
        w = weights[i]
        g["w"] += w
        g["wy"] += w * y
        g["w2_y2"] += w * w * y * y
        g["w2_y"] += w * w * y
        g["w2"] += w * w
        g["n"] += 1
    return list(groups.values())


def glm_fit(data, yvar, family, weights=None, include_treatment=True):
    names, x = design_matrix(data, include_treatment=include_treatment)
    n = len(data)
    p = len(names)
    weights = [1.0] * n if weights is None else weights
    groups = grouped_records(data, x, yvar, weights, family)
    beta = [0.0] * p
    if family == "poisson":
        total_y = sum(d[yvar] for d in data)
        beta[0] = math.log((total_y + 0.1) / sum(d["enrollment_days"] for d in data))
    for _ in range(100):
        a = [[0.0] * p for _ in range(p)]
        score = [0.0] * p
        for g in groups:
            xb = sum(g["x"][j] * beta[j] for j in range(p))
            if family == "poisson":
                mu = math.exp(max(min(xb + g["offset"], 30), -30))
                var_factor = g["w"] * mu
                resid_factor = g["wy"] - g["w"] * mu
            else:
                pr = 1.0 / (1.0 + math.exp(-max(min(xb, 35), -35)))
                pr = min(max(pr, 1e-8), 1 - 1e-8)
                var_factor = g["w"] * pr * (1 - pr)
                resid_factor = g["wy"] - g["w"] * pr
            for j in range(p):
                score[j] += g["x"][j] * resid_factor
                xj = g["x"][j]
                if xj == 0:
                    continue
                for k in range(p):
                    a[j][k] += var_factor * xj * g["x"][k]
        inv = invert(a)
        delta = [sum(inv[j][k] * score[k] for k in range(p)) for j in range(p)]
        beta = [beta[j] + delta[j] for j in range(p)]
        if max(abs(v) for v in delta) < 1e-8:
            break

    # Sandwich/robust covariance, grouped exactly by summing w^2(y-mu)^2 within each covariate pattern.
    a = [[0.0] * p for _ in range(p)]
    meat = [[0.0] * p for _ in range(p)]
    for g in groups:
        xb = sum(g["x"][j] * beta[j] for j in range(p))
        if family == "poisson":
            mu = math.exp(max(min(xb + g["offset"], 30), -30))
            var_factor = g["w"] * mu
        else:
            mu = 1.0 / (1.0 + math.exp(-max(min(xb, 35), -35)))
            mu = min(max(mu, 1e-8), 1 - 1e-8)
            var_factor = g["w"] * mu * (1 - mu)
        # Sum_i w_i^2 (y_i - mu_i)^2 = sum w2*y2 - 2*mu*sum w2*y + mu^2*sum w2
        robust_factor = g["w2_y2"] - 2 * mu * g["w2_y"] + mu * mu * g["w2"]
        for j in range(p):
            xj = g["x"][j]
            if xj == 0:
                continue
            for k in range(p):
                a[j][k] += var_factor * xj * g["x"][k]
                meat[j][k] += robust_factor * xj * g["x"][k]
    bread = invert(a)
    temp = [[sum(bread[j][l] * meat[l][k] for l in range(p)) for k in range(p)] for j in range(p)]
    vcov = [[sum(temp[j][l] * bread[l][k] for l in range(p)) for k in range(p)] for j in range(p)]
    return names, beta, vcov


def p_value(z):
    return math.erfc(abs(z) / math.sqrt(2))


def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    jmtes = load_school(JMTES, "JMTES", 1)
    jes = load_school(JES, "JES", 0)
    data = jmtes + jes
    source_audit = [
        {"school": "JMTES", "source_file": os.path.basename(JMTES), "source_report_date": "2026-06-15", "students_loaded": len(jmtes), "workbook_title": jmtes[0]["source_title"] if jmtes else ""},
        {"school": "JES", "source_file": os.path.basename(JES), "source_report_date": "2026-06-15", "students_loaded": len(jes), "workbook_title": jes[0]["source_title"] if jes else ""},
    ]

    # Propensity score and overlap weights.
    names, beta, _ = glm_fit(data, "jmtes", "logit", include_treatment=False)
    _, x = design_matrix(data, include_treatment=False)
    for i, d in enumerate(data):
        xb = sum(x[i][j] * beta[j] for j in range(len(beta)))
        ps = 1.0 / (1.0 + math.exp(-max(min(xb, 35), -35)))
        d["propensity"] = ps
        d["overlap_weight"] = 1.0 - ps if d["jmtes"] == 1.0 else ps

    desc_labels = [
        ("classroom_total", "Total school referrals"), ("classroom_l1", "School Level I referrals"),
        ("classroom_l2", "School Level II referrals"), ("classroom_l3", "School Level III referrals"),
        ("classroom_l4", "School Level IV referrals"), ("bus_total", "Total bus referrals"),
        ("bus_l1", "Bus Level I referrals"), ("bus_l2", "Bus Level II referrals"), ("bus_l3", "Bus Level III referrals"),
    ]
    desc = []
    for y, label in desc_labels:
        for school in ["JMTES", "JES"]:
            vals = [d[y] for d in data if d["school"] == school]
            desc.append({"outcome": label, "school": school, "n": len(vals), "mean": statistics.mean(vals), "sd": statistics.stdev(vals), "median": statistics.median(vals), "min": min(vals), "max": max(vals)})
    write_csv(os.path.join(BASE, "jmtes_jes_referral_data_source_audit.csv"), source_audit)
    write_csv(os.path.join(BASE, "jmtes_jes_referral_descriptive_statistics.csv"), desc)

    weights = [d["overlap_weight"] for d in data]
    poisson_outcomes = [
        ("classroom_total", "Classroom referrals"), ("classroom_severity_points", "Classroom severity-weighted frequency"),
        ("bus_total", "Bus referrals"), ("bus_severity_points", "Bus severity-weighted frequency"),
        ("classroom_l1", "Classroom L-I"), ("classroom_l2", "Classroom L-II"), ("classroom_l3", "Classroom L-III"),
        ("classroom_l4", "Classroom L-IV"), ("bus_l1", "Bus L-I"), ("bus_l2", "Bus L-II"), ("bus_l3", "Bus L-III"),
    ]
    results = []
    for y, label in poisson_outcomes:
        if sum(d[y] for d in data if d["jmtes"] == 1.0) == 0 or sum(d[y] for d in data if d["jmtes"] == 0.0) == 0:
            coef = se = p = irr = float("nan")
        else:
            names, beta, vcov = glm_fit(data, y, "poisson", weights)
            j = names.index("jmtes")
            coef = beta[j]
            se = math.sqrt(max(vcov[j][j], 0.0))
            p = p_value(coef / se) if se > 0 else float("nan")
            irr = math.exp(coef)
        def weighted_rate(group):
            rows = [d for d in data if d["jmtes"] == group]
            return sum(d["overlap_weight"] * d[y] for d in rows) / sum(d["overlap_weight"] * d["enrollment_days"] for d in rows) * 170.0
        results.append({"outcome": y, "label": label, "coefficient": coef, "robust_se": se, "p_value": p, "stars": "" if math.isnan(p) else stars(p), "irr": irr, "percent_difference": 100 * (irr - 1) if not math.isnan(irr) else float("nan"), "jes_weighted_rate_per_170_days": weighted_rate(0.0), "jmtes_weighted_rate_per_170_days": weighted_rate(1.0), "observations": len(data), "events": sum(d[y] for d in data)})
    write_csv(os.path.join(BASE, "jmtes_jes_referral_poisson_results.csv"), results)

    logit_results = []
    for y, label in [("any_school_referral", "Any school referral"), ("any_bus_referral", "Any bus referral"), ("any_referral", "Any school or bus referral")]:
        names, beta, vcov = glm_fit(data, y, "logit", weights)
        j = names.index("jmtes")
        coef = beta[j]
        se = math.sqrt(max(vcov[j][j], 0.0))
        p = p_value(coef / se) if se > 0 else float("nan")
        def weighted_probability(group):
            rows = [d for d in data if d["jmtes"] == group]
            return sum(d["overlap_weight"] * d[y] for d in rows) / sum(d["overlap_weight"] for d in rows)
        logit_results.append({"outcome": y, "label": label, "coefficient": coef, "robust_se": se, "p_value": p, "stars": stars(p), "odds_ratio": math.exp(coef), "jes_weighted_probability": weighted_probability(0.0), "jmtes_weighted_probability": weighted_probability(1.0), "observations": len(data), "events": sum(d[y] for d in data)})
    write_csv(os.path.join(BASE, "jmtes_jes_referral_any_referral_logit_robustness_results.csv"), logit_results)
    write_csv(os.path.join(BASE, "jmtes_jes_referral_student_data.csv"), data)
    print(f"Loaded {len(jmtes)} JMTES and {len(jes)} JES students; wrote overlap-weighted covariate-adjusted outputs.")


if __name__ == "__main__":
    main()
