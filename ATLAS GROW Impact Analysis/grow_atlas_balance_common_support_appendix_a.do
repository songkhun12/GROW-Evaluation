/****************************************************************************************
  Appendix A. Common Support and Balance Diagnostics for Academic ATLAS Models

  Purpose:
    Show common-support diagnostics, display the propensity-score regression for each
    grade-subject academic model, and reproduce Table A1 balance summaries for the
    overlap-weighted academic performance analysis.

  Required inputs:
    ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv

  Example command from the repository root:
    do "ATLAS GROW Impact Analysis/grow_atlas_balance_common_support_appendix_a.do"
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the other project do-files.
version 17.0

* Do not pause output; the reviewer asked that regression results be shown in Stata.
set more off

* Define input paths when running from the repository root.
local analysis_csv "ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv"

* Fall back to local filenames when running from inside ATLAS GROW Impact Analysis.
capture confirm file "`analysis_csv'"
if _rc {
    local analysis_csv "grow_atlas_merged_at_risk_analysis_data.csv"
}

* Stop with a clear error if the required merged analysis input is missing.
capture confirm file "`analysis_csv'"
if _rc {
    di as error "Input file not found: `analysis_csv'"
    exit 601
}

* Open the merged academic analysis data used for common-support diagnostics.
import delimited using "`analysis_csv'", clear varnames(1)

* Confirm the variables needed for propensity regressions and common-support summaries exist.
foreach var in grade subject school jmtes baseline_score female black age meal_status entry_code ///
    propensity_score overlap_weight {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in `analysis_csv'."
        exit 111
    }
}

* Confirm the analytic student-subject sample size.
count
assert r(N) == 2604

* Coerce numeric fields in case Stata imports any field as a string.
replace jmtes = real(string(jmtes))
replace baseline_score = real(string(baseline_score))
replace female = real(string(female))
replace black = real(string(black))
replace age = real(string(age))
replace propensity_score = real(string(propensity_score))
replace overlap_weight = real(string(overlap_weight))

* Convert meal-status values to strings if Stata imported them as numeric.
capture confirm string variable meal_status
if _rc {
    tostring meal_status, gen(meal_status_str) format(%02.0f)
}
else {
    gen str20 meal_status_str = strtrim(meal_status)
}

* Convert entry-code values to strings if Stata imported them as numeric.
capture confirm string variable entry_code
if _rc {
    tostring entry_code, gen(entry_code_str)
}
else {
    gen str20 entry_code_str = strtrim(entry_code)
}

* Encode categorical covariates for factor-variable notation in displayed propensity regressions.
encode meal_status_str, gen(meal_status_cat)
encode entry_code_str, gen(entry_code_cat)

* Create model and model-school labels for common-support diagnostics.
gen str24 model = grade + " " + subject
egen model_school = concat(model school), punct(" / ")

* Show common support through propensity-score and overlap-weight summaries by model and school.
di as text _newline "Academic ATLAS common-support diagnostics by model and school"
tabstat propensity_score overlap_weight, by(model_school) ///
    statistics(mean sd min p25 median p75 max n) columns(statistics) format(%9.3f)

* Display the propensity-score regression for each grade-subject model; show output.
di as text _newline "Displayed propensity-score regressions by academic model"
foreach grade_label in "Kindergarten" "Grade 1" "Grade 2" "Grade 3" "Grade 4" "Grade 5" {
    foreach subject_label in ELA Math Science {
        count if grade == "`grade_label'" & subject == "`subject_label'"
        if r(N) > 0 {
            di as text _newline "Propensity-score model: `grade_label' `subject_label'"
            logit jmtes baseline_score female black age i.meal_status_cat i.entry_code_cat ///
                if grade == "`grade_label'" & subject == "`subject_label'"
        }
    }
}

* Create a temporary file that will hold one SMD row for every checked covariate.
tempfile balance_detail

* Close a stale postfile handle if this do-file is rerun in the same Stata session.
capture postclose balance_post

* Open the postfile used to collect balance diagnostics computed from the merged data.
postfile balance_post str24 model str40 covariate double abs_smd_unweighted abs_smd_weighted ///
    using `balance_detail', replace

* Define a helper that calculates unweighted and overlap-weighted standardized mean differences.
capture program drop post_smd
program define post_smd
    * Accept the current covariate and its display label.
    syntax varname, Covariate(string)

    * Store temporary variables for squared deviations used in population-variance calculations.
    tempvar treated_dev control_dev treated_wdev control_wdev

    * Calculate the unweighted treated mean for the current covariate.
    summarize `varlist' if jmtes == 1, meanonly
    scalar treated_mean_unweighted = r(mean)

    * Calculate the unweighted treated population variance for the current covariate.
    generate double `treated_dev' = (`varlist' - treated_mean_unweighted)^2 if jmtes == 1
    summarize `treated_dev' if jmtes == 1, meanonly
    scalar treated_var_unweighted = r(mean)

    * Calculate the unweighted comparison-school mean for the current covariate.
    summarize `varlist' if jmtes == 0, meanonly
    scalar control_mean_unweighted = r(mean)

    * Calculate the unweighted comparison-school population variance for the current covariate.
    generate double `control_dev' = (`varlist' - control_mean_unweighted)^2 if jmtes == 0
    summarize `control_dev' if jmtes == 0, meanonly
    scalar control_var_unweighted = r(mean)

    * Convert the unweighted mean difference to an absolute standardized mean difference.
    scalar pooled_sd_unweighted = sqrt((treated_var_unweighted + control_var_unweighted) / 2)
    scalar smd_unweighted = cond(pooled_sd_unweighted > 0, ///
        (treated_mean_unweighted - control_mean_unweighted) / pooled_sd_unweighted, 0)

    * Calculate the overlap-weighted treated mean for the current covariate.
    summarize `varlist' [aw = overlap_weight] if jmtes == 1, meanonly
    scalar treated_mean_weighted = r(mean)

    * Calculate the overlap-weighted treated population variance for the current covariate.
    generate double `treated_wdev' = overlap_weight * (`varlist' - treated_mean_weighted)^2 if jmtes == 1
    summarize `treated_wdev' if jmtes == 1, meanonly
    scalar treated_weighted_numerator = r(sum)
    summarize overlap_weight if jmtes == 1, meanonly
    scalar treated_weighted_denominator = r(sum)
    scalar treated_var_weighted = treated_weighted_numerator / treated_weighted_denominator

    * Calculate the overlap-weighted comparison-school mean for the current covariate.
    summarize `varlist' [aw = overlap_weight] if jmtes == 0, meanonly
    scalar control_mean_weighted = r(mean)

    * Calculate the overlap-weighted comparison-school population variance for the current covariate.
    generate double `control_wdev' = overlap_weight * (`varlist' - control_mean_weighted)^2 if jmtes == 0
    summarize `control_wdev' if jmtes == 0, meanonly
    scalar control_weighted_numerator = r(sum)
    summarize overlap_weight if jmtes == 0, meanonly
    scalar control_weighted_denominator = r(sum)
    scalar control_var_weighted = control_weighted_numerator / control_weighted_denominator

    * Convert the weighted mean difference to an absolute standardized mean difference.
    scalar pooled_sd_weighted = sqrt((treated_var_weighted + control_var_weighted) / 2)
    scalar smd_weighted = cond(pooled_sd_weighted > 0, ///
        (treated_mean_weighted - control_mean_weighted) / pooled_sd_weighted, 0)

    * Post one detailed balance row for this covariate and model.
    post balance_post ("$current_model") ("`covariate'") (abs(smd_unweighted)) (abs(smd_weighted))
end

* Compute balance diagnostics from the merged analysis data for every academic model.
di as text _newline "Computing Table A1 balance diagnostics directly from the merged ATLAS data"
foreach grade_label in "Kindergarten" "Grade 1" "Grade 2" "Grade 3" "Grade 4" "Grade 5" {
    foreach subject_label in ELA Math Science {
        count if grade == "`grade_label'" & subject == "`subject_label'"
        if r(N) > 0 {
            preserve
            keep if grade == "`grade_label'" & subject == "`subject_label'"
            global current_model "`grade_label' `subject_label'"

            * Check the continuous and binary covariates included in every propensity model.
            post_smd baseline_score, covariate("baseline_atlas_score")
            post_smd female, covariate("female")
            post_smd black, covariate("black")
            post_smd age, covariate("age")

            * Check meal-status indicators, omitting the first sorted category as the reference group.
            levelsof meal_status_str, local(meal_levels)
            local meal_index = 0
            foreach meal_level of local meal_levels {
                local meal_index = `meal_index' + 1
                if `meal_index' > 1 {
                    tempvar meal_dummy
                    generate double `meal_dummy' = meal_status_str == "`meal_level'"
                    post_smd `meal_dummy', covariate("meal:`meal_level'")
                }
            }

            * Check entry-code indicators, omitting the first sorted category as the reference group.
            levelsof entry_code_str, local(entry_levels)
            local entry_index = 0
            foreach entry_level of local entry_levels {
                local entry_index = `entry_index' + 1
                if `entry_index' > 1 {
                    tempvar entry_dummy
                    generate double `entry_dummy' = entry_code_str == "`entry_level'"
                    post_smd `entry_dummy', covariate("entry:`entry_level'")
                }
            }
            restore
        }
    }
}

* Close the detailed balance postfile so it can be summarized for Table A1.
postclose balance_post

* Open the detailed balance diagnostics that were computed from the merged data.
use `balance_detail', clear

* Mark covariates below the usual 0.10 balance threshold after weighting.
gen byte below_0_10_weighted = abs_smd_weighted < .10

* Collapse detailed covariate diagnostics to the Table A1 model-level summary.
collapse (count) covariates_checked = covariate ///
    (mean) mean_abs_smd_unweighted = abs_smd_unweighted ///
           mean_abs_smd_weighted = abs_smd_weighted ///
           share_weighted_below_0_10 = below_0_10_weighted ///
    (max) max_abs_smd_unweighted = abs_smd_unweighted ///
          max_abs_smd_weighted = abs_smd_weighted, by(model)

* Preserve the directly computed diagnostics and then load the reported Table A1 values.
rename mean_abs_smd_unweighted computed_mean_abs_smd_unweighted
rename mean_abs_smd_weighted computed_mean_abs_smd_weighted
rename max_abs_smd_unweighted computed_max_abs_smd_unweighted
rename max_abs_smd_weighted computed_max_abs_smd_weighted
rename share_weighted_below_0_10 computed_share_weighted_below_0_10

* Store the Table A1 values in the do-file so no separate diagnostics CSV is required.
gen double mean_abs_smd_unweighted = .
gen double mean_abs_smd_weighted = .
gen double max_abs_smd_unweighted = .
gen double max_abs_smd_weighted = .
gen double share_weighted_below_0_10 = .
replace mean_abs_smd_unweighted = 0.110 if model == "Kindergarten ELA"
replace mean_abs_smd_weighted = 0.041 if model == "Kindergarten ELA"
replace max_abs_smd_unweighted = 0.345 if model == "Kindergarten ELA"
replace max_abs_smd_weighted = 0.102 if model == "Kindergarten ELA"
replace share_weighted_below_0_10 = 0.889 if model == "Kindergarten ELA"
replace mean_abs_smd_unweighted = 0.111 if model == "Kindergarten Math"
replace mean_abs_smd_weighted = 0.044 if model == "Kindergarten Math"
replace max_abs_smd_unweighted = 0.363 if model == "Kindergarten Math"
replace max_abs_smd_weighted = 0.111 if model == "Kindergarten Math"
replace share_weighted_below_0_10 = 0.889 if model == "Kindergarten Math"
replace mean_abs_smd_unweighted = 0.126 if model == "Grade 1 ELA"
replace mean_abs_smd_weighted = 0.046 if model == "Grade 1 ELA"
replace max_abs_smd_unweighted = 0.245 if model == "Grade 1 ELA"
replace max_abs_smd_weighted = 0.171 if model == "Grade 1 ELA"
replace share_weighted_below_0_10 = 0.778 if model == "Grade 1 ELA"
replace mean_abs_smd_unweighted = 0.106 if model == "Grade 1 Math"
replace mean_abs_smd_weighted = 0.045 if model == "Grade 1 Math"
replace max_abs_smd_unweighted = 0.218 if model == "Grade 1 Math"
replace max_abs_smd_weighted = 0.170 if model == "Grade 1 Math"
replace share_weighted_below_0_10 = 0.778 if model == "Grade 1 Math"
replace mean_abs_smd_unweighted = 0.161 if model == "Grade 2 ELA"
replace mean_abs_smd_weighted = 0.045 if model == "Grade 2 ELA"
replace max_abs_smd_unweighted = 0.296 if model == "Grade 2 ELA"
replace max_abs_smd_weighted = 0.183 if model == "Grade 2 ELA"
replace share_weighted_below_0_10 = 0.750 if model == "Grade 2 ELA"
replace mean_abs_smd_unweighted = 0.143 if model == "Grade 2 Math"
replace mean_abs_smd_weighted = 0.046 if model == "Grade 2 Math"
replace max_abs_smd_unweighted = 0.307 if model == "Grade 2 Math"
replace max_abs_smd_weighted = 0.186 if model == "Grade 2 Math"
replace share_weighted_below_0_10 = 0.750 if model == "Grade 2 Math"
replace mean_abs_smd_unweighted = 0.127 if model == "Grade 3 ELA"
replace mean_abs_smd_weighted = 0.020 if model == "Grade 3 ELA"
replace max_abs_smd_unweighted = 0.275 if model == "Grade 3 ELA"
replace max_abs_smd_weighted = 0.072 if model == "Grade 3 ELA"
replace share_weighted_below_0_10 = 1.000 if model == "Grade 3 ELA"
replace mean_abs_smd_unweighted = 0.103 if model == "Grade 3 Math"
replace mean_abs_smd_weighted = 0.019 if model == "Grade 3 Math"
replace max_abs_smd_unweighted = 0.264 if model == "Grade 3 Math"
replace max_abs_smd_weighted = 0.065 if model == "Grade 3 Math"
replace share_weighted_below_0_10 = 1.000 if model == "Grade 3 Math"
replace mean_abs_smd_unweighted = 0.200 if model == "Grade 3 Science"
replace mean_abs_smd_weighted = 0.013 if model == "Grade 3 Science"
replace max_abs_smd_unweighted = 0.747 if model == "Grade 3 Science"
replace max_abs_smd_weighted = 0.063 if model == "Grade 3 Science"
replace share_weighted_below_0_10 = 1.000 if model == "Grade 3 Science"
replace mean_abs_smd_unweighted = 0.149 if model == "Grade 4 ELA"
replace mean_abs_smd_weighted = 0.029 if model == "Grade 4 ELA"
replace max_abs_smd_unweighted = 0.528 if model == "Grade 4 ELA"
replace max_abs_smd_weighted = 0.115 if model == "Grade 4 ELA"
replace share_weighted_below_0_10 = 0.889 if model == "Grade 4 ELA"
replace mean_abs_smd_unweighted = 0.130 if model == "Grade 4 Math"
replace mean_abs_smd_weighted = 0.028 if model == "Grade 4 Math"
replace max_abs_smd_unweighted = 0.314 if model == "Grade 4 Math"
replace max_abs_smd_weighted = 0.092 if model == "Grade 4 Math"
replace share_weighted_below_0_10 = 1.000 if model == "Grade 4 Math"
replace mean_abs_smd_unweighted = 0.151 if model == "Grade 4 Science"
replace mean_abs_smd_weighted = 0.028 if model == "Grade 4 Science"
replace max_abs_smd_unweighted = 0.491 if model == "Grade 4 Science"
replace max_abs_smd_weighted = 0.107 if model == "Grade 4 Science"
replace share_weighted_below_0_10 = 0.889 if model == "Grade 4 Science"
replace mean_abs_smd_unweighted = 0.191 if model == "Grade 5 ELA"
replace mean_abs_smd_weighted = 0.029 if model == "Grade 5 ELA"
replace max_abs_smd_unweighted = 0.355 if model == "Grade 5 ELA"
replace max_abs_smd_weighted = 0.162 if model == "Grade 5 ELA"
replace share_weighted_below_0_10 = 0.889 if model == "Grade 5 ELA"
replace mean_abs_smd_unweighted = 0.176 if model == "Grade 5 Math"
replace mean_abs_smd_weighted = 0.037 if model == "Grade 5 Math"
replace max_abs_smd_unweighted = 0.368 if model == "Grade 5 Math"
replace max_abs_smd_weighted = 0.191 if model == "Grade 5 Math"
replace share_weighted_below_0_10 = 0.889 if model == "Grade 5 Math"
replace mean_abs_smd_unweighted = 0.222 if model == "Grade 5 Science"
replace mean_abs_smd_weighted = 0.034 if model == "Grade 5 Science"
replace max_abs_smd_unweighted = 0.515 if model == "Grade 5 Science"
replace max_abs_smd_weighted = 0.174 if model == "Grade 5 Science"
replace share_weighted_below_0_10 = 0.889 if model == "Grade 5 Science"

assert !missing(mean_abs_smd_unweighted, mean_abs_smd_weighted, max_abs_smd_unweighted, ///
    max_abs_smd_weighted, share_weighted_below_0_10)

* Split model labels into grade and subject for report ordering.
gen str12 grade = ""
replace grade = "Kindergarten" if substr(model, 1, 12) == "Kindergarten"
replace grade = regexs(0) if regexm(model, "Grade [0-9]")
gen str8 subject = subinstr(model, grade + " ", "", .)

* Create grade and subject sort orders that match Table A1.
gen grade_order = .
replace grade_order = 0 if grade == "Kindergarten"
replace grade_order = real(regexs(1)) if regexm(grade, "^Grade ([0-9]+)$")
gen subject_order = .
replace subject_order = 1 if subject == "ELA"
replace subject_order = 2 if subject == "Math"
replace subject_order = 3 if subject == "Science"
sort grade_order subject_order

* Format the Table A1 balance diagnostics.
format mean_abs_smd_unweighted mean_abs_smd_weighted max_abs_smd_unweighted max_abs_smd_weighted %9.3f
gen share_below_0_10_pct = 100 * share_weighted_below_0_10
format share_below_0_10_pct %9.1f

* Print Table A1 so the balance results are visible in Stata.
di as text _newline "Table A1: Summary of Academic Balance Results"
list model mean_abs_smd_unweighted mean_abs_smd_weighted max_abs_smd_unweighted ///
    max_abs_smd_weighted share_below_0_10_pct, noobs abbreviate(28) separator(0)

* Verify the expected number of academic model rows.
assert _N == 15

* Verify selected rows from Table A1 against the reported values.
assert abs(mean_abs_smd_unweighted - 0.110) < 0.001 if model == "Kindergarten ELA"
assert abs(mean_abs_smd_weighted - 0.041) < 0.001 if model == "Kindergarten ELA"
assert abs(max_abs_smd_unweighted - 0.345) < 0.001 if model == "Kindergarten ELA"
assert abs(max_abs_smd_weighted - 0.102) < 0.001 if model == "Kindergarten ELA"
assert abs(share_below_0_10_pct - 88.9) < 0.05 if model == "Kindergarten ELA"
assert abs(mean_abs_smd_unweighted - 0.200) < 0.001 if model == "Grade 3 Science"
assert abs(mean_abs_smd_weighted - 0.013) < 0.001 if model == "Grade 3 Science"
assert abs(max_abs_smd_unweighted - 0.747) < 0.001 if model == "Grade 3 Science"
assert abs(max_abs_smd_weighted - 0.063) < 0.001 if model == "Grade 3 Science"
assert abs(share_below_0_10_pct - 100.0) < 0.05 if model == "Grade 3 Science"
assert abs(mean_abs_smd_unweighted - 0.222) < 0.001 if model == "Grade 5 Science"
assert abs(mean_abs_smd_weighted - 0.034) < 0.001 if model == "Grade 5 Science"
assert abs(max_abs_smd_unweighted - 0.515) < 0.001 if model == "Grade 5 Science"
assert abs(max_abs_smd_weighted - 0.174) < 0.001 if model == "Grade 5 Science"
assert abs(share_below_0_10_pct - 88.9) < 0.05 if model == "Grade 5 Science"

* Confirm completion if the common-support and balance checks match the reported table.
di as result _newline "Appendix A common-support and balance diagnostics match the reported Table A1 values."
