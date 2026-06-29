# Student Incentive Tracker Source Audit

## Purpose

This audit checks whether the Student Incentive Tracker workbook currently present in the repository contains the second-semester Jan-May 2026 incentive columns needed for the recoded CSV.

## Source workbook checked

`SROI/Data/GROW Student Incentive Tracking (as of 2.3.26) (PW_ 2025Data).xlsx`

## Finding

The workbook currently in the repository only exposes populated worksheet cells through spreadsheet column **Q** on the student/classroom sheets. That corresponds to the first incentive set ending with the rewards column. The workbook file name is also dated **as of 2.3.26**, which is before the 5.22.26 second-semester deposit date referenced in the requested Jan-May 2026 columns.

The requested Jan-May 2026 fields are not present as populated worksheet columns in this repository copy of the workbook:

- Jan-May 2026 Incentive 1 - EA Lesson Activities
- Jan-May 2026 Incentive 2 - 1 HR Financial Literacy Module Online
- Jan-May 2026 Incentive 3 - Met Reading Goal
- Jan-May 2026 think-time count
- Jan-May 2026 Incentive 4 - Met Behavior Goal
- Jan-May 2026 missed-days count
- Jan-May 2026 Incentive 5 - Miss three days or less
- Jan-May 2026 Teacher Verification
- Spring 2026 Rewards
- 2nd semester incentives deposited (5.22.26)
- 2025-26 Incentive TOTAL

## Implication

The Jan-May 2026 values cannot be accurately extracted from the workbook currently stored in the repository. Filling those values from the current source would require fabricating data. A newer tracker workbook containing the Jan-May 2026 columns is needed to produce a complete recoded CSV with both incentive periods populated.

## Current recoding rule

For columns that are present in the source workbook, exact check marks are recoded to `1`, exact `X` values are recoded to `0`, and empty cells remain empty.
