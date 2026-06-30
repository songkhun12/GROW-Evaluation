/****************************************************************************************
  Appendix B. Robustness Tests for ATLAS GROW Academic Performance Outcomes

  Purpose:
    Run the Appendix B robustness checks from the merged ATLAS at-risk analysis file:
      1. calipered nearest-neighbor matching with replacement, followed by the
         baseline- and covariate-adjusted outcome regression; and
      2. difference-in-differences-style gain-score regressions.

  Required input:
    ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv

  Example command from the repository root:
    do "ATLAS GROW Impact Analysis/grow_atlas_robustness_appendix_b.do"
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the project replication files.
version 17.0

* Do not pause output; the reviewer asked that regression results be shown in Stata.
set more off

* Define the merged at-risk analysis CSV when running from the repository root.
local input_csv "ATLAS GROW Impact Analysis/grow_atlas_merged_at_risk_analysis_data.csv"

* Fall back to the local filename when running from inside the ATLAS GROW Impact Analysis folder.
capture confirm file "`input_csv'"
if _rc {
    local input_csv "grow_atlas_merged_at_risk_analysis_data.csv"
}

* Stop with a clear error if the merged analysis file is missing.
capture confirm file "`input_csv'"
if _rc {
    di as error "Input file not found: `input_csv'"
    exit 601
}

* Import the merged analytic data used for both robustness checks.
import delimited using "`input_csv'", clear varnames(1)

* Confirm the variables needed for matching and gain-score regressions are present.
foreach var in grade school jmtes subject post_score baseline_score female black age ///
    meal_status entry_code propensity_score overlap_weight {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in `input_csv'."
        exit 111
    }
}

* Confirm the merged file contains the full analytic student-subject sample.
count
assert r(N) == 2604

* Coerce numeric fields in case Stata imports any field as a string.
replace jmtes = real(string(jmtes))
replace post_score = real(string(post_score))
replace baseline_score = real(string(baseline_score))
replace female = real(string(female))
replace black = real(string(black))
replace age = real(string(age))
replace propensity_score = real(string(propensity_score))
replace overlap_weight = real(string(overlap_weight))

* Build the gain score for the difference-in-differences-style models.
gen double gain_score = post_score - baseline_score

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

* Encode categorical covariates for factor-variable notation.
encode meal_status_str, gen(meal_status_cat)
encode entry_code_str, gen(entry_code_cat)

* Compute propensity-score logits for calipered matching.
gen double logit_ps = log(propensity_score / (1 - propensity_score))

* Show the propensity-score inputs used by the robustness matching step.
gen str24 model = grade + " " + subject
egen model_school = concat(model school), punct(" / ")
di as text _newline "Appendix B propensity-score diagnostics from merged ATLAS file"
tabstat propensity_score logit_ps, by(model_school) ///
    statistics(mean sd min p25 median p75 max n) columns(statistics) format(%9.3f)

* Create temporary files for Appendix B matching and gain-score result rows.
tempfile matching_results did_results

* Close any stale post handles so the file can be re-run in one Stata session.
capture postclose matching_post
capture postclose did_post

* Open a postfile for Table B1 matching results.
postfile matching_post str12 grade str8 subject double coefficient std_error p_value ///
    n treated_n control_n residual_df using `matching_results', replace

* Open a postfile for Table B2 gain-score results.
postfile did_post str12 grade str8 subject double coefficient std_error p_value ///
    n treated_n control_n residual_df using `did_results', replace

* Drop helper programs if they already exist from a prior run.
capture program drop run_matching_model
capture program drop run_did_model

* Define the calipered nearest-neighbor matching robustness model.
program define run_matching_model
    * Require the grade and subject labels for the current model.
    syntax, Grade(string) Subject(string)

    * Announce the matching model so the Stata log clearly shows each robustness test.
    di as text _newline "Table B1 matching model: `grade' `subject'"

    * Restrict to the current grade-subject sample.
    preserve
        keep if grade == "`grade'" & subject == "`subject'"

        * Estimate the propensity-score caliper as 0.20 SD of the logit propensity score.
        summarize logit_ps
        scalar match_caliper = 0.20 * r(sd)

        * Save the JES control pool with control-prefixed variable names.
        tempfile controls matched_pairs treated_rows control_rows matched_sample
        preserve
            keep if jmtes == 0
            gen byte join_key = 1
            keep join_key post_score baseline_score female black age meal_status_cat entry_code_cat logit_ps propensity_score
            rename post_score c_post_score
            rename baseline_score c_baseline_score
            rename female c_female
            rename black c_black
            rename age c_age
            rename meal_status_cat c_meal_status_cat
            rename entry_code_cat c_entry_code_cat
            rename logit_ps c_logit_ps
            rename propensity_score c_propensity_score
            save `controls', replace
        restore

        * Keep treated JMTES rows, then join all possible JES controls for matching.
        keep if jmtes == 1
        gen long treated_id = _n
        gen byte join_key = 1
        joinby join_key using `controls'

        * Apply the propensity-score caliper.
        gen double ps_distance = abs(logit_ps - c_logit_ps)
        keep if ps_distance <= match_caliper

        * Choose the nearest control by propensity score, breaking ties by baseline-score distance.
        gen double baseline_distance = abs(baseline_score - c_baseline_score)
        bysort treated_id (ps_distance baseline_distance): keep if _n == 1
        save `matched_pairs', replace

        * Build the treated side of the matched analysis file.
        use `matched_pairs', clear
        keep grade subject post_score baseline_score female black age meal_status_cat entry_code_cat jmtes
        save `treated_rows', replace

        * Build the matched JES side of the matched analysis file; controls may repeat by design.
        use `matched_pairs', clear
        keep grade subject c_post_score c_baseline_score c_female c_black c_age c_meal_status_cat c_entry_code_cat
        rename c_post_score post_score
        rename c_baseline_score baseline_score
        rename c_female female
        rename c_black black
        rename c_age age
        rename c_meal_status_cat meal_status_cat
        rename c_entry_code_cat entry_code_cat
        gen byte jmtes = 0
        save `control_rows', replace

        * Combine treated and matched comparison observations.
        use `treated_rows', clear
        append using `control_rows'
        save `matched_sample', replace

        * Display the baseline- and covariate-adjusted outcome regression on the matched sample.
        regress post_score jmtes baseline_score female black age i.meal_status_cat i.entry_code_cat

        * Store the JMTES estimate, standard error, p-value, N, and residual df.
        scalar b_jmtes = _b[jmtes]
        scalar se_jmtes = _se[jmtes]
        scalar p_jmtes = 2 * ttail(e(df_r), abs(b_jmtes / se_jmtes))
        scalar model_n = e(N)
        scalar model_df = e(df_r)

        * Count matched JMTES and matched JES observations in the estimation sample.
        count if e(sample) & jmtes == 1
        scalar model_treated_n = r(N)
        count if e(sample) & jmtes == 0
        scalar model_control_n = r(N)

        * Post the matching robustness row.
        post matching_post ("`grade'") ("`subject'") (b_jmtes) (se_jmtes) (p_jmtes) ///
            (model_n) (model_treated_n) (model_control_n) (model_df)
    restore
end

* Define the difference-in-differences-style gain-score robustness model.
program define run_did_model
    * Require the grade and subject labels for the current model.
    syntax, Grade(string) Subject(string)

    * Announce the gain-score model so the Stata log clearly shows each robustness test.
    di as text _newline "Table B2 gain-score model: `grade' `subject'"

    * Display the baseline- and covariate-adjusted gain-score regression.
    regress gain_score jmtes baseline_score female black age i.meal_status_cat i.entry_code_cat ///
        if grade == "`grade'" & subject == "`subject'"

    * Store the JMTES estimate, standard error, p-value, N, and residual df.
    scalar b_jmtes = _b[jmtes]
    scalar se_jmtes = _se[jmtes]
    scalar p_jmtes = 2 * ttail(e(df_r), abs(b_jmtes / se_jmtes))
    scalar model_n = e(N)
    scalar model_df = e(df_r)

    * Count JMTES and JES observations in the estimation sample.
    count if e(sample) & jmtes == 1
    scalar model_treated_n = r(N)
    count if e(sample) & jmtes == 0
    scalar model_control_n = r(N)

    * Post the gain-score robustness row.
    post did_post ("`grade'") ("`subject'") (b_jmtes) (se_jmtes) (p_jmtes) ///
        (model_n) (model_treated_n) (model_control_n) (model_df)
end

* Run Table B1 matching models and Table B2 gain-score models for every grade-subject cell.
foreach grade_label in "Kindergarten" "Grade 1" "Grade 2" "Grade 3" "Grade 4" "Grade 5" {
    foreach subject_label in ELA Math Science {
        count if grade == "`grade_label'" & subject == "`subject_label'"
        if r(N) > 0 {
            run_matching_model, grade("`grade_label'") subject("`subject_label'")
            run_did_model, grade("`grade_label'") subject("`subject_label'")
        }
    }
}

* Close the posted robustness result files.
postclose matching_post
postclose did_post

* Open and format Table B1 matching results.
use `matching_results', clear
gen str10 table = "Table B1"
tempfile matching_formatted
save `matching_formatted', replace

* Open and format Table B2 gain-score results.
use `did_results', clear
gen str10 table = "Table B2"
append using `matching_formatted'

* Create grade and subject sort orders for appendix table display.
gen grade_order = .
replace grade_order = 0 if grade == "Kindergarten"
replace grade_order = real(regexs(1)) if regexm(grade, "^Grade ([0-9]+)$")
gen subject_order = .
replace subject_order = 1 if subject == "ELA"
replace subject_order = 2 if subject == "Math"
replace subject_order = 3 if subject == "Science"

* Create rounded reporting columns and significance stars.
gen coefficient_rounded = round(coefficient, .01)
gen se_rounded = round(std_error, .01)
gen str3 stars = ""
replace stars = "*" if p_value < .10
replace stars = "**" if p_value < .05
replace stars = "***" if p_value < .01
gen str12 coefficient_with_stars = string(coefficient_rounded, "%9.2f") + stars
format coefficient_rounded se_rounded %9.2f
sort table grade_order subject_order

* Print both robustness tables so the results are visible in the Stata output.
di as text _newline "Table B1 and Table B2 robustness results"
list table grade subject coefficient_with_stars se_rounded n treated_n control_n residual_df, ///
    noobs abbreviate(24) separator(0)

* Verify the expected row counts for both appendix tables.
assert _N == 30
count if table == "Table B1"
assert r(N) == 15
count if table == "Table B2"
assert r(N) == 15

* Verify selected reported values from Table B1 matching robustness checks.
assert abs(coefficient_rounded - 1.86) < .005 if table == "Table B1" & grade == "Kindergarten" & subject == "ELA"
assert abs(coefficient_rounded - 10.42) < .005 if table == "Table B1" & grade == "Grade 4" & subject == "Math"
assert abs(coefficient_rounded - 5.29) < .005 if table == "Table B1" & grade == "Grade 5" & subject == "Science"

* Verify selected reported values from Table B2 gain-score robustness checks.
assert abs(coefficient_rounded - 0.89) < .005 if table == "Table B2" & grade == "Kindergarten" & subject == "ELA"
assert abs(coefficient_rounded - 9.66) < .005 if table == "Table B2" & grade == "Grade 4" & subject == "Math"
assert abs(coefficient_rounded - 5.79) < .005 if table == "Table B2" & grade == "Grade 5" & subject == "Science"

* Confirm completion if all robustness checks pass.
di as result _newline "Appendix B robustness checks completed and matched the reported values."
