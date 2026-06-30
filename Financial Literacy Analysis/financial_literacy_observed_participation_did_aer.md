# Simplified Difference-in-Differences Style Models by Observed Participation Group

This American Economic Review-style table reports simplified difference-in-differences style models using only the curriculum participation groups observed in the analytic sample: curriculum only, Economics Arkansas activities only, and both online curriculum plus Economics Arkansas activities. The dependent variable is the financial literacy assessment score measured as percent correct. The online-only group is not modeled because no students in the analytic sample completed only the online curriculum.

| Variable | Model 1: Unadjusted | Model 2: Adjusted |
|---|---:|---:|
| Post | -9.09 | -9.09 |
|  | (24.27) | (20.27) |
| Activities only | -0.82 | 7.14 |
|  | (17.57) | (16.72) |
| Online + activities | 18.70 | 10.72 |
|  | (17.41) | (16.81) |
| Post × Activities only | 11.95 | 11.95 |
|  | (24.84) | (20.75) |
| Post × Online + activities | 12.86 | 12.86 |
|  | (24.62) | (20.56) |
| Grade 4 and Grade 5 indicators | No | Yes |
| Student covariates | No | Yes |
| Student random intercept | Yes | Yes |
| Observations | 114 | 114 |
| Students | 57 | 57 |

*Notes:* Standard errors are shown in parentheses. Percent-correct scores use grade-specific assessment lengths: Grade 3 has 10 questions, and Grades 4 and 5 have 11 questions. The omitted reference group is students who received only the financial education curriculum. The coefficient on `Post` is the pre-post change for the curriculum-only group. `Post × Activities only` estimates whether the activities-only group changed differently from the curriculum-only group. `Post × Online + activities` estimates whether students who completed both supplemental components changed differently from the curriculum-only group. Model 2 adjusts for Grade 4 and Grade 5 indicators, with Grade 3 as the reference group, plus attendance, gender, race/ethnicity, age, meal-status code, entry code, and school/bus referral severity. Because supplemental participation was not randomly assigned, the estimates should be interpreted as descriptive associations rather than causal effects.
