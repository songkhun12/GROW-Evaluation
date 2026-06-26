#!/usr/bin/env python3
"""Create overlap-weighting balance and common-support diagnostics.

Outputs cover the academic ATLAS models and the existing attendance and referral
(behavior) overlap-weighted model data. The diagnostics report standardized mean
differences before and after overlap weighting and propensity-score histograms by
school to document common support.
"""

import csv
import math
from pathlib import Path

from run_atlas_grow_impact import build_analysis_records, fit_propensity_scores

OUTDIR = Path("ATLAS GROW Impact Analysis")
ATTENDANCE_FILE = Path("Attendance Evaluation/jmtes_jes_overlap_weighted_attendance_student_data.csv")
BEHAVIOR_FILE = Path("Referral Evaluation/jmtes_jes_referral_student_data.csv")


def to_float(value):
    try:
        return float(str(value).strip())
    except Exception:
        return None


def weighted_mean(values, weights):
    total_w = sum(weights)
    return sum(v * w for v, w in zip(values, weights)) / total_w if total_w else 0.0


def weighted_var(values, weights):
    mean = weighted_mean(values, weights)
    total_w = sum(weights)
    return sum(w * (v - mean) ** 2 for v, w in zip(values, weights)) / total_w if total_w else 0.0


def smd(rows, variable, value_fn, treat_key="treat", weight_key=None):
    treated_values, control_values, treated_weights, control_weights = [], [], [], []
    for row in rows:
        value = value_fn(row)
        if value is None:
            continue
        weight = float(row.get(weight_key, 1.0)) if weight_key else 1.0
        if int(float(row[treat_key])) == 1:
            treated_values.append(value); treated_weights.append(weight)
        else:
            control_values.append(value); control_weights.append(weight)
    if not treated_values or not control_values:
        return None
    mt = weighted_mean(treated_values, treated_weights)
    mc = weighted_mean(control_values, control_weights)
    vt = weighted_var(treated_values, treated_weights)
    vc = weighted_var(control_values, control_weights)
    pooled = math.sqrt((vt + vc) / 2.0)
    if pooled == 0:
        diff = 0.0 if abs(mt - mc) < 1e-12 else None
    else:
        diff = (mt - mc) / pooled
    if diff is None:
        return None
    return mt, mc, diff


def add_balance_row(output, domain, model, variable, rows, value_fn, treat_key="treat", weight_key="overlap_weight"):
    before = smd(rows, variable, value_fn, treat_key=treat_key, weight_key=None)
    after = smd(rows, variable, value_fn, treat_key=treat_key, weight_key=weight_key)
    if not before or not after:
        return
    output.append(
        {
            "domain": domain,
            "model": model,
            "covariate": variable,
            "treated_mean_unweighted": before[0],
            "control_mean_unweighted": before[1],
            "smd_unweighted": before[2],
            "treated_mean_weighted": after[0],
            "control_mean_weighted": after[1],
            "smd_weighted": after[2],
            "abs_smd_unweighted": abs(before[2]),
            "abs_smd_weighted": abs(after[2]),
            "improvement": abs(before[2]) - abs(after[2]),
        }
    )


def academic_diagnostics():
    records = build_analysis_records()
    balance_rows, ps_rows = [], []
    for grade in sorted(set(r["grade"] for r in records)):
        for subject in sorted(set(r["subject"] for r in records if r["grade"] == grade)):
            rows = [r.copy() for r in records if r["grade"] == grade and r["subject"] == subject]
            if len(rows) < 8 or len({r["treat"] for r in rows}) < 2:
                continue
            rows = fit_propensity_scores(rows)
            model = f"{grade} {subject}"
            for row in rows:
                ps_rows.append({"domain": "Academic", "model": model, "school": row["school"], "propensity": row["propensity_score"]})
            add_balance_row(balance_rows, "Academic", model, "baseline_atlas_score", rows, lambda r: float(r["baseline"]))
            add_balance_row(balance_rows, "Academic", model, "female", rows, lambda r: float(r["female"]))
            add_balance_row(balance_rows, "Academic", model, "black", rows, lambda r: float(r["black"]))
            add_balance_row(balance_rows, "Academic", model, "age", rows, lambda r: float(r["age"]))
            add_balance_row(balance_rows, "Academic", model, "meal_status_disadvantaged", rows, lambda r: 0.0 if r["meal"] in ["", "00", "Missing"] else 1.0)
            for entry in sorted(set(r["entry"] for r in rows)):
                add_balance_row(balance_rows, "Academic", model, f"entry_code={entry}", rows, lambda r, e=entry: 1.0 if r["entry"] == e else 0.0)
    return balance_rows, ps_rows


