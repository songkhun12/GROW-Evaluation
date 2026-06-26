# Impact of GROW on Academic Performance: Comparing ATLAS Scores Between JMTES and JES

This report estimates the impact of GROW on 2026 ATLAS performance using the merged at-risk files for Kindergarten through Grade 5. The preferred analysis is an overlap-weighted propensity score approach combined with a baseline-adjusted and covariate-adjusted regression. Two robustness checks are also reported: propensity-score matching followed by the same baseline/covariate-adjusted regression framework, and a DiD-style gain-score regression that adjusts for baseline score and student covariates.

Table: Overlap-weighted propensity score + baseline/covariate-adjusted regression estimates of GROW impact on 2026 ATLAS scores

| Grade | Subject | JMTES Effect | N | JMTES N | JES N | Controls | Baseline Adjusted | Covariate Adjusted | R-squared | Outcome Mean |
|---|---:|---:|---:|---:|---:|---|---|---|---:|---:|
| Kindergarten | ELA | 0.82<br>(1.77) | 166 | 52 | 114 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.402 | 1059.4 |
| Kindergarten | Math | 1.26<br>(1.71) | 164 | 52 | 112 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.632 | 1058.7 |
| Grade 1 | ELA | 1.79<br>(2.13) | 170 | 59 | 111 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.209 | 1055.3 |
| Grade 1 | Math | -1.21<br>(1.65) | 170 | 59 | 111 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.657 | 1052.9 |
| Grade 2 | ELA | 3.81<br>(2.82) | 156 | 67 | 89 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.274 | 1051.9 |
| Grade 2 | Math | 1.10<br>(1.53) | 155 | 67 | 88 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.605 | 1050.4 |
| Grade 3 | ELA | 7.26***<br>(1.59) | 204 | 85 | 119 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.433 | 1045.6 |
| Grade 3 | Math | 6.40***<br>(1.72) | 203 | 84 | 119 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.477 | 1044.1 |
| Grade 3 | Science | 2.65**<br>(1.27) | 198 | 82 | 116 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.515 | 1047.8 |
| Grade 4 | ELA | 5.13***<br>(1.38) | 188 | 74 | 114 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.635 | 1048.6 |
| Grade 4 | Math | 9.71***<br>(1.46) | 188 | 74 | 114 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.675 | 1045.1 |
| Grade 4 | Science | 6.05***<br>(1.35) | 189 | 75 | 114 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.566 | 1048.7 |
| Grade 5 | ELA | 1.92<br>(1.36) | 151 | 53 | 98 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.697 | 1046.9 |
| Grade 5 | Math | 1.94<br>(1.58) | 152 | 53 | 99 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.771 | 1042.3 |
| Grade 5 | Science | 5.44***<br>(1.61) | 150 | 53 | 97 | Baseline, gender, race, age, meal, entry; overlap weights from propensity score | Yes | Yes | 0.556 | 1046.2 |

Notes: Cells report the coefficient on JMTES, the GROW school, with standard errors in parentheses. * p<0.10, ** p<0.05, *** p<0.01. Models are estimated separately by grade and subject. Baseline is the same-subject prior summative score when available; otherwise the same-subject winter or fall score is used.

Table: Propensity-score matching + baseline/covariate-adjusted regression estimates of GROW impact on 2026 ATLAS scores

| Grade | Subject | JMTES Effect | N | JMTES N | JES N | Controls | Baseline Adjusted | Covariate Adjusted | R-squared | Outcome Mean |
|---|---:|---:|---:|---:|---:|---|---|---|---:|---:|
| Kindergarten | ELA | 1.86<br>(1.63) | 102 | 51 | 51 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.555 | 1060.3 |
| Kindergarten | Math | 3.18<br>(1.93) | 102 | 51 | 51 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.732 | 1058.4 |
| Grade 1 | ELA | 0.92<br>(2.47) | 118 | 59 | 59 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.195 | 1057.4 |
| Grade 1 | Math | -0.83<br>(1.89) | 116 | 58 | 58 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.691 | 1051.9 |
| Grade 2 | ELA | 5.27<br>(3.29) | 128 | 64 | 64 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.367 | 1051.1 |
| Grade 2 | Math | 1.89<br>(1.99) | 124 | 62 | 62 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.645 | 1046.0 |
| Grade 3 | ELA | 6.33***<br>(1.89) | 160 | 80 | 80 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.472 | 1047.0 |
| Grade 3 | Math | 7.66***<br>(1.92) | 156 | 78 | 78 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.468 | 1043.9 |
| Grade 3 | Science | 2.38*<br>(1.45) | 152 | 76 | 76 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.517 | 1049.8 |
| Grade 4 | ELA | 4.99***<br>(1.47) | 146 | 73 | 73 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.688 | 1052.9 |
| Grade 4 | Math | 10.42***<br>(1.61) | 148 | 74 | 74 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.663 | 1049.0 |
| Grade 4 | Science | 6.62***<br>(1.59) | 146 | 73 | 73 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.618 | 1050.3 |
| Grade 5 | ELA | 3.14**<br>(1.58) | 104 | 52 | 52 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.762 | 1048.6 |
| Grade 5 | Math | 0.48<br>(1.60) | 106 | 53 | 53 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.847 | 1045.7 |
| Grade 5 | Science | 5.29**<br>(2.08) | 100 | 50 | 50 | Propensity-score caliper matching; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.597 | 1050.6 |

