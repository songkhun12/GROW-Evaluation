# Grade 4 ATLAS G.R.O.W Analysis Results

Source data regenerated from the current GitHub workbook files: `JMTES ATLAS Report_Updated 5.22.26 (PW_ ATLAS).xlsx` and `JES ATLAS Report 25-26_Updated 5.28.26 (PW Titans2026).xlsx`.

## Mean ATLAS Scores

| Subject | Wave | JES Mean | JES n | JMTES Mean | JMTES n |
|---|---:|---:|---:|---:|---:|
| ELA | Summer 2025 | 1041.55 | 109 | 1051.83 | 60 |
| ELA | Fall 2025 |  |  | 1042.70 | 69 |
| ELA | Winter 2025 | 1040.14 | 115 | 1049.86 | 72 |
| ELA | Summer 2026 | 1044.08 | 120 | 1054.76 | 76 |
| Math | Summer 2025 | 1037.57 | 109 | 1046.02 | 60 |
| Math | Fall 2025 | 1032.88 | 102 | 1036.04 | 70 |
| Math | Winter 2025 | 1034.07 | 112 | 1042.50 | 72 |
| Math | Summer 2026 | 1039.65 | 121 | 1052.49 | 76 |
| Science | Summer 2025 | 1043.79 | 109 | 1055.47 | 60 |
| Science | Fall 2025 |  |  | 1044.89 | 71 |
| Science | Winter 2025 | 1040.32 | 113 | 1049.96 | 72 |
| Science | Summer 2026 | 1044.61 | 121 | 1053.75 | 76 |

## Primary ANCOVA Results

Summer 2025 prior-year scores are used as the common baseline for ELA, Math, and Science. This is preferable to DiD as the primary analysis because there is only one common pre-treatment baseline suitable for all subjects and the parallel-trends assumption cannot be tested with the available files.

| Subject | Adjusted treatment effect | p-value | 95% CI | Interpretation |
|---|---:|---:|---:|---|
| ELA | 6.14 | <0.001 | [2.97, 9.32] | Statistically significant positive adjusted effect. |
| Math | 8.20 | <0.001 | [5.06, 11.35] | Statistically significant positive adjusted effect. |
| Science | 3.62 | 0.030 | [0.36, 6.89] | Statistically significant positive adjusted effect. |

## Robustness and Sensitivity Checks

| Subject | DiD-style effect | Gain effect | Robust DiD p | Wilcoxon p | Winsorized gain | Matching effect | Matching matched/total | IPW effect | Permutation p | Bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ELA | 2.74 (p=0.445) | 2.74 (p=0.125) | 0.471 | 0.045 | 2.56 (p=0.092) | 3.34 (p=0.020) | 58/60 | 5.67 (p=0.015) | <0.001 | [2.91, 9.48] |
| Math | 6.18 (p=0.112) | 6.18 (p<0.001) | 0.104 | <0.001 | 5.22 (p<0.001) | 10.08 (p<0.001) | 60/60 | 8.27 (p=0.001) | <0.001 | [5.22, 11.60] |
| Science | 0.04 (p=0.990) | 0.04 (p=0.983) | 0.991 | 0.866 | -0.04 (p=0.980) | 5.04 (p=0.004) | 54/60 | 3.03 (p=0.141) | 0.017 | [0.62, 6.73] |

## Matching Balance

| Subject | Treated baseline mean | Matched control baseline mean | Mean baseline difference after matching | Mean absolute distance |
|---|---:|---:|---:|---:|
| ELA | 1050.53 | 1050.38 | 0.155 | 0.431 |
| Math | 1046.02 | 1046.07 | -0.050 | 0.317 |
| Science | 1052.56 | 1052.56 | 0.000 | 0.148 |

## Interpretation

Grade 4 shows statistically significant positive primary ANCOVA effects for ELA, Math, and Science. Robustness checks are strongest and most consistent for Math, favorable for ELA, and more mixed for Science because gain-style checks are near zero while ANCOVA, matching, permutation, and bootstrap checks are positive. Overall, Grade 4 provides evidence of a G.R.O.W impact, especially for ELA and Math, with Science positive but somewhat less robust.
