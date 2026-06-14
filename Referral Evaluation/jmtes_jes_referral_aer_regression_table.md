# AER-Style Regression Table: GROW and Behavioral Referral Outcomes

Poisson models use overlap weights from the propensity score model and include grade, female, Black, age, meal-status code, entry code, and an exposure offset for enrollment days. Robust standard errors are reported in parentheses. Coefficients are incidence rate ratios (IRRs) for JMTES relative to JES; values below 1 indicate lower referral rates at JMTES.

## Table 1. Classroom Referral Outcomes

| | Total | Level I | Level II | Level III | Level IV | Severity-weighted |
|---|---:|---:|---:|---:|---:|---:|
| JMTES IRR | 0.409*** | 0.137*** | 0.215*** | 0.660** | 2.226 | 0.478*** |
| Robust SE | (0.196) | (0.770) | (0.327) | (0.195) | (0.602) | (0.194) |
| 95% CI | [0.279, 0.600] | [0.030, 0.618] | [0.113, 0.408] | [0.450, 0.967] | [0.684, 7.246] | [0.327, 0.700] |
| Percent difference | -59.1% | -86.3% | -78.5% | -34.0% | 122.6% | -52.2% |
| JES weighted rate per 170 days | 0.67 | 0.06 | 0.33 | 0.27 | 0.01 | 1.56 |
| JMTES weighted rate per 170 days | 0.27 | 0.01 | 0.07 | 0.18 | 0.01 | 0.75 |
| Observations | 1095 | 1095 | 1095 | 1095 | 1095 | 1095 |

## Table 2. Bus Referral Outcomes

| | Total | Level I | Level II | Level III | Severity-weighted |
|---|---:|---:|---:|---:|---:|
| JMTES IRR | 0.194*** | Sparse/unstable | 0.132*** | 1.425 | 0.207*** |
| Robust SE | (0.317) | -- | (0.383) | (0.723) | (0.324) |
| 95% CI | [0.104, 0.362] | -- | [0.062, 0.280] | [0.345, 5.881] | [0.110, 0.391] |
| Percent difference | -80.6% | -- | -86.8% | 42.5% | -79.3% |
| JES weighted rate per 170 days | 0.16 | 0.00 | 0.16 | 0.01 | 0.33 |
| JMTES weighted rate per 170 days | 0.03 | 0.00 | 0.02 | 0.01 | 0.07 |
| Observations | 1095 | 1095 | 1095 | 1095 | 1095 |

Notes: Robust standard errors are in parentheses. *** p<0.01, ** p<0.05, * p<0.10. All models include covariates and enrollment-days exposure offset. The Bus/Local Level I model is flagged as sparse/unstable because only one event appears in the analytic file and the comparison group has a zero weighted rate; its finite-sample IRR is therefore not substantively interpretable.

## Discussion

For overall classroom referrals, the estimated JMTES incidence rate ratio is 0.409, implying a -59.1% difference in the referral rate relative to comparable JES students. The 95% confidence interval is [0.279, 0.600].
For classroom severity-weighted frequency, the incidence rate ratio is 0.478, implying a -52.2% difference in severity-weighted referral frequency.
For overall bus referrals, the estimated JMTES incidence rate ratio is 0.194, implying a -80.6% difference in the bus referral rate. The 95% confidence interval is [0.104, 0.362].
For bus severity-weighted frequency, the incidence rate ratio is 0.207, implying a -79.3% difference in severity-weighted bus referral frequency.
Because the design is quasi-experimental, these estimates should be interpreted as overlap-weighted adjusted associations rather than randomized causal effects.
