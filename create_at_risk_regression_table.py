#!/usr/bin/env python3
"""Create all-grade, all-subject regression outputs from merged At-Risk CSV files."""
from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import NormalDist
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
RESULTS_CSV = ROOT / "at_risk_atlas_regression_results.csv"
RTF = ROOT / "at_risk_atlas_regression_table_AER.rtf"

GRADE_FILES = {
    "K": (
        ROOT / "Kindergarten/JES Atlas Report - Kindergarten - Merged At Risk.csv",
        ROOT / "Kindergarten/JMTES Atlas Report - Kindergarten - Merged At Risk.csv",
    ),
    "1": (
        ROOT / "Grade 1/JES Atlas Report - Grade 1 - Merged At Risk.csv",
        ROOT / "Grade 1/JMTES Atlas Report - Grade 1 - Merged At Risk.csv",
    ),
    "2": (
        ROOT / "Grade 2/JES Atlas Report - Grade 2 - Merged At Risk.csv",
        ROOT / "Grade 2/JMTES Atlas Report - Grade 2 - Merged At Risk.csv",
    ),
    "3": (
        ROOT / "Grade 3/JES Atlas Report - Grade 3 - Merged At Risk.csv",
        ROOT / "Grade 3/JMTES Atlas Report - Grade 3 - Merged At Risk.csv",
    ),
    "4": (
        ROOT / "Grade 4/JES Atlas Report - Grade 4 - Merged At Risk.csv",
        ROOT / "Grade 4/JMTES Atlas Report - Grade 4 - Current Year - Merged At Risk.csv",
    ),
    "5": (
        ROOT / "Grade 5/JES Atlas Report - Grade 5 - Merged At Risk.csv",
        ROOT / "Grade 5/JMTES Atlas Report - Grade 5 - Current Year - Merged At Risk.csv",
    ),
}

SUBJECT_SPECS = {
    "K": [("ELA", "ELA Sum 2026", "ELA Winter 2025"), ("Math", "Math Sum 2026", "Math Winter 2025")],
    "1": [("ELA", "ELA Sum 2026", "ELA Sum 2025"), ("Math", "Math Sum 2026", "Math Sum 2025")],
    "2": [("ELA", "ELA Sum 2026", "ELA Sum 2025"), ("Math", "Math Sum 2026", "Math Sum 2025")],
    "3": [("ELA", "ELA Sum 2026", "ELA Sum 2025"), ("Math", "Math Sum 2026", "Math Sum 2025"), ("Science", "Science Sum 2026", "Science Winter 2025")],
    "4": [("ELA", "ELA Sum 2026", "ELA Winter 2025"), ("Math", "Math Sum 2026", "Math Winter 2025"), ("Science", "Science Sum 2026", "Science Winter 2025")],
    "5": [("ELA", "ELA Sum 2026", "ELA Winter 2025"), ("Math", "Math Sum 2026", "Math Winter 2025"), ("Science", "Science Sum 2026", "Science Winter 2025")],
}

VARIABLE_LABELS = {
    "JMTES": "JMTES treatment school",
    "baseline": "Baseline score",
    "unexcused": "Unexcused absences",
    "excused": "Excused absences",
    "female": "Female",
    "black": "Black",
    "meal_assistance": "Meal assistance",
}


def read_merged_csv(path: Path, school: str) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    header_idx = next(i for i, row in enumerate(rows) if "At Risk - State Report Id" in row)
    header = rows[header_idx]
    records = []
    for row in rows[header_idx + 1 :]:
        if not any(cell.strip() for cell in row):
            continue
        row = row + [""] * (len(header) - len(row))
        record = dict(zip(header, row))
        record["school"] = school
        record["JMTES"] = 1.0 if school == "JMTES" else 0.0
        records.append(record)
    return records


def to_float(value: str) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        out = float(str(value).strip())
        return out if out >= 900 else None
    except ValueError:
        return None


def absence_float(value: str) -> float:
    try:
        return float(str(value).strip()) if str(value).strip() else 0.0
    except ValueError:
        return 0.0


def indicator(value: str, target: str) -> float:
    return 1.0 if str(value).strip().lower() == target.lower() else 0.0


def meal_assistance(value: str) -> float:
    return 1.0 if str(value).strip() in {"02", "04", "05", "06"} else 0.0


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*matrix)]


def matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def matvec(a: list[list[float]], x: list[float]) -> list[float]:
    return [sum(v * xv for v, xv in zip(row, x)) for row in a]


