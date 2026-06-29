/****************************************************************************************
  Stata replication of the overlap-weighted Poisson referral analysis for Tables 7 and 8.
  The file uses the exported referral analysis dataset containing the propensity scores
  and overlap weights used in the report, then runs the reported covariate-adjusted
  Poisson models with robust standard errors and enrollment-days exposure.
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the other project do-files.
version 17.0

* Prevent Stata from pausing output during long model output.
set more off

* Clear any data currently in memory before opening the referral analysis file.
clear

* Define the exported referral analysis file with propensity scores and overlap weights.
local input_csv "Referral Evaluation/jmtes_jes_referral_student_data.csv"

* If running from inside Referral Evaluation, fall back to the local file name.
capture confirm file "`input_csv'"
if _rc {
    local input_csv "jmtes_jes_referral_student_data.csv"
}

* Stop with a clear error if the referral analysis file is missing.
capture confirm file "`input_csv'"
if _rc {
    di as error "Input file not found: `input_csv'"
    exit 601
}

* Open the student-level referral analysis dataset.
import delimited using "`input_csv'", clear varnames(1)

* Confirm that every variable needed for the propensity diagnostics and Poisson models exists.
foreach var in school jmtes grade female black age meal_status entry_code enrollment_days overlap_weight propensity classroom_total classroom_severity_points bus_total bus_severity_points classroom_l1 classroom_l2 classroom_l3 classroom_l4 bus_l1 bus_l2 bus_l3 {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in the open dataset."
        exit 111
    }
}

* Ensure the treatment indicator is numeric after import.
replace jmtes = real(string(jmtes))

* Ensure the female indicator is numeric after import.
replace female = real(string(female))

* Ensure the Black race/ethnicity indicator is numeric after import.
replace black = real(string(black))

* Store the reported propensity score under a descriptive Stata name.
gen double propensity_score = propensity

* Ensure the overlap weight variable is numeric after import.
replace overlap_weight = real(string(overlap_weight))

* Convert grade to a numeric categorical variable for factor-variable notation.
encode grade, gen(grade_cat)

* Convert meal-status values to strings if Stata imported them as numeric.
capture confirm string variable meal_status
if _rc {
    tostring meal_status, gen(meal_status_str) format(%02.0f)
}
else {
    gen str20 meal_status_str = strtrim(meal_status)
}

* Convert meal-status strings to a numeric categorical variable.
encode meal_status_str, gen(meal_status_cat)

* Convert entry-code values to strings if Stata imported them as numeric.
capture confirm string variable entry_code
if _rc {
    tostring entry_code, gen(entry_code_str)
}
else {
    gen str20 entry_code_str = strtrim(entry_code)
}

* Convert entry-code strings to a numeric categorical variable.
encode entry_code_str, gen(entry_code_cat)

* Show the propensity-score and overlap-weight step before outcome models.
di as text _newline "Propensity score and overlap weight diagnostics"
summarize propensity_score overlap_weight
tabstat propensity_score overlap_weight, by(school) statistics(mean sd min p25 median p75 max n) columns(statistics) format(%9.3f)

* Define the shared covariate adjustment used in the reported referral models.
global referral_covariates i.grade_cat female black age i.meal_status_cat i.entry_code_cat

* Count the full analytic sample once for posting and assertions.
count
scalar analytic_n = r(N)

* Create a temporary dataset for Table 7 and Table 8 model results.
tempfile referral_results

* Open a postfile to collect model estimates and reporting quantities.
postfile referral_out str24 table_name str36 outcome double coefficient robust_se irr percent_difference jes_rate jmtes_rate observations events using `referral_results', replace

* Define a reusable Stata program for one covariate-adjusted overlap-weighted Poisson model.
program define run_referral_poisson
    * Require the outcome variable, label, and table name as program options.
    syntax, Outcome(name) Label(string) Table(string)

    * Show which model is being estimated.
    di as text _newline "Estimating `table': `label'"

    * Estimate the overlap-weighted Poisson model with robust standard errors and exposure.
    poisson `outcome' jmtes $referral_covariates [pw = overlap_weight], exposure(enrollment_days) vce(robust)

    * Store the JMTES coefficient from the displayed Poisson model.
    scalar b_jmtes = _b[jmtes]

    * Store the robust standard error for the JMTES coefficient.
    scalar se_jmtes = _se[jmtes]

    * Convert the coefficient to an incidence rate ratio.
    scalar irr_jmtes = exp(b_jmtes)

    * Convert the incidence rate ratio to a percent difference.
    scalar pct_diff = 100 * (irr_jmtes - 1)

    * Calculate the weighted JES referral rate per 170 enrolled days.
    generate double __event_jes = overlap_weight * `outcome' if jmtes == 0
    generate double __days_jes = overlap_weight * enrollment_days if jmtes == 0
    summarize __event_jes, meanonly
    scalar jes_events_w = r(sum)
    summarize __days_jes, meanonly
    scalar jes_days_w = r(sum)
    scalar jes_rate_170 = jes_events_w / jes_days_w * 170
    drop __event_jes __days_jes

    * Calculate the weighted JMTES referral rate per 170 enrolled days.
    generate double __event_jmtes = overlap_weight * `outcome' if jmtes == 1
    generate double __days_jmtes = overlap_weight * enrollment_days if jmtes == 1
    summarize __event_jmtes, meanonly
    scalar jmtes_events_w = r(sum)
    summarize __days_jmtes, meanonly
    scalar jmtes_days_w = r(sum)
    scalar jmtes_rate_170 = jmtes_events_w / jmtes_days_w * 170
    drop __event_jmtes __days_jmtes

    * Count the unweighted number of referral events for the outcome.
    summarize `outcome', meanonly
    scalar event_count = r(sum)

    * Post the model row to the temporary results file.
    post referral_out ("`table'") ("`label'") (b_jmtes) (se_jmtes) (irr_jmtes) (pct_diff) (jes_rate_170) (jmtes_rate_170) (analytic_n) (event_count)
end

* Run Table 7: total and severity-weighted school and bus referral models.
run_referral_poisson, outcome(classroom_total) label("School-based referrals") table("Table 7")
run_referral_poisson, outcome(classroom_severity_points) label("School severity-weighted") table("Table 7")
run_referral_poisson, outcome(bus_total) label("Bus referrals") table("Table 7")
run_referral_poisson, outcome(bus_severity_points) label("Bus severity-weighted") table("Table 7")

* Run Table 8: school referral severity-level models.
run_referral_poisson, outcome(classroom_l1) label("Classroom L-I") table("Table 8")
run_referral_poisson, outcome(classroom_l2) label("Classroom L-II") table("Table 8")
run_referral_poisson, outcome(classroom_l3) label("Classroom L-III") table("Table 8")
run_referral_poisson, outcome(classroom_l4) label("Classroom L-IV") table("Table 8")

* Report Bus Level I as unavailable because the reported table marks this rare-event model n/a.
di as text _newline "Skipping Table 8: Bus L-I because the reported model is n/a for one total event."
summarize bus_l1, meanonly
scalar bus_l1_events = r(sum)
generate double __event_jes_busl1 = overlap_weight * bus_l1 if jmtes == 0
generate double __days_jes_busl1 = overlap_weight * enrollment_days if jmtes == 0
summarize __event_jes_busl1, meanonly
scalar bus_l1_jes_events_w = r(sum)
summarize __days_jes_busl1, meanonly
scalar bus_l1_jes_days_w = r(sum)
generate double __event_jmtes_busl1 = overlap_weight * bus_l1 if jmtes == 1
generate double __days_jmtes_busl1 = overlap_weight * enrollment_days if jmtes == 1
summarize __event_jmtes_busl1, meanonly
scalar bus_l1_jmtes_events_w = r(sum)
summarize __days_jmtes_busl1, meanonly
scalar bus_l1_jmtes_days_w = r(sum)
scalar bus_l1_jes_rate = bus_l1_jes_events_w / bus_l1_jes_days_w * 170
scalar bus_l1_jmtes_rate = bus_l1_jmtes_events_w / bus_l1_jmtes_days_w * 170
drop __event_jes_busl1 __days_jes_busl1 __event_jmtes_busl1 __days_jmtes_busl1
post referral_out ("Table 8") ("Bus L-I") (.) (.) (.) (.) (bus_l1_jes_rate) (bus_l1_jmtes_rate) (analytic_n) (bus_l1_events)

* Run Table 8: remaining bus referral severity-level models.
run_referral_poisson, outcome(bus_l2) label("Bus L-II") table("Table 8")
run_referral_poisson, outcome(bus_l3) label("Bus L-III") table("Table 8")

* Close the model-results postfile.
postclose referral_out

* Open the posted model results.
use `referral_results', clear

* Format numeric columns to match report precision.
format coefficient robust_se irr jes_rate jmtes_rate %9.3f
format percent_difference %9.1f
format observations events %9.0f

* Print Table 7 replication rows.
di as text _newline "Table 7 replication results"
list outcome coefficient robust_se irr percent_difference jes_rate jmtes_rate observations events if table_name == "Table 7", noobs abbreviate(24) separator(0)

* Print Table 8 replication rows.
di as text _newline "Table 8 replication results"
list outcome coefficient robust_se irr percent_difference jes_rate jmtes_rate observations events if table_name == "Table 8", noobs abbreviate(24) separator(0)

* Assert Table 7 matches the reported values after rounding.
assert abs(coefficient + 0.957) < 0.0015 if outcome == "School-based referrals"
assert abs(robust_se - 0.200) < 0.0015 if outcome == "School-based referrals"
assert abs(irr - 0.384) < 0.0015 if outcome == "School-based referrals"
assert abs(jes_rate - 0.665) < 0.0015 if outcome == "School-based referrals"
assert abs(jmtes_rate - 0.256) < 0.0015 if outcome == "School-based referrals"
assert abs(coefficient + 0.790) < 0.0015 if outcome == "School severity-weighted"
assert abs(robust_se - 0.198) < 0.0015 if outcome == "School severity-weighted"
assert abs(irr - 0.454) < 0.0015 if outcome == "School severity-weighted"
assert abs(jes_rate - 1.549) < 0.0015 if outcome == "School severity-weighted"
assert abs(jmtes_rate - 0.708) < 0.0015 if outcome == "School severity-weighted"
assert abs(coefficient + 1.815) < 0.0015 if outcome == "Bus referrals"
assert abs(robust_se - 0.329) < 0.0015 if outcome == "Bus referrals"
assert abs(irr - 0.163) < 0.0015 if outcome == "Bus referrals"
assert abs(jes_rate - 0.163) < 0.0015 if outcome == "Bus referrals"
assert abs(jmtes_rate - 0.027) < 0.0015 if outcome == "Bus referrals"
assert abs(coefficient + 1.785) < 0.0015 if outcome == "Bus severity-weighted"
assert abs(robust_se - 0.336) < 0.0015 if outcome == "Bus severity-weighted"
assert abs(irr - 0.168) < 0.0015 if outcome == "Bus severity-weighted"
assert abs(jes_rate - 0.332) < 0.0015 if outcome == "Bus severity-weighted"
assert abs(jmtes_rate - 0.057) < 0.0015 if outcome == "Bus severity-weighted"

* Assert Table 8 matches the reported values after rounding.
assert abs(coefficient + 3.226) < 0.0015 if outcome == "Classroom L-I"
assert abs(robust_se - 0.996) < 0.0015 if outcome == "Classroom L-I"
assert abs(irr - 0.040) < 0.0015 if outcome == "Classroom L-I"
assert abs(coefficient + 1.554) < 0.0015 if outcome == "Classroom L-II"
assert abs(robust_se - 0.317) < 0.0015 if outcome == "Classroom L-II"
assert abs(irr - 0.211) < 0.0015 if outcome == "Classroom L-II"
assert abs(coefficient + 0.472) < 0.0015 if outcome == "Classroom L-III"
assert abs(robust_se - 0.197) < 0.0015 if outcome == "Classroom L-III"
assert abs(irr - 0.624) < 0.0015 if outcome == "Classroom L-III"
assert abs(coefficient - 0.755) < 0.0015 if outcome == "Classroom L-IV"
assert abs(robust_se - 0.598) < 0.0015 if outcome == "Classroom L-IV"
assert abs(irr - 2.127) < 0.0015 if outcome == "Classroom L-IV"
assert missing(coefficient) if outcome == "Bus L-I"
assert abs(coefficient + 2.112) < 0.0015 if outcome == "Bus L-II"
assert abs(robust_se - 0.383) < 0.0015 if outcome == "Bus L-II"
assert abs(irr - 0.121) < 0.0015 if outcome == "Bus L-II"
assert abs(coefficient + 0.163) < 0.0015 if outcome == "Bus L-III"
assert abs(robust_se - 0.750) < 0.0015 if outcome == "Bus L-III"
assert abs(irr - 0.849) < 0.0015 if outcome == "Bus L-III"
assert observations == 1093
