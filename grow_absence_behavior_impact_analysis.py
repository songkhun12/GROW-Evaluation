#!/usr/bin/env python3
"""Estimate GROW impacts comparing JMTES (treatment) with JES (control).

The source At Risk report exports already contain absence counts adjusted to a
170-day school year. This script adds behavior outcomes adjusted to the same
170-day basis, estimates several observational treatment-control contrasts, and
writes reviewable CSV/Markdown outputs.
"""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from pathlib import Path

FULL_SCHOOL_YEAR_DAYS = 170
JMTES_REPORT_DAYS = 159
JES_REPORT_DAYS = 170
BOOTSTRAP_REPS = 100
RANDOM_SEED = 20260612

INPUTS = [
    {
        "school": "JMTES",
        "treatment": 1,
        "report_days": JMTES_REPORT_DAYS,
        "path": "JMTES At Risk Report with Absence Percentages.csv",
    },
    {
        "school": "JES",
        "treatment": 0,
        "report_days": JES_REPORT_DAYS,
        "path": "JES At Risk Report with Absence Percentages.csv",
    },
]

OUTCOME_LABELS = {
    "excused_absences_170": "Excused absences per 170-day year",
    "unexcused_absences_170": "Unexcused absences per 170-day year",
    "total_absences_170": "Total absences per 170-day year",
    "excused_absence_pct": "Excused absence % of 170-day year",
    "unexcused_absence_pct": "Unexcused absence % of 170-day year",
    "total_absence_pct": "Total absence % of 170-day year",
    "school_behavior_referrals_170": "School behavior referrals (unweighted count) per 170-day year",
    "bus_behavior_referrals_170": "Bus behavior referrals (unweighted count) per 170-day year",
    "school_behavior_severity_points_170": "School behavior severity points per 170-day year",
    "bus_behavior_severity_points_170": "Bus behavior severity points per 170-day year",
    "school_highest_behavior_severity": "Highest school behavior severity category (0-4)",
    "bus_highest_behavior_severity": "Highest bus behavior severity category (0-3)",
}

PRIMARY_OUTCOMES = [
    "excused_absence_pct",
    "unexcused_absence_pct",
    "total_absence_pct",
    "school_behavior_severity_points_170",
    "bus_behavior_severity_points_170",
    "school_highest_behavior_severity",
    "bus_highest_behavior_severity",
]

ALL_OUTCOMES = list(OUTCOME_LABELS)


def to_float(value: str | None) -> float:
    text = str(value or "").strip()
    return float(text) if text else 0.0


def clean(value: str | None) -> str:
    return str(value or "").strip()


