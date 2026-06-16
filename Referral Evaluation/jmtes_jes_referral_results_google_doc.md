# Impact of GROW on Behavioral Outcomes: Comparing Behavioral Referrals Between JMTES and JES

This file updates the behavioral referral analysis using the June 15, 2026 at-risk report files for both schools: `JMTES At Risk Report_Updated 6.15.26 (PW_ #MTE2026).xlsx` and `JES At Risk Report_Updated 6.15.26 (PW_ #JES2026).xlsx`. The updated files contain 417 JMTES students and 676 JES students, for 1,093 total observations. Because the updated source files do not include student-specific enrollment-day exposure, referral rates are presented on the same 170-day scale for all students.

## Data Source Verification

The analysis script verifies that the inputs are the June 15, 2026 files for both schools and writes `jmtes_jes_referral_data_source_audit.csv` when outputs are regenerated.

| School | Source file | Source report date | Students loaded | Workbook title |
|---|---|---:|---:|---|
| JMTES | JMTES At Risk Report_Updated 6.15.26 (PW_ #MTE2026).xlsx | 2026-06-15 | 417 | Taylor Elementary RTI - at Risk Report |
| JES | JES At Risk Report_Updated 6.15.26 (PW_ #JES2026).xlsx | 2026-06-15 | 676 | Jacksonville Elementary School RTI - at Risk Report |

## Methodology

To estimate the impact of GROW on student behavioral outcomes, the analysis uses the same overlap-weighted comparison strategy used in the academic performance and attendance analyses. This approach makes JMTES and JES students more comparable before estimating the program effect. Students who are similar across the two schools based on observed characteristics receive more weight, while students who are less comparable receive less weight.

Behavioral referrals are analyzed as count outcomes because they measure the number of times a student received a referral. Since referral counts cannot be negative and many students have no referrals, the analysis uses overlap-weighted Poisson regression models with robust standard errors rather than ordinary least squares regression. The models include an exposure adjustment for enrollment days so students are compared based on referral rates during the time they were enrolled. The updated June 15, 2026 files do not include a student-specific enrollment-days field, so the analysis applies the common 170-day exposure used for the reporting scale and includes `log(EnrollmentDays)` as the Poisson offset.

For each behavioral referral outcome, the analysis estimates the model:

`log(E[Referralsᵢ]) = β₀ + β₁JMTESᵢ + β₂Gradeᵢ + β₃Femaleᵢ + β₄Blackᵢ + β₅Ageᵢ + β₆MealStatusᵢ + β₇EntryCodeᵢ + log(EnrollmentDaysᵢ)`

Separate overlap-weighted Poisson models are estimated for total school-based referrals, each school-based severity level, total bus-related referrals, and each bus-related severity level. JMTESᵢ is the treatment indicator, coded 1 for students at JMTES and 0 for students at JES. The remaining covariates are grade, gender, race/ethnicity, age, meal status, and entry code. The main estimate of interest is β₁. In the Poisson model, exp(β₁) is interpreted as an incidence rate ratio; values below 1 indicate lower referral rates at JMTES, and values above 1 indicate higher referral rates at JMTES.

## Table 2
Impact of GROW on Total and Severity-Weighted Behavioral Referral Outcomes

|  | Classroom referrals | Classroom severity-weighted frequency | Bus referrals | Bus severity-weighted frequency |
|---|---:|---:|---:|---:|
|  | (1) | (2) | (3) | (4) |
| Model | OW Poisson + covariates | OW Poisson + covariates | OW Poisson + covariates | OW Poisson + covariates |
| JMTES (GROW school) | -0.957*** | -0.790*** | -1.815*** | -1.785*** |
|  | (0.200) | (0.198) | (0.329) | (0.336) |
| Incidence rate ratio | 0.384 | 0.454 | 0.163 | 0.168 |
| Percent difference | -61.6% | -54.6% | -83.7% | -83.2% |
| JES rate per 170 days | 0.665 | 1.549 | 0.163 | 0.332 |
| JMTES rate per 170 days | 0.256 | 0.708 | 0.027 | 0.057 |
| Observations | 1,093 | 1,093 | 1,093 | 1,093 |
| Referral events | 573 | 1,385 | 121 | 246 |

Notes: The table reports updated overlap-weighted covariate-adjusted Poisson regression estimates using the June 15, 2026 referral datasets. The JMTES coefficient is the log incidence-rate difference between JMTES and JES. Standard errors are shown in parentheses. Incidence rate ratios below 1 indicate lower referral rates at JMTES. *** p<0.01, ** p<0.05, * p<0.10.

## Table 3
Impact of GROW on Behavioral Referral Outcomes by Severity Level

|  | Classroom L-I | Classroom L-II | Classroom L-III | Classroom L-IV | Bus L-I | Bus L-II | Bus L-III |
|---|---:|---:|---:|---:|---:|---:|---:|
|  | (1) | (2) | (3) | (4) | (5) | (6) | (7) |
| Model | OW Poisson + covariates | OW Poisson + covariates | OW Poisson + covariates | OW Poisson + covariates | n/a | OW Poisson + covariates | OW Poisson + covariates |
| JMTES (GROW school) | -3.226*** | -1.554*** | -0.472** | 0.755 | n/a | -2.112*** | -0.163 |
|  | (0.996) | (0.317) | (0.197) | (0.598) | n/a | (0.383) | (0.750) |
| Incidence rate ratio | 0.040 | 0.211 | 0.624 | 2.127 | n/a | 0.121 | 0.849 |
| Percent difference | -96.0% | -78.9% | -37.6% | +112.7% | n/a | -87.9% | -15.1% |
| JES rate per 170 days | 0.062 | 0.330 | 0.267 | 0.007 | 0.000 | 0.158 | 0.005 |
| JMTES rate per 170 days | 0.002 | 0.069 | 0.171 | 0.014 | 0.003 | 0.020 | 0.005 |
| Observations | 1,093 | 1,093 | 1,093 | 1,093 | 1,093 | 1,093 | 1,093 |
| Referral events | 43 | 259 | 260 | 11 | 1 | 115 | 5 |

Notes: Columns report updated level-specific overlap-weighted covariate-adjusted Poisson models for each referral severity level. The Bus Level I model is marked n/a because there was only one recorded Bus Level I event and no JES Bus Level I events, making a level-specific rate-ratio estimate unstable. Rare-event categories, especially Classroom Level IV and Bus Level III, should be interpreted cautiously. *** p<0.01, ** p<0.05, * p<0.10.

The updated results continue to show substantially lower behavioral referral rates at JMTES relative to JES. For classroom referrals, JMTES students had an estimated referral rate 61.6 percent lower than JES students. The classroom referral rate was 0.256 referrals per 170 days at JMTES, compared with 0.665 at JES.

The severity-weighted classroom referral measure points in the same direction. The incidence rate ratio was 0.454, meaning the severity-weighted classroom referral rate was 54.6 percent lower at JMTES than at JES. This indicates that the difference is not limited to the number of referrals, but also appears when referrals are weighted by seriousness.

The severity-level classroom models show that the lower classroom referral rate at JMTES is concentrated in Level I, Level II, and Level III referrals. Estimated rates were 96.0 percent lower for Level I referrals, 78.9 percent lower for Level II referrals, and 37.6 percent lower for Level III referrals. Level IV referrals were rare in both schools. The Level IV point estimate is positive, but it is not statistically significant and is based on only 11 total events, so it should not be interpreted as evidence of a meaningful increase in severe referrals at JMTES.

The bus referral results show an even larger descriptive difference. JMTES students had an overall bus referral rate 83.7 percent lower than JES students and a severity-weighted bus referral rate 83.2 percent lower. The strongest level-specific bus result is for Transportation Level II referrals, where the JMTES rate was 87.9 percent lower than the JES rate.

The Bus Level I and Bus Level III results should be interpreted with caution. Bus Level I is marked as not available because there was only one event in the full sample and no Bus Level I events at JES. Bus Level III had only five events across both schools, yielding an imprecise and statistically insignificant estimate. These rare-event categories do not change the overall interpretation: the total bus referral and severity-weighted bus referral measures show substantially lower rates at JMTES in the updated data.

As a robustness check, Appendix Table AX re-estimates the behavioral referral comparison using any-referral logistic models that measure whether students had at least one referral, rather than the number of referrals received. The results are consistent with the count-based analysis: JMTES students were less likely to have any school referral, any bus referral, or any school or bus referral overall.

Overall, the updated June 15, 2026 referral data continue to suggest that JMTES had fewer behavioral referrals than JES in both school-based and bus settings. Because the design is not randomized and the updated source files do not contain a student-specific exposure variable, these overlap-weighted covariate-adjusted estimates should be interpreted as quasi-experimental evidence rather than definitive causal proof.
