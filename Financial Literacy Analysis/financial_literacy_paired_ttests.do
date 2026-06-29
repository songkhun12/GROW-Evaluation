/****************************************************************************************
Purpose: Conduct paired-samples t-tests for financial literacy assessment scores.
Dataset: all_grades_financial_literacy_scores.csv should already be open in Stata.
Output:  Stata paired t-test output for raw scores and percent correct.
Notes:   Raw-score tests compare post_total_correct to pre_total_correct. Percent-correct
         tests use grade-specific test lengths: Grade 3 has 10 questions, and Grades 4
         and 5 have 11 questions. The paired difference is post-test minus pre-test.
****************************************************************************************/

version 18.0
set more off

* Confirm that the already-open dataset contains the variables needed for the tests.
confirm variable grade pre_total_correct post_total_correct

* Ensure score variables are numeric if the CSV was imported with string score fields.
foreach var in pre_total_correct post_total_correct {
    capture confirm numeric variable `var'
    if _rc {
        destring `var', replace ignore(" ")
    }
}

capture confirm numeric variable grade
if _rc {
    destring grade, replace ignore(" ")
}

* Paired-samples t-tests using raw scores by grade and for the combined sample.
ttest post_total_correct == pre_total_correct if grade == 3
ttest post_total_correct == pre_total_correct if grade == 4
ttest post_total_correct == pre_total_correct if grade == 5
ttest post_total_correct == pre_total_correct

* Create percent-correct variables using grade-specific test lengths.
capture drop max_score pre_percent_correct post_percent_correct
quietly generate max_score = .
quietly replace max_score = 10 if grade == 3
quietly replace max_score = 11 if inlist(grade, 4, 5)
quietly generate pre_percent_correct = 100 * pre_total_correct / max_score if !missing(pre_total_correct, max_score)
quietly generate post_percent_correct = 100 * post_total_correct / max_score if !missing(post_total_correct, max_score)
label variable pre_percent_correct  "Pre-test percent correct"
label variable post_percent_correct "Post-test percent correct"

* Paired-samples t-tests using percent correct by grade and for the combined sample.
ttest post_percent_correct == pre_percent_correct if grade == 3
ttest post_percent_correct == pre_percent_correct if grade == 4
ttest post_percent_correct == pre_percent_correct if grade == 5
ttest post_percent_correct == pre_percent_correct
