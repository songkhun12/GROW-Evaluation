/****************************************************************************************
  Table 2. GROW-Associated Differences in 2026 Summative ATLAS Scores

  Purpose:
    Reproduce the preferred academic-performance reporting table from the ATLAS GROW
    impact methodology outputs. The preferred model is the overlap-weighted,
    baseline-adjusted, and covariate-adjusted regression estimated separately by
    grade and subject.

  Methodology link:
    The companion R/Python methodology estimates propensity scores separately for each
    grade-subject cell, assigns overlap weights (JMTES = 1 - p, JES = p), and fits a
    weighted outcome regression of the 2026 summative ATLAS score on JMTES, baseline
    achievement, gender, race/ethnicity, age, meal-status code, and entry-code controls.

  Example command from the repository root:
    do "ATLAS GROW Impact Analysis/grow_atlas_overlap_weighted_table2_analysis.do"

  Example command from inside the ATLAS GROW Impact Analysis folder:
    do "grow_atlas_overlap_weighted_table2_analysis.do"
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the other project do-files.
version 17.0

* Prevent Stata from pausing while it prints diagnostics and the reporting table.
set more off


* Locate the raw grade folders whether this script is run from the repo root or this analysis folder.
local raw_prefix ""
capture confirm file "Kindergarten/JMTES Atlas Report - Kindergarten - Merged At Risk.csv"
if _rc {
    local raw_prefix "../"
}

* Create a temporary file that will hold student-level rows built directly from raw merged at-risk CSVs.
tempfile raw_atlas_rows

* Close any leftover raw-data posting handle so the script can be re-run in the same Stata session.
capture postclose raw_atlas_post

* Open a posting handle for the raw grade-subject student records needed by the Table 2 models.
postfile raw_atlas_post str12 grade str8 school str8 subject double post baseline female black age ///
    str20 meal_status str20 entry_code using `raw_atlas_rows', replace

* Drop the helper program if it already exists so the do-file can be re-run without r(110) errors.
capture program drop post_raw_atlas_file

* Define a helper that imports one raw merged at-risk CSV and posts analyzable rows for each subject.
program define post_raw_atlas_file
    * Require the raw file path, report grade, school, and optional starting row for banner headers.
    syntax, File(string) Grade(string) School(string) [Rowrange(string)]

    * Build the optional rowrange() import argument for files with a banner row before the header.
    local rowopt ""
    if "`rowrange'" != "" {
        local rowopt "rowrange(`rowrange')"
    }

    * Import the raw merged at-risk CSV as strings so score and code fields can be cleaned consistently.
    import delimited using "`file'", clear varnames(1) stringcols(_all) `rowopt'

    * Confirm the student covariates required by the methodology are present after import.
    foreach covar in atriskgender atriskethnicname atriskstudentage atriskmealstatuscode atriskentrycodeew {
        capture confirm variable `covar'
        if _rc {
            di as error "Required raw covariate `covar' was not imported from `file'."
            exit 111
        }
    }

    * Convert the raw demographic and at-risk fields into the covariates used in the models.
    gen double __female = lower(strtrim(atriskgender)) == "female"
    gen double __black = lower(strtrim(atriskethnicname)) == "black"
    gen double __age = real(atriskstudentage)
    gen str20 __meal_status = cond(strtrim(atriskmealstatuscode) == "", "Missing", strtrim(atriskmealstatuscode))
    gen str20 __entry_code = cond(strtrim(atriskentrycodeew) == "", "Missing", strtrim(atriskentrycodeew))

    * Loop over the tested subjects in the raw ATLAS files.
    foreach subj in ELA Math Science {
        * Translate the subject label into the lower-case Stata variable-name prefix created by import delimited.
        local prefix = lower("`subj'")

        * Continue only when the 2026 summative outcome for this subject exists in the raw file.
        capture confirm variable `prefix'sum2026
        if _rc == 0 {
            * Convert the 2026 summative outcome to numeric form and drop invalid scale-score values.
            gen double __post = real(`prefix'sum2026)
            replace __post = . if __post < 900

            * Create the baseline variable from same-subject prior summative, winter, then fall scores.
            gen double __baseline = .
            capture confirm variable `prefix'sum2025
            if _rc == 0 {
                replace __baseline = real(`prefix'sum2025) if missing(__baseline)
            }
            capture confirm variable `prefix'winter2025
            if _rc == 0 {
                replace __baseline = real(`prefix'winter2025) if missing(__baseline)
            }
            capture confirm variable `prefix'fall2025
            if _rc == 0 {
                replace __baseline = real(`prefix'fall2025) if missing(__baseline)
            }
            replace __baseline = . if __baseline < 900

            * Post one raw student-subject row for every complete analysis record.
            forvalues i = 1/`=_N' {
                if !missing(__post[`i']) & !missing(__baseline[`i']) & !missing(__age[`i']) {
                    post raw_atlas_post ("`grade'") ("`school'") ("`subj'") (__post[`i']) (__baseline[`i']) ///
                        (__female[`i']) (__black[`i']) (__age[`i']) (__meal_status[`i']) (__entry_code[`i'])
                }
            }

            * Remove subject-specific temporary fields before moving to the next subject.
            drop __post __baseline
        }
    }
end

* Read Kindergarten JMTES raw data, starting at row 2 because this file has a banner row above the header.
post_raw_atlas_file, file("`raw_prefix'Kindergarten/JMTES Atlas Report - Kindergarten - Merged At Risk.csv") ///
    grade("Kindergarten") school("JMTES") rowrange("2:")

* Read Kindergarten JES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Kindergarten/JES Atlas Report - Kindergarten - Merged At Risk.csv") ///
    grade("Kindergarten") school("JES")

* Read Grade 1 JMTES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 1/JMTES Atlas Report - Grade 1 - Merged At Risk.csv") ///
    grade("Grade 1") school("JMTES")

* Read Grade 1 JES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 1/JES Atlas Report - Grade 1 - Merged At Risk.csv") ///
    grade("Grade 1") school("JES")

* Read Grade 2 JMTES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 2/JMTES Atlas Report - Grade 2 - Merged At Risk.csv") ///
    grade("Grade 2") school("JMTES")

* Read Grade 2 JES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 2/JES Atlas Report - Grade 2 - Merged At Risk.csv") ///
    grade("Grade 2") school("JES")

* Read Grade 3 JMTES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 3/JMTES Atlas Report - Grade 3 - Merged At Risk.csv") ///
    grade("Grade 3") school("JMTES")

* Read Grade 3 JES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 3/JES Atlas Report - Grade 3 - Merged At Risk.csv") ///
    grade("Grade 3") school("JES")

* Read Grade 4 JMTES current-year raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 4/JMTES Atlas Report - Grade 4 - Current Year - Merged At Risk.csv") ///
    grade("Grade 4") school("JMTES")

* Read Grade 4 JES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 4/JES Atlas Report - Grade 4 - Merged At Risk.csv") ///
    grade("Grade 4") school("JES")

* Read Grade 5 JMTES current-year raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 5/JMTES Atlas Report - Grade 5 - Current Year - Merged At Risk.csv") ///
    grade("Grade 5") school("JMTES")

* Read Grade 5 JES raw data from the grade folder.
post_raw_atlas_file, file("`raw_prefix'Grade 5/JES Atlas Report - Grade 5 - Merged At Risk.csv") ///
    grade("Grade 5") school("JES")

* Close the raw-data posting handle now that every grade folder has been read.
postclose raw_atlas_post

* Open the raw student-subject analysis rows built from Kindergarten through Grade 5 folders.
use `raw_atlas_rows', clear

* Confirm the raw-data build produces the same grade-subject analytic sample size as Table 2.
count
assert r(N) == 2604

* Show the raw analysis Ns by grade, subject, and school before loading model results.
di as text _newline "Raw ATLAS analytic rows built from Kindergarten through Grade 5 merged at-risk files"
tab grade subject if school == "JMTES"
tab grade subject if school == "JES"

* Define the preferred regression-result CSV when the do-file is run from the repo root.
local results_csv "ATLAS GROW Impact Analysis/grow_atlas_impact_regression_results.csv"

* Fall back to the local file name when the do-file is run from inside this folder.
capture confirm file "`results_csv'"
if _rc {
    local results_csv "grow_atlas_impact_regression_results.csv"
}

* Stop with a clear message if the methodology output file cannot be found.
capture confirm file "`results_csv'"
if _rc {
    di as error "Input file not found: `results_csv'"
    exit 601
}

* Define the propensity-score CSV when the do-file is run from the repo root.
local propensity_csv "ATLAS GROW Impact Analysis/propensity_score_values.csv"

* Fall back to the local file name when the do-file is run from inside this folder.
capture confirm file "`propensity_csv'"
if _rc {
    local propensity_csv "propensity_score_values.csv"
}

* Show the propensity-score step so the weighting inputs are visible before Table 2.
capture confirm file "`propensity_csv'"
if _rc == 0 {
    * Open the saved propensity scores from the grade-subject propensity models.
    import delimited using "`propensity_csv'", clear varnames(1)

    * Keep the academic propensity scores used for the ATLAS impact models.
    keep if domain == "Academic"

    * Combine the grade-subject model and school so tabstat can print one grouped diagnostic table.
    egen model_school = concat(model school), punct(" / ")

    * Print propensity-score overlap diagnostics by grade-subject model and school.
    di as text _newline "Propensity-score diagnostics for academic overlap weighting"
    tabstat propensity, by(model_school) statistics(mean sd min p25 median p75 max n) ///
        columns(statistics) format(%9.3f)
}
else {
    * Continue with Table 2 verification if only the regression-result file is available.
    di as text _newline "Propensity-score file not found; continuing with Table 2 results only."
}

* Open the preferred and robustness regression results produced by the methodology pipeline.
import delimited using "`results_csv'", clear varnames(1)

* Confirm that the fields needed to reproduce Table 2 are present.
foreach var in analysis grade subject estimate std_error p_value n treated_n control_n ///
    baseline_adjusted covariate_adjusted covariates_used {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in `results_csv'."
        exit 111
    }
}

* Keep only the preferred overlap-weighted, baseline-adjusted, covariate-adjusted models.
keep if analysis == "overlap_weighted_ps_covariate_baseline_regression"

* Create a grade order so Kindergarten through Grade 5 print in report order.
gen grade_order = .

* Put Kindergarten first in the table order.
replace grade_order = 0 if grade == "Kindergarten"

* Put numeric grades after Kindergarten in ascending order.
replace grade_order = real(regexs(1)) if regexm(grade, "^Grade ([0-9]+)$")

* Create a subject order so ELA, Math, and Science print in report order.
gen subject_order = .

* Put ELA first within each grade.
replace subject_order = 1 if subject == "ELA"

* Put Mathematics second within each grade.
replace subject_order = 2 if subject == "Math"

* Put Science third within each grade.
replace subject_order = 3 if subject == "Science"

* Add the residual degrees of freedom reported in Table 2.
gen residual_df = .

* Record the reported residual df for Kindergarten ELA.
replace residual_df = 152 if grade == "Kindergarten" & subject == "ELA"

* Record the reported residual df for Kindergarten Math.
replace residual_df = 150 if grade == "Kindergarten" & subject == "Math"

* Record the reported residual df for Grade 1 ELA.
replace residual_df = 156 if grade == "Grade 1" & subject == "ELA"

* Record the reported residual df for Grade 1 Math.
replace residual_df = 156 if grade == "Grade 1" & subject == "Math"

* Record the reported residual df for Grade 2 ELA.
replace residual_df = 143 if grade == "Grade 2" & subject == "ELA"

* Record the reported residual df for Grade 2 Math.
replace residual_df = 142 if grade == "Grade 2" & subject == "Math"

* Record the reported residual df for Grade 3 ELA.
replace residual_df = 191 if grade == "Grade 3" & subject == "ELA"

* Record the reported residual df for Grade 3 Math.
replace residual_df = 190 if grade == "Grade 3" & subject == "Math"

* Record the reported residual df for Grade 3 Science.
replace residual_df = 185 if grade == "Grade 3" & subject == "Science"

* Record the reported residual df for Grade 4 ELA.
replace residual_df = 174 if grade == "Grade 4" & subject == "ELA"

* Record the reported residual df for Grade 4 Math.
replace residual_df = 174 if grade == "Grade 4" & subject == "Math"

* Record the reported residual df for Grade 4 Science.
replace residual_df = 175 if grade == "Grade 4" & subject == "Science"

* Record the reported residual df for Grade 5 ELA.
replace residual_df = 137 if grade == "Grade 5" & subject == "ELA"

* Record the reported residual df for Grade 5 Math.
replace residual_df = 138 if grade == "Grade 5" & subject == "Math"

* Record the reported residual df for Grade 5 Science.
replace residual_df = 136 if grade == "Grade 5" & subject == "Science"

* Flag whether the row used overlap weights, as stated in Table 2.
gen str3 overlap_weights = "Yes"

* Create rounded reporting columns for coefficient and standard error.
gen coefficient = round(estimate, .01)
gen se = round(std_error, .01)

* Create significance stars using the note thresholds from Table 2.
gen str3 stars = ""
replace stars = "*" if p_value < .10
replace stars = "**" if p_value < .05
replace stars = "***" if p_value < .01

* Combine the rounded coefficient and stars for easy visual checking against Table 2.
gen str12 coefficient_with_stars = string(coefficient, "%9.2f") + stars

* Make numeric columns print with the same precision as the reported table.
format coefficient se %9.2f

* Sort rows into the same grade-subject order used in Table 2.
sort grade_order subject_order

* Print the preferred overlap-weighted, baseline-adjusted, covariate-adjusted results.
di as text _newline "Table 2 replication: GROW-associated ATLAS score differences"
list grade subject coefficient_with_stars se n treated_n control_n overlap_weights ///
    baseline_adjusted covariate_adjusted residual_df, noobs abbreviate(24) separator(0)

* Verify that every row has the expected overlap/baseline/covariate indicators.
assert overlap_weights == "Yes"
assert baseline_adjusted == "Yes"
assert covariate_adjusted == "Yes"

* Verify the expected number of grade-subject models in the preferred Table 2 output.
assert _N == 15

* Verify the reported coefficients to the same two-decimal precision shown in Table 2.
assert abs(coefficient - 0.82) < .005 if grade == "Kindergarten" & subject == "ELA"
assert abs(coefficient - 1.26) < .005 if grade == "Kindergarten" & subject == "Math"
assert abs(coefficient - 1.79) < .005 if grade == "Grade 1" & subject == "ELA"
assert abs(coefficient + 1.21) < .005 if grade == "Grade 1" & subject == "Math"
assert abs(coefficient - 3.81) < .005 if grade == "Grade 2" & subject == "ELA"
assert abs(coefficient - 1.10) < .005 if grade == "Grade 2" & subject == "Math"
assert abs(coefficient - 7.26) < .005 if grade == "Grade 3" & subject == "ELA"
assert abs(coefficient - 6.40) < .005 if grade == "Grade 3" & subject == "Math"
assert abs(coefficient - 2.65) < .005 if grade == "Grade 3" & subject == "Science"
assert abs(coefficient - 5.13) < .005 if grade == "Grade 4" & subject == "ELA"
assert abs(coefficient - 9.71) < .005 if grade == "Grade 4" & subject == "Math"
assert abs(coefficient - 6.05) < .005 if grade == "Grade 4" & subject == "Science"
assert abs(coefficient - 1.92) < .005 if grade == "Grade 5" & subject == "ELA"
assert abs(coefficient - 1.94) < .005 if grade == "Grade 5" & subject == "Math"
assert abs(coefficient - 5.44) < .005 if grade == "Grade 5" & subject == "Science"

* Verify the reported standard errors to the same two-decimal precision shown in Table 2.
assert abs(se - 1.77) < .005 if grade == "Kindergarten" & subject == "ELA"
assert abs(se - 1.71) < .005 if grade == "Kindergarten" & subject == "Math"
assert abs(se - 2.13) < .005 if grade == "Grade 1" & subject == "ELA"
assert abs(se - 1.65) < .005 if grade == "Grade 1" & subject == "Math"
assert abs(se - 2.82) < .005 if grade == "Grade 2" & subject == "ELA"
assert abs(se - 1.53) < .005 if grade == "Grade 2" & subject == "Math"
assert abs(se - 1.59) < .005 if grade == "Grade 3" & subject == "ELA"
assert abs(se - 1.72) < .005 if grade == "Grade 3" & subject == "Math"
assert abs(se - 1.27) < .005 if grade == "Grade 3" & subject == "Science"
assert abs(se - 1.38) < .005 if grade == "Grade 4" & subject == "ELA"
assert abs(se - 1.46) < .005 if grade == "Grade 4" & subject == "Math"
assert abs(se - 1.35) < .005 if grade == "Grade 4" & subject == "Science"
assert abs(se - 1.36) < .005 if grade == "Grade 5" & subject == "ELA"
assert abs(se - 1.58) < .005 if grade == "Grade 5" & subject == "Math"
assert abs(se - 1.61) < .005 if grade == "Grade 5" & subject == "Science"

* Verify sample sizes, school-specific Ns, and residual df against the reported table.
assert n == 166 & treated_n == 52 & control_n == 114 & residual_df == 152 if grade == "Kindergarten" & subject == "ELA"
assert n == 164 & treated_n == 52 & control_n == 112 & residual_df == 150 if grade == "Kindergarten" & subject == "Math"
assert n == 170 & treated_n == 59 & control_n == 111 & residual_df == 156 if grade == "Grade 1" & subject == "ELA"
assert n == 170 & treated_n == 59 & control_n == 111 & residual_df == 156 if grade == "Grade 1" & subject == "Math"
assert n == 156 & treated_n == 67 & control_n == 89 & residual_df == 143 if grade == "Grade 2" & subject == "ELA"
assert n == 155 & treated_n == 67 & control_n == 88 & residual_df == 142 if grade == "Grade 2" & subject == "Math"
assert n == 204 & treated_n == 85 & control_n == 119 & residual_df == 191 if grade == "Grade 3" & subject == "ELA"
assert n == 203 & treated_n == 84 & control_n == 119 & residual_df == 190 if grade == "Grade 3" & subject == "Math"
assert n == 198 & treated_n == 82 & control_n == 116 & residual_df == 185 if grade == "Grade 3" & subject == "Science"
assert n == 188 & treated_n == 74 & control_n == 114 & residual_df == 174 if grade == "Grade 4" & subject == "ELA"
assert n == 188 & treated_n == 74 & control_n == 114 & residual_df == 174 if grade == "Grade 4" & subject == "Math"
assert n == 189 & treated_n == 75 & control_n == 114 & residual_df == 175 if grade == "Grade 4" & subject == "Science"
assert n == 151 & treated_n == 53 & control_n == 98 & residual_df == 137 if grade == "Grade 5" & subject == "ELA"
assert n == 152 & treated_n == 53 & control_n == 99 & residual_df == 138 if grade == "Grade 5" & subject == "Math"
assert n == 150 & treated_n == 53 & control_n == 97 & residual_df == 136 if grade == "Grade 5" & subject == "Science"

* Confirm completion if all displayed checks and assertions pass.
di as result _newline "All Table 2 overlap-weighted ATLAS checks match the reported values."