def read_model_data(path, domain):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            row["domain"] = domain
            row["treat"] = int(float(row.get("jmtes", 0)))
            row["overlap_weight"] = to_float(row.get("overlap_weight")) or 1.0
            row["propensity_score"] = to_float(row.get("propensity"))
            row["female_num"] = to_float(row.get("female"))
            row["black_num"] = to_float(row.get("black"))
            row["age_num"] = to_float(row.get("age"))
            row["meal"] = row.get("meal_status", "Missing") or "Missing"
            row["entry"] = row.get("entry_code", "Missing") or "Missing"
            row["grade_value"] = row.get("grade", "Missing") or "Missing"
            row["school"] = row.get("school", "")
            rows.append(row)
    return rows


def nonacademic_diagnostics(path, domain):
    rows = read_model_data(path, domain)
    balance_rows = []
    add_balance_row(balance_rows, domain, f"{domain} model", "female", rows, lambda r: r["female_num"])
    add_balance_row(balance_rows, domain, f"{domain} model", "black", rows, lambda r: r["black_num"])
    add_balance_row(balance_rows, domain, f"{domain} model", "age", rows, lambda r: r["age_num"])
    add_balance_row(balance_rows, domain, f"{domain} model", "meal_status_disadvantaged", rows, lambda r: 0.0 if r["meal"] in ["", "00", "Missing"] else 1.0)
    for entry in sorted(set(r["entry"] for r in rows)):
        add_balance_row(balance_rows, domain, f"{domain} model", f"entry_code={entry}", rows, lambda r, e=entry: 1.0 if r["entry"] == e else 0.0)
    for grade in sorted(set(r["grade_value"] for r in rows)):
        add_balance_row(balance_rows, domain, f"{domain} model", f"grade={grade}", rows, lambda r, g=grade: 1.0 if r["grade_value"] == g else 0.0)
    ps_rows = [{"domain": domain, "model": f"{domain} model", "school": r["school"], "propensity": r["propensity_score"]} for r in rows if r["propensity_score"] is not None]
    return balance_rows, ps_rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def histogram_counts(ps_rows, bins=20):
    counts = {"JMTES": [0] * bins, "JES": [0] * bins}
    for row in ps_rows:
        school = "JMTES" if row["school"] == "JMTES" else "JES"
        p = max(0.0, min(0.999999, float(row["propensity"])))
        counts[school][int(p * bins)] += 1
    return counts


