#!/usr/bin/env python3
"""Create overlap-weighted, matching, and DiD ATLAS results from merged CSVs."""
from __future__ import annotations

import csv
import math
from pathlib import Path

from create_at_risk_regression_table import (
    GRADE_FILES,
    SUBJECT_SPECS,
    ROOT,
    absence_float,
    fmt,
    indicator,
    invert,
    matmul,
    matvec,
    meal_assistance,
    read_merged_csv,
    to_float,
    transpose,
)

RESULTS_CSV = ROOT / "at_risk_atlas_additional_methods_results.csv"
TABLE_RTF = ROOT / "at_risk_atlas_additional_methods_AER.rtf"
COVARS = ["baseline", "unexcused", "excused", "female", "black", "meal_assistance"]


def rows_for_model(grade: str, outcome_col: str, baseline_col: str) -> list[dict[str, float]]:
    jes_file, jmtes_file = GRADE_FILES[grade]
    records = read_merged_csv(jes_file, "JES") + read_merged_csv(jmtes_file, "JMTES")
    rows = []
    for row in records:
        outcome = to_float(row.get(outcome_col, ""))
        baseline = to_float(row.get(baseline_col, ""))
        if outcome is None or baseline is None:
            continue
        rows.append({
            "treat": row["JMTES"],
            "outcome": outcome,
            "change": outcome - baseline,
            "baseline": baseline,
            "unexcused": absence_float(row.get("At Risk - Unexcused", "")),
            "excused": absence_float(row.get("At Risk - Excused", "")),
            "female": indicator(row.get("At Risk - Gender", ""), "Female"),
            "black": indicator(row.get("At Risk - Ethnic Name", ""), "Black"),
            "meal_assistance": meal_assistance(row.get("At Risk - Meal Status Code", "")),
        })
    return rows


def standardize(rows: list[dict[str, float]]) -> tuple[list[list[float]], list[float], list[float]]:
    means = [sum(r[c] for r in rows) / len(rows) for c in COVARS]
    sds = []
    for c, m in zip(COVARS, means):
        ss = sum((r[c] - m) ** 2 for r in rows)
        sds.append(math.sqrt(ss / (len(rows) - 1)) if ss > 0 else 1.0)
    x = [[(r[c] - m) / sd for c, m, sd in zip(COVARS, means, sds)] for r in rows]
    return x, means, sds


def ols_coef(y: list[float], x: list[list[float]], weights: list[float] | None = None) -> tuple[float, float]:
    if weights is None:
        weights = [1.0] * len(y)
    xw = [[v * math.sqrt(w) for v in row] for row, w in zip(x, weights)]
    yw = [v * math.sqrt(w) for v, w in zip(y, weights)]
    xt = transpose(xw)
    xtx_inv = invert(matmul(xt, xw))
    beta = matvec(xtx_inv, matvec(xt, yw))
    fitted = matvec(x, beta)
    resid = [yi - fi for yi, fi in zip(y, fitted)]
    k = len(beta)
    denom = max(len(y) - k, 1)
    sigma2 = sum(w * e * e for w, e in zip(weights, resid)) / denom
    se = math.sqrt(max(xtx_inv[1][1] * sigma2, 0.0))
    return beta[1], se


def logistic_pscore(rows: list[dict[str, float]]) -> list[float]:
    x_std, _, _ = standardize(rows)
    x = [[1.0] + row for row in x_std]
    y = [r["treat"] for r in rows]
    beta = [0.0] * len(x[0])
    for _ in range(50):
        eta = [sum(b * xv for b, xv in zip(beta, row)) for row in x]
        p = [min(max(1 / (1 + math.exp(-max(min(e, 30), -30))), 1e-4), 1 - 1e-4) for e in eta]
        w = [pi * (1 - pi) for pi in p]
        z = [e + (yi - pi) / wi for e, yi, pi, wi in zip(eta, y, p, w)]
        xw = [[v * math.sqrt(wi) for v in row] for row, wi in zip(x, w)]
        zw = [zi * math.sqrt(wi) for zi, wi in zip(z, w)]
        new_beta = matvec(invert(matmul(transpose(xw), xw)), matvec(transpose(xw), zw))
        if max(abs(a - b) for a, b in zip(beta, new_beta)) < 1e-8:
            beta = new_beta
            break
        beta = new_beta
    return [min(max(1 / (1 + math.exp(-max(min(sum(b * xv for b, xv in zip(beta, row)), 30), -30))), 1e-4), 1 - 1e-4) for row in x]


