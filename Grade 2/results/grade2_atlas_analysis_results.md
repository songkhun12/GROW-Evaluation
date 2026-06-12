# Grade 2 ATLAS G.R.O.W Analysis Results

Source data regenerated from the current GitHub workbook files: `JMTES ATLAS Report_Updated 5.22.26 (PW_ ATLAS).xlsx` and `JES ATLAS Report 25-26_Updated 5.28.26 (PW Titans2026).xlsx`.

## Mean ATLAS Scores

| Subject | Wave | JES Mean | JES n | JMTES Mean | JMTES n |
|---|---:|---:|---:|---:|---:|
| ELA | Summer 2025 | 1047.26 | 88 | 1043.11 | 63 |
| ELA | Winter 2025 | 1047.46 | 89 | 1049.14 | 65 |
| ELA | Summer 2026 | 1050.68 | 90 | 1053.05 | 66 |
| Math | Summer 2025 | 1049.55 | 87 | 1048.56 | 63 |
| Math | Winter 2025 | 1044.62 | 88 | 1045.72 | 64 |
| Math | Summer 2026 | 1049.37 | 90 | 1050.70 | 66 |

## Primary ANCOVA Results

Summer 2025 baseline is used for ELA and Math.

| Subject | Adjusted treatment effect | p-value | 95% CI | Interpretation |
|---|---:|---:|---:|---|
| ELA | 4.51 | 0.133 | [-1.37, 10.38] | Not statistically significant. |
| Math | 1.26 | 0.451 | [-2.02, 4.54] | Not statistically significant. |

## Robustness and Sensitivity Checks

| Subject | DiD-style effect | Gain effect | Robust DiD p | Wilcoxon p | Winsorized gain | Matching effect | Matching matched/total | IPW effect | Permutation p | Bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ELA | 6.85 (p=0.139) | 6.85 (p=0.051) | 0.131 | 0.144 | 5.70 (p=0.072) | 6.05 (p=0.092) | 63/63 | 4.25 (p=0.185) | 0.141 | [-1.51, 11.00] |
| Math | 1.52 (p=0.665) | 1.52 (p=0.395) | 0.655 | 0.423 | 1.45 (p=0.371) | -1.41 (p=0.375) | 63/63 | 1.20 (p=0.623) | 0.452 | [-1.87, 4.47] |

## Matching Balance

| Subject | Treated baseline mean | Matched control baseline mean | Mean baseline difference after matching | Mean absolute distance |
|---|---:|---:|---:|---:|
| ELA | 1043.11 | 1043.10 | 0.016 | 0.460 |
| Math | 1048.56 | 1048.62 | -0.063 | 0.317 |

## Interpretation

The updated Grade 2 analysis is directionally positive for ELA and modestly positive or mixed for Math, but the primary ANCOVA estimates are not statistically significant at p < .05. ELA shows the strongest suggestive evidence across gain-score and matching checks, while Math does not show a consistent impact signal. Therefore, Grade 2 results should be interpreted as suggestive for ELA but not conclusive evidence of a G.R.O.W impact.
