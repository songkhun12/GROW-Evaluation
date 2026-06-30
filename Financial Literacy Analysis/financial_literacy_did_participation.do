/****************************************************************************************
Purpose: Estimate a pre-post difference-in-differences model for percent-correct financial
         literacy scores by online-module and Economics Arkansas activity participation.
Dataset: all_grades_financial_literacy_scores.csv should already be open in Stata.
Output:  Stata regression output for the student fixed-effects DiD specification.
Notes:   Percent-correct scores use grade-specific test lengths: Grade 3 has 10 questions,
         while Grades 4 and 5 have 11 questions. The model estimates:
         Score_it = b0 + b1 Post_t + b2 Online_i + b3 Activities_i
                    + b4 Online_i*Activities_i + b5 Post_t*Online_i
                    + b6 Post_t*Activities_i + b7 Post_t*Online_i*Activities_i
                    + b8 Grade_i + u_i + e_it.
         Time-invariant main effects and grade are absorbed by student fixed effects.
         In this dataset, there are no students in the online-only group, so Stata will
         omit one collinear online interaction term from the saturated model.
****************************************************************************************/

version 18.0
set more off

* Confirm that the already-open dataset contains the variables needed for the analysis.
confirm variable student_id grade pre_total_correct post_total_correct ///
    incentive_1_ea_lesson_activities_participation ///
    incentive_2_fin_literacy_module_online_participation

* Ensure score, grade, and participation variables are numeric if imported as strings.
foreach var in grade pre_total_correct post_total_correct ///
    incentive_1_ea_lesson_activities_participation ///
    incentive_2_fin_literacy_module_online_participation {
    capture confirm numeric variable `var'
    if _rc {
        destring `var', replace ignore(" ")
    }
}

* Create percent-correct scores on a common 0-to-100 scale.
capture drop max_score pre_percent_correct post_percent_correct
quietly generate max_score = .
quietly replace max_score = 10 if grade == 3
quietly replace max_score = 11 if inlist(grade, 4, 5)
quietly generate pre_percent_correct = 100 * pre_total_correct / max_score if !missing(pre_total_correct, max_score)
quietly generate post_percent_correct = 100 * post_total_correct / max_score if !missing(post_total_correct, max_score)
label variable pre_percent_correct  "Pre-test percent correct"
label variable post_percent_correct "Post-test percent correct"

* Grade controls use Grade 3 as the reference group.
capture drop grade4 grade5
quietly generate grade4 = grade == 4 if !missing(grade)
quietly generate grade5 = grade == 5 if !missing(grade)
label variable grade4 "Grade 4 indicator"
label variable grade5 "Grade 5 indicator"

* Define treatment component indicators.
capture drop online activities
quietly generate online = incentive_2_fin_literacy_module_online_participation == 1 if !missing(incentive_2_fin_literacy_module_online_participation)
quietly generate activities = incentive_1_ea_lesson_activities_participation == 1 if !missing(incentive_1_ea_lesson_activities_participation)
label variable online     "Completed online curriculum module"
label variable activities "Participated in Economics Arkansas activities"

* Create a numeric student panel identifier that is safe for xtset/reshape.
capture drop student_panel_id
capture confirm numeric variable student_id
if _rc {
    egen student_panel_id = group(student_id), label
}
else {
    egen student_panel_id = group(student_id), label
}
label variable student_panel_id "Student fixed-effect identifier"

* Reshape from one row per student to one row per student-test period.
preserve
keep student_panel_id grade4 grade5 online activities pre_percent_correct post_percent_correct
rename pre_percent_correct score0
rename post_percent_correct score1
reshape long score, i(student_panel_id) j(post)
label define post_lbl 0 "Pre-test" 1 "Post-test", replace
label values post post_lbl
label variable score "Percent correct score"
label variable post  "Post-test indicator"

* Student fixed-effects DiD model. Stata absorbs time-invariant main effects and grade.
xtset student_panel_id post
xtreg score i.post##i.online##i.activities grade4 grade5, fe vce(cluster student_panel_id)

* First-difference equivalent for the identified post interactions. Because the online-only
* cell is empty, the post-by-online and triple interaction are not separately identified.
restore
capture drop percent_gain online_activities
quietly generate percent_gain = post_percent_correct - pre_percent_correct if !missing(pre_percent_correct, post_percent_correct)
quietly generate online_activities = online * activities
label variable percent_gain "Post-pre difference in percent correct"
label variable online_activities "Online curriculum x Economics Arkansas activities"
regress percent_gain online activities online_activities
