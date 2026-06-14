# Appendix Robustness Analysis: Attendance Outcomes with High Unexcused Absence Outliers Removed

Table A1 Robustness of GROW Attendance Estimates After Trimming High Unexcused Absence Values

|  | Unexcused absence % |  | Excused absence % |  | Total absence % |  |
|---|---:|---:|---:|---:|---:|---:|
|  | (1) | (2) | (3) | (4) | (5) | (6) |
|  | OW | OW + covariates | OW | OW + covariates | OW | OW + covariates |
| JMTES (GROW school) | -1.380*** | -1.380*** | 0.658*** | 0.658*** | -0.723** | -0.723** |
|  | (0.301) | (0.295) | (0.137) | (0.136) | (0.344) | (0.338) |
| JES weighted mean | 6.711 | 6.711 | 1.146 | 1.146 | 7.857 | 7.857 |
| JMTES weighted mean | 5.332 | 5.332 | 1.804 | 1.804 | 7.134 | 7.134 |
| Student covariates | No | Yes | No | Yes | No | Yes |
| Overlap weights | Yes | Yes | Yes | Yes | Yes | Yes |
| Observations | 1,041 | 1,041 | 1,041 | 1,041 | 1,041 | 1,041 |
| Residual df | 1,039 | 1,021 | 1,039 | 1,021 | 1,039 | 1,021 |

Cutoff criterion: Students were excluded if their unexcused absence percentage was above the pooled 95th percentile of the JMTES/JES analytic sample. The cutoff was 23.53%. This removed 54 of 1095 students (4.9%): 1 from JMTES and 53 from JES.

Notes: The table reports overlap-weighted regression estimates after trimming high-end unexcused absence values. The outcome is the percentage of enrolled days missed. Standard errors are in parentheses. Student covariates include grade, gender, race/ethnicity, age, meal-status disadvantage, and entry-code controls. *** p<0.01, ** p<0.05, * p<0.10.

## Discussion

This robustness check trims the highest unexcused absence values because the JES unexcused absence distribution is right-skewed, with a mean notably above the median. The cutoff was set before re-estimating the models at the pooled 95th percentile of unexcused absence percentage (23.53%).

After removing students above this cutoff, the estimated JMTES association with unexcused absences remains negative. In the covariate-adjusted overlap-weighted model, JMTES students had 1.38 percentage points fewer unexcused absences than comparable JES students. The trimmed weighted means were 5.33% for JMTES and 6.71% for JES.

The excused absence result remains positive but smaller in magnitude than the unexcused absence reduction. In the trimmed covariate-adjusted model, JMTES had 0.66 percentage points more excused absences than comparable JES students.

For total absences, the trimmed covariate-adjusted estimate remains negative at -0.72 percentage points. This indicates that the main conclusion of lower overall missed instructional time at JMTES is not driven only by the highest unexcused absence values in the JES distribution.

Overall, the robustness analysis supports the main attendance findings. The size of the unexcused and total absence estimates is somewhat smaller after trimming the upper tail, as expected when extreme high-absence observations are removed, but the direction and statistical significance of the results remain consistent with the primary overlap-weighted analysis.
