/****************************************************************************************
  Table 1. Descriptive Statistics for 2026 Summative ATLAS Assessment Scores

  Purpose:
    Open the combined student-level 2026 summative ATLAS CSV and use tabstat to calculate
    school-level descriptive statistics for each grade/subject cell. The combined CSV was
    created by stacking the Kindergarten through Grade 5 cleaned student files and keeping
    non-missing Summer 2026 JMTES/JES scores.

  Input:
    results/atlas_2026_summative_student_scores.csv

  Outputs:
    results/atlas_2026_summative_descriptive_statistics_stata.csv
    results/atlas_2026_summative_descriptive_statistics_stata.dta

  Run from the repository root:
    do "results/atlas_2026_summative_descriptive_statistics.do"
****************************************************************************************/

version 17.0
clear all
set more off

local input_csv  "results/atlas_2026_summative_student_scores.csv"
local output_csv "results/atlas_2026_summative_descriptive_statistics_stata.csv"
local output_dta "results/atlas_2026_summative_descriptive_statistics_stata.dta"

        capture confirm numeric variable `score_col'
        if _rc destring `score_col', replace force

        keep `score_col'
        rename `score_col' score
        keep if !missing(score)
        gen str20 grade = "`grade'"
        gen str10 school = "`school'"
        gen str10 subject = "`subject'"
        append using `one_file'
        save `one_file', replace
    }

label variable grade      "Grade"
label variable subject    "Subject"
label variable school     "School"
label variable student_id "Student ID"
label variable score      "2026 Summative ATLAS score"

* Print the descriptive statistics requested for each grade/subject/school cell.
levelsof grade, local(grades)
foreach g of local grades {
    levelsof subject if grade == "`g'", local(subjects)
    foreach s of local subjects {
        di as text _newline "Grade: `g' | Subject: `s'"
        tabstat score if grade == "`g'" & subject == "`s'", by(school) ///
            statistics(mean sd median n) columns(statistics) format(%9.2f)
    }
}

* Save a compact table with the same quantities and the JMTES - JES mean difference.
preserve
    collapse (count) n = score (mean) mean = score (sd) sd = score (p50) median = score, ///
        by(grade subject school)

    reshape wide n mean sd median, i(grade subject) j(school) string

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
    format jmtes_n jes_n %9.0f

    order grade subject jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean ///
        jmtes_median jes_median observations jmtes_n jes_n

    label variable jmtes_mean         "JMTES mean"
    label variable jmtes_sd           "JMTES standard deviation"
    label variable jes_mean           "JES mean"
    label variable jes_sd             "JES standard deviation"
    label variable difference_in_mean "Difference in means (JMTES - JES)"
    label variable jmtes_median       "JMTES median"
    label variable jes_median         "JES median"
    label variable observations       "Observations (JMTES/JES)"

    notes: Recomputed from results/atlas_2026_summative_student_scores.csv.
    notes: tabstat output above reports mean, standard deviation, median, and N by school.

    save "`output_dta'", replace
    export delimited grade subject jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean ///
        jmtes_median jes_median observations jmtes_n jes_n using "`output_csv'", replace
restore
