/****************************************************************************************
  Table 3. Descriptive Statistics for Attendance Outcomes

  Assumption:
    The combined 6.15.26 at-risk attendance file is already open in Stata. The open
    dataset must contain:
      school unexcused_absence_pct excused_absence_pct total_absence_pct

  Example command to open the prepared combined file before running this do-file:
    import delimited using "Attendance Evaluation/jmtes_jes_at_risk_report_6_15_26_combined.csv", clear varnames(1)

  Run after opening the data:
    do "Attendance Evaluation/jmtes_jes_attendance_descriptive_statistics.do"
****************************************************************************************/

version 17.0
set more off

foreach var in school unexcused_absence_pct excused_absence_pct total_absence_pct {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in the open dataset."
        exit 111
    }
}

label variable unexcused_absence_pct "Unexcused absence %"
label variable excused_absence_pct   "Excused absence %"
label variable total_absence_pct     "Total absence %"

* Descriptive statistics by school for each attendance outcome.
tabstat unexcused_absence_pct excused_absence_pct total_absence_pct, ///
    by(school) statistics(mean sd median n) columns(statistics) format(%9.3f)

* Compact Table 3 check with school-specific means/SDs/medians and JMTES - JES differences.
preserve
    collapse ///
        (mean) mean_unexcused = unexcused_absence_pct ///
               mean_excused   = excused_absence_pct ///
               mean_total     = total_absence_pct ///
        (sd)   sd_unexcused   = unexcused_absence_pct ///
               sd_excused     = excused_absence_pct ///
               sd_total       = total_absence_pct ///
        (p50)  med_unexcused  = unexcused_absence_pct ///
               med_excused    = excused_absence_pct ///
               med_total      = total_absence_pct ///
        (count) n             = unexcused_absence_pct, ///
        by(school)

    gen one = 1
    reshape wide mean_unexcused mean_excused mean_total ///
        sd_unexcused sd_excused sd_total ///
        med_unexcused med_excused med_total n, i(one) j(school) string

    foreach stat in mean sd med {
        foreach outcome in unexcused excused total {
            foreach school in JMTES JES {
                local `stat'_`outcome'`school' = `stat'_`outcome'`school'[1]
            }
        }
    }
    local nJMTES = nJMTES[1]
    local nJES = nJES[1]

    clear
    set obs 4
    gen str22 outcome = ""
    replace outcome = "Unexcused absence %" in 1
    replace outcome = "Excused absence %" in 2
    replace outcome = "Total absence %" in 3
    replace outcome = "Observations" in 4

    gen jmtes_mean = .
    gen jmtes_sd = .
    gen jes_mean = .
    gen jes_sd = .
    gen difference_in_mean = .
    gen jmtes_median = .
    gen jes_median = .

    replace jmtes_mean = `mean_unexcusedJMTES' in 1
    replace jmtes_sd = `sd_unexcusedJMTES' in 1
    replace jes_mean = `mean_unexcusedJES' in 1
    replace jes_sd = `sd_unexcusedJES' in 1
    replace difference_in_mean = `mean_unexcusedJMTES' - `mean_unexcusedJES' in 1
    replace jmtes_median = `med_unexcusedJMTES' in 1
    replace jes_median = `med_unexcusedJES' in 1

    replace jmtes_mean = `mean_excusedJMTES' in 2
    replace jmtes_sd = `sd_excusedJMTES' in 2
    replace jes_mean = `mean_excusedJES' in 2
    replace jes_sd = `sd_excusedJES' in 2
    replace difference_in_mean = `mean_excusedJMTES' - `mean_excusedJES' in 2
    replace jmtes_median = `med_excusedJMTES' in 2
    replace jes_median = `med_excusedJES' in 2

    replace jmtes_mean = `mean_totalJMTES' in 3
    replace jmtes_sd = `sd_totalJMTES' in 3
    replace jes_mean = `mean_totalJES' in 3
    replace jes_sd = `sd_totalJES' in 3
    replace difference_in_mean = `mean_totalJMTES' - `mean_totalJES' in 3
    replace jmtes_median = `med_totalJMTES' in 3
    replace jes_median = `med_totalJES' in 3

    replace jmtes_mean = `nJMTES' in 4
    replace jes_mean = `nJES' in 4

    format jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean jmtes_median jes_median %9.3f
    list outcome jmtes_mean jmtes_sd jes_mean jes_sd difference_in_mean ///
        jmtes_median jes_median, noobs abbreviate(24) separator(0)
restore