Notes: Cells report the coefficient on JMTES, the GROW school, with standard errors in parentheses. * p<0.10, ** p<0.05, *** p<0.01. Models are estimated separately by grade and subject. Baseline is the same-subject prior summative score when available; otherwise the same-subject winter or fall score is used.

Table: DiD-style gain-score + baseline/covariate-adjusted regression estimates of GROW impact on 2026 ATLAS scores

| Grade | Subject | JMTES Effect | N | JMTES N | JES N | Controls | Baseline Adjusted | Covariate Adjusted | R-squared | Outcome Mean |
|---|---:|---:|---:|---:|---:|---|---|---|---:|---:|
| Kindergarten | ELA | 0.89<br>(2.14) | 166 | 52 | 114 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.533 | 10.9 |
| Kindergarten | Math | 1.21<br>(2.06) | 164 | 52 | 112 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.175 | 11.3 |
| Grade 1 | ELA | 1.70<br>(2.54) | 170 | 59 | 111 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.605 | 14.4 |
| Grade 1 | Math | -1.22<br>(1.83) | 170 | 59 | 111 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.205 | 1.4 |
| Grade 2 | ELA | 3.76<br>(2.96) | 156 | 67 | 89 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.368 | 6.1 |
| Grade 2 | Math | 1.05<br>(1.64) | 155 | 67 | 88 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.235 | 1.1 |
| Grade 3 | ELA | 7.17***<br>(1.61) | 204 | 85 | 119 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.560 | 0.3 |
| Grade 3 | Math | 6.31***<br>(1.73) | 203 | 84 | 119 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.223 | -2.7 |
| Grade 3 | Science | 2.80*<br>(1.44) | 198 | 82 | 116 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.282 | 6.9 |
| Grade 4 | ELA | 5.34***<br>(1.52) | 188 | 74 | 114 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.243 | 3.6 |
| Grade 4 | Math | 9.66***<br>(1.55) | 188 | 74 | 114 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.295 | 5.6 |
| Grade 4 | Science | 6.11***<br>(1.49) | 189 | 75 | 114 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.242 | 2.6 |
| Grade 5 | ELA | 1.95<br>(1.58) | 151 | 53 | 98 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.235 | 3.1 |
| Grade 5 | Math | 1.70<br>(1.70) | 152 | 53 | 99 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.106 | 2.0 |
| Grade 5 | Science | 5.79***<br>(1.79) | 150 | 53 | 97 | Gain-score DiD-style model; regression adjusts for baseline, gender, race, age, meal, entry | Yes | Yes | 0.226 | 1.9 |

Notes: Cells report the coefficient on JMTES, the GROW school, with standard errors in parentheses. * p<0.10, ** p<0.05, *** p<0.01. Models are estimated separately by grade and subject. Baseline is the same-subject prior summative score when available; otherwise the same-subject winter or fall score is used.

## Results Discussion

The overlap-weighted propensity score results are the primary estimates because they give the most influence to JMTES and JES students with similar observed pre-outcome characteristics while retaining the full comparable analysis sample. These models adjust for the baseline same-subject ATLAS score and for gender, race/ethnicity, age, meal-status code, and entry code.

The matching results are a robustness check using calipered nearest-neighbor matching on the estimated propensity score. After matching, the outcome regression again adjusts for baseline ATLAS score and the same student covariates, so the matching table is not an unadjusted mean-difference table.

The DiD-style results are implemented as gain-score regressions. The dependent variable is the change from baseline ATLAS score to 2026 summative ATLAS score, and the model adjusts for baseline score plus the same covariates. This estimates whether JMTES students gained more or less than comparable JES students from the pre-outcome baseline to 2026.

Positive JMTES coefficients indicate higher adjusted performance or growth for JMTES students relative to comparable JES students. Negative coefficients indicate lower adjusted performance or growth. Because students were not randomly assigned to schools, the estimates should still be interpreted as adjusted associations based on observed covariates rather than as definitive causal effects.

# Appendix: Balance and Common-Support Diagnostics

The overlap-weighted design requires evidence that JMTES and JES students are comparable on observed pre-outcome characteristics after weighting. The diagnostic appendix adds standardized mean differences before and after overlap weighting for baseline ATLAS score, gender, race/ethnicity, age, meal-status disadvantage, entry code, and grade-level indicators for the attendance and behavior models. It also adds propensity-score overlap histograms for the academic, attendance, and behavior analyses.

The detailed balance appendix is saved in `overlap_balance_diagnostics.md`, with machine-readable outputs in `overlap_balance_diagnostics.csv` and `overlap_balance_summary.csv`. The common-support figures are saved as `propensity_overlap_academic.svg`, `propensity_overlap_attendance.svg`, and `propensity_overlap_behavior.svg`.

These diagnostics speak directly to validity. If the weighted standardized mean differences are smaller than the unweighted differences and the histograms show common support, the overlap-weighted estimates rely more on comparisons among students who looked similar before the outcome year. This strengthens the credibility of the adjusted comparisons, although the results remain non-randomized estimates and cannot rule out unobserved confounding.
