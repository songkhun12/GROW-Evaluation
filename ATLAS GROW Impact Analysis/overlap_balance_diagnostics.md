# Appendix A: Balance and Common-Support Diagnostics for GROW Overlap-Weighted Analyses

This appendix reports standardized mean differences (SMDs) before and after overlap weighting. Smaller absolute SMDs indicate better balance; values below 0.10 are commonly treated as evidence of adequate balance on an observed covariate.

## Summary by Model

| domain | model | covariates_checked | mean_abs_smd_unweighted | mean_abs_smd_weighted | max_abs_smd_unweighted | max_abs_smd_weighted | share_weighted_below_0_10 |
|---|---|---|---|---|---|---|---|
| Academic | Grade 1 ELA | 9 | 0.126 | 0.046 | 0.245 | 0.171 | 0.778 |
| Academic | Grade 1 Math | 9 | 0.106 | 0.045 | 0.218 | 0.170 | 0.778 |
| Academic | Grade 2 ELA | 8 | 0.161 | 0.045 | 0.296 | 0.183 | 0.750 |
| Academic | Grade 2 Math | 8 | 0.143 | 0.046 | 0.307 | 0.186 | 0.750 |
| Academic | Grade 3 ELA | 8 | 0.127 | 0.020 | 0.275 | 0.072 | 1.000 |
| Academic | Grade 3 Math | 8 | 0.103 | 0.019 | 0.264 | 0.065 | 1.000 |
| Academic | Grade 3 Science | 8 | 0.200 | 0.013 | 0.747 | 0.063 | 1.000 |
| Academic | Grade 4 ELA | 9 | 0.149 | 0.029 | 0.528 | 0.115 | 0.889 |
| Academic | Grade 4 Math | 9 | 0.130 | 0.028 | 0.314 | 0.092 | 1.000 |
| Academic | Grade 4 Science | 9 | 0.151 | 0.028 | 0.491 | 0.107 | 0.889 |
| Academic | Grade 5 ELA | 9 | 0.191 | 0.029 | 0.355 | 0.162 | 0.889 |
| Academic | Grade 5 Math | 9 | 0.176 | 0.037 | 0.368 | 0.191 | 0.889 |
| Academic | Grade 5 Science | 9 | 0.222 | 0.034 | 0.515 | 0.174 | 0.889 |
| Academic | Kindergarten ELA | 9 | 0.110 | 0.041 | 0.345 | 0.102 | 0.889 |
| Academic | Kindergarten Math | 9 | 0.111 | 0.044 | 0.363 | 0.111 | 0.889 |
| Attendance | Attendance model | 16 | 0.066 | 0.000 | 0.150 | 0.000 | 1.000 |
| Behavior | Behavior model | 16 | 0.066 | 0.000 | 0.150 | 0.000 | 1.000 |

## Largest Remaining Weighted Imbalances

| domain | model | covariate | smd_unweighted | smd_weighted | improvement |
|---|---|---|---|---|---|
| Academic | Grade 5 Math | entry_code=R1 | -0.143 | -0.191 | -0.048 |
| Academic | Grade 2 Math | entry_code=S | -0.227 | -0.186 | 0.041 |
| Academic | Grade 2 ELA | entry_code=S | -0.224 | -0.183 | 0.041 |
| Academic | Grade 5 Science | entry_code=R1 | -0.144 | -0.174 | -0.030 |
| Academic | Grade 1 ELA | entry_code=HS | 0.186 | 0.171 | 0.014 |
| Academic | Grade 1 Math | entry_code=S | -0.192 | -0.170 | 0.022 |
| Academic | Grade 1 Math | entry_code=HS | 0.186 | 0.164 | 0.021 |
| Academic | Grade 1 ELA | entry_code=S | -0.192 | -0.163 | 0.028 |
| Academic | Grade 5 ELA | entry_code=R1 | -0.144 | -0.162 | -0.018 |
| Academic | Grade 2 Math | entry_code=C | 0.261 | 0.138 | 0.123 |
| Academic | Grade 2 ELA | entry_code=C | 0.264 | 0.134 | 0.130 |
| Academic | Grade 4 ELA | entry_code=S | 0.138 | 0.115 | 0.023 |
| Academic | Kindergarten Math | entry_code=R | 0.089 | 0.111 | -0.021 |
| Academic | Grade 4 Science | entry_code=S | 0.136 | 0.107 | 0.029 |
| Academic | Kindergarten ELA | entry_code=R | 0.084 | 0.102 | -0.017 |

## Propensity-Score Overlap Figures

* Academic ATLAS models: `propensity_overlap_academic.svg`
* Attendance model: `propensity_overlap_attendance.svg`
* Behavior/referral model: `propensity_overlap_behavior.svg`

## Interpretation for Validity

The diagnostics directly test whether the overlap-weighting design improved comparability between JMTES and JES on observed pre-outcome characteristics. When weighted SMDs are meaningfully smaller than unweighted SMDs, the weighted analysis is less dependent on extrapolating from unlike students. The common-support histograms show whether both schools have students across similar propensity-score ranges, which is necessary for overlap weighting to estimate effects among comparable students. These diagnostics strengthen the validity argument for the preferred overlap-weighted analyses, while still leaving the usual caveat that unobserved differences cannot be ruled out in a non-randomized design.
