# Difference-in-Differences Style Regression Models

This American Economic Review-style table reports unadjusted and adjusted difference-in-differences style models for the combined Grade 3-5 sample. The dependent variable is the financial literacy assessment score measured as percent correct. The Stata do file estimates the models in long format with one pre-test and one post-test observation per student and a student-level random intercept.

| Variable | Model 1: Unadjusted | Model 2: Adjusted |
|---|---:|---:|
| Post | -9.09 | -9.09 |
|  | (—) | (—) |
| Online | 19.52 | 3.59 |
|  | (4.54) | (5.44) |
| Activities | -0.82 | 7.14 |
|  | (3.46) | (8.77) |
| Online × Activities | Omitted | Omitted |
|  | — | — |
| Post × Online | 0.91 | 0.91 |
|  | (6.69) | (5.98) |
| Post × Activities | 11.95 | 11.95 |
|  | (5.20) | (5.10) |
| Post × Online × Activities | Omitted | Omitted |
|  | — | — |
| Grade controls | No | Yes |
| Student covariates | No | Yes |
| Student random intercept | Yes | Yes |
| Observations | 114 | 114 |
| Students | 57 | 57 |

*Notes:* Robust standard errors are shown in parentheses. Percent-correct scores use grade-specific assessment lengths: Grade 3 has 10 questions, and Grades 4 and 5 have 11 questions. Dashes are shown for the robust standard error on `Post` because the baseline curriculum-only group contains one student. Model 1 includes the post-test indicator, online-module participation, Economics Arkansas activity participation, the online-by-activities interaction, and interactions between the post-test indicator and supplemental exposure variables. Model 2 adds grade, attendance, gender, race/ethnicity, age, meal-status code, entry code, and school/bus referral severity covariates. The online-only cell is empty in the analytic dataset; therefore, the Online × Activities and Post × Online × Activities terms are collinear with the corresponding online terms and are omitted. The interaction terms involving Post describe differences in pre-post gains across supplemental exposure groups and should be interpreted as descriptive associations rather than causal effects.
