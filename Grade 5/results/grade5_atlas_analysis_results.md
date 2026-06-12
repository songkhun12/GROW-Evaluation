# Grade 5 ATLAS G.R.O.W Analysis Results

Source data regenerated from the current GitHub workbook files: `JMTES ATLAS Report_Updated 5.22.26 (PW_ ATLAS).xlsx` and `JES ATLAS Report 25-26_Updated 5.28.26 (PW Titans2026).xlsx`.

## Mean ATLAS Scores

| Subject | Wave | JES Mean | JES n | JMTES Mean | JMTES n |
|---|---:|---:|---:|---:|---:|
| ELA | Summer 2025 | 1041.66 | 92 | 1055.88 | 34 |
| ELA | Fall 2025 |  |  | 1045.70 | 44 |
| ELA | Winter 2025 | 1041.48 | 92 | 1046.86 | 51 |
| ELA | Summer 2026 | 1045.16 | 98 | 1050.58 | 52 |
| Math | Summer 2025 | 1038.43 | 91 | 1052.38 | 34 |
| Math | Fall 2025 | 1037.23 | 87 | 1038.27 | 48 |
| Math | Winter 2025 | 1034.62 | 95 | 1043.37 | 51 |
| Math | Summer 2026 | 1040.38 | 98 | 1046.13 | 52 |
| Science | Summer 2025 | 1041.40 | 92 | 1054.68 | 34 |
| Science | Fall 2025 |  |  | 1046.17 | 46 |
| Science | Winter 2025 | 1042.13 | 93 | 1048.43 | 51 |
| Science | Summer 2026 | 1042.55 | 98 | 1052.98 | 52 |

## Primary ANCOVA Results

Summer 2025 prior-year scores are used as the common baseline for ELA, Math, and Science. This is preferable to DiD as the primary analysis because there is only one common pre-treatment baseline suitable for all subjects and the parallel-trends assumption cannot be tested with the available files.

| Subject | Adjusted treatment effect | p-value | 95% CI | Interpretation |
|---|---:|---:|---:|---|
| ELA | -1.56 | 0.391 | [-5.13, 2.01] | Not statistically significant. |
| Math | -1.05 | 0.572 | [-4.68, 2.58] | Not statistically significant. |
| Science | 4.23 | 0.030 | [0.40, 8.06] | Statistically significant positive adjusted effect. |

## Robustness and Sensitivity Checks

| Subject | DiD-style effect | Gain effect | Robust DiD p | Wilcoxon p | Winsorized gain | Matching effect | Matching matched/total | IPW effect | Permutation p | Bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ELA | -6.09 (p=0.092) | -6.09 (p<0.001) | 0.128 | 0.002 | -5.46 (p<0.001) | -1.88 (p=0.231) | 32/34 | -4.19 (p=0.085) | 0.335 | [-4.88, 2.00] |
| Math | -3.12 (p=0.505) | -3.12 (p=0.082) | 0.529 | 0.033 | -3.31 (p=0.030) | 0.31 (p=0.876) | 32/34 | -0.75 (p=0.794) | 0.547 | [-4.30, 2.25] |
| Science | -0.37 (p=0.916) | -0.37 (p=0.851) | 0.927 | 0.928 | -0.41 (p=0.828) | 2.39 (p=0.223) | 31/34 | 2.32 (p=0.320) | 0.023 | [0.53, 8.29] |

## Matching Balance

| Subject | Treated baseline mean | Matched control baseline mean | Mean baseline difference after matching | Mean absolute distance |
|---|---:|---:|---:|---:|
| ELA | 1054.16 | 1054.12 | 0.031 | 0.531 |
| Math | 1050.28 | 1050.28 | 0.000 | 0.500 |
| Science | 1052.23 | 1052.23 | 0.000 | 0.323 |

## Interpretation

Grade 5 does not show a positive adjusted impact for ELA or Math in the primary ANCOVA after accounting for the higher JMTES Summer 2025 baselines. Science shows a statistically significant positive primary ANCOVA effect, but the gain-score and DiD-style checks are near zero or negative and matching/IPW are not statistically significant. Overall, Grade 5 evidence is inconclusive: there is no evidence of ELA or Math improvement attributable to G.R.O.W, while Science is positive in ANCOVA but should be interpreted cautiously.
