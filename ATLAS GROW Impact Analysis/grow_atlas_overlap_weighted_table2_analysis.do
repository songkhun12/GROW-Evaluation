/****************************************************************************************
  Table 2. GROW-Associated Differences in 2026 Summative ATLAS Scores

  Purpose:
    Run the preferred academic-performance analysis from a single merged at-risk
    analysis CSV. The model is estimated separately by grade and subject using
    overlap weights, baseline score adjustment, and student covariates.

  Required input:
    ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv

  Example command from the repository root:
    do "ATLAS GROW Impact Analysis/grow_atlas_overlap_weighted_table2_analysis.do"

  Example command from inside the ATLAS GROW Impact Analysis folder:
    do "grow_atlas_overlap_weighted_table2_analysis.do"
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the other project do-files.
version 17.0

* Prevent Stata from pausing while it prints diagnostics and regression output.
set more off

* Define the merged at-risk analysis CSV when the do-file is run from the repo root.
local input_csv "ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv"

* Fall back to the local file name when the do-file is run from inside this folder.
capture confirm file "`input_csv'"
if _rc {
    local input_csv "grow_atlas_merged_at_risk_analysis_data.csv"
}

* Stop with a clear message if the merged at-risk analysis file cannot be found.
capture confirm file "`input_csv'"
if _rc {
    di as error "Input file not found: `input_csv'"
    exit 601
}

* Open the single merged at-risk analysis CSV used for all Table 2 models.
import delimited using "`input_csv'", clear varnames(1)

* Confirm that every variable needed for the propensity diagnostics and regressions exists.
foreach var in grade school jmtes subject post_score baseline_score female black age ///
    meal_status entry_code propensity_score overlap_weight {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in `input_csv'."
        exit 111
    }
}

* Confirm the merged file contains the complete Kindergarten through Grade 5 analytic sample.
count
assert r(N) == 2604

* Ensure the treatment indicator is numeric after import.
replace jmtes = real(string(jmtes))

* Ensure the outcome and baseline scores are numeric after import.
replace post_score = real(string(post_score))
replace baseline_score = real(string(baseline_score))

* Ensure the demographic indicators and age are numeric after import.
replace female = real(string(female))
replace black = real(string(black))
replace age = real(string(age))

* Ensure the saved propensity scores and overlap weights are numeric after import.
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

* Encode meal-status and entry-code strings for factor-variable notation in regressions.
encode meal_status_str, gen(meal_status_cat)
encode entry_code_str, gen(entry_code_cat)

* Create a combined grade-subject label for propensity and overlap-weight diagnostics.
gen str24 model = grade + " " + subject

* Create a model-school label so tabstat can show the propensity step by cell and school.
egen model_school = concat(model school), punct(" / ")

* Show the propensity-score and overlap-weight step before estimating outcome models.
di as text _newline "Propensity-score and overlap-weight diagnostics from the merged at-risk file"
tabstat propensity_score overlap_weight, by(model_school) ///
    statistics(mean sd min p25 median p75 max n) columns(statistics) format(%9.3f)

* Create a temporary results file for Table 2 model outputs.
tempfile table2_results

* Close any leftover posting handle so the do-file can be re-run in the same Stata session.
capture postclose table2_post

* Open a posting handle for coefficient, standard error, sample size, and residual df.
postfile table2_post str12 grade str8 subject double coefficient std_error p_value ///
    n treated_n control_n residual_df using `table2_results', replace

* Drop the helper program if it already exists so the do-file can be re-run without r(110).
capture program drop run_atlas_table2_model

* Define a helper program to estimate one grade-subject overlap-weighted regression.
program define run_atlas_table2_model
    * Require the grade and subject labels for the current model.
    syntax, Grade(string) Subject(string)

    * Display which grade-subject model is being estimated.
    di as text _newline "Estimating Table 2 model: `grade' `subject'"

    * Run the overlap-weighted, baseline-adjusted, covariate-adjusted regression.
    regress post_score jmtes baseline_score female black age i.meal_status_cat ///
        i.entry_code_cat [aw = overlap_weight] if grade == "`grade'" & subject == "`subject'"

    * Store the JMTES coefficient and standard error from the displayed regression.
    scalar b_jmtes = _b[jmtes]
    scalar se_jmtes = _se[jmtes]

    * Store the two-sided p-value for significance-star checks.
    scalar p_jmtes = 2 * ttail(e(df_r), abs(b_jmtes / se_jmtes))

    * Store model sample size and residual degrees of freedom.
    scalar model_n = e(N)
    scalar model_df = e(df_r)

    * Count JMTES students in the estimation sample.
    count if e(sample) & jmtes == 1
    scalar model_treated_n = r(N)

    * Count JES students in the estimation sample.
    count if e(sample) & jmtes == 0
    scalar model_control_n = r(N)

    * Post the model row into the Table 2 results file.
    post table2_post ("`grade'") ("`subject'") (b_jmtes) (se_jmtes) (p_jmtes) ///
        (model_n) (model_treated_n) (model_control_n) (model_df)
end

* Estimate Kindergarten ELA.
run_atlas_table2_model, grade("Kindergarten") subject("ELA")

* Estimate Kindergarten Math.
run_atlas_table2_model, grade("Kindergarten") subject("Math")

* Estimate Grade 1 ELA.
run_atlas_table2_model, grade("Grade 1") subject("ELA")

* Estimate Grade 1 Math.
run_atlas_table2_model, grade("Grade 1") subject("Math")

* Estimate Grade 2 ELA.
run_atlas_table2_model, grade("Grade 2") subject("ELA")

* Estimate Grade 2 Math.
run_atlas_table2_model, grade("Grade 2") subject("Math")

* Estimate Grade 3 ELA.
run_atlas_table2_model, grade("Grade 3") subject("ELA")

* Estimate Grade 3 Math.
run_atlas_table2_model, grade("Grade 3") subject("Math")

* Estimate Grade 3 Science.
run_atlas_table2_model, grade("Grade 3") subject("Science")

* Estimate Grade 4 ELA.
run_atlas_table2_model, grade("Grade 4") subject("ELA")

* Estimate Grade 4 Math.
run_atlas_table2_model, grade("Grade 4") subject("Math")

* Estimate Grade 4 Science.
run_atlas_table2_model, grade("Grade 4") subject("Science")

* Estimate Grade 5 ELA.
run_atlas_table2_model, grade("Grade 5") subject("ELA")

* Estimate Grade 5 Math.
run_atlas_table2_model, grade("Grade 5") subject("Math")

* Estimate Grade 5 Science.
run_atlas_table2_model, grade("Grade 5") subject("Science")

* Close the posted model results.
postclose table2_post

* Open the posted Table 2 results.
use `table2_results', clear

* Create a grade order so Kindergarten through Grade 5 print in report order.
gen grade_order = .
replace grade_order = 0 if grade == "Kindergarten"
replace grade_order = real(regexs(1)) if regexm(grade, "^Grade ([0-9]+)$")

* Create a subject order so ELA, Math, and Science print in report order.
gen subject_order = .
replace subject_order = 1 if subject == "ELA"
replace subject_order = 2 if subject == "Math"
replace subject_order = 3 if subject == "Science"

* Create rounded reporting columns for coefficient and standard error.
gen coefficient_rounded = round(coefficient, .01)
gen se_rounded = round(std_error, .01)

* Create significance stars using the note thresholds from Table 2.
gen str3 stars = ""
replace stars = "*" if p_value < .10
replace stars = "**" if p_value < .05
replace stars = "***" if p_value < .01

* Combine the rounded coefficient and stars for easy visual checking against Table 2.
gen str12 coefficient_with_stars = string(coefficient_rounded, "%9.2f") + stars

* Make numeric columns print with the same precision as the reported table.
format coefficient_rounded se_rounded %9.2f

* Sort rows into the same grade-subject order used in Table 2.
sort grade_order subject_order

* Print the preferred overlap-weighted, baseline-adjusted, covariate-adjusted results.
di as text _newline "Table 2 replication from merged at-risk analysis data"
list grade subject coefficient_with_stars se_rounded n treated_n control_n residual_df, ///
    noobs abbreviate(24) separator(0)

* Verify the expected number of grade-subject models in the preferred Table 2 output.
assert _N == 15

* Verify the reported coefficients to the same two-decimal precision shown in Table 2.
assert abs(coefficient_rounded - 0.82) < .005 if grade == "Kindergarten" & subject == "ELA"
assert abs(coefficient_rounded - 1.26) < .005 if grade == "Kindergarten" & subject == "Math"
assert abs(coefficient_rounded - 1.79) < .005 if grade == "Grade 1" & subject == "ELA"
assert abs(coefficient_rounded + 1.21) < .005 if grade == "Grade 1" & subject == "Math"
assert abs(coefficient_rounded - 3.81) < .005 if grade == "Grade 2" & subject == "ELA"
assert abs(coefficient_rounded - 1.10) < .005 if grade == "Grade 2" & subject == "Math"
assert abs(coefficient_rounded - 7.26) < .005 if grade == "Grade 3" & subject == "ELA"
assert abs(coefficient_rounded - 6.40) < .005 if grade == "Grade 3" & subject == "Math"
assert abs(coefficient_rounded - 2.65) < .005 if grade == "Grade 3" & subject == "Science"
assert abs(coefficient_rounded - 5.13) < .005 if grade == "Grade 4" & subject == "ELA"
assert abs(coefficient_rounded - 9.71) < .005 if grade == "Grade 4" & subject == "Math"
assert abs(coefficient_rounded - 6.05) < .005 if grade == "Grade 4" & subject == "Science"
assert abs(coefficient_rounded - 1.92) < .005 if grade == "Grade 5" & subject == "ELA"
assert abs(coefficient_rounded - 1.94) < .005 if grade == "Grade 5" & subject == "Math"
assert abs(coefficient_rounded - 5.44) < .005 if grade == "Grade 5" & subject == "Science"

* Verify sample sizes and school-specific Ns against the reported table.
assert n == 166 & treated_n == 52 & control_n == 114 if grade == "Kindergarten" & subject == "ELA"
assert n == 164 & treated_n == 52 & control_n == 112 if grade == "Kindergarten" & subject == "Math"
assert n == 170 & treated_n == 59 & control_n == 111 if grade == "Grade 1" & subject == "ELA"
assert n == 170 & treated_n == 59 & control_n == 111 if grade == "Grade 1" & subject == "Math"
assert n == 156 & treated_n == 67 & control_n == 89 if grade == "Grade 2" & subject == "ELA"
assert n == 155 & treated_n == 67 & control_n == 88 if grade == "Grade 2" & subject == "Math"
assert n == 204 & treated_n == 85 & control_n == 119 if grade == "Grade 3" & subject == "ELA"
assert n == 203 & treated_n == 84 & control_n == 119 if grade == "Grade 3" & subject == "Math"
assert n == 198 & treated_n == 82 & control_n == 116 if grade == "Grade 3" & subject == "Science"
assert n == 188 & treated_n == 74 & control_n == 114 if grade == "Grade 4" & subject == "ELA"
assert n == 188 & treated_n == 74 & control_n == 114 if grade == "Grade 4" & subject == "Math"
assert n == 189 & treated_n == 75 & control_n == 114 if grade == "Grade 4" & subject == "Science"
assert n == 151 & treated_n == 53 & control_n == 98 if grade == "Grade 5" & subject == "ELA"
assert n == 152 & treated_n == 53 & control_n == 99 if grade == "Grade 5" & subject == "Math"
assert n == 150 & treated_n == 53 & control_n == 97 if grade == "Grade 5" & subject == "Science"

* Confirm completion if all displayed checks and assertions pass.
di as result _newline "All Table 2 overlap-weighted ATLAS checks match the reported values."