def meal_group(code: str) -> str:
    return "Full Pay" if clean(code) == "03" else "Free/Reduced/Direct/Medicaid"


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in INPUTS:
        with open(spec["path"], newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                report_days = int(spec["report_days"])
                annualizer = FULL_SCHOOL_YEAR_DAYS / report_days
                l1 = to_float(raw.get("L-1"))
                l2 = to_float(raw.get("L-2"))
                l3 = to_float(raw.get("L-3"))
                l4 = to_float(raw.get("L-4"))
                local = to_float(raw.get("Local"))
                bus1 = to_float(raw.get("Transportation 1"))
                bus2 = to_float(raw.get("Transportation 2"))
                bus3 = to_float(raw.get("Transportation 3"))
                total_absences_170 = to_float(raw.get("Total Absences Adjusted to 170-Day Year"))
                school_highest_severity = 4 if l4 > 0 else 3 if l3 > 0 else 2 if l2 > 0 else 1 if l1 > 0 else 0
                bus_highest_severity = 3 if bus3 > 0 else 2 if bus2 > 0 else 1 if (local + bus1) > 0 else 0
                row = {
                    "school": spec["school"],
                    "treatment": int(spec["treatment"]),
                    "report_days": report_days,
                    "student_id": clean(raw.get("Student Id")),
                    "grade": clean(raw.get("Student Grade")),
                    "gender": clean(raw.get("Gender")),
                    "ethnicity": clean(raw.get("Ethnic Name")),
                    "age": to_float(raw.get("Student Age")),
                    "meal_code": clean(raw.get("Meal Status Code")),
                    "meal_group": meal_group(raw.get("Meal Status Code")),
                    "entry_code": clean(raw.get("Entry Code - E/W")),
                    "excused_absences_170": to_float(raw.get("Excused Absences Adjusted to 170-Day Year")),
                    "unexcused_absences_170": to_float(raw.get("Unexcused Absences Adjusted to 170-Day Year")),
                    "total_absences_170": total_absences_170,
                    "excused_absence_pct": to_float(raw.get("Excused Absence %")),
                    "unexcused_absence_pct": to_float(raw.get("Unexcused Absence %")),
                    "total_absence_pct": to_float(raw.get("Total Absence %")),
                    "school_behavior_referrals_170": (l1 + l2 + l3 + l4) * annualizer,
                    "bus_behavior_referrals_170": (local + bus1 + bus2 + bus3) * annualizer,
                    "school_behavior_severity_points_170": (l1 + 2 * l2 + 3 * l3 + 4 * l4) * annualizer,
                    "bus_behavior_severity_points_170": ((local + bus1) + 2 * bus2 + 3 * bus3) * annualizer,
                    "school_highest_behavior_severity": school_highest_severity,
                    "bus_highest_behavior_severity": bus_highest_severity,
                }
                rows.append(row)
    return rows


def categories(rows: list[dict[str, object]], field: str) -> list[str]:
    return sorted({str(row[field]) for row in rows})


def build_feature_spec(rows: list[dict[str, object]]) -> dict[str, list[str]]:
    return {
        "grade": categories(rows, "grade"),
        "gender": categories(rows, "gender"),
        "ethnicity": categories(rows, "ethnicity"),
        "meal_code": categories(rows, "meal_code"),
        "entry_code": categories(rows, "entry_code"),
    }


def feature_names(spec: dict[str, list[str]]) -> list[str]:
    names = ["Intercept", "age_centered"]
    for field in ["grade", "gender", "ethnicity", "meal_code", "entry_code"]:
        for level in spec[field][1:]:
            names.append(f"{field}={level}")
    return names


def feature_vector(row: dict[str, object], spec: dict[str, list[str]], age_mean: float) -> list[float]:
    values = [1.0, float(row["age"]) - age_mean]
    for field in ["grade", "gender", "ethnicity", "meal_code", "entry_code"]:
        row_level = str(row[field])
        for level in spec[field][1:]:
            values.append(1.0 if row_level == level else 0.0)
    return values


def transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*matrix)]


def mat_vec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def solve_linear(a: list[list[float]], b: list[float], ridge: float = 1e-8) -> list[float]:
    n = len(b)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        aug[i][i] += ridge
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            aug[col][col] += 1e-6
            pivot = col
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pivot_value = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= pivot_value
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor == 0:
                continue
            for j in range(col, n + 1):
                aug[r][j] -= factor * aug[col][j]
    return [aug[i][n] for i in range(n)]


def ols_fit(x: list[list[float]], y: list[float], ridge: float = 1e-8) -> list[float]:
    xt = transpose(x)
    xtx = [[sum(xt_i[k] * xt_j[k] for k in range(len(x))) for xt_j in xt] for xt_i in xt]
    xty = [sum(xt_i[k] * y[k] for k in range(len(x))) for xt_i in xt]
    return solve_linear(xtx, xty, ridge=ridge)


def logistic_fit(x: list[list[float]], y: list[int], ridge: float = 0.01, max_iter: int = 25) -> list[float]:
    p = len(x[0])
    beta = [0.0] * p
    for _ in range(max_iter):
        eta = [max(-30.0, min(30.0, sum(beta[j] * row[j] for j in range(p)))) for row in x]
        mu = [1.0 / (1.0 + math.exp(-e)) for e in eta]
        gradient = [sum((y[i] - mu[i]) * x[i][j] for i in range(len(x))) - ridge * beta[j] for j in range(p)]
        hessian = []
        for j in range(p):
            hessian_row = []
            for k in range(p):
                value = sum(mu[i] * (1.0 - mu[i]) * x[i][j] * x[i][k] for i in range(len(x)))
                if j == k:
                    value += ridge
                hessian_row.append(value)
            hessian.append(hessian_row)
        step = solve_linear(hessian, gradient, ridge=1e-8)
        beta = [beta[j] + step[j] for j in range(p)]
        if max(abs(s) for s in step) < 1e-6:
            break
    return beta


