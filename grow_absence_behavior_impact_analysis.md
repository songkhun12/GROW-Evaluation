# GROW Impact Analysis: JMTES Treatment vs JES Control

## Design and primary estimand

This analysis treats JMTES as the GROW treatment school and JES as the comparison school. The primary analysis is an overlap-weighted propensity-score comparison of student outcomes, adjusting for grade, gender, ethnicity, age, meal-status code, and entry code. The estimated effect is `JMTES - JES`, so negative values indicate lower absences or referrals at JMTES.

JMTES data were pulled on May 7, 2026, before the end of the 170-day school year. JMTES absence and behavior counts are therefore scaled from 159 report school days to a 170-day school-year rate. JES was pulled after the end of the year and uses 170 report school days.

The primary overlap-weighted design is the most defensible option available because the data are observational and cross-sectional, with one treatment school and one control school. Overlap weighting emphasizes comparable students across the two schools and improves balance on measured covariates, but it cannot remove unmeasured school-level confounding.

## Why overlap weighting is preferred for absences

A covariate-adjusted regression estimates the JMTES effect by fitting one linear model to all students and adjusting for covariates in the outcome model. That is useful and transparent, but it can rely on model extrapolation when JMTES and JES have different student compositions. For example, if some grade, meal-status, entry-code, or demographic combinations are much more common in one school, regression still uses the linear model to project what the other school's outcomes would have been for those less-comparable students.

Overlap-weighted propensity scores first model each student's probability of being in JMTES given observed baseline covariates. Treated JMTES students receive weight `1 - propensity score`; control JES students receive weight `propensity score`. Students who look plausible in either school receive the most weight, while students whose covariates make them nearly certain to be in one school receive less weight. The resulting estimand is the average JMTES-vs-JES difference for the students in the region of common support, where the comparison is most credible.

This matters for identifying GROW impact on absences because it makes the treatment and comparison groups more similar before comparing outcomes. In this analysis, the largest absolute standardized covariate difference fell from 0.14 before weighting to 0.02 after overlap weighting. That improved balance means the absence comparison is less dependent on functional-form assumptions than the regression-only approach. Regression results are still reported as robustness checks, and they point in the same direction as the overlap-weighted findings.

Behavior outcomes use the At Risk Report code definitions and now account for severity instead of assuming every referral is equal. School behavior severity points weight L-1 through L-4 referrals as 1, 2, 3, and 4 points, respectively. Bus behavior severity points weight Local/Transportation 1 as 1 point, Transportation 2 as 2 points, and Transportation 3 as 3 points. The analysis also reports each student's highest observed severity category as an ordered outcome. JMTES behavior counts are scaled from 159 report days to the 170-day school-year rate.

## Sample and balance

- JMTES treatment students: 419
- JES control students: 676
- Largest absolute standardized covariate difference before weighting: 0.14
- Largest absolute standardized covariate difference after overlap weighting: 0.02

## Primary and robustness results

| Outcome | Primary overlap-weighted effect | 95% bootstrap CI | Unadjusted | Regression adjusted | Exact-stratified |
|---|---:|---:|---:|---:|---:|
| Excused absence % of 170-day year | 0.58 | [0.34, 0.78] | 0.50 | 0.58 | 0.58 |
| Unexcused absence % of 170-day year | -3.41 | [-4.22, -2.54] | -3.56 | -3.41 | -3.26 |
| Total absence % of 170-day year | -2.83 | [-3.77, -1.88] | -3.06 | -2.82 | -2.68 |
| School behavior severity points per 170-day year | -0.81 | [-1.21, -0.39] | -0.88 | -0.81 | -0.79 |
| Bus behavior severity points per 170-day year | -0.26 | [-0.35, -0.16] | -0.26 | -0.26 | -0.24 |
| Highest school behavior severity category (0-4) | -0.29 | [-0.42, -0.14] | -0.29 | -0.29 | -0.26 |
| Highest bus behavior severity category (0-3) | -0.12 | [-0.17, -0.04] | -0.12 | -0.12 | -0.11 |

## Interpretation guidance

- The absence percentage outcomes are percentage-point differences in the share of the 170-day year absent.
- The primary behavior outcomes are severity-point differences per 170-day school year and highest-severity-category differences, so more serious referrals receive more weight than less serious referrals.
- Because treatment is assigned at the school level and only two schools are observed, these estimates should be interpreted as adjusted treatment-control contrasts rather than definitive randomized causal effects.
- The exact-stratified analysis matches cells defined by grade, gender, ethnicity, and meal group and is included as a robustness check for observable-composition differences.
