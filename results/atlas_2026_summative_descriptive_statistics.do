/****************************************************************************************
  Table 1. Descriptive Statistics for 2026 Summative ATLAS Assessment Scores

  Purpose:
    Recompute Table 1 directly from the school ATLAS Excel workbooks. The do-file finds
    the real header row in each workbook, keeps the subject-specific "Sum 2026" score
    column, and calculates means, standard deviations, medians, observation counts, and
    the JMTES minus JES mean difference.

  Outputs:
    results/atlas_2026_summative_descriptive_statistics_stata.csv
    results/atlas_2026_summative_descriptive_statistics_stata.dta

  Run from the repository root:
    do "results/atlas_2026_summative_descriptive_statistics.do"
****************************************************************************************/

version 17.0
clear all
set more off

local output_csv "results/atlas_2026_summative_descriptive_statistics_stata.csv"
local output_dta "results/atlas_2026_summative_descriptive_statistics_stata.dta"
tempfile all_scores school_stats jmtes_stats jes_stats

program define append_atlas_scores
    version 17.0
    syntax, Grade(string) School(string) File(string) Subjects(string) Saving(string) [First]

    capture confirm file "`file'"
    if _rc {
        di as error "Input file not found: `file'"
        di as error "Run this do-file from the repository root."
        exit 601
    }

    import excel using "`file'", clear allstring

    local header_row = .
    quietly count
    local nrows = r(N)
    ds
    local vars `r(varlist)'
    forvalues i = 1/`nrows' {
        foreach v of local vars {
            if inlist(strtrim(`v'[`i']), "Student ID", "Student IDs", "ID Number") {
                local header_row = `i'
                continue, break
            }
        }
        if `header_row' < . continue, break
    }

    if `header_row' == . {
        di as error "Could not locate the ATLAS header row in: `file'"
        exit 459
    }

    import excel using "`file'", clear firstrow cellrange(A`header_row')

    tempfile one_file
    clear
    save `one_file', emptyok replace

    foreach subject of local subjects {
        import excel using "`file'", clear firstrow cellrange(A`header_row')
        ds *`subject'*Sum*2026*, has(type numeric)
        local score_col `r(varlist)'
        if "`score_col'" == "" {
            ds *`subject'*Sum*2026*
            local score_col `r(varlist)'
        }
        local score_col : word 1 of `score_col'
        if "`score_col'" == "" {
            di as error "Missing `subject' Sum 2026 score column in: `file'"
            exit 111
        }

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

    use `one_file', clear
    if "`first'" != "" {
        save `saving', replace
    }
    else {
        append using `saving'
        save `saving', replace
    }
end

append_atlas_scores, grade("Kindergarten") school("JMTES") ///
    file("Kindergarten/JMTES Atlas Report - Kindergarten.xlsx") subjects("ELA Math") ///
    saving(`all_scores') first
append_atlas_scores, grade("Kindergarten") school("JES") ///
    file("Kindergarten/JES Atlas Report - Kindergarten.xlsx") subjects("ELA Math") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 1") school("JMTES") ///
    file("Grade 1/JMTES Atlas Report - Grade 1.xlsx") subjects("ELA Math") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 1") school("JES") ///
    file("Grade 1/JES Atlas Report - Grade 1.xlsx") subjects("ELA Math") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 2") school("JMTES") ///
    file("Grade 2/JMTES Atlas Report - Grade 2.xlsx") subjects("ELA Math") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 2") school("JES") ///
    file("Grade 2/JES Atlas Report - Grade 2.xlsx") subjects("ELA Math") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 3") school("JMTES") ///
    file("Grade 3/JMTES Atlas Report - Grade 3.xlsx") subjects("ELA Math Science") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 3") school("JES") ///
    file("Grade 3/JES Atlas Report - Grade 3.xlsx") subjects("ELA Math Science") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 4") school("JMTES") ///
    file("Grade 4/JMTES Atlas Report - Grade 4 - Current Year.xlsx") subjects("ELA Math Science") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 4") school("JES") ///
    file("Grade 4/JES Atlas Report - Grade 4.xlsx") subjects("ELA Math Science") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 5") school("JMTES") ///
    file("Grade 5/JMTES Atlas Report - Grade 5 - Current Year.xlsx") subjects("ELA Math Science") ///
    saving(`all_scores')
append_atlas_scores, grade("Grade 5") school("JES") ///
    file("Grade 5/JES Atlas Report - Grade 5.xlsx") subjects("ELA Math Science") ///
    saving(`all_scores')

use `all_scores', clear
collapse (count) n = score (mean) mean = score (sd) sd = score (p50) median = score, ///
    by(grade subject school)
save `school_stats', replace

preserve
    keep if school == "JMTES"
    rename (mean sd median n) (jmtes_mean jmtes_sd jmtes_median jmtes_n)
    keep grade subject jmtes_*
    save `jmtes_stats', replace
restore

keep if school == "JES"
rename (mean sd median n) (jes_mean jes_sd jes_median jes_n)
keep grade subject jes_*
save `jes_stats', replace

use `jmtes_stats', clear
merge 1:1 grade subject using `jes_stats', nogen assert(match)
gen difference_in_mean = jmtes_mean - jes_mean
gen observations = string(jmtes_n, "%9.0f") + "/" + string(jes_n, "%9.0f")

gen grade_order = .
replace grade_order = 0 if grade == "Kindergarten"
replace grade_order = real(regexs(1)) if regexm(grade, "^Grade ([0-9]+)$")
gen subject_order = .
replace subject_order = 1 if subject == "ELA"
replace subject_order = 2 if subject == "Math"
replace subject_order = 3 if subject == "Science"
sort grade_order subject_order

label variable grade              "Grade"
label variable subject            "Subject"
label variable jmtes_mean         "JMTES mean"
label variable jmtes_sd           "JMTES standard deviation"
label variable jes_mean           "JES mean"
label variable jes_sd             "JES standard deviation"
label variable difference_in_mean "Difference in means (JMTES - JES)"
label variable jmtes_median       "JMTES median"
label variable jes_median         "JES median"
label variable observations       "Observations (JMTES/JES)"

format jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean %9.2f
format jmtes_median jes_median %9.1f
format jmtes_n jes_n %9.0f
order grade subject jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean ///
    jmtes_median jes_median observations jmtes_n jes_n

notes: Recomputed from the school ATLAS Excel workbooks listed in this do-file.
notes: Restricted to non-missing subject-specific Sum 2026 scores for JMTES and JES.

save "`output_dta'", replace
export delimited grade subject jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean ///
    jmtes_median jes_median observations jmtes_n jes_n using "`output_csv'", replace

list grade subject jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean ///
    jmtes_median jes_median observations, abbreviate(20) noobs separator(0)