def write_histogram_svg(path, title, ps_rows, bins=20):
    counts = histogram_counts(ps_rows, bins=bins)
    max_count = max(max(counts["JMTES"]), max(counts["JES"]), 1)
    width, height = 900, 430
    margin_left, margin_bottom, top = 60, 55, 55
    plot_width, plot_height = width - 90, height - 110
    bar_w = plot_width / bins / 2.3
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append('<rect width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{width/2}" y="25" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold">{title}</text>')
    svg.append(f'<line x1="{margin_left}" y1="{top + plot_height}" x2="{margin_left + plot_width}" y2="{top + plot_height}" stroke="black"/>')
    svg.append(f'<line x1="{margin_left}" y1="{top}" x2="{margin_left}" y2="{top + plot_height}" stroke="black"/>')
    for i in range(bins):
        x0 = margin_left + i * (plot_width / bins)
        for school, color, offset in [("JES", "#4C78A8", 0), ("JMTES", "#F58518", bar_w)]:
            h = counts[school][i] / max_count * plot_height
            svg.append(f'<rect x="{x0 + offset:.1f}" y="{top + plot_height - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{color}" opacity="0.78"/>')
    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        x = margin_left + tick * plot_width
        svg.append(f'<line x1="{x}" y1="{top + plot_height}" x2="{x}" y2="{top + plot_height + 5}" stroke="black"/>')
        svg.append(f'<text x="{x}" y="{top + plot_height + 22}" text-anchor="middle" font-family="Arial" font-size="12">{tick:.2f}</text>')
    svg.append(f'<text x="{margin_left + plot_width/2}" y="{height - 10}" text-anchor="middle" font-family="Arial" font-size="13">Estimated propensity score</text>')
    svg.append(f'<text x="18" y="{top + plot_height/2}" transform="rotate(-90 18,{top + plot_height/2})" text-anchor="middle" font-family="Arial" font-size="13">Count</text>')
    svg.append(f'<rect x="{width-170}" y="45" width="14" height="14" fill="#4C78A8" opacity="0.78"/><text x="{width-150}" y="57" font-family="Arial" font-size="13">JES</text>')
    svg.append(f'<rect x="{width-170}" y="67" width="14" height="14" fill="#F58518" opacity="0.78"/><text x="{width-150}" y="79" font-family="Arial" font-size="13">JMTES</text>')
    svg.append('</svg>')
    path.write_text("\n".join(svg))


def summary_rows(balance_rows):
    grouped = {}
    for row in balance_rows:
        key = (row["domain"], row["model"])
        grouped.setdefault(key, []).append(row)
    output = []
    for (domain, model), rows in sorted(grouped.items()):
        before = [r["abs_smd_unweighted"] for r in rows]
        after = [r["abs_smd_weighted"] for r in rows]
        output.append(
            {
                "domain": domain,
                "model": model,
                "covariates_checked": len(rows),
                "mean_abs_smd_unweighted": sum(before) / len(before),
                "mean_abs_smd_weighted": sum(after) / len(after),
                "max_abs_smd_unweighted": max(before),
                "max_abs_smd_weighted": max(after),
                "share_weighted_below_0_10": sum(1 for value in after if value < 0.10) / len(after),
            }
        )
    return output


def md_table(rows, columns, float_cols=None):
    float_cols = set(float_cols or [])
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        vals = []
        for col in columns:
            value = row[col]
            vals.append(f"{value:.3f}" if col in float_cols else str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)



def append_diagnostics_to_main_report():
    report = OUTDIR / "grow_atlas_impact_results.md"
    if not report.exists():
        return
    text = report.read_text()
    marker = "# Appendix: Balance and Common-Support Diagnostics"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n\n"
    appendix = """# Appendix: Balance and Common-Support Diagnostics

The overlap-weighted design requires evidence that JMTES and JES students are comparable on observed pre-outcome characteristics after weighting. The diagnostic appendix adds standardized mean differences before and after overlap weighting for baseline ATLAS score, gender, race/ethnicity, age, meal-status disadvantage, entry code, and grade-level indicators for the attendance and behavior models. It also adds propensity-score overlap histograms for the academic, attendance, and behavior analyses.

The detailed balance appendix is saved in `overlap_balance_diagnostics.md`, with machine-readable outputs in `overlap_balance_diagnostics.csv` and `overlap_balance_summary.csv`. The common-support figures are saved as `propensity_overlap_academic.svg`, `propensity_overlap_attendance.svg`, and `propensity_overlap_behavior.svg`.

These diagnostics speak directly to validity. If the weighted standardized mean differences are smaller than the unweighted differences and the histograms show common support, the overlap-weighted estimates rely more on comparisons among students who looked similar before the outcome year. This strengthens the credibility of the adjusted comparisons, although the results remain non-randomized estimates and cannot rule out unobserved confounding.
"""
    updated = text.rstrip() + "\n\n" + appendix
    report.write_text(updated)
    # Keep the Word-compatible report in sync without importing analysis code.
    import html as _html
    doc_html = '<html><head><meta charset="utf-8"><style>body{font-family:Calibri,Arial,sans-serif;line-height:1.35;}pre{white-space:pre-wrap;font-family:Consolas,monospace;font-size:10pt;}h1,h2{color:#1f4e79;}</style></head><body><pre>' + _html.escape(updated) + '</pre></body></html>'
    (OUTDIR / "grow_atlas_impact_results.doc").write_text(doc_html)

