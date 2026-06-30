/****************************************************************************************
Purpose: Estimate simplified difference-in-differences style models using only the observed
         curriculum participation groups in the combined Grade 3-5 sample.
Dataset: all_grades_financial_literacy_scores.csv should already be open in Stata.
Output:  Stata mixed-model regression output for unadjusted and adjusted models.
Notes:   The online-only group is empty in the analytic sample, so the model compares the
         three observed groups: curriculum only, Economics Arkansas activities only, and
         both online curriculum plus Economics Arkansas activities. Regressions are not
         run quietly so results are displayed in Stata.
****************************************************************************************/

version 18.0
set more off

* Confirm that the already-open dataset contains the variables needed for the analysis.
confirm variable student_id grade pre_total_correct post_total_correct ///
    incentive_1_ea_lesson_activities_participation ///
    incentive_2_fin_literacy_module_online_participation ///
    at_risk_total_absence_pct_enrolled at_risk_gender at_risk_ethnic_name ///
    at_risk_student_age at_risk_meal_status_code at_risk_entry_code_e_w ///
    at_risk_school_referral_severity_points_170 at_risk_bus_referral_severity_points_170

* Ensure score, grade, participation, and continuous covariate variables are numeric.
foreach var in grade pre_total_correct post_total_correct ///
    incentive_1_ea_lesson_activities_participation ///
    incentive_2_fin_literacy_module_online_participation ///
    at_risk_total_absence_pct_enrolled at_risk_student_age ///
    at_risk_school_referral_severity_points_170 at_risk_bus_referral_severity_points_170 {
    capture confirm numeric variable `var'
    if _rc {
        destring `var', replace ignore(" ")
    }
}

* Convert categorical covariates to numeric factor variables when needed.
capture drop gender_id ethnicity_id meal_status_id entry_code_id
capture confirm string variable at_risk_gender
if !_rc {
    encode at_risk_gender, gen(gender_id)
}
else {
    generate gender_id = at_risk_gender
}

capture confirm string variable at_risk_ethnic_name
if !_rc {
    encode at_risk_ethnic_name, gen(ethnicity_id)
}
else {
    generate ethnicity_id = at_risk_ethnic_name
}

capture confirm string variable at_risk_meal_status_code
if !_rc {
    encode at_risk_meal_status_code, gen(meal_status_id)
}
else {
    generate meal_status_id = at_risk_meal_status_code
}

capture confirm string variable at_risk_entry_code_e_w
if !_rc {
    encode at_risk_entry_code_e_w, gen(entry_code_id)
}
else {
    generate entry_code_id = at_risk_entry_code_e_w
}

* Percent-correct outcomes place grade-specific assessments on a common 0-to-100 scale.
capture drop max_score pre_percent_correct post_percent_correct
generate max_score = .
replace max_score = 10 if grade == 3
replace max_score = 11 if inlist(grade, 4, 5)
generate pre_percent_correct = 100 * pre_total_correct / max_score if !missing(pre_total_correct, max_score)
generate post_percent_correct = 100 * post_total_correct / max_score if !missing(post_total_correct, max_score)
label variable pre_percent_correct  "Pre-test percent correct"
label variable post_percent_correct "Post-test percent correct"

* Define observed participation groups. Online-only is intentionally not modeled because no
* students in the analytic sample completed only the online curriculum.
capture drop observed_participation
generate observed_participation = .
replace observed_participation = 1 if incentive_1_ea_lesson_activities_participation == 0 & incentive_2_fin_literacy_module_online_participation == 0
replace observed_participation = 2 if incentive_1_ea_lesson_activities_participation == 1 & incentive_2_fin_literacy_module_online_participation == 0
replace observed_participation = 3 if incentive_1_ea_lesson_activities_participation == 1 & incentive_2_fin_literacy_module_online_participation == 1
label define observed_participation_lbl ///
    1 "Curriculum only" ///
    2 "Activities only" ///
    3 "Online + activities", replace
label values observed_participation observed_participation_lbl
label variable observed_participation "Observed curriculum participation group"

* Numeric student identifier for the random intercept.
capture drop student_panel_id
egen student_panel_id = group(student_id), label
label variable student_panel_id "Student random-intercept identifier"

* Reshape to long format: post = 0 for pre-test, post = 1 for post-test.
preserve
keep if inlist(observed_participation, 1, 2, 3)
keep student_panel_id grade observed_participation pre_percent_correct post_percent_correct ///
    at_risk_total_absence_pct_enrolled gender_id ethnicity_id at_risk_student_age ///
    meal_status_id entry_code_id at_risk_school_referral_severity_points_170 ///
    at_risk_bus_referral_severity_points_170
rename pre_percent_correct score0
rename post_percent_correct score1
reshape long score, i(student_panel_id) j(post)
label define post_lbl 0 "Pre-test" 1 "Post-test", replace
label values post post_lbl
label variable score "Financial literacy score: percent correct"
label variable post  "Post-test indicator"

* Model 1: unadjusted DiD-style model comparing observed participation groups.
mixed score i.post##ib1.observed_participation || student_panel_id:, mle
estimates store observed_did_model_1

* Model 2: adjusted DiD-style model with grade and student-level covariates.
mixed score i.post##ib1.observed_participation i.grade ///
    c.at_risk_total_absence_pct_enrolled i.gender_id i.ethnicity_id ///
    c.at_risk_student_age i.meal_status_id i.entry_code_id ///
    c.at_risk_school_referral_severity_points_170 ///
    c.at_risk_bus_referral_severity_points_170 ///
    || student_panel_id:, mle
estimates store observed_did_model_2

restore