def predict_logit(x: list[list[float]], beta: list[float]) -> list[float]:
    preds = []
    for row in x:
        eta = max(-30.0, min(30.0, sum(b * v for b, v in zip(beta, row))))
        preds.append(1.0 / (1.0 + math.exp(-eta)))
    return preds


def weighted_mean(values: list[float], weights: list[float]) -> float:
    total_weight = sum(weights)
    return sum(v * w for v, w in zip(values, weights)) / total_weight if total_weight else float("nan")


def unadjusted_effect(rows: list[dict[str, object]], outcome: str) -> float:
    treated = [float(row[outcome]) for row in rows if row["treatment"] == 1]
    control = [float(row[outcome]) for row in rows if row["treatment"] == 0]
    return sum(treated) / len(treated) - sum(control) / len(control)


def overlap_effect(rows: list[dict[str, object]], outcome: str, ps: list[float]) -> float:
    treated_values, treated_weights, control_values, control_weights = [], [], [], []
    for row, score in zip(rows, ps):
        if row["treatment"] == 1:
            treated_values.append(float(row[outcome]))
            treated_weights.append(1.0 - score)
        else:
            control_values.append(float(row[outcome]))
            control_weights.append(score)
    return weighted_mean(treated_values, treated_weights) - weighted_mean(control_values, control_weights)


def regression_effect(rows: list[dict[str, object]], outcome: str, x_covariates: list[list[float]]) -> float:
    x = []
    y = []
    for row, covars in zip(rows, x_covariates):
        x.append([1.0, float(row["treatment"])] + covars[1:])
        y.append(float(row[outcome]))
    beta = ols_fit(x, y, ridge=1e-7)
    return beta[1]


def exact_stratified_effect(rows: list[dict[str, object]], outcome: str) -> tuple[float, int, int]:
    cells: dict[tuple[str, str, str, str], dict[int, list[float]]] = defaultdict(lambda: {0: [], 1: []})
    for row in rows:
        key = (str(row["grade"]), str(row["gender"]), str(row["ethnicity"]), str(row["meal_group"]))
        cells[key][int(row["treatment"])].append(float(row[outcome]))
    weighted_diffs = []
    treated_in_overlap = 0
    treated_total = sum(1 for row in rows if row["treatment"] == 1)
    for groups in cells.values():
        if groups[0] and groups[1]:
            n_treated = len(groups[1])
            treated_in_overlap += n_treated
            diff = sum(groups[1]) / len(groups[1]) - sum(groups[0]) / len(groups[0])
            weighted_diffs.append((n_treated, diff))
    effect = sum(w * d for w, d in weighted_diffs) / sum(w for w, _ in weighted_diffs)
    return effect, treated_in_overlap, treated_total


def percentile(values: list[float], pct: float) -> float:
    sorted_values = sorted(values)
    if not sorted_values:
        return float("nan")
    position = (len(sorted_values) - 1) * pct
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[int(position)]
    return sorted_values[lower] * (upper - position) + sorted_values[upper] * (position - lower)


def bootstrap_primary(rows: list[dict[str, object]], spec: dict[str, list[str]], outcomes: list[str]) -> dict[str, tuple[float, float]]:
    rng = random.Random(RANDOM_SEED)
    results = {outcome: [] for outcome in outcomes}
    n = len(rows)
    for _ in range(BOOTSTRAP_REPS):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        if len({row["treatment"] for row in sample}) < 2:
            continue
        age_mean = sum(float(row["age"]) for row in sample) / len(sample)
        x = [feature_vector(row, spec, age_mean) for row in sample]
        y = [int(row["treatment"]) for row in sample]
        try:
            beta = logistic_fit(x, y)
            ps = [min(0.99, max(0.01, value)) for value in predict_logit(x, beta)]
            for outcome in outcomes:
                results[outcome].append(overlap_effect(sample, outcome, ps))
        except Exception:
            continue
    return {outcome: (percentile(vals, 0.025), percentile(vals, 0.975)) for outcome, vals in results.items()}


