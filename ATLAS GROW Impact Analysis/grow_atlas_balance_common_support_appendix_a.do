/****************************************************************************************
  Appendix A. Common Support and Balance Diagnostics for Academic ATLAS Models

  Purpose:
    Show common-support diagnostics, display the propensity-score regression for each
    grade-subject academic model, and reproduce Table A1 balance summaries for the
    overlap-weighted academic performance analysis.

  Required inputs:
    ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv
    ATLAS GROW Impact Analysis/overlap_balance_diagnostics.csv

  Example command from the repository root:
    do "ATLAS GROW Impact Analysis/grow_atlas_balance_common_support_appendix_a.do"
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the other project do-files.
version 17.0

* Do not pause output; the reviewer asked that regression results be shown in Stata.
set more off

* Define input paths when running from the repository root.
local analysis_csv "ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv"
local balance_csv "ATLAS GROW Impact Analysis/overlap_balance_diagnostics.csv"

* Fall back to local filenames when running from inside ATLAS GROW Impact Analysis.
capture confirm file "`analysis_csv'"
if _rc {
    local analysis_csv "grow_atlas_merged_at_risk_analysis_data.csv"
    local balance_csv "overlap_balance_diagnostics.csv"
}

* Stop with a clear error if either required input is missing.
foreach file in "`analysis_csv'" "`balance_csv'" {
    capture confirm file "`file'"
    if _rc {
        di as error "Input file not found: `file'"
        exit 601
    }
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

* Open the detailed academic balance diagnostics and derive the Table A1 summary.
import delimited using "`balance_csv'", clear varnames(1)

* Keep only the academic balance diagnostics.
keep if domain == "Academic"

* Confirm required balance-diagnostic variables exist.
foreach var in model covariate abs_smd_unweighted abs_smd_weighted {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in `balance_csv'."
        exit 111
    }
}

* Coerce SMD fields in case Stata imports them as strings.
replace abs_smd_unweighted = real(string(abs_smd_unweighted))
replace abs_smd_weighted = real(string(abs_smd_weighted))

* Mark covariates below the usual 0.10 balance threshold after weighting.
gen byte below_0_10_weighted = abs_smd_weighted < .10

* Collapse detailed covariate diagnostics to the Table A1 model-level summary.
collapse (count) covariates_checked = covariate ///
    (mean) mean_abs_smd_unweighted = abs_smd_unweighted ///
           mean_abs_smd_weighted = abs_smd_weighted ///
           share_weighted_below_0_10 = below_0_10_weighted ///
    (max) max_abs_smd_unweighted = abs_smd_unweighted ///
          max_abs_smd_weighted = abs_smd_weighted, by(model)

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
