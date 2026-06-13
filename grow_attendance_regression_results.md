# Covariate-Adjusted Attendance Regression Results

This analysis implements the requested attendance methodology: OLS regressions of absence rates on a JMTES treatment indicator, Female, Black, an ordered SES/meal-status measure, and grade indicators.

Absence outcomes are percentages of enrolled school days missed. Enrolled days are calculated from each student's entry date through the relevant report/school-year end date, excluding non-school days in the 170-day calendar.

| Outcome | JMTES coefficient | Robust SE | 95% CI | p-value |
|---|---:|---:|---:|---:|
| Unexcused absence rate (% enrolled days) | -4.44 | 0.60 | [-5.62, -3.27] | 0.0000 |
| Excused absence rate (% enrolled days) | 0.78 | 0.18 | [0.42, 1.13] | 0.0000 |
| Total absence rate (% enrolled days) | -3.67 | 0.65 | [-4.94, -2.40] | 0.0000 |

## Interpretation

Negative coefficients indicate lower absence rates at JMTES than JES after adjusting for the included covariates. The regression results support the same broad conclusion as the overlap-weighted analysis: JMTES has lower unexcused and total absence rates, while excused absence is slightly higher.

This regression approach is useful and easy to communicate, but the overlap-weighted analysis remains more defensible as the primary observational design because it explicitly targets the region of covariate overlap between JMTES and JES students. The regression estimates are therefore best used as a robustness check that aligns with the requested methodology.