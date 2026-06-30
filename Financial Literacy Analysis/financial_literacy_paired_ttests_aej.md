# Paired-Samples T-Tests for Financial Literacy Assessment Scores

This table reports paired-samples t-tests comparing post-test performance with pre-test performance in `all_grades_financial_literacy_scores.csv`. The paired difference is post-test minus pre-test. Percent-correct results use grade-specific test lengths: Grade 3 has 10 questions, and Grades 4 and 5 have 11 questions.

| Sample | Measure | N | Pre mean | Post mean | Difference | SE(diff.) | t-statistic | p-value |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Grade 3 | Raw score | 21 | 4.81 | 4.86 | 0.05 | 0.48 | 0.10 | 0.921 |
| Grade 4 | Raw score | 15 | 4.93 | 5.60 | 0.67 | 0.51 | 1.30 | 0.215 |
| Grade 5 | Raw score | 21 | 8.10 | 8.52 | 0.43 | 0.26 | 1.63 | 0.119 |
| All grades | Raw score | 57 | 6.05 | 6.40 | 0.35 | 0.24 | 1.47 | 0.148 |
| Grade 3 | Percent correct | 21 | 48.10 | 48.57 | 0.48 | 4.75 | 0.10 | 0.921 |
| Grade 4 | Percent correct | 15 | 44.85 | 50.91 | 6.06 | 4.67 | 1.30 | 0.215 |
| Grade 5 | Percent correct | 21 | 73.59 | 77.49 | 3.90 | 2.39 | 1.63 | 0.119 |
| All grades | Percent correct | 57 | 56.63 | 59.84 | 3.21 | 2.29 | 1.40 | 0.167 |

*Notes:* Raw-score differences are measured in points. Percent-correct differences are measured in percentage points. The p-values are two-sided paired t-test p-values for the null hypothesis that the mean paired difference equals zero. No significance stars are shown because none of the tests are statistically significant at the 10 percent level.
