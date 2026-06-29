/****************************************************************************************
Purpose: Create descriptive statistics for financial literacy assessment scores.
Dataset: all_grades_financial_literacy_scores.csv should already be open in Stata.
Output:  financial_literacy_descriptive_statistics_aej.tex
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

* Build an AEJ-style LaTeX table from the same descriptive statistics.
preserve
keep grade pre_total_correct post_total_correct score_gain
keep if !missing(grade)

tempfile bygrade allgrades tabledata
collapse ///
    (count) n=pre_total_correct ///
    (mean) pre_mean=pre_total_correct post_mean=post_total_correct diff_mean=score_gain ///
    (sd) pre_sd=pre_total_correct post_sd=post_total_correct diff_sd=score_gain ///
    (median) pre_median=pre_total_correct post_median=post_total_correct diff_median=score_gain, ///
    by(grade)
generate str12 sample = "Grade " + string(grade)
save `bygrade', replace

restore
preserve
keep pre_total_correct post_total_correct score_gain
collapse ///
    (count) n=pre_total_correct ///
    (mean) pre_mean=pre_total_correct post_mean=post_total_correct diff_mean=score_gain ///
    (sd) pre_sd=pre_total_correct post_sd=post_total_correct diff_sd=score_gain ///
    (median) pre_median=pre_total_correct post_median=post_total_correct diff_median=score_gain
generate grade = 999
generate str12 sample = "All grades"
save `allgrades', replace

use `bygrade', clear
append using `allgrades'
sort grade
save `tabledata', replace

file open aej using "financial_literacy_descriptive_statistics_aej.tex", write replace
file write aej "\begin{table}[!htbp]\centering" _n
file write aej "\caption{Descriptive Statistics for Financial Literacy Assessment Scores}" _n
file write aej "\label{tab:financial_literacy_descriptive_statistics}" _n
file write aej "\begin{tabular}{lcccccccccc}" _n
file write aej "\toprule" _n
file write aej "& & \multicolumn{3}{c}{Pre-test} & \multicolumn{3}{c}{Post-test} & \multicolumn{3}{c}{Difference} \\" _n
file write aej "\cmidrule(lr){3-5}\cmidrule(lr){6-8}\cmidrule(lr){9-11}" _n
file write aej "Sample & N & Mean & SD & Median & Mean & SD & Median & Mean & SD & Median \\" _n
file write aej "\midrule" _n

use `tabledata', clear
forvalues i = 1/`=_N' {
    local sample = sample[`i']
    local n = string(n[`i'], "%9.0f")
    local pre_mean = string(pre_mean[`i'], "%9.2f")
    local pre_sd = string(pre_sd[`i'], "%9.2f")
    local pre_median = string(pre_median[`i'], "%9.2f")
    local post_mean = string(post_mean[`i'], "%9.2f")
    local post_sd = string(post_sd[`i'], "%9.2f")
    local post_median = string(post_median[`i'], "%9.2f")
    local diff_mean = string(diff_mean[`i'], "%9.2f")
    local diff_sd = string(diff_sd[`i'], "%9.2f")
    local diff_median = string(diff_median[`i'], "%9.2f")
    file write aej "`sample' & `n' & `pre_mean' & `pre_sd' & `pre_median' & `post_mean' & `post_sd' & `post_median' & `diff_mean' & `diff_sd' & `diff_median' \\" _n
}

file write aej "\bottomrule" _n
file write aej "\end{tabular}" _n
file write aej "\begin{minipage}{0.95\linewidth}" _n
file write aej "\vspace{0.2cm}\footnotesize \emph{Notes:} The sample is drawn from \texttt{all\_grades\_financial\_literacy\_scores.csv}. Difference is the student-level post-test minus pre-test score; its mean equals the post-test mean minus the pre-test mean. Standard deviations are sample standard deviations." _n
file write aej "\end{minipage}" _n
file write aej "\end{table}" _n
file close aej
restore
