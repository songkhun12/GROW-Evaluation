# GROW Financial Literacy Pre-Post Analysis Report

## Introduction

This report analyzes financial literacy pre- and post-test outcomes for 57 GROW students in grades 3-5. The analysis estimates whether students improved from pre-test to post-test, whether gains differed by grade, and which adjusted model is most appropriate for reporting.

The recommended strategy is to use unadjusted paired pre-post results as the main finding, a combined-grade repeated-measures model to test whether gains differed by grade, and a limited adjusted ANCOVA model as a supplemental analysis.

## Data and measurement

The analysis uses `all_grades_financial_literacy_scores.csv` in the Financial Literacy Analysis folder. The file includes 57 students: 21 in Grade 3, 15 in Grade 4, and 21 in Grade 5. Each assessment includes 10 scored items, so total correct scores were converted to percent-correct scores by dividing by 10 and multiplying by 100.

Key variables are:

- **Pre-test percent correct:** `pre_total_correct / 10 * 100`.
- **Post-test percent correct:** `post_total_correct / 10 * 100`.
- **Gain:** post-test percent correct minus pre-test percent correct.
- **Grade:** Grade 3, Grade 4, or Grade 5.
- **Attendance:** total absence percentage while enrolled, measured as `at_risk_total_absence_pct_enrolled`.
- **Demographics:** gender and race/ethnicity are available, but are best treated as optional sensitivity controls because the sample is small.

The sample included 31 male students and 26 female students. Race/ethnicity was coded as 42 Black students and 15 NonBlack students. The mean total absence percentage was 6.8%, ranging from 0.6% to 18.8%.

## Methodology

### Main paired pre-post analysis

The primary analysis uses paired t-tests comparing each student's post-test percent-correct score with that same student's pre-test percent-correct score. This was conducted overall and separately by grade. This approach is appropriate because each student contributes both a pre-test and post-test score.

### Combined-grade repeated-measures model

The main combined-grade model is:

\[
\text{Score \%}_{it} = \beta_0 + \beta_1\text{Post}_{it} + \beta_2\text{Grade}_{i} + \beta_3(\text{Post}_{it} \times \text{Grade}_{i}) + u_i + e_{it}
\]

This model uses a student random intercept to account for repeated observations. The post-by-grade interaction tests whether score gains differed by grade.

### Supplemental adjusted model

The recommended adjusted model is an ANCOVA model:

\[
\text{Post Score \%}_{i} = \beta_0 + \beta_1\text{Pre Score \%}_{i} + \beta_2\text{Grade}_{i} + \beta_3\text{Attendance}_{i} + e_i
\]

This model is preferred as the adjusted analysis because it is easy to explain and well suited to a two-wave pre-post design. It adjusts for baseline financial literacy, grade level, and attendance while avoiding overfitting.

A fuller demographic model adding gender and race/ethnicity can be included as a sensitivity check, but it should not be the main adjusted model unless demographic adjustment is specifically required.

## Results

| Group | N | Pre mean % | Post mean % | Mean gain, percentage points | Gain SD | Paired t |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 57 | 60.5 | 64.0 | 3.5 | 18.1 | 1.47 |
| Grade 3 | 21 | 48.1 | 48.6 | 0.5 | 21.8 | 0.10 |
| Grade 4 | 15 | 49.3 | 56.0 | 6.7 | 19.9 | 1.30 |
| Grade 5 | 21 | 81.0 | 85.2 | 4.3 | 12.1 | 1.63 |

Overall, students increased from 60.5% correct at pre-test to 64.0% correct at post-test, a gain of 3.5 percentage points. Grade 4 had the largest descriptive gain, followed by Grade 5. Grade 3 showed almost no average change.

The repeated-measures mixed model should be interpreted as the formal combined-grade test of whether gains differed by grade. The post-by-grade interaction is the key term for that question. If the interaction terms are not statistically significant when the RMarkdown file is rendered, the appropriate conclusion is that descriptive gains varied by grade, but the data do not provide strong evidence that gains differed statistically across grades.

The adjusted ANCOVA model should be interpreted as a supplemental check. Because the sample size is modest and there is no comparison group, adjusted findings should not be presented as definitive causal evidence. Instead, they show whether the descriptive post-test pattern remains similar after accounting for pre-test score, grade, and attendance.

## Discussion and conclusion: Which model would I recommend?

I recommend the following reporting sequence:

1. **Main finding:** paired t-tests overall and by grade.
2. **Main combined-grade model:** repeated-measures mixed model with post, grade, and post-by-grade interaction, plus student random intercept.
3. **Preferred adjusted supplemental model:** ANCOVA predicting post-test percent correct from pre-test percent correct, grade, and attendance.

The most defensible adjusted model is:

\[
\text{Post Score \%} = \beta_0 + \beta_1(\text{Pre Score \%}) + \beta_2(\text{Grade}) + \beta_3(\text{Attendance}) + e_i
\]

This model is recommended because it controls for the most important baseline difference, pre-test financial literacy, while also accounting for grade and attendance. It avoids adding too many predictors for a 57-student sample.

The conclusion should be cautious but positive: participating students showed a modest average improvement in financial literacy scores from pre-test to post-test, with larger descriptive gains in Grades 4 and 5 than Grade 3. Because this is a one-group pre-post design without a non-participant comparison group, results should be framed as improvement over time among GROW participants rather than definitive causal proof of program impact.
