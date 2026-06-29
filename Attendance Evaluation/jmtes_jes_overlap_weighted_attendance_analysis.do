/****************************************************************************************
  Stata replication of the overlap-weighted attendance analysis for Table 4.
  Run from the repository root or from the Attendance Evaluation folder after adjusting
  the input path below if needed.
****************************************************************************************/

* Use Stata 17 syntax so the file is compatible with the project do-files.
version 17.0

* Prevent Stata from pausing output during a batch run.
set more off

* Clear any data already in memory before opening the attendance analysis file.
clear

* Define the combined June 15, 2026 JMTES/JES at-risk attendance file.
local input_csv "Attendance Evaluation/jmtes_jes_at_risk_report_6_15_26_combined.csv"

* If the do-file is run from inside Attendance Evaluation, use the local file name instead.
capture confirm file "`input_csv'"
if _rc {
    local input_csv "jmtes_jes_at_risk_report_6_15_26_combined.csv"
}

* Stop with a clear error if the combined attendance file cannot be found.
capture confirm file "`input_csv'"
if _rc {
    di as error "Input file not found: `input_csv'"
    exit 601
}

* Open the combined student-level attendance data.
import delimited using "`input_csv'", clear varnames(1)

* Confirm that every variable needed for the propensity model and outcomes is present.
foreach var in school student_grade gender ethnic_name student_age meal_status_code entry_code unexcused_absence_pct excused_absence_pct total_absence_pct {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in the open dataset."
        exit 111
    }
}

* Code JMTES as the treated/GROW school and JES as the comparison school.
gen byte jmtes = (school == "JMTES")

* Code female as 1 for female students and 0 otherwise.
gen byte female = (lower(strtrim(gender)) == "female")

* Code Black as 1 for Black students and 0 otherwise.
gen byte black = (lower(strtrim(ethnic_name)) == "black")

* Store student age in a short variable name for model readability.
gen double age = student_age

* Convert grade to a numeric categorical variable for Stata factor-variable notation.
encode student_grade, gen(grade_cat)

* Convert meal-status code to string if Stata imported it as numeric.
capture confirm string variable meal_status_code
if _rc {
    tostring meal_status_code, gen(meal_status_str) format(%02.0f)
}
else {
    gen str20 meal_status_str = strtrim(meal_status_code)
}

* Convert meal-status string values to a numeric categorical variable.
encode meal_status_str, gen(meal_status_cat)

* Convert entry code to string if Stata imported it as numeric.
capture confirm string variable entry_code
if _rc {
    tostring entry_code, gen(entry_code_str)
}
else {
    gen str20 entry_code_str = strtrim(entry_code)
}

* Convert entry-code string values to a numeric categorical variable.
encode entry_code_str, gen(entry_code_cat)

* Estimate the propensity score model specified in the methodology.
logit jmtes i.grade_cat female black age i.meal_status_cat i.entry_code_cat

* Predict each student's probability of attending JMTES.
predict double propensity_score, pr

* Create overlap weights: JMTES students receive 1-p, and JES students receive p.
gen double overlap_weight = cond(jmtes == 1, 1 - propensity_score, propensity_score)

* Label the outcome variables for readable Stata output.
label variable unexcused_absence_pct "Unexcused absence %"
label variable excused_absence_pct   "Excused absence %"
label variable total_absence_pct     "Total absence %"

* Define the three attendance outcomes used in Table 4.
local outcomes unexcused_absence_pct excused_absence_pct total_absence_pct

* Define display labels that match the reported table.
local label_unexcused_absence_pct "Unexcused absence %"
local label_excused_absence_pct   "Excused absence %"
local label_total_absence_pct     "Total absence %"

* Create a temporary results file for the six regression rows.
tempfile table4_results

* Open a postfile to collect estimates, standard errors, weighted means, N, and residual df.
postfile table4 str28 outcome str18 model double estimate std_error jes_weighted_mean jmtes_weighted_mean n residual_df using `table4_results', replace

* Loop over each attendance outcome.
foreach y of local outcomes {

    * Save the human-readable outcome label for this iteration.
    local y_label "`label_`y''"

    * Compute the JES overlap-weighted mean for this outcome.
    quietly summarize `y' if jmtes == 0 [aw = overlap_weight], meanonly
    scalar jes_mean = r(mean)

    * Compute the JMTES overlap-weighted mean for this outcome.
    quietly summarize `y' if jmtes == 1 [aw = overlap_weight], meanonly
    scalar jmtes_mean = r(mean)

    * Estimate the unadjusted overlap-weighted regression model.
    quietly regress `y' jmtes [aw = overlap_weight]

    * Post the unadjusted model results.
    post table4 ("`y_label'") ("OW") (_b[jmtes]) (_se[jmtes]) (jes_mean) (jmtes_mean) (e(N)) (e(df_r))

    * Estimate the covariate-adjusted overlap-weighted regression model.
    quietly regress `y' jmtes i.grade_cat female black age i.meal_status_cat i.entry_code_cat [aw = overlap_weight]

    * Post the adjusted model results.
    post table4 ("`y_label'") ("OW + covariates") (_b[jmtes]) (_se[jmtes]) (jes_mean) (jmtes_mean) (e(N)) (e(df_r))
}

* Close the posted results dataset.
postclose table4

* Open the results dataset for formatting and verification.
use `table4_results', clear

* Format numeric columns to match the reported precision.
format estimate std_error jes_weighted_mean jmtes_weighted_mean %9.3f
format n residual_df %9.0f

* Print the Table 4 replication results.
list outcome model estimate std_error jes_weighted_mean jmtes_weighted_mean n residual_df, noobs abbreviate(24) separator(0)

* Verify that estimates and standard errors round to the reported Table 4 values.
assert abs(estimate + 2.771) < 0.0015 if outcome == "Unexcused absence %"
assert abs(std_error - 0.453) < 0.0015 if outcome == "Unexcused absence %" & model == "OW"
assert abs(std_error - 0.444) < 0.0015 if outcome == "Unexcused absence %" & model == "OW + covariates"
assert abs(estimate - 0.531) < 0.0015 if outcome == "Excused absence %"
assert abs(std_error - 0.149) < 0.0015 if outcome == "Excused absence %" & model == "OW"
assert abs(std_error - 0.147) < 0.0015 if outcome == "Excused absence %" & model == "OW + covariates"
assert abs(estimate + 2.240) < 0.0015 if outcome == "Total absence %"
assert abs(std_error - 0.496) < 0.0015 if outcome == "Total absence %" & model == "OW"
assert abs(std_error - 0.489) < 0.0015 if outcome == "Total absence %" & model == "OW + covariates"

* Verify that weighted means, observations, and residual df match the reported table.
assert abs(jes_weighted_mean - 8.833) < 0.0015 if outcome == "Unexcused absence %"
assert abs(jmtes_weighted_mean - 6.062) < 0.0015 if outcome == "Unexcused absence %"
assert abs(jes_weighted_mean - 1.246) < 0.0015 if outcome == "Excused absence %"
assert abs(jmtes_weighted_mean - 1.777) < 0.0015 if outcome == "Excused absence %"
assert abs(jes_weighted_mean - 10.079) < 0.0015 if outcome == "Total absence %"
assert abs(jmtes_weighted_mean - 7.839) < 0.0015 if outcome == "Total absence %"
assert n == 1093
assert residual_df == 1091 if model == "OW"
assert residual_df == 1073 if model == "OW + covariates"