def invert(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-10:
            raise ValueError("Singular matrix")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        div = aug[col][col]
        aug[col] = [v / div for v in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [v - factor * p for v, p in zip(aug[row], aug[col])]
    return [row[n:] for row in aug]


def ols_hc1(y: list[float], x: list[list[float]], names: list[str]) -> dict[str, object]:
    n = len(y)
    k = len(names)
    xt = transpose(x)
    xtx_inv = invert(matmul(xt, x))
    beta = matvec(xtx_inv, matvec(xt, y))
    fitted = matvec(x, beta)
    resid = [yi - fi for yi, fi in zip(y, fitted)]
    meat = [[0.0 for _ in range(k)] for _ in range(k)]
    for xi, ei in zip(x, resid):
        for a in range(k):
            for b in range(k):
                meat[a][b] += xi[a] * xi[b] * ei * ei
    scale = n / (n - k)
    vcov = matmul(matmul(xtx_inv, meat), xtx_inv)
    vcov = [[scale * val for val in row] for row in vcov]
    se = [math.sqrt(max(vcov[i][i], 0.0)) for i in range(k)]
    mean_y = sum(y) / n
    tss = sum((yi - mean_y) ** 2 for yi in y)
    rss = sum(ei * ei for ei in resid)
    r2 = 1 - rss / tss if tss else float("nan")
    normal = NormalDist()
    pvals = [2 * (1 - normal.cdf(abs(b / s))) if s > 0 else float("nan") for b, s in zip(beta, se)]
    return {"n": n, "r2": r2, "coef": dict(zip(names, beta)), "se": dict(zip(names, se)), "p": dict(zip(names, pvals))}


def model_data(grade: str, subject: str, outcome_col: str, baseline_col: str) -> tuple[list[float], list[list[float]]]:
    jes_file, jmtes_file = GRADE_FILES[grade]
    records = read_merged_csv(jes_file, "JES") + read_merged_csv(jmtes_file, "JMTES")
    y: list[float] = []
    x: list[list[float]] = []
    for row in records:
        outcome = to_float(row.get(outcome_col, ""))
        baseline = to_float(row.get(baseline_col, ""))
        if outcome is None or baseline is None:
            continue
        y.append(outcome)
        x.append([
            1.0,
            row["JMTES"],
            baseline,
            absence_float(row.get("At Risk - Unexcused", "")),
            absence_float(row.get("At Risk - Excused", "")),
            indicator(row.get("At Risk - Gender", ""), "Female"),
            indicator(row.get("At Risk - Ethnic Name", ""), "Black"),
            meal_assistance(row.get("At Risk - Meal Status Code", "")),
        ])
    return y, x


def stars(p: float) -> str:
    if math.isnan(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def fmt(value: float) -> str:
    return "" if math.isnan(value) else f"{value:.3f}"


def run_models() -> list[dict[str, object]]:
    results = []
    names = ["Intercept", "JMTES", "baseline", "unexcused", "excused", "female", "black", "meal_assistance"]
    for grade, specs in SUBJECT_SPECS.items():
        for subject, outcome, baseline in specs:
            y, x = model_data(grade, subject, outcome, baseline)
            fit = ols_hc1(y, x, names)
            fit.update({"grade": grade, "subject": subject, "outcome": outcome, "baseline_col": baseline, "model": f"G{grade} {subject}"})
            results.append(fit)
    return results


def write_results_csv(results: list[dict[str, object]]) -> None:
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["model", "grade", "subject", "outcome", "baseline", "variable", "coefficient", "robust_se", "p_value", "n", "r_squared"])
        for result in results:
            for var in VARIABLE_LABELS:
                writer.writerow([
                    result["model"], result["grade"], result["subject"], result["outcome"], result["baseline_col"], VARIABLE_LABELS[var],
                    fmt(result["coef"][var]), fmt(result["se"][var]), fmt(result["p"][var]), result["n"], fmt(result["r2"]),
                ])


def table_rows(results: list[dict[str, object]]) -> list[list[str]]:
    rows = [["", *[r["model"] for r in results]]]
    for var, label in VARIABLE_LABELS.items():
        rows.append([label, *[fmt(r["coef"][var]) + stars(r["p"][var]) for r in results]])
        rows.append(["", *[f"({fmt(r['se'][var])})" for r in results]])
    rows.append(["Observations", *[str(r["n"]) for r in results]])
    rows.append(["R-squared", *[fmt(r["r2"]) for r in results]])
    return rows


def rtf_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def write_rtf(results: list[dict[str, object]]) -> None:
    rows = table_rows(results)
    lines = [
        r"{\rtf1\ansi\deff0",
        r"\paperw15840\paperh12240\landscape\margl720\margr720\margt720\margb720",
        r"\b Table 1--At-Risk Covariate-Adjusted ATLAS Regression Results\b0\par",
        r"\par",
    ]
    for row in rows:
        lines.append(r"\trowd\trgaph60")
        for idx in range(len(row)):
            lines.append(rf"\cellx{1800 + idx * 850}")
        for cell in row:
            lines.append(rf"\intbl {rtf_escape(cell)}\cell")
        lines.append(r"\row")
    lines.extend([
        r"\par",
        r"Notes: Each column is a separate OLS model. The dependent variable is the Summer 2026 ATLAS score for the indicated grade and subject. Robust HC1 standard errors are in parentheses. All models adjust for the listed baseline score, absences, gender, race, and meal assistance. * p<0.10, ** p<0.05, *** p<0.01.\par",
        "}",
    ])
    RTF.write_text("\n".join(lines), encoding="utf-8")

def main() -> None:
    results = run_models()
    write_results_csv(results)
    write_rtf(results)
    print(f"Wrote {RESULTS_CSV.relative_to(ROOT)}")
    print(f"Wrote {RTF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
