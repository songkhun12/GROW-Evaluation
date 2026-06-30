/****************************************************************************************
  Appendix F. Robustness Test of GROW Referral Estimates Using Any-Referral Logistic Models

  Purpose:
    Reproduce Table F1 by estimating overlap-weighted logistic regression models for
    whether each student had any school referral, any bus referral, or any school/bus
    referral during the study period.

  Required input:
    Referral Evaluation/jmtes_jes_referral_student_data.csv

  Example command from the repository root:
    do "Referral Evaluation/jmtes_jes_referral_any_referral_logit_robustness_analysis.do"
****************************************************************************************/

* Use Stata 17 syntax for compatibility with the project replication files.
version 17.0

* Do not pause output; the reviewer asked that regression results be shown in Stata.
set more off

* Clear any data already in memory before opening the referral analysis file.
clear

* Define the referral analysis file with propensity scores and overlap weights.
local input_csv "Referral Evaluation/jmtes_jes_referral_student_data.csv"

* Fall back to the local filename when running from inside Referral Evaluation.
capture confirm file "`input_csv'"
if _rc {
    local input_csv "jmtes_jes_referral_student_data.csv"
}

* Stop with a clear error if the required analysis file is missing.
capture confirm file "`input_csv'"
if _rc {
    di as error "Input file not found: `input_csv'"
    exit 601
}

* Open the student-level referral analysis file.
import delimited using "`input_csv'", clear varnames(1)

* Confirm all variables needed for Table F1 are present.
foreach var in school jmtes grade female black age meal_status entry_code overlap_weight ///
    any_school_referral any_bus_referral any_referral {
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
replace overlap_weight = real(string(overlap_weight))
replace any_school_referral = real(string(any_school_referral))
replace any_bus_referral = real(string(any_bus_referral))
replace any_referral = real(string(any_referral))

* Confirm the full analytic sample size used by Table F1.
count
assert r(N) == 1093

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

* Show overlap-weight diagnostics before running logistic models.
di as text _newline "Appendix F overlap-weight diagnostics"
summarize overlap_weight
tabstat overlap_weight, by(school) statistics(mean sd min p25 median p75 max n) ///
    columns(statistics) format(%9.3f)

* Label outcomes for readable Stata output.
label variable any_school_referral "Any school referral"
label variable any_bus_referral    "Any bus referral"
label variable any_referral        "Any school or bus referral"

* Define the any-referral outcomes used in Table F1.
local outcomes any_school_referral any_bus_referral any_referral

* Define display labels that match the reported table.
local label_any_school_referral "Any school referral"
local label_any_bus_referral    "Any bus referral"
local label_any_referral        "Any school or bus referral"

* Create a temporary results file for the three logistic robustness models.
tempfile tablef1_results

* Close any stale post handle so the do-file can be re-run in the same Stata session.
capture postclose tablef1

* Open a postfile to collect coefficients, robust SEs, odds ratios, probabilities, N, and events.
postfile tablef1 str30 outcome double coefficient robust_se odds_ratio jes_weighted_probability ///
    jmtes_weighted_probability probability_difference n events using `tablef1_results', replace

* Loop over each any-referral outcome.
foreach y of local outcomes {

    * Save the human-readable outcome label for this iteration.
    local y_label "`label_`y''"

    * Compute the JES overlap-weighted probability for this outcome.
    summarize `y' if jmtes == 0 [aw = overlap_weight], meanonly
    scalar jes_probability = r(mean)

    * Compute the JMTES overlap-weighted probability for this outcome.
    summarize `y' if jmtes == 1 [aw = overlap_weight], meanonly
    scalar jmtes_probability = r(mean)

    * Count the unweighted number of students with this referral outcome.
    summarize `y', meanonly
    scalar referral_events = r(sum)

    * Estimate and show the covariate-adjusted overlap-weighted logistic robustness model.
    di as text _newline "Table F1 OW logit + covariates model: `y_label'"
    logit `y' jmtes i.grade_cat female black age i.meal_status_cat i.entry_code_cat ///
        [pw = overlap_weight], vce(robust)

    * Post the logistic model results and weighted probabilities.
    post tablef1 ("`y_label'") (_b[jmtes]) (_se[jmtes]) (exp(_b[jmtes])) ///
        (jes_probability) (jmtes_probability) (jmtes_probability - jes_probability) (e(N)) (referral_events)
}

* Close the posted results dataset.
postclose tablef1

* Open the results dataset for formatting and verification.
use `tablef1_results', clear

* Format numeric columns to match the reported table precision.
format coefficient robust_se odds_ratio %9.3f
format jes_weighted_probability jmtes_weighted_probability probability_difference %9.3f
format n events %9.0f

* Print the Table F1 robustness replication results.
di as text _newline "Table F1 any-referral logistic robustness results"
list outcome coefficient robust_se odds_ratio jes_weighted_probability ///
    jmtes_weighted_probability probability_difference n events, noobs abbreviate(30) separator(0)

* Verify coefficients, robust standard errors, and odds ratios against reported Table F1 values.
assert abs(coefficient + 0.883) < 0.0015 if outcome == "Any school referral"
assert abs(robust_se - 0.181) < 0.0015 if outcome == "Any school referral"
assert abs(odds_ratio - 0.413) < 0.0015 if outcome == "Any school referral"
assert abs(coefficient + 1.286) < 0.0015 if outcome == "Any bus referral"
assert abs(robust_se - 0.338) < 0.0015 if outcome == "Any bus referral"
assert abs(odds_ratio - 0.276) < 0.0015 if outcome == "Any bus referral"
assert abs(coefficient + 0.893) < 0.0015 if outcome == "Any school or bus referral"
assert abs(robust_se - 0.172) < 0.0015 if outcome == "Any school or bus referral"
assert abs(odds_ratio - 0.409) < 0.0015 if outcome == "Any school or bus referral"

* Verify weighted probabilities, probability differences, observations, and events.
assert abs(jes_weighted_probability - 0.250) < 0.0015 if outcome == "Any school referral"
assert abs(jmtes_weighted_probability - 0.127) < 0.0015 if outcome == "Any school referral"
assert abs(probability_difference + 0.123) < 0.0015 if outcome == "Any school referral"
assert events == 223 if outcome == "Any school referral"
assert abs(jes_weighted_probability - 0.088) < 0.0015 if outcome == "Any bus referral"
assert abs(jmtes_weighted_probability - 0.027) < 0.0015 if outcome == "Any bus referral"
assert abs(probability_difference + 0.061) < 0.0015 if outcome == "Any bus referral"
assert events == 70 if outcome == "Any bus referral"
assert abs(jes_weighted_probability - 0.284) < 0.0015 if outcome == "Any school or bus referral"
assert abs(jmtes_weighted_probability - 0.146) < 0.0015 if outcome == "Any school or bus referral"
assert abs(probability_difference + 0.138) < 0.0015 if outcome == "Any school or bus referral"
assert events == 253 if outcome == "Any school or bus referral"
assert n == 1093

* Confirm completion if every check passes.
di as result _newline "Table F1 any-referral logistic robustness checks match the reported values."
