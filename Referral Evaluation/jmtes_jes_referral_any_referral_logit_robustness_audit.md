# Audit of Any-Referral Logistic Robustness Analysis

This audit double-checks that the any-referral logistic robustness analysis uses the correct referral source data and the intended model specification.

## Outcome definitions checked against source files

The any-referral outcomes were recalculated directly from the original at-risk report columns:

| Robustness outcome | Source definition | Total students with outcome | JMTES | JES |
|---|---|---:|---:|---:|
| `any_school_referral` | `L-1 + L-2 + L-3 + L-4 > 0` | 223 | 53 | 170 |
| `any_bus_referral` | `Local + Transportation 1 + Transportation 2 + Transportation 3 > 0` | 71 | 12 | 59 |
| `any_referral` | Any school referral or any bus referral | 254 | 62 | 192 |

These totals match the `events` column in `Referral Evaluation/jmtes_jes_referral_any_referral_logit_robustness_results.csv`.

## R Markdown model specification checked

The R Markdown file defines the binary outcomes as:

- `referrals$any_school_referral <- as.numeric(referrals$classroom_total > 0)`
- `referrals$any_bus_referral <- as.numeric(referrals$bus_total > 0)`
- `referrals$any_referral <- as.numeric(referrals$classroom_total > 0 | referrals$bus_total > 0)`

The robustness models use the intended overlap-weighted logistic regression specification:

`outcome ~ jmtes + grade + female + black + age + meal_status + entry_code`

with `family = binomial(link = "logit")` and `weights = overlap_weight`.

## Weighted probability checks

Weighted probabilities in the robustness table were recalculated from `Referral Evaluation/jmtes_jes_referral_student_data.csv` using the stored overlap weights:

| Outcome | JES weighted probability | JMTES weighted probability |
|---|---:|---:|
| `any_school_referral` | 0.2503740985 | 0.1258354270 |
| `any_bus_referral` | 0.0883621027 | 0.0303541806 |
| `any_referral` | 0.2829693357 | 0.1478270826 |

These values match `Referral Evaluation/jmtes_jes_referral_any_referral_logit_robustness_results.csv`.

## Conclusion

The any-referral robustness analysis is using the correct source columns, correctly converts referral counts into binary any-referral outcomes, applies the intended overlap-weighted logistic regression with the same student covariates used elsewhere in the referral analysis, and reports weighted probabilities that match direct recalculation from the analytic file.
