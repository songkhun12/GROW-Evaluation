#!/usr/bin/env python3
"""Run GROW ATLAS impact analyses from merged at-risk grade files.

The script intentionally uses only the Python standard library so it can run in the
current repository environment. It estimates three requested analyses for every
available grade-subject cell:
  1. overlap-weighted propensity score regression with baseline and covariates,
  2. propensity-score caliper matching followed by baseline/covariate regression,
  3. DiD-style gain-score regression with baseline and covariates.
"""

import csv
import glob
import html
import math
import statistics
from pathlib import Path

GRADES = ["Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
SUBJECTS = ["ELA", "Math", "Science"]
OUTDIR = Path("ATLAS GROW Impact Analysis")


def read_csv_smart(path, school, grade_label):
    """Read merged at-risk files, including JMTES files with a banner header row."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header_i = 0
    for i, row in enumerate(rows[:6]):
        if "Grade" in row and any("Student" in cell or "ID Number" in cell for cell in row):
            header_i = i
            break
    headers = rows[header_i]
    output = []
    for row in rows[header_i + 1 :]:
        if not any(cell.strip() for cell in row):
            continue
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))
        rec = {headers[i]: row[i] for i in range(len(headers))}
        rec["school"] = school
        rec["treat"] = 1 if school == "JMTES" else 0
        rec["grade_file"] = grade_label
        output.append(rec)
    return output


def numeric_score(value):
    try:
        score = float(str(value).strip())
        return score if score >= 900 else None
    except Exception:
        return None


def numeric_or_none(value):
    try:
        return float(str(value).strip())
    except Exception:
        return None


def grade_files(grade, school):
    files = sorted(glob.glob(f"{grade}/{school}*Merged At Risk.csv"))
    if len(files) > 1:
        current_year = [f for f in files if "Current Year" in f]
        return current_year or files[:1]
    return files


def build_analysis_records():
    records = []
    for grade in GRADES:
        for school in ["JMTES", "JES"]:
            files = grade_files(grade, school)
            if not files:
                continue
            for raw in read_csv_smart(files[0], school, grade):
                for subject in SUBJECTS:
                    post = numeric_score(raw.get(f"{subject} Sum 2026", ""))
                    if post is None:
                        continue
                    baseline = (
                        numeric_score(raw.get(f"{subject} Sum 2025", ""))
                        or numeric_score(raw.get(f"{subject} Winter 2025", ""))
                        or numeric_score(raw.get(f"{subject} Fall 2025", ""))
                    )
                    if baseline is None:
                        continue
                    gender = raw.get("At Risk - Gender", "").strip().lower()
                    race = raw.get("At Risk - Ethnic Name", "").strip().lower()
                    age = numeric_or_none(raw.get("At Risk - Student Age", ""))
                    if age is None:
                        continue
                    records.append(
                        {
                            "grade": grade,
                            "subject": subject,
                            "school": school,
                            "treat": 1 if school == "JMTES" else 0,
                            "post": post,
                            "baseline": baseline,
                            "gain": post - baseline,
                            "female": 1 if gender.startswith("f") else 0,
                            "black": 1 if race == "black" else 0,
                            "age": age,
                            "meal": raw.get("At Risk - Meal Status Code", "").strip() or "Missing",
                            "entry": raw.get("At Risk - Entry Code - E/W", "").strip() or "Missing",
                        }
                    )
    return records


def inverse(matrix):
    n = len(matrix)
    aug = [list(map(float, matrix[i])) + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(aug[r][i]))
        if abs(aug[pivot][i]) < 1e-10:
            raise ValueError("singular matrix")
        aug[i], aug[pivot] = aug[pivot], aug[i]
        divisor = aug[i][i]
        aug[i] = [value / divisor for value in aug[i]]
        for r in range(n):
            if r == i:
                continue
            factor = aug[r][i]
            aug[r] = [aug[r][c] - factor * aug[i][c] for c in range(2 * n)]
    return [row[n:] for row in aug]


def candidate_covariates(rows):
    covariates = ["treat", "baseline", "female", "black", "age"]
    for prefix, key in [("meal:", "meal"), ("entry:", "entry")]:
        vals = sorted(set(r[key] for r in rows))
        covariates.extend(prefix + v for v in vals[1:])
    return covariates


def value_for(row, variable):
    if variable.startswith("meal:"):
        return 1.0 if row["meal"] == variable[5:] else 0.0
    if variable.startswith("entry:"):
        return 1.0 if row["entry"] == variable[6:] else 0.0
    return float(row[variable])


def design_matrix(rows, outcome, covariates, weight=None):
    y, X, w = [], [], []
    for row in rows:
        if row.get(outcome) is None:
            continue
        try:
            x_row = [1.0] + [value_for(row, var) for var in covariates]
        except Exception:
            continue
        y.append(float(row[outcome]))
        X.append(x_row)
        w.append(float(row.get(weight, 1.0)) if weight else 1.0)
    return y, X, w


def drop_unusable_columns(y, X, w, covariates):
    names = ["Intercept"] + covariates
    keep = [0]
    for j in range(1, len(names)):
        column = [row[j] for row in X]
        if max(column) - min(column) > 1e-12:
            keep.append(j)
    kept_names = [names[j] for j in keep]
    kept_X = [[row[j] for j in keep] for row in X]

    # Iteratively remove the last non-treatment column if exact collinearity remains.
    while True:
        k = len(kept_names)
        if len(y) <= k:
            return None, None
        xtwx = [[sum(w[i] * kept_X[i][a] * kept_X[i][b] for i in range(len(y))) for b in range(k)] for a in range(k)]
        try:
            inverse(xtwx)
            return kept_names, kept_X
        except ValueError:
            removable = [i for i, name in enumerate(kept_names) if name not in ["Intercept", "treat"]]
            if not removable:
                return None, None
            remove = removable[-1]
            kept_names.pop(remove)
            kept_X = [[value for j, value in enumerate(row) if j != remove] for row in kept_X]


def weighted_ols(rows, outcome, covariates, weight=None):
    y, X, w = design_matrix(rows, outcome, covariates, weight)
    if not y:
        return None
    names, X = drop_unusable_columns(y, X, w, covariates)
    if names is None or "treat" not in names:
        return None
    n, k = len(y), len(names)
    xtwx = [[sum(w[i] * X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    xtwy = [sum(w[i] * X[i][a] * y[i] for i in range(n)) for a in range(k)]
    inv = inverse(xtwx)
    beta = [sum(inv[a][b] * xtwy[b] for b in range(k)) for a in range(k)]
    residuals = [y[i] - sum(beta[j] * X[i][j] for j in range(k)) for i in range(n)]
    df = n - k
    sse = sum(w[i] * residuals[i] ** 2 for i in range(n))
    sigma2 = sse / df if df > 0 else 0.0
    se = [math.sqrt(max(0.0, sigma2 * inv[j][j])) for j in range(k)]
    ybar = sum(w[i] * y[i] for i in range(n)) / sum(w)
    tss = sum(w[i] * (y[i] - ybar) ** 2 for i in range(n))
    treat_idx = names.index("treat")
    treated_n = sum(1 for row in rows if row.get("treat") == 1 and row.get(outcome) is not None)
    control_n = sum(1 for row in rows if row.get("treat") == 0 and row.get(outcome) is not None)
    return {
        "estimate": beta[treat_idx],
        "std_error": se[treat_idx],
        "p_value": normal_p(beta[treat_idx] / se[treat_idx] if se[treat_idx] else 0.0),
        "n": n,
        "k": k,
        "treated_n": treated_n,
        "control_n": control_n,
        "r_squared": 1.0 - sse / tss if tss else 0.0,
        "mean_y": sum(y) / n,
        "covariates_used": "; ".join(name for name in names if name not in ["Intercept", "treat"]),
    }


def fit_propensity_scores(rows):
    covariates = [v for v in candidate_covariates(rows) if v != "treat"]
    numeric_vars = ["baseline", "age"]
    means = {v: statistics.mean(row[v] for row in rows) for v in numeric_vars}
    sds = {v: statistics.pstdev(row[v] for row in rows) or 1.0 for v in numeric_vars}

    def ps_features(row):
        values = [1.0]
        for var in covariates:
            value = value_for(row, var)
            if var in means:
                value = (value - means[var]) / sds[var]
            values.append(value)
        return values

    X = [ps_features(row) for row in rows]
    y = [row["treat"] for row in rows]
    if len(set(y)) < 2:
        return rows
    beta = [0.0] * len(X[0])
    learning_rate = 0.03
    ridge = 0.01
    for _ in range(3500):
        gradient = [0.0] * len(beta)
        for x_row, target in zip(X, y):
            z = max(-30.0, min(30.0, sum(beta[j] * x_row[j] for j in range(len(beta)))))
            p = 1.0 / (1.0 + math.exp(-z))
            for j in range(len(beta)):
                gradient[j] += (target - p) * x_row[j]
        for j in range(len(beta)):
            beta[j] += learning_rate * (gradient[j] - ridge * beta[j]) / len(y)

    for row in rows:
        x_row = ps_features(row)
        z = max(-30.0, min(30.0, sum(beta[j] * x_row[j] for j in range(len(beta)))))
        ps = min(0.99, max(0.01, 1.0 / (1.0 + math.exp(-z))))
        row["propensity_score"] = ps
        row["overlap_weight"] = 1.0 - ps if row["treat"] == 1 else ps
        row["logit_ps"] = math.log(ps / (1.0 - ps))
    return rows


def matched_sample(rows):
    treated = [row for row in rows if row["treat"] == 1]
    controls = [row for row in rows if row["treat"] == 0]
    if not treated or not controls:
        return []
    logits = [row["logit_ps"] for row in rows]
    caliper = 0.20 * (statistics.pstdev(logits) or 1.0)
    matched = []
    pair_id = 0
    for treated_row in treated:
        control_row = min(controls, key=lambda c: abs(c["logit_ps"] - treated_row["logit_ps"]))
        if abs(control_row["logit_ps"] - treated_row["logit_ps"]) <= caliper:
            pair_id += 1
            tcopy = treated_row.copy(); ccopy = control_row.copy()
            tcopy["match_pair"] = pair_id; ccopy["match_pair"] = pair_id
            tcopy["match_caliper"] = caliper; ccopy["match_caliper"] = caliper
            matched.extend([tcopy, ccopy])
    return matched


def normal_p(t_stat):
    return math.erfc(abs(t_stat) / math.sqrt(2.0))


def stars(p_value):
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def effect_cell(result):
    return f"{result['estimate']:.2f}{stars(result['p_value'])}<br>({result['std_error']:.2f})"


def make_table(title, rows):
    header = [
        f"Table: {title} estimates of GROW impact on 2026 ATLAS scores",
        "",
        "| Grade | Subject | JMTES Effect | N | JMTES N | JES N | Controls | Baseline Adjusted | Covariate Adjusted | R-squared | Outcome Mean |",
        "|---|---:|---:|---:|---:|---:|---|---|---|---:|---:|",
    ]
    body = []
    for row in rows:
        body.append(
            "| {grade} | {subject} | {effect} | {n} | {treated_n} | {control_n} | {controls} | {baseline} | {covariates} | {r2:.3f} | {mean:.1f} |".format(
                grade=row["grade"],
                subject=row["subject"],
                effect=effect_cell(row),
                n=row["n"],
                treated_n=row["treated_n"],
                control_n=row["control_n"],
                controls=row["controls"],
                baseline=row["baseline_adjusted"],
                covariates=row["covariate_adjusted"],
                r2=row["r_squared"],
                mean=row["mean_y"],
            )
        )
    notes = [
        "",
        "Notes: Cells report the coefficient on JMTES, the GROW school, with standard errors in parentheses. * p<0.10, ** p<0.05, *** p<0.01. Models are estimated separately by grade and subject. Baseline is the same-subject prior summative score when available; otherwise the same-subject winter or fall score is used.",
    ]
    return "\n".join(header + body + notes)


def markdown_to_word_html(markdown_text):
    return (
        '<html><head><meta charset="utf-8"><style>'
        'body{font-family:Calibri,Arial,sans-serif;line-height:1.35;}'
        'pre{white-space:pre-wrap;font-family:Consolas,monospace;font-size:10pt;}'
        'h1,h2{color:#1f4e79;}'
        '</style></head><body><pre>'
        + html.escape(markdown_text)
        + "</pre></body></html>"
    )


def add_result(all_results, table_rows, analysis, grade, subject, result, controls, baseline_adjusted, covariate_adjusted):
    row = {
        "analysis": analysis,
        "grade": grade,
        "subject": subject,
        "estimate": result["estimate"],
        "std_error": result["std_error"],
        "p_value": result["p_value"],
        "n": result["n"],
        "treated_n": result["treated_n"],
        "control_n": result["control_n"],
        "r_squared": result["r_squared"],
        "mean_y": result["mean_y"],
        "controls": controls,
        "baseline_adjusted": baseline_adjusted,
        "covariate_adjusted": covariate_adjusted,
        "covariates_used": result["covariates_used"],
    }
    all_results.append(row)
    table_rows.append(row)


def main():
    OUTDIR.mkdir(exist_ok=True)
    data = build_analysis_records()
    tables = {
        "Overlap-weighted propensity score + baseline/covariate-adjusted regression": [],
        "Propensity-score matching + baseline/covariate-adjusted regression": [],
        "DiD-style gain-score + baseline/covariate-adjusted regression": [],
    }
    all_results = []

    for grade in GRADES:
        for subject in SUBJECTS:
            rows = [row.copy() for row in data if row["grade"] == grade and row["subject"] == subject]
            if len(rows) < 8 or len({row["treat"] for row in rows}) < 2:
                continue
            rows = fit_propensity_scores(rows)
            covariates = candidate_covariates(rows)

            overlap = weighted_ols(rows, "post", covariates, weight="overlap_weight")
            if overlap:
                add_result(
                    all_results,
                    tables["Overlap-weighted propensity score + baseline/covariate-adjusted regression"],
                    "overlap_weighted_ps_covariate_baseline_regression",
                    grade,
                    subject,
                    overlap,
                    "Baseline, gender, race, age, meal, entry; overlap weights from propensity score",
                    "Yes",
                    "Yes",
                )

            matched = matched_sample(rows)
            match_model = weighted_ols(matched, "post", covariates) if matched else None
            if match_model:
                add_result(
                    all_results,
                    tables["Propensity-score matching + baseline/covariate-adjusted regression"],
                    "propensity_score_matching_covariate_baseline_regression",
                    grade,
                    subject,
                    match_model,
                    "Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry",
                    "Yes",
                    "Yes",
                )

            did_model = weighted_ols(rows, "gain", covariates)
            if did_model:
                add_result(
                    all_results,
                    tables["DiD-style gain-score + baseline/covariate-adjusted regression"],
                    "did_style_gain_covariate_baseline_regression",
                    grade,
                    subject,
                    did_model,
                    "Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry",
                    "Yes",
                    "Yes",
                )

    sections = [
        "# Impact of GROW on Academic Performance: Comparing ATLAS Scores Between JMTES and JES",
        "",
        "This report estimates the impact of GROW on 2026 ATLAS performance using the merged at-risk files for Kindergarten through Grade 5. The preferred analysis is an overlap-weighted propensity score approach combined with a baseline-adjusted and covariate-adjusted regression. Two robustness checks are also reported: propensity-score matching followed by the same baseline/covariate-adjusted regression framework, and a DiD-style gain-score regression that adjusts for baseline score and student covariates.",
        "",
    ]
    for title, rows in tables.items():
        table_md = make_table(title, rows)
        sections.append(table_md)
        sections.append("")
        filename = {
            "Overlap-weighted propensity score + baseline/covariate-adjusted regression": "overlap_weighted_ps_aer_regression_table.md",
            "Propensity-score matching + baseline/covariate-adjusted regression": "matching_aer_regression_table.md",
            "DiD-style gain-score + baseline/covariate-adjusted regression": "did_aer_regression_table.md",
        }[title]
        (OUTDIR / filename).write_text(table_md)

    sections.extend(
        [
            "## Results Discussion",
            "",
            "The overlap-weighted propensity score results are the primary estimates because they give the most influence to JMTES and JES students with similar observed pre-outcome characteristics while retaining the full comparable analysis sample. These models adjust for the baseline same-subject ATLAS score and for gender, race/ethnicity, age, meal-status code, and entry code.",
            "",
            "The matching results are a robustness check using calipered nearest-neighbor matching on the estimated propensity score. After matching, the outcome regression again adjusts for baseline ATLAS score and the same student covariates, so the matching table is not an unadjusted mean-difference table.",
            "",
            "The DiD-style results are implemented as gain-score regressions. The dependent variable is the change from baseline ATLAS score to 2026 summative ATLAS score, and the model adjusts for baseline score plus the same covariates. This estimates whether JMTES students gained more or less than comparable JES students from the pre-outcome baseline to 2026.",
            "",
            "Positive JMTES coefficients indicate higher adjusted performance or growth for JMTES students relative to comparable JES students. Negative coefficients indicate lower adjusted performance or growth. Because students were not randomly assigned to schools, the estimates should still be interpreted as adjusted associations based on observed covariates rather than as definitive causal effects.",
        ]
    )
    report_md = "\n".join(sections)
    (OUTDIR / "grow_atlas_impact_results.md").write_text(report_md)
    (OUTDIR / "grow_atlas_impact_results.doc").write_text(markdown_to_word_html(report_md))

    with open(OUTDIR / "grow_atlas_impact_regression_results.csv", "w", newline="") as f:
        fieldnames = [
            "analysis",
            "grade",
            "subject",
            "estimate",
            "std_error",
            "p_value",
            "n",
            "treated_n",
            "control_n",
            "r_squared",
            "mean_y",
            "controls",
            "baseline_adjusted",
            "covariate_adjusted",
            "covariates_used",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"Wrote {OUTDIR} with {len(all_results)} regression estimates")


if __name__ == "__main__":
    main()
