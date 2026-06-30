/****************************************************************************************
Purpose: Conduct paired-samples t-tests for percent-correct financial literacy outcomes by
         grade and curriculum participation group.
Dataset: all_grades_financial_literacy_scores.csv should already be open in Stata.
Output:  Stata paired t-test output for each grade-by-participation combination and for
         the combined all-grade sample by participation group.
Notes:   Percent-correct scores use grade-specific test lengths: Grade 3 has 10 questions,
         while Grades 4 and 5 have 11 questions. The paired difference is post-test minus
         pre-test percent correct.
****************************************************************************************/

version 18.0
set more off

* Confirm that the already-open dataset contains the variables needed for the analysis.
confirm variable grade pre_total_correct post_total_correct ///
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

* Percent-correct outcomes place grades with different assessment lengths on a common scale.
capture drop max_score pre_percent_correct post_percent_correct percent_gain
quietly generate max_score = .
quietly replace max_score = 10 if grade == 3
quietly replace max_score = 11 if inlist(grade, 4, 5)
quietly generate pre_percent_correct = 100 * pre_total_correct / max_score if !missing(pre_total_correct, max_score)
quietly generate post_percent_correct = 100 * post_total_correct / max_score if !missing(post_total_correct, max_score)
quietly generate percent_gain = post_percent_correct - pre_percent_correct if !missing(pre_percent_correct, post_percent_correct)
label variable pre_percent_correct  "Pre-test percent correct"
label variable post_percent_correct "Post-test percent correct"
label variable percent_gain         "Difference in means"

* Define mutually exclusive curriculum participation groups.
capture drop curriculum_participation
quietly generate curriculum_participation = .
quietly replace curriculum_participation = 1 if incentive_1_ea_lesson_activities_participation == 0 & incentive_2_fin_literacy_module_online_participation == 0
quietly replace curriculum_participation = 2 if incentive_1_ea_lesson_activities_participation == 0 & incentive_2_fin_literacy_module_online_participation == 1
quietly replace curriculum_participation = 3 if incentive_1_ea_lesson_activities_participation == 1 & incentive_2_fin_literacy_module_online_participation == 0
quietly replace curriculum_participation = 4 if incentive_1_ea_lesson_activities_participation == 1 & incentive_2_fin_literacy_module_online_participation == 1
label define curriculum_participation_lbl ///
    1 "Financial education only" ///
    2 "Online only" ///
    3 "Economics Arkansas only" ///
    4 "Online + Economics Arkansas", replace
label values curriculum_participation curriculum_participation_lbl
label variable curriculum_participation "Curriculum participation group"

* Paired-samples t-tests for each grade-by-participation combination.
forvalues g = 3/5 {
    foreach p in 1 2 3 4 {
        quietly count if grade == `g' & curriculum_participation == `p' & ///
            !missing(pre_percent_correct, post_percent_correct)
        if r(N) >= 2 {
            display as text "Paired t-test: Grade `g', participation group `p'"
            ttest post_percent_correct == pre_percent_correct if grade == `g' & curriculum_participation == `p'
        }
        else {
            display as text "Skipping Grade `g', participation group `p': fewer than two paired observations."
        }
    }
}

* Paired-samples t-tests for each participation group in the combined all-grade sample.
foreach p in 1 2 3 4 {
    quietly count if curriculum_participation == `p' & ///
        !missing(pre_percent_correct, post_percent_correct)
    if r(N) >= 2 {
        display as text "Paired t-test: All grades, participation group `p'"
        ttest post_percent_correct == pre_percent_correct if curriculum_participation == `p'
    }
    else {
        display as text "Skipping all grades, participation group `p': fewer than two paired observations."
    }
}
