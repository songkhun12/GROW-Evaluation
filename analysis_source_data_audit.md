# Source Data and Output Audit

This audit double-checks that the attendance and referral analyses pull values from the intended source files and that key generated results match the source data.

## Source files

The repository contains root-level at-risk report CSVs and copies in `Attendance Evaluation/`. The root-level and `Attendance Evaluation/` copies are byte-identical for both schools:

| School | Root file | Attendance Evaluation file | Rows | Report school days | Hash check |
|---|---|---|---:|---:|---|
| JMTES | `JMTES At Risk Report with Absence Percentages.csv` | `Attendance Evaluation/JMTES At Risk Report with Absence Percentages.csv` | 419 | 159 | Match |
| JES | `JES At Risk Report with Absence Percentages.csv` | `Attendance Evaluation/JES At Risk Report with Absence Percentages.csv` | 676 | 170 | Match |

Because the files match exactly, the attendance R Markdown and referral R Markdown are using the same underlying source data even though the attendance analysis reads from `Attendance Evaluation/` and the referral analysis reads the parent-directory copies.

## Attendance checks

The attendance descriptive statistics were recalculated directly from the source columns:

| Outcome | JMTES mean | JES mean | Source column |
|---|---:|---:|---|
| Unexcused absence % | 5.4443436754 | 9.0087721893 | `Unexcused Absence %` |
| Excused absence % | 1.7890930788 | 1.2872633136 | `Excused Absence %` |
| Total absence % | 7.2319331742 | 10.2957100592 | `Total Absence %` |

These recalculated values match `Attendance Evaluation/jmtes_jes_attendance_descriptive_statistics.csv`.

The unexcused absence trimming robustness summary was also checked against the source files. The cutoff is 23.53%, and the source data confirm that 54 students are above that cutoff: 1 from JMTES and 53 from JES.

## Referral checks

The referral analytic file contains 1,095 rows, matching the combined source files. Referral outcome totals were recalculated directly from the source columns and match `Referral Evaluation/jmtes_jes_referral_poisson_results.csv`:

| Outcome | Source columns | Total events |
|---|---|---:|
| `classroom_total` | `L-1` + `L-2` + `L-3` + `L-4` | 574 |
| `classroom_l1` | `L-1` | 45 |
| `classroom_l2` | `L-2` | 258 |
| `classroom_l3` | `L-3` | 260 |
| `classroom_l4` | `L-4` | 11 |
| `bus_total` | `Local` + `Transportation 1` + `Transportation 2` + `Transportation 3` | 122 |
| `bus_l1` | `Local` + `Transportation 1` | 1 |
| `bus_l2` | `Transportation 2` | 115 |
| `bus_l3` | `Transportation 3` | 6 |

## Conclusion

The audit confirms that the analyses use the intended JMTES and JES at-risk report files, that the duplicate file locations contain identical data, and that the key descriptive and referral outcome values in the generated outputs match direct recalculations from the source files.