def overlap_weighted_ancova(rows: list[dict[str, float]]) -> tuple[float, float]:
    ps = logistic_pscore(rows)
    weights = [(1 - p) if r["treat"] == 1 else p for r, p in zip(rows, ps)]
    x = [[1.0, r["treat"], *[r[c] for c in COVARS]] for r in rows]
    y = [r["outcome"] for r in rows]
    return ols_coef(y, x, weights)


def did_covariate_adjusted(rows: list[dict[str, float]]) -> tuple[float, float]:
    x = [[1.0, r["treat"], r["unexcused"], r["excused"], r["female"], r["black"], r["meal_assistance"]] for r in rows]
    y = [r["change"] for r in rows]
    return ols_coef(y, x)


def nearest_neighbor_matching(rows: list[dict[str, float]]) -> tuple[float, float]:
    x_std, _, _ = standardize(rows)
    treated = [(r, x) for r, x in zip(rows, x_std) if r["treat"] == 1]
    controls = [(r, x) for r, x in zip(rows, x_std) if r["treat"] == 0]
    diffs = []
    for tr, tx in treated:
        match, _ = min(controls, key=lambda cx: sum((a - b) ** 2 for a, b in zip(tx, cx[1])))
        diffs.append(tr["outcome"] - match["outcome"])
    estimate = sum(diffs) / len(diffs)
    sd = math.sqrt(sum((d - estimate) ** 2 for d in diffs) / (len(diffs) - 1)) if len(diffs) > 1 else 0.0
    return estimate, sd / math.sqrt(len(diffs))


def run() -> list[dict[str, object]]:
    out = []
    methods = [
        ("Overlap-weighted baseline-adjusted ANCOVA", overlap_weighted_ancova),
        ("Nearest-neighbor matching", nearest_neighbor_matching),
        ("Covariate-adjusted DiD/gain score", did_covariate_adjusted),
    ]
    for grade, specs in SUBJECT_SPECS.items():
        for subject, outcome, baseline in specs:
            rows = rows_for_model(grade, outcome, baseline)
            for method, fn in methods:
                est, se = fn(rows)
                out.append({
                    "model": f"G{grade} {subject}",
                    "grade": grade,
                    "subject": subject,
                    "method": method,
                    "estimate": est,
                    "se": se,
                    "n": len(rows),
                    "outcome": outcome,
                    "baseline": baseline,
                })
    return out


def write_csv(results: list[dict[str, object]]) -> None:
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["model", "grade", "subject", "method", "estimate", "se", "n", "outcome", "baseline"])
        writer.writeheader()
        for r in results:
            row = r.copy()
            row["estimate"] = fmt(row["estimate"])
            row["se"] = fmt(row["se"])
            writer.writerow(row)


def rtf_escape(text: object) -> str:
    return str(text).replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def write_rtf(results: list[dict[str, object]]) -> None:
    models = []
    for r in results:
        if r["model"] not in models:
            models.append(r["model"])
    methods = ["Overlap-weighted baseline-adjusted ANCOVA", "Nearest-neighbor matching", "Covariate-adjusted DiD/gain score"]
    lines = [r"{\rtf1\ansi\deff0", r"\paperw15840\paperh12240\landscape\margl720\margr720\margt720\margb720", r"\b Table 2--Alternative ATLAS Estimates: Overlap Weighting, Matching, and DiD\b0\par", r"\par"]
    table = [["", *models]]
    for method in methods:
        table.append([method, *[fmt(next(r for r in results if r["model"] == m and r["method"] == method)["estimate"]) for m in models]])
        table.append(["", *[f"({fmt(next(r for r in results if r['model'] == m and r['method'] == method)['se'])})" for m in models]])
    table.append(["Observations", *[str(next(r for r in results if r["model"] == m)["n"]) for m in models]])
    for row in table:
        lines.append(r"\trowd\trgaph60")
        for idx in range(len(row)):
            lines.append(rf"\cellx{2600 + idx * 850}")
        for cell in row:
            lines.append(rf"\intbl {rtf_escape(cell)}\cell")
        lines.append(r"\row")
    lines.append(r"\par Notes: Entries are estimated JMTES minus JES effects. Overlap-weighted ANCOVA uses propensity-score overlap weights and adjusts for baseline score, absences, gender, race, and meal assistance. Matching is nearest-neighbor matching with replacement on the same covariates. DiD is a covariate-adjusted gain-score model from baseline to Summer 2026. Standard errors are in parentheses.\par")
    lines.append("}")
    TABLE_RTF.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    results = run()
    write_csv(results)
    write_rtf(results)
    print(f"Wrote {RESULTS_CSV.relative_to(ROOT)}")
    print(f"Wrote {TABLE_RTF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
