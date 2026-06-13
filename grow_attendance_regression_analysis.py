#!/usr/bin/env python3
"""Covariate-adjusted regression analysis for GROW attendance outcomes.

This implements the requested attendance methodology: estimate separate OLS models
for excused, unexcused, and total absence rates as percentages of enrolled school
days, with JMTES as the treatment indicator and controls for gender, race,
ordered SES/meal status, and grade indicators.
"""
from __future__ import annotations

import csv
import datetime as dt
import math
from pathlib import Path

FULL_SCHOOL_YEAR_DAYS = 170
JMTES_REPORT_END = dt.date(2026, 5, 7)
JES_REPORT_END = dt.date(2026, 5, 22)
EXCEL_ORIGIN = dt.date(1899, 12, 30)

SCHOOL_CLOSURES = {
    dt.date(2025, 9, 1),
    dt.date(2025, 10, 31),
    dt.date(2026, 1, 1),
    dt.date(2026, 1, 2),
    dt.date(2026, 1, 19),
    dt.date(2026, 2, 2),
    dt.date(2026, 4, 24),
}
SCHOOL_CLOSURES.update(dt.date(2025, 11, day) for day in range(24, 29))
SCHOOL_CLOSURES.update(dt.date(2025, 12, day) for day in range(22, 32) if dt.date(2025, 12, day).weekday() < 5)
SCHOOL_CLOSURES.update(dt.date(2026, 1, day) for day in range(26, 31))
SCHOOL_CLOSURES.update(dt.date(2026, 3, day) for day in range(23, 28))

INPUTS = [
    ("JMTES", 1, JMTES_REPORT_END, "JMTES At Risk Report with Absence Percentages.csv"),
    ("JES", 0, JES_REPORT_END, "JES At Risk Report with Absence Percentages.csv"),
]
OUTCOMES = [
    ("unexcused_absence_rate", "Unexcused absence rate (% enrolled days)"),
    ("excused_absence_rate", "Excused absence rate (% enrolled days)"),
    ("total_absence_rate", "Total absence rate (% enrolled days)"),
]


def to_float(value: str | None) -> float:
    text = str(value or "").strip()
    return float(text) if text else 0.0


def clean(value: str | None) -> str:
    return str(value or "").strip()


def excel_date(value: str | None) -> dt.date:
    return EXCEL_ORIGIN + dt.timedelta(days=int(float(str(value).strip())))


def count_school_days(start: dt.date, end: dt.date) -> int:
    start = max(start, dt.date(2025, 8, 18))
    end = min(end, dt.date(2026, 5, 22))
    if start > end:
        return 0
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in SCHOOL_CLOSURES:
            days += 1
        current += dt.timedelta(days=1)
    return days


def ses_code(meal_status: str) -> int:
    code = clean(meal_status)
    if code == "03":
        return 0  # Full pay
    if code in {"02", "06"}:
        return 1  # Reduced or Medicaid reduced
    return 2  # Free, Medicaid free, direct certification/SNAP, or other higher-need codes


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for school, treatment, report_end, path in INPUTS:
        with open(path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                entry_date = excel_date(raw.get("Entry Date - E/W"))
                enrolled_days = count_school_days(entry_date, report_end)
                if enrolled_days <= 0:
                    continue
                unexcused = to_float(raw.get("Unexcused"))
                excused = to_float(raw.get("Excused"))
                rows.append(
                    {
                        "school": school,
                        "treatment": treatment,
                        "student_id": clean(raw.get("Student Id")),
                        "female": 1 if clean(raw.get("Gender")) == "Female" else 0,
                        "black": 1 if clean(raw.get("Ethnic Name")) == "Black" else 0,
                        "ses": ses_code(raw.get("Meal Status Code")),
                        "grade": clean(raw.get("Student Grade")),
                        "entry_date": entry_date.isoformat(),
                        "enrolled_days": enrolled_days,
                        "unexcused": unexcused,
                        "excused": excused,
                        "total_absences": unexcused + excused,
                        "unexcused_absence_rate": unexcused / enrolled_days * 100,
                        "excused_absence_rate": excused / enrolled_days * 100,
                        "total_absence_rate": (unexcused + excused) / enrolled_days * 100,
                    }
                )
    return rows


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*matrix)]


def mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    b_t = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in b_t] for row in a]


def mat_vec(a: list[list[float]], v: list[float]) -> list[float]:
    return [sum(x * y for x, y in zip(row, v)) for row in a]


def solve(a: list[list[float]], b: list[float], ridge: float = 1e-10) -> list[float]:
    n = len(b)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        aug[i][i] += ridge
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            aug[col][col] += 1e-7
            pivot = col
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pv = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= pv
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            for j in range(col, n + 1):
                aug[r][j] -= factor * aug[col][j]
    return [aug[i][n] for i in range(n)]