def standardized_difference(rows: list[dict[str, object]], feature_index: int, x: list[list[float]], weights: list[float] | None = None) -> float:
    treated = []
    control = []
    tw = []
    cw = []
    for i, row in enumerate(rows):
        value = x[i][feature_index]
        weight = weights[i] if weights is not None else 1.0
        if row["treatment"] == 1:
            treated.append(value)
            tw.append(weight)
        else:
            control.append(value)
            cw.append(weight)
    mt = weighted_mean(treated, tw)
    mc = weighted_mean(control, cw)
    vt = weighted_mean([(v - mt) ** 2 for v in treated], tw)
    vc = weighted_mean([(v - mc) ** 2 for v in control], cw)
    pooled = math.sqrt((vt + vc) / 2.0)
    return 0.0 if pooled == 0 else (mt - mc) / pooled


def write_csv(path: str, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fmt_num(value: float) -> str:
    return f"{value:.2f}"


def main() -> None:
    rows = load_rows()
    spec = build_feature_spec(rows)
    age_mean = sum(float(row["age"]) for row in rows) / len(rows)
    x = [feature_vector(row, spec, age_mean) for row in rows]
    treatment = [int(row["treatment"]) for row in rows]
    ps_beta = logistic_fit(x, treatment)
    ps = [min(0.99, max(0.01, value)) for value in predict_logit(x, ps_beta)]

    primary_ci = bootstrap_primary(rows, spec, PRIMARY_OUTCOMES)

    analysis_rows = []
    for outcome in ALL_OUTCOMES:
        unadj = unadjusted_effect(rows, outcome)
        overlap = overlap_effect(rows, outcome, ps)
        regression = regression_effect(rows, outcome, x)
        exact, overlap_n, treated_n = exact_stratified_effect(rows, outcome)
        ci_low, ci_high = primary_ci.get(outcome, (float("nan"), float("nan")))
        analysis_rows.append(
            {
                "outcome": OUTCOME_LABELS[outcome],
                "estimand": "JMTES - JES",
                "primary_overlap_weighted_effect": fmt_num(overlap),
                "primary_bootstrap_ci_low": "" if math.isnan(ci_low) else fmt_num(ci_low),
                "primary_bootstrap_ci_high": "" if math.isnan(ci_high) else fmt_num(ci_high),
                "unadjusted_difference": fmt_num(unadj),
                "covariate_adjusted_regression_difference": fmt_num(regression),
                "exact_stratified_difference": fmt_num(exact),
                "treated_students_in_exact_overlap": overlap_n,
                "total_treated_students": treated_n,
            }
        )

    write_csv(
        "grow_absence_behavior_impact_results.csv",
        analysis_rows,
        [
            "outcome",
            "estimand",
            "primary_overlap_weighted_effect",
            "primary_bootstrap_ci_low",
            "primary_bootstrap_ci_high",
            "unadjusted_difference",
            "covariate_adjusted_regression_difference",
            "exact_stratified_difference",
            "treated_students_in_exact_overlap",
            "total_treated_students",
        ],
    )

    balance_rows = []
    names = feature_names(spec)
    overlap_weights = [(1 - score) if row["treatment"] == 1 else score for row, score in zip(rows, ps)]
    for idx, name in enumerate(names[1:], start=1):
        balance_rows.append(
            {
                "covariate": name,
                "unweighted_standardized_difference": fmt_num(standardized_difference(rows, idx, x)),
                "overlap_weighted_standardized_difference": fmt_num(standardized_difference(rows, idx, x, overlap_weights)),
            }
        )
    write_csv(
        "grow_absence_behavior_balance.csv",
        balance_rows,
        ["covariate", "unweighted_standardized_difference", "overlap_weighted_standardized_difference"],
    )

    school_summary = []
    for school in ["JMTES", "JES"]:
        school_rows = [row for row in rows if row["school"] == school]
        summary = {
            "school": school,
            "treatment_status": "Treatment" if school == "JMTES" else "Control",
            "students": len(school_rows),
            "report_school_days": school_rows[0]["report_days"],
            "full_school_year_days": FULL_SCHOOL_YEAR_DAYS,
        }
        for outcome in PRIMARY_OUTCOMES:
            summary[OUTCOME_LABELS[outcome]] = fmt_num(sum(float(row[outcome]) for row in school_rows) / len(school_rows))
        school_summary.append(summary)
    write_csv("grow_absence_behavior_school_summary.csv", school_summary, list(school_summary[0]))

    max_unweighted = max(abs(float(row["unweighted_standardized_difference"])) for row in balance_rows)
    max_weighted = max(abs(float(row["overlap_weighted_standardized_difference"])) for row in balance_rows)

    primary_table = [row for row in analysis_rows if row["outcome"] in [OUTCOME_LABELS[o] for o in PRIMARY_OUTCOMES]]
    md_lines = [
        "# GROW Impact Analysis: JMTES Treatment vs JES Control",
        "",
        "## Design and primary estimand",
        "",
        "This analysis treats JMTES as the GROW treatment school and JES as the comparison school. The primary analysis is an overlap-weighted propensity-score comparison of student outcomes, adjusting for grade, gender, ethnicity, age, meal-status code, and entry code. The estimated effect is `JMTES - JES`, so negative values indicate lower absences or referrals at JMTES.",
        "",
        "JMTES data were pulled on May 7, 2026, before the end of the 170-day school year. JMTES absence and behavior counts are therefore scaled from 159 report school days to a 170-day school-year rate. JES was pulled after the end of the year and uses 170 report school days.",
        "",
        "The primary overlap-weighted design is the most defensible option available because the data are observational and cross-sectional, with one treatment school and one control school. Overlap weighting emphasizes comparable students across the two schools and improves balance on measured covariates, but it cannot remove unmeasured school-level confounding.",
        "",
        "Behavior outcomes use the At Risk Report code definitions and now account for severity instead of assuming every referral is equal. School behavior severity points weight L-1 through L-4 referrals as 1, 2, 3, and 4 points, respectively. Bus behavior severity points weight Local/Transportation 1 as 1 point, Transportation 2 as 2 points, and Transportation 3 as 3 points. The analysis also reports each student's highest observed severity category as an ordered outcome. JMTES behavior counts are scaled from 159 report days to the 170-day school-year rate.",
        "",
        "## Sample and balance",
        "",
        f"- JMTES treatment students: {sum(1 for row in rows if row['treatment'] == 1)}",
        f"- JES control students: {sum(1 for row in rows if row['treatment'] == 0)}",
        f"- Largest absolute standardized covariate difference before weighting: {max_unweighted:.2f}",
        f"- Largest absolute standardized covariate difference after overlap weighting: {max_weighted:.2f}",
        "",
        "## Primary and robustness results",
        "",
        "| Outcome | Primary overlap-weighted effect | 95% bootstrap CI | Unadjusted | Regression adjusted | Exact-stratified |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in primary_table:
        ci = f"[{row['primary_bootstrap_ci_low']}, {row['primary_bootstrap_ci_high']}]"
        md_lines.append(
            f"| {row['outcome']} | {row['primary_overlap_weighted_effect']} | {ci} | {row['unadjusted_difference']} | {row['covariate_adjusted_regression_difference']} | {row['exact_stratified_difference']} |"
        )
    md_lines.extend(
        [
            "",
            "## Interpretation guidance",
            "",
            "- The absence percentage outcomes are percentage-point differences in the share of the 170-day year absent.",
            "- The primary behavior outcomes are severity-point differences per 170-day school year and highest-severity-category differences, so more serious referrals receive more weight than less serious referrals.",
            "- Because treatment is assigned at the school level and only two schools are observed, these estimates should be interpreted as adjusted treatment-control contrasts rather than definitive randomized causal effects.",
            "- The exact-stratified analysis matches cells defined by grade, gender, ethnicity, and meal group and is included as a robustness check for observable-composition differences.",
            "",
        ]
    )
    Path("grow_absence_behavior_impact_analysis.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
