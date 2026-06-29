/****************************************************************************************
  Table 1. Descriptive Statistics for 2026 Summative ATLAS Assessment Scores

  Assumption:
    The student-level 2026 summative ATLAS data file is already open in Stata and ready
    for tabstat. The open dataset must include these variables:
      grade subject school score

  Example command to open the prepared CSV before running this file:
    import delimited using "results/atlas_2026_summative_student_scores.csv", clear varnames(1)

  Run after opening the data:
    do "results/atlas_2026_summative_descriptive_statistics.do"
****************************************************************************************/

version 17.0
set more off

* Confirm the variables needed for tabstat are available in the open dataset.
foreach var in grade subject school score {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in the open dataset."
        exit 111
    }
}

* Print mean, standard deviation, median, and N by school within each grade/subject cell.
sort grade subject school
by grade subject: tabstat score, by(school) statistics(mean sd median n) ///
    columns(statistics) format(%9.2f)

* Create a compact Table 1 check in memory, including JMTES - JES differences in means.
preserve
    collapse (mean) mean = score (sd) sd = score (p50) median = score (count) n = score, ///
        by(grade subject school)

    reshape wide mean sd median n, i(grade subject) j(school) string

    gen difference_in_mean = meanJMTES - meanJES
    gen observations = string(nJMTES, "%9.0f") + "/" + string(nJES, "%9.0f")

    rename meanJMTES   jmtes_mean
    rename sdJMTES     jmtes_sd
    rename medianJMTES jmtes_median
    rename nJMTES      jmtes_n
    rename meanJES     jes_mean
    rename sdJES       jes_sd
    rename medianJES   jes_median
    rename nJES        jes_n

    gen grade_order = .
    replace grade_order = 0 if grade == "Kindergarten"
    replace grade_order = real(regexs(1)) if regexm(grade, "^Grade ([0-9]+)$")
    gen subject_order = .
    replace subject_order = 1 if subject == "ELA"
    replace subject_order = 2 if subject == "Math"
    replace subject_order = 3 if subject == "Science"
    sort grade_order subject_order

    format jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean %9.2f
    format jmtes_median jes_median %9.1f

    list grade subject jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean ///
        jmtes_median jes_median observations, noobs abbreviate(20) separator(0)
restore
