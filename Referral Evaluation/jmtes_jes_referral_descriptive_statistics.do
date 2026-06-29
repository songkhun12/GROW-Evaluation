/****************************************************************************************
  Tables 5 and 6. Descriptive Statistics for Attendance and Referral Outcomes

  Assumption:
    The combined 6.15.26 at-risk referral file is already open in Stata. The open dataset
    must contain school plus the attendance, school-referral, and bus-referral variables
    listed below.

  Example command to open the prepared combined file before running this do-file:
    import delimited using "Referral Evaluation/jmtes_jes_at_risk_report_6_15_26_combined.csv", clear varnames(1)

  Run after opening the data:
    do "Referral Evaluation/jmtes_jes_referral_descriptive_statistics.do"
****************************************************************************************/

version 17.0
set more off

local attendance_vars unexcused_absence_pct excused_absence_pct total_absence_pct
local school_referral_vars total_school_referrals school_l1_referrals school_l2_referrals school_l3_referrals school_l4_referrals
local bus_referral_vars total_bus_referrals bus_l1_referrals bus_l2_referrals bus_l3_referrals

foreach var in school `attendance_vars' `school_referral_vars' `bus_referral_vars' {
    capture confirm variable `var'
    if _rc {
        di as error "Required variable `var' is not in the open dataset."
        exit 111
    }
}

label variable unexcused_absence_pct "Unexcused absence %"
label variable excused_absence_pct   "Excused absence %"
label variable total_absence_pct     "Total absence %"
label variable total_school_referrals "Total school referrals"
label variable school_l1_referrals    "School Level I referrals"
label variable school_l2_referrals    "School Level II referrals"
label variable school_l3_referrals    "School Level III referrals"
label variable school_l4_referrals    "School Level IV referrals"
label variable total_bus_referrals    "Total bus referrals"
label variable bus_l1_referrals       "Bus Level I referrals"
label variable bus_l2_referrals       "Bus Level II referrals"
label variable bus_l3_referrals       "Bus Level III referrals"

* Table 5 attendance outcomes.
di as text _newline "Table 5: Descriptive Statistics for Attendance Outcomes"
tabstat `attendance_vars', by(school) statistics(mean sd median n) columns(statistics) format(%9.3f)

* Table 5 school-based referral outcomes.
di as text _newline "Table 5: Descriptive Statistics for School-Based Referral Outcomes"
tabstat `school_referral_vars', by(school) statistics(mean sd median n) columns(statistics) format(%9.3f)

