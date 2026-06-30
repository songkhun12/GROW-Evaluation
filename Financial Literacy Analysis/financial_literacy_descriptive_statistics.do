/****************************************************************************************
Purpose: Create descriptive statistics for financial literacy assessment scores.
Dataset: all_grades_financial_literacy_scores.csv should already be open in Stata.
Output:  Stata tabstat output for raw scores and percent correct.
Notes:   The table reports pre-test, post-test, and gain-score statistics by grade and
         for the pooled sample. The difference in means is the mean gain score:
         post_total_correct - pre_total_correct.
****************************************************************************************/

version 18.0
set more off

* Confirm that the already-open dataset contains the variables needed for the table.
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

* Difference in means: student-level post-pre gain, whose mean equals post mean minus pre mean.
capture drop score_gain
quietly generate score_gain = post_total_correct - pre_total_correct if !missing(pre_total_correct, post_total_correct)
label variable pre_total_correct  "Pre-test score"
label variable post_total_correct "Post-test score"
label variable score_gain         "Difference in means"

* Required tabstat calculations by grade and for the combined all-grade sample.
tabstat pre_total_correct post_total_correct score_gain, by(grade) statistics(n mean sd median) columns(statistics)
tabstat pre_total_correct post_total_correct score_gain, statistics(n mean sd median) columns(statistics)

* Percent-correct statistics use grade-specific test lengths:
* Grade 3 has 10 questions; grades 4 and 5 have 11 questions.
capture drop max_score pre_percent_correct post_percent_correct percent_gain
quietly generate max_score = .
quietly replace max_score = 10 if grade == 3
quietly replace max_score = 11 if inlist(grade, 4, 5)
quietly generate pre_percent_correct = 100 * pre_total_correct / max_score if !missing(pre_total_correct, max_score)
quietly generate post_percent_correct = 100 * post_total_correct / max_score if !missing(post_total_correct, max_score)
quietly generate percent_gain = post_percent_correct - pre_percent_correct if !missing(pre_percent_correct, post_percent_correct)
label variable pre_percent_correct  "Pre-test percent correct"
label variable post_percent_correct "Post-test percent correct"
label variable percent_gain         "Difference in mean percent correct"

* Percent-correct tabstat calculations by grade and for the combined all-grade sample.
tabstat pre_percent_correct post_percent_correct percent_gain, by(grade) statistics(n mean sd median) columns(statistics)
tabstat pre_percent_correct post_percent_correct percent_gain, statistics(n mean sd median) columns(statistics)
