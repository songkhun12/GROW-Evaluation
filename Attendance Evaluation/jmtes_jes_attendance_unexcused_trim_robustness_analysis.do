/****************************************************************************************
  Appendix D. Robustness of GROW Attendance Estimates After Trimming High Unexcused
  Absence Values

  Purpose:
    Reproduce Table D1 by excluding students whose unexcused absence percentage is above
    the pooled 95th percentile cutoff (23.53%) and then re-estimating the overlap-
    weighted attendance regressions with and without student covariates.

  Required input:
    Attendance Evaluation/jmtes_jes_overlap_weighted_attendance_student_data.csv

  Example command from the repository root:
    do "Attendance Evaluation/jmtes_jes_attendance_unexcused_trim_robustness_analysis.do"
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the project replication files.
version 17.0

* Do not pause output; the reviewer asked that regression results be shown in Stata.
set more off

* Clear any data currently in memory before opening the attendance analysis file.
clear

* Define the attendance analysis file with propensity scores and overlap weights.
local input_csv "Attendance Evaluation/jmtes_jes_overlap_weighted_attendance_student_data.csv"

* Fall back to the local filename when running from inside Attendance Evaluation.
capture confirm file "`input_csv'"
if _rc {
    local input_csv "jmtes_jes_overlap_weighted_attendance_student_data.csv"
}

* Stop with a clear error if the required analysis file is missing.
capture confirm file "`input_csv'"
if _rc {
    di as error "Input file not found: `input_csv'"
    exit 601
}

* Open the full student-level attendance analysis file.
import delimited using "`input_csv'", clear varnames(1)

* Confirm the variables needed for trimming, weighting, and regressions are present.
foreach var in school jmtes grade female black age meal_status entry_code unexcused_pct ///
    excused_pct total_pct propensity overlap_weight {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in `input_csv'."
        exit 111
    }
}

* Coerce numeric fields in case Stata imports any field as a string.
replace jmtes = real(string(jmtes))
replace female = real(string(female))
replace black = real(string(black))
replace age = real(string(age))
replace unexcused_pct = real(string(unexcused_pct))
replace excused_pct = real(string(excused_pct))
replace total_pct = real(string(total_pct))
replace propensity = real(string(propensity))
replace overlap_weight = real(string(overlap_weight))

* Store the propensity score under a descriptive variable name for diagnostics.
gen double propensity_score = propensity

* Confirm the starting sample size reported in Appendix D.
count
assert r(N) == 1093

* Define the pooled 95th-percentile unexcused absence cutoff reported in Appendix D.
scalar trim_cutoff = 23.53

* Mark students above the pooled 95th percentile of unexcused absence percentage.
gen byte trimmed_high_unexcused = unexcused_pct > trim_cutoff

* Show and verify the number of trimmed students overall and by school.
di as text _newline "Students above pooled 95th-percentile unexcused absence cutoff"
tab school trimmed_high_unexcused
count if trimmed_high_unexcused == 1
assert r(N) == 55
count if trimmed_high_unexcused == 1 & jmtes == 1
assert r(N) == 2
count if trimmed_high_unexcused == 1 & jmtes == 0
assert r(N) == 53

* Keep the trimmed analytic sample for Table D1.
keep if trimmed_high_unexcused == 0

* Confirm the trimmed analytic sample size.
count
assert r(N) == 1038

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

* Encode meal-status strings as numeric categories.
encode meal_status_str, gen(meal_status_cat)

* Convert entry-code values to strings if Stata imported them as numeric.
capture confirm string variable entry_code
if _rc {
    tostring entry_code, gen(entry_code_str)
}
else {
    gen str20 entry_code_str = strtrim(entry_code)
}

* Encode entry-code strings as numeric categories.
encode entry_code_str, gen(entry_code_cat)

* Show propensity-score and overlap-weight diagnostics after trimming.
di as text _newline "Trimmed-sample propensity-score and overlap-weight diagnostics"
summarize propensity_score overlap_weight
tabstat propensity_score overlap_weight, by(school) ///
    statistics(mean sd min p25 median p75 max n) columns(statistics) format(%9.3f)

* Label outcomes for readable regression output.
label variable unexcused_pct "Unexcused absence %"
label variable excused_pct   "Excused absence %"
label variable total_pct     "Total absence %"

* Define the three attendance outcomes used in Table D1.
local outcomes unexcused_pct excused_pct total_pct

* Define display labels that match the reported table.
local label_unexcused_pct "Unexcused absence %"
local label_excused_pct   "Excused absence %"
local label_total_pct     "Total absence %"

* Create a temporary results file for the six robustness regression rows.
tempfile tabled1_results

* Close any stale post handle so the do-file can be re-run in the same Stata session.
capture postclose tabled1

* Open a postfile to collect estimates, standard errors, weighted means, N, and residual df.
postfile tabled1 str28 outcome str18 model double estimate std_error jes_weighted_mean ///
    jmtes_weighted_mean n residual_df using `tabled1_results', replace

* Loop over each attendance outcome and estimate the OW and OW + covariates models.
foreach y of local outcomes {

    * Save the human-readable outcome label for this iteration.
    local y_label "`label_`y''"

    * Compute the JES overlap-weighted mean for this outcome after trimming.
    summarize `y' if jmtes == 0 [aw = overlap_weight], meanonly
    scalar jes_mean = r(mean)

    * Compute the JMTES overlap-weighted mean for this outcome after trimming.
    summarize `y' if jmtes == 1 [aw = overlap_weight], meanonly
    scalar jmtes_mean = r(mean)

    * Estimate and show the unadjusted overlap-weighted robustness regression.
    di as text _newline "Table D1 OW model: `y_label'"
    regress `y' jmtes [aw = overlap_weight]

    * Post the unadjusted model results.
    post tabled1 ("`y_label'") ("OW") (_b[jmtes]) (_se[jmtes]) (jes_mean) (jmtes_mean) (e(N)) (e(df_r))

    * Estimate and show the covariate-adjusted overlap-weighted robustness regression.
    di as text _newline "Table D1 OW + covariates model: `y_label'"
    regress `y' jmtes i.grade_cat female black age i.meal_status_cat i.entry_code_cat [aw = overlap_weight]

    * Post the adjusted model results.
    post tabled1 ("`y_label'") ("OW + covariates") (_b[jmtes]) (_se[jmtes]) (jes_mean) (jmtes_mean) (e(N)) (e(df_r))
}

* Close the posted results dataset.
postclose tabled1

* Open the results dataset for formatting and verification.
use `tabled1_results', clear

* Format numeric columns to match the reported precision.
format estimate std_error jes_weighted_mean jmtes_weighted_mean %9.3f
format n residual_df %9.0f

* Print the Table D1 robustness replication results.
di as text _newline "Table D1 robustness results after trimming high unexcused absence values"
list outcome model estimate std_error jes_weighted_mean jmtes_weighted_mean n residual_df, ///
    noobs abbreviate(24) separator(0)

* Verify that estimates and standard errors round to the reported Table D1 values.
assert abs(estimate + 0.760) < 0.0015 if outcome == "Unexcused absence %" & model == "OW"
assert abs(std_error - 0.301) < 0.0015 if outcome == "Unexcused absence %" & model == "OW"
assert abs(estimate + 0.777) < 0.0015 if outcome == "Unexcused absence %" & model == "OW + covariates"
assert abs(std_error - 0.293) < 0.0015 if outcome == "Unexcused absence %" & model == "OW + covariates"
assert abs(estimate - 0.595) < 0.0015 if outcome == "Excused absence %" & model == "OW"
assert abs(std_error - 0.135) < 0.0015 if outcome == "Excused absence %" & model == "OW"
assert abs(estimate - 0.605) < 0.0015 if outcome == "Excused absence %" & model == "OW + covariates"
assert abs(std_error - 0.134) < 0.0015 if outcome == "Excused absence %" & model == "OW + covariates"
assert abs(estimate + 0.164) < 0.0015 if outcome == "Total absence %" & model == "OW"
assert abs(std_error - 0.346) < 0.0015 if outcome == "Total absence %" & model == "OW"
assert abs(estimate + 0.172) < 0.0015 if outcome == "Total absence %" & model == "OW + covariates"
assert abs(std_error - 0.338) < 0.0015 if outcome == "Total absence %" & model == "OW + covariates"

* Verify that weighted means, observations, and residual df match the reported Table D1 values.
assert abs(jes_weighted_mean - 6.682) < 0.0015 if outcome == "Unexcused absence %"
assert abs(jmtes_weighted_mean - 5.923) < 0.0015 if outcome == "Unexcused absence %"
assert abs(jes_weighted_mean - 1.157) < 0.0015 if outcome == "Excused absence %"
assert abs(jmtes_weighted_mean - 1.752) < 0.0015 if outcome == "Excused absence %"
assert abs(jes_weighted_mean - 7.839) < 0.0015 if outcome == "Total absence %"
assert abs(jmtes_weighted_mean - 7.675) < 0.0015 if outcome == "Total absence %"
assert n == 1038
assert residual_df == 1036 if model == "OW"
assert residual_df == 1018 if model == "OW + covariates"

* Confirm completion if every check passes.
di as result _newline "Table D1 trimmed attendance robustness checks match the reported values."