* Table 6 bus referral outcomes.
di as text _newline "Table 6: Descriptive Statistics for Bus Referral Outcomes"
tabstat `bus_referral_vars', by(school) statistics(mean sd median n) columns(statistics) format(%9.3f)

* Compact difference-in-means checks for the reported tables.
preserve
    collapse ///
        (mean) m_unex=unexcused_absence_pct m_ex=excused_absence_pct m_totabs=total_absence_pct ///
               m_schtot=total_school_referrals m_schl1=school_l1_referrals m_schl2=school_l2_referrals m_schl3=school_l3_referrals m_schl4=school_l4_referrals ///
               m_bustot=total_bus_referrals m_busl1=bus_l1_referrals m_busl2=bus_l2_referrals m_busl3=bus_l3_referrals ///
        (sd)   sd_unex=unexcused_absence_pct sd_ex=excused_absence_pct sd_totabs=total_absence_pct ///
               sd_schtot=total_school_referrals sd_schl1=school_l1_referrals sd_schl2=school_l2_referrals sd_schl3=school_l3_referrals sd_schl4=school_l4_referrals ///
               sd_bustot=total_bus_referrals sd_busl1=bus_l1_referrals sd_busl2=bus_l2_referrals sd_busl3=bus_l3_referrals ///
        (p50)  p_unex=unexcused_absence_pct p_ex=excused_absence_pct p_totabs=total_absence_pct ///
               p_schtot=total_school_referrals p_schl1=school_l1_referrals p_schl2=school_l2_referrals p_schl3=school_l3_referrals p_schl4=school_l4_referrals ///
               p_bustot=total_bus_referrals p_busl1=bus_l1_referrals p_busl2=bus_l2_referrals p_busl3=bus_l3_referrals ///
        (count) n=unexcused_absence_pct, by(school)

    gen one = 1
    reshape wide m_* sd_* p_* n, i(one) j(school) string

    di as text _newline "Compact checks: JMTES mean (SD), JES mean (SD), difference, JMTES median, JES median"
    di as text "Unexcused absence %: " %9.3f m_unexJMTES[1] " (" %9.3f sd_unexJMTES[1] ") | " %9.3f m_unexJES[1] " (" %9.3f sd_unexJES[1] ") | " %9.3f (m_unexJMTES[1]-m_unexJES[1]) " | " %9.3f p_unexJMTES[1] " | " %9.3f p_unexJES[1]
    di as text "Excused absence %:   " %9.3f m_exJMTES[1] " (" %9.3f sd_exJMTES[1] ") | " %9.3f m_exJES[1] " (" %9.3f sd_exJES[1] ") | " %9.3f (m_exJMTES[1]-m_exJES[1]) " | " %9.3f p_exJMTES[1] " | " %9.3f p_exJES[1]
    di as text "Total absence %:     " %9.3f m_totabsJMTES[1] " (" %9.3f sd_totabsJMTES[1] ") | " %9.3f m_totabsJES[1] " (" %9.3f sd_totabsJES[1] ") | " %9.3f (m_totabsJMTES[1]-m_totabsJES[1]) " | " %9.3f p_totabsJMTES[1] " | " %9.3f p_totabsJES[1]
    di as text "Total school referrals: " %9.3f m_schtotJMTES[1] " (" %9.3f sd_schtotJMTES[1] ") | " %9.3f m_schtotJES[1] " (" %9.3f sd_schtotJES[1] ") | " %9.3f (m_schtotJMTES[1]-m_schtotJES[1]) " | " %9.3f p_schtotJMTES[1] " | " %9.3f p_schtotJES[1]
    di as text "School Level I referrals: " %9.3f m_schl1JMTES[1] " (" %9.3f sd_schl1JMTES[1] ") | " %9.3f m_schl1JES[1] " (" %9.3f sd_schl1JES[1] ") | " %9.3f (m_schl1JMTES[1]-m_schl1JES[1]) " | " %9.3f p_schl1JMTES[1] " | " %9.3f p_schl1JES[1]
    di as text "School Level II referrals: " %9.3f m_schl2JMTES[1] " (" %9.3f sd_schl2JMTES[1] ") | " %9.3f m_schl2JES[1] " (" %9.3f sd_schl2JES[1] ") | " %9.3f (m_schl2JMTES[1]-m_schl2JES[1]) " | " %9.3f p_schl2JMTES[1] " | " %9.3f p_schl2JES[1]
    di as text "School Level III referrals: " %9.3f m_schl3JMTES[1] " (" %9.3f sd_schl3JMTES[1] ") | " %9.3f m_schl3JES[1] " (" %9.3f sd_schl3JES[1] ") | " %9.3f (m_schl3JMTES[1]-m_schl3JES[1]) " | " %9.3f p_schl3JMTES[1] " | " %9.3f p_schl3JES[1]
    di as text "School Level IV referrals: " %9.3f m_schl4JMTES[1] " (" %9.3f sd_schl4JMTES[1] ") | " %9.3f m_schl4JES[1] " (" %9.3f sd_schl4JES[1] ") | " %9.3f (m_schl4JMTES[1]-m_schl4JES[1]) " | " %9.3f p_schl4JMTES[1] " | " %9.3f p_schl4JES[1]
    di as text "Total bus referrals: " %9.3f m_bustotJMTES[1] " (" %9.3f sd_bustotJMTES[1] ") | " %9.3f m_bustotJES[1] " (" %9.3f sd_bustotJES[1] ") | " %9.3f (m_bustotJMTES[1]-m_bustotJES[1]) " | " %9.3f p_bustotJMTES[1] " | " %9.3f p_bustotJES[1]
    di as text "Bus Level I referrals: " %9.3f m_busl1JMTES[1] " (" %9.3f sd_busl1JMTES[1] ") | " %9.3f m_busl1JES[1] " (" %9.3f sd_busl1JES[1] ") | " %9.3f (m_busl1JMTES[1]-m_busl1JES[1]) " | " %9.3f p_busl1JMTES[1] " | " %9.3f p_busl1JES[1]
    di as text "Bus Level II referrals: " %9.3f m_busl2JMTES[1] " (" %9.3f sd_busl2JMTES[1] ") | " %9.3f m_busl2JES[1] " (" %9.3f sd_busl2JES[1] ") | " %9.3f (m_busl2JMTES[1]-m_busl2JES[1]) " | " %9.3f p_busl2JMTES[1] " | " %9.3f p_busl2JES[1]
    di as text "Bus Level III referrals: " %9.3f m_busl3JMTES[1] " (" %9.3f sd_busl3JMTES[1] ") | " %9.3f m_busl3JES[1] " (" %9.3f sd_busl3JES[1] ") | " %9.3f (m_busl3JMTES[1]-m_busl3JES[1]) " | " %9.3f p_busl3JMTES[1] " | " %9.3f p_busl3JES[1]
    di as text "Observations: JMTES=" %9.0f nJMTES[1] " JES=" %9.0f nJES[1]
restore
