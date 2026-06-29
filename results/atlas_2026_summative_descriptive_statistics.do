/****************************************************************************************
  2026 Summative ATLAS descriptive statistics table

  Purpose:
    Recreate the descriptive-statistics table from the results CSV in Stata and save a
    Stata dataset that can be used for reporting or additional checks.

  Input:
    results/atlas_2026_summative_descriptive_statistics_unformatted.csv

  Outputs:
    results/atlas_2026_summative_descriptive_statistics.dta
    results/atlas_2026_summative_descriptive_statistics_stata.csv

  Run from the repository root:
    do "results/atlas_2026_summative_descriptive_statistics.do"
****************************************************************************************/

version 17.0
clear all
set more off

local input_csv  "results/atlas_2026_summative_descriptive_statistics_unformatted.csv"
local output_dta "results/atlas_2026_summative_descriptive_statistics.dta"
local output_csv "results/atlas_2026_summative_descriptive_statistics_stata.csv"

capture confirm file "`input_csv'"
if _rc {
    di as error "Input file not found: `input_csv'"
    di as error "Run this do-file from the repository root."
    exit 601
}

import delimited using "`input_csv'", clear varnames(1)

order grade subject jmtes_mean jmtes_sd jmtes_median jmtes_n jes_mean jes_sd jes_median jes_n difference_in_mean

label variable grade              "Grade"
label variable subject            "Subject"
label variable jmtes_mean         "JMTES mean"
label variable jmtes_sd           "JMTES standard deviation"
label variable jmtes_median       "JMTES median"
label variable jmtes_n            "JMTES observations"
label variable jes_mean           "JES mean"
label variable jes_sd             "JES standard deviation"
label variable jes_median         "JES median"
label variable jes_n              "JES observations"
label variable difference_in_mean "Difference in mean (JMTES - JES)"

format jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean %9.2f
format jmtes_median jes_median %9.1f
format jmtes_n jes_n %9.0f

notes: Descriptive statistics are based on non-missing student-level 2026 summative ATLAS scores.
notes: Input CSV was created by results/atlas_2026_summative_descriptive_statistics.Rmd.

save "`output_dta'", replace
export delimited using "`output_csv'", replace

list grade subject jmtes_mean jmtes_sd jmtes_median jmtes_n jes_mean jes_sd jes_median jes_n difference_in_mean, ///
    abbreviate(20) noobs separator(0)
