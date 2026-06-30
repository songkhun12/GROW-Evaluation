# Difference-in-Differences Model for Financial Literacy Percent-Correct Scores

This AER-style table reports a pre-post difference-in-differences specification for financial literacy percent-correct scores. Percent-correct outcomes use grade-specific test lengths: Grade 3 has 10 questions, while Grades 4 and 5 have 11 questions. The model includes student fixed effects; therefore, time-invariant main effects for Online, Activities, Online × Activities, and Grade are absorbed and are not separately identified in the fixed-effects regression.

| Variable | Coefficient | Standard error |
|---|---:|---:|
| Post | -9.09 | (17.53) |
| Post × Online | 0.91 | (4.84) |
| Post × Activities | 11.95 | (17.95) |
| Post × Online × Activities | Omitted | — |
| Student fixed effects | Yes |  |
| Grade 4 and Grade 5 indicators | Absorbed; Grade 3 reference |  |
| Observations | 114 |  |
| Students | 57 |  |

*Notes:* The dependent variable is percent correct on the financial literacy assessment. Coefficients are measured in percentage points. `Post` is the pre-post change for the baseline group: students with neither online-module completion nor Economics Arkansas activity participation. `Post × Online` is the additional pre-post change associated with online-module completion, holding activity participation constant where supported by the data. `Post × Activities` is the additional pre-post change associated with Economics Arkansas activity participation, holding online-module completion constant where supported by the data. The `Post × Online × Activities` term is not separately identified because the dataset contains no online-only students; all online-module participants also participated in Economics Arkansas activities. Standard errors shown are from the first-difference equivalent with the collinear triple interaction omitted. Results are descriptive and should not be interpreted as causal effects of curriculum components.