def main():
    OUTDIR.mkdir(exist_ok=True)
    academic_balance, academic_ps = academic_diagnostics()
    attendance_balance, attendance_ps = nonacademic_diagnostics(ATTENDANCE_FILE, "Attendance")
    behavior_balance, behavior_ps = nonacademic_diagnostics(BEHAVIOR_FILE, "Behavior")
    balance = academic_balance + attendance_balance + behavior_balance
    summaries = summary_rows(balance)

    balance_fields = ["domain", "model", "covariate", "treated_mean_unweighted", "control_mean_unweighted", "smd_unweighted", "treated_mean_weighted", "control_mean_weighted", "smd_weighted", "abs_smd_unweighted", "abs_smd_weighted", "improvement"]
    summary_fields = ["domain", "model", "covariates_checked", "mean_abs_smd_unweighted", "mean_abs_smd_weighted", "max_abs_smd_unweighted", "max_abs_smd_weighted", "share_weighted_below_0_10"]
    write_csv(OUTDIR / "overlap_balance_diagnostics.csv", balance, balance_fields)
    write_csv(OUTDIR / "overlap_balance_summary.csv", summaries, summary_fields)
    write_csv(OUTDIR / "propensity_score_values.csv", academic_ps + attendance_ps + behavior_ps, ["domain", "model", "school", "propensity"])

    write_histogram_svg(OUTDIR / "propensity_overlap_academic.svg", "Academic ATLAS propensity-score overlap", academic_ps)
    write_histogram_svg(OUTDIR / "propensity_overlap_attendance.svg", "Attendance propensity-score overlap", attendance_ps)
    write_histogram_svg(OUTDIR / "propensity_overlap_behavior.svg", "Behavior propensity-score overlap", behavior_ps)

    worst = sorted(balance, key=lambda r: r["abs_smd_weighted"], reverse=True)[:15]
    md = [
        "# Balance and Common-Support Diagnostics for GROW Overlap-Weighted Analyses",
        "",
        "This appendix reports standardized mean differences (SMDs) before and after overlap weighting. Smaller absolute SMDs indicate better balance; values below 0.10 are commonly treated as evidence of adequate balance on an observed covariate.",
        "",
        "## Summary by Model",
        "",
        md_table(summaries, summary_fields, float_cols=set(summary_fields) - {"domain", "model", "covariates_checked"}),
        "",
        "## Largest Remaining Weighted Imbalances",
        "",
        md_table(worst, ["domain", "model", "covariate", "smd_unweighted", "smd_weighted", "improvement"], float_cols={"smd_unweighted", "smd_weighted", "improvement"}),
        "",
        "## Propensity-Score Overlap Figures",
        "",
        "* Academic ATLAS models: `propensity_overlap_academic.svg`",
        "* Attendance model: `propensity_overlap_attendance.svg`",
        "* Behavior/referral model: `propensity_overlap_behavior.svg`",
        "",
        "## Interpretation for Validity",
        "",
        "The diagnostics directly test whether the overlap-weighting design improved comparability between JMTES and JES on observed pre-outcome characteristics. When weighted SMDs are meaningfully smaller than unweighted SMDs, the weighted analysis is less dependent on extrapolating from unlike students. The common-support histograms show whether both schools have students across similar propensity-score ranges, which is necessary for overlap weighting to estimate effects among comparable students. These diagnostics strengthen the validity argument for the preferred overlap-weighted analyses, while still leaving the usual caveat that unobserved differences cannot be ruled out in a non-randomized design.",
    ]
    (OUTDIR / "overlap_balance_diagnostics.md").write_text("\n".join(md))
    append_diagnostics_to_main_report()
    print(f"Wrote diagnostics to {OUTDIR}")


if __name__ == "__main__":
    main()
