# Grade 3 ATLAS G.R.O.W Analysis Results

Source data regenerated from the current GitHub workbook files: `JMTES ATLAS Report_Updated 5.22.26 (PW_ ATLAS).xlsx` and `JES ATLAS Report 25-26_Updated 5.28.26 (PW Titans2026).xlsx`.

## Mean ATLAS Scores

| Subject | Wave | JES Mean | JES n | JMTES Mean | JMTES n |
|---|---:|---:|---:|---:|---:|
| ELA | Summer 2025 | 1044.12 | 113 | 1046.57 | 75 |
| ELA | Fall 2025 |  |  | 1041.79 | 77 |
| ELA | Winter 2025 | 1039.18 | 117 | 1047.17 | 84 |
| ELA | Summer 2026 | 1041.85 | 123 | 1050.61 | 85 |
| Math | Summer 2025 | 1047.19 | 113 | 1047.67 | 75 |
| Math | Fall 2025 | 1031.19 | 105 | 1029.75 | 77 |
| Math | Winter 2025 | 1034.06 | 115 | 1039.25 | 81 |
| Math | Summer 2026 | 1041.48 | 123 | 1047.96 | 85 |
| Science | Fall 2025 |  |  | 1041.66 | 76 |
| Science | Winter 2025 | 1036.58 | 117 | 1047.30 | 81 |
| Science | Summer 2026 | 1043.99 | 123 | 1052.82 | 85 |

## Primary ANCOVA Results

Summer 2025 baseline is used for ELA and Math; Winter 2025 baseline is used for Science because no common prior-year Science score is available.

| Subject | Adjusted treatment effect | p-value | 95% CI | Interpretation |
|---|---:|---:|---:|---|
| ELA | 6.85 | <0.001 | [3.57, 10.13] | Statistically significant positive adjusted effect. |
| Math | 6.42 | <0.001 | [3.07, 9.76] | Statistically significant positive adjusted effect. |
| Science | 2.20 | 0.117 | [-0.55, 4.95] | Not statistically significant. |

## Robustness and Sensitivity Checks

| Subject | DiD-style effect | Gain effect | Robust DiD p | Wilcoxon p | Winsorized gain | Matching effect | Matching matched/total | IPW effect | Permutation p | Bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ELA | 5.42 (p=0.146) | 5.42 (p=0.027) | 0.158 | 0.009 | 5.27 (p=0.014) | 5.38 (p=0.002) | 73/75 | 6.81 (p=0.001) | <0.001 | [3.17, 10.44] |
| Math | 6.27 (p=0.070) | 6.27 (p<0.001) | 0.071 | 0.002 | 5.28 (p<0.001) | 7.67 (p<0.001) | 75/75 | 6.44 (p=0.007) | <0.001 | [2.92, 9.86] |
| Science | -1.47 (p=0.597) | -1.47 (p=0.324) | 0.618 | 0.216 | -1.53 (p=0.260) | 6.12 (p<0.001) | 75/81 | 2.37 (p=0.195) | 0.102 | [-0.58, 5.01] |

## Matching Balance

| Subject | Treated baseline mean | Matched control baseline mean | Mean baseline difference after matching | Mean absolute distance |
|---|---:|---:|---:|---:|
| ELA | 1046.60 | 1046.45 | 0.151 | 0.288 |
| Math | 1047.67 | 1047.75 | -0.080 | 0.293 |
| Science | 1044.49 | 1044.57 | -0.080 | 0.267 |

## Interpretation

The updated Grade 3 analysis shows statistically significant positive primary ANCOVA effects for ELA and Math, and most robustness checks for ELA/Math are directionally consistent. Science remains exploratory because the common baseline is Winter 2025 rather than Summer 2025; the primary ANCOVA and IPW estimates are positive but not statistically significant, while matching is positive. Overall, Grade 3 provides the strongest evidence among the upper elementary analyses for improved ELA and Math ATLAS scores at JMTES.