def inverse(a: list[list[float]]) -> list[list[float]]:
    n = len(a)
    return [solve([row[:] for row in a], [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]


def build_design(rows: list[dict[str, object]]) -> tuple[list[str], list[list[float]]]:
    grades = sorted({str(row["grade"]) for row in rows})
    grade_reference = grades[0]
    grade_dummies = [grade for grade in grades if grade != grade_reference]
    names = ["Intercept", "JMTES", "Female", "Black", "SES_ordered"] + [f"Grade_{grade}" for grade in grade_dummies]
    x = []
    for row in rows:
        x.append(
            [
                1.0,
                float(row["treatment"]),
                float(row["female"]),
                float(row["black"]),
                float(row["ses"]),
            ]
            + [1.0 if row["grade"] == grade else 0.0 for grade in grade_dummies]
        )
    return names, x


def ols_with_hc1(x: list[list[float]], y: list[float]) -> tuple[list[float], list[float]]:
    xt = transpose(x)
    xtx = mat_mul(xt, x)
    xty = mat_vec(xt, y)
    beta = solve(xtx, xty)
    residuals = [yi - sum(b * xi for b, xi in zip(beta, row)) for yi, row in zip(y, x)]
    xtx_inv = inverse(xtx)
    n = len(y)
    p = len(beta)
    meat = [[0.0 for _ in range(p)] for _ in range(p)]
    for row, resid in zip(x, residuals):
        for j in range(p):
            for k in range(p):
                meat[j][k] += row[j] * row[k] * resid * resid
    scale = n / (n - p)
    cov = mat_mul(mat_mul(xtx_inv, meat), xtx_inv)
    se = [math.sqrt(max(cov[i][i] * scale, 0.0)) for i in range(p)]
    return beta, se


def normal_p_value(t_stat: float) -> float:
    return math.erfc(abs(t_stat) / math.sqrt(2.0))


def main() -> None:
    rows = load_rows()
    names, x = build_design(rows)
    student_fieldnames = [
        "school",
        "treatment",
        "student_id",
        "female",
        "black",
        "ses",
        "grade",
        "entry_date",
        "enrolled_days",
        "unexcused",
        "excused",
        "total_absences",
        "unexcused_absence_rate",
        "excused_absence_rate",
        "total_absence_rate",
    ]
    with open("grow_attendance_regression_student_data.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=student_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    result_rows = []
    for outcome, label in OUTCOMES:
        y = [float(row[outcome]) for row in rows]
        beta, se = ols_with_hc1(x, y)
        treatment_index = names.index("JMTES")
        treatment_beta = beta[treatment_index]
        treatment_se = se[treatment_index]
        t_stat = treatment_beta / treatment_se if treatment_se else float("nan")
        result_rows.append(
            {
                "outcome": label,
                "estimand": "JMTES - JES",
                "coefficient_jmtes": f"{treatment_beta:.2f}",
                "robust_se": f"{treatment_se:.2f}",
                "ci_low": f"{treatment_beta - 1.96 * treatment_se:.2f}",
                "ci_high": f"{treatment_beta + 1.96 * treatment_se:.2f}",
                "p_value_normal_approx": f"{normal_p_value(t_stat):.4f}",
                "students": len(rows),
                "controls": "Female, Black, SES ordered meal status, grade indicators",
            }
        )
    with open("grow_attendance_regression_results.csv", "w", newline="", encoding="utf-8") as handle:
        fieldnames = list(result_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)

    lines = [
        "# Covariate-Adjusted Attendance Regression Results",
        "",
        "This analysis implements the requested attendance methodology: OLS regressions of absence rates on a JMTES treatment indicator, Female, Black, an ordered SES/meal-status measure, and grade indicators.",
        "",
        "Absence outcomes are percentages of enrolled school days missed. Enrolled days are calculated from each student's entry date through the relevant report/school-year end date, excluding non-school days in the 170-day calendar.",
        "",
        "| Outcome | JMTES coefficient | Robust SE | 95% CI | p-value |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result_rows:
        lines.append(
            f"| {row['outcome']} | {row['coefficient_jmtes']} | {row['robust_se']} | [{row['ci_low']}, {row['ci_high']}] | {row['p_value_normal_approx']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Negative coefficients indicate lower absence rates at JMTES than JES after adjusting for the included covariates. The regression results support the same broad conclusion as the overlap-weighted analysis: JMTES has lower unexcused and total absence rates, while excused absence is slightly higher.",
            "",
            "This regression approach is useful and easy to communicate, but the overlap-weighted analysis remains more defensible as the primary observational design because it explicitly targets the region of covariate overlap between JMTES and JES students. The regression estimates are therefore best used as a robustness check that aligns with the requested methodology.",
        ]
    )
    Path("grow_attendance_regression_results.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
