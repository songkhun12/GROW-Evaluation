/****************************************************************************************
Student Incentive Distribution Analysis

Assumption: the student incentive tracker or merged incentive/at-risk dataset is already
open in Stata. The code below uses the variable names that Stata commonly creates after
importing the committed merged CSV with `import delimited, varnames(1) case(preserve)`.
If your open dataset uses different variable names, update only the local macros in the
configuration section.
****************************************************************************************/

version 17.0
set more off

*-------------------------------------------------------------------------------
* Configuration: update these local macros if your open dataset has different
* Stata variable names.
*-------------------------------------------------------------------------------
local total_incentive "v202526IncentiveTOTAL"

local inc1_aug "AugDec2025IncentivesIncentive1EALessonActivities"
local inc1_jan "JanMay2026IncentivesIncentive1EALessonActivities"

local inc2_aug "AugDec2025IncentivesIncentive21HRFinLiteracyModuleOnline"
local inc2_jan "JanMay2026IncentivesIncentive21HRFinLiteracyModuleOnline"

local inc3_aug "AugDec2025IncentivesIncentive3MetReadingGoal"
local inc3_jan "JanMay2026IncentivesIncentive3MetReadingGoal"

local inc4_aug "AugDec2025IncentivesIncentive4MetBehaviorGoal"
local inc4_jan "JanMay2026IncentivesIncentive4MetBehaviorGoal"

local inc5_aug "AugDec2025IncentivesIncentive5Missthreedaysorless"
local inc5_jan "JanMay2026IncentivesIncentive5Missthreedaysorless"

*-------------------------------------------------------------------------------
* Validate required variables.
*-------------------------------------------------------------------------------
foreach v in `total_incentive' `inc1_aug' `inc1_jan' `inc2_aug' `inc2_jan' ///
    `inc3_aug' `inc3_jan' `inc4_aug' `inc4_jan' `inc5_aug' `inc5_jan' {
    capture confirm variable `v'
    if _rc {
        di as error "Required variable not found: `v'"
        di as error "Update the configuration locals at the top of this do file to match your open dataset."
        exit 111
    }
}

*-------------------------------------------------------------------------------
* Total 2025-26 incentive dollars distributed.
*-------------------------------------------------------------------------------
capture confirm numeric variable `total_incentive'
if _rc {
    destring `total_incentive', replace ignore("$, ") force
}

quietly summarize `total_incentive', meanonly
di as text "Total 2025-26 incentives distributed: " as result %12.2fc r(sum)
di as text "Average 2025-26 incentive per student: " as result %12.2fc r(mean)
di as text "Number of students in open dataset: " as result %12.0fc r(N)

*-------------------------------------------------------------------------------
* Number and percent of students receiving each incentive value.
* Includes all observed incentive values, not only 0, 100, 200, and 300.
*-------------------------------------------------------------------------------
preserve
    generate incentive_total_value = `total_incentive'
    replace incentive_total_value = 0 if missing(incentive_total_value)

    contract incentive_total_value, freq(students)
    egen total_students = total(students)
    generate percent = students / total_students * 100
    format percent %9.1f

    di as text "Distribution of students by total 2025-26 incentive amount"
    list incentive_total_value students percent, noobs clean

    graph pie students, over(incentive_total_value) plabel(_all percent, format(%4.1f)) ///
        title("Distribution of Students by Total 2025-26 Incentive Amount") ///
        note("Slices are all observed values of 2025-26 Incentive TOTAL.")
    graph export "Incentive Tracker/incentive_total_distribution_pie.png", replace width(2000)
restore

*-------------------------------------------------------------------------------
* Completion indicators by incentive type.
* A student completed an incentive if either Aug-Dec 2025 or Jan-May 2026 equals 1.
*-------------------------------------------------------------------------------
foreach v in `inc1_aug' `inc1_jan' `inc2_aug' `inc2_jan' `inc3_aug' `inc3_jan' ///
    `inc4_aug' `inc4_jan' `inc5_aug' `inc5_jan' {
    capture confirm numeric variable `v'
    if _rc {
        destring `v', replace ignore(" ") force
    }
}

generate byte completed_inc1 = (`inc1_aug' == 1 | `inc1_jan' == 1)
generate byte completed_inc2 = (`inc2_aug' == 1 | `inc2_jan' == 1)
generate byte completed_inc3 = (`inc3_aug' == 1 | `inc3_jan' == 1)
generate byte completed_inc4 = (`inc4_aug' == 1 | `inc4_jan' == 1)
generate byte completed_inc5 = (`inc5_aug' == 1 | `inc5_jan' == 1)

label define completion_status 0 "Not completed" 1 "Completed", replace
foreach v in completed_inc1 completed_inc2 completed_inc3 completed_inc4 completed_inc5 {
    label values `v' completion_status
}

local incentive_label1 "Incentive 1: EA Lesson Activities"
local incentive_label2 "Incentive 2: 1 HR Financial Literacy Module Online"
local incentive_label3 "Incentive 3: Met Reading Goal"
local incentive_label4 "Incentive 4: Met Behavior Goal"
local incentive_label5 "Incentive 5: Miss Three Days or Less"

local i = 1
foreach v in completed_inc1 completed_inc2 completed_inc3 completed_inc4 completed_inc5 {
    local label "`incentive_label`i''"

    di as text "Completion distribution for `label'"
    tabulate `v', missing

    graph pie, over(`v') plabel(_all percent, format(%4.1f)) ///
        title("`label'") ///
        subtitle("Completed vs. not completed")
    graph export "Incentive Tracker/incentive`i'_completion_pie.png", replace width(2000)

    local ++i
}
