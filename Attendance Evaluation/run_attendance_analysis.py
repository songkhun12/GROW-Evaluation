#!/usr/bin/env python3
"""Regenerate attendance evaluation outputs from the June 15, 2026 at-risk reports.

Implements the stated methodology: estimate a propensity score from grade, gender,
race/ethnicity, age, meal-status code, and entry code; construct overlap weights; and
estimate weighted linear models for unexcused, excused, and total absence percentages.
"""
from __future__ import annotations

from zipfile import ZipFile
import csv, math, os, statistics
import xml.etree.ElementTree as ET

BASE = os.path.dirname(__file__)
JES = os.path.join(BASE, "JES At Risk Report_Updated 6.15.26 (PW_ #JES2026).xlsx")
JMTES = os.path.join(BASE, "JMTES At Risk Report_Updated 6.15.26 (PW_ #MTE2026).xlsx")
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def colidx(ref):
    letters = ''.join(ch for ch in ref if ch.isalpha()); n = 0
    for ch in letters: n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def read_xlsx(path):
    with ZipFile(path) as z:
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('a:si', NS): ss.append(''.join(t.text or '' for t in si.findall('.//a:t', NS)))
        root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    rows = []
    for row in root.findall('.//a:sheetData/a:row', NS):
        vals = {}
        for cell in row.findall('a:c', NS):
            v = cell.find('a:v', NS); val = '' if v is None else v.text
            if cell.get('t') == 's' and val != '': val = ss[int(val)]
            vals[colidx(cell.get('r', 'A1'))] = val
        if vals: rows.append([vals.get(i, '') for i in range(max(vals) + 1)])
    title, header = rows[0][0], rows[1]
    return title, [dict(zip(header, row + [''] * (len(header) - len(row)))) for row in rows[2:]]


def clean(x): return str(x).strip()
def num(x):
    try:
        s = clean(x); return 0.0 if s == '' else float(s)
    except Exception: return 0.0


def load_school(path, school, jmtes):
    title, records = read_xlsx(path); out = []
    for raw in records:
        if not clean(raw.get('Student Id', '')): continue
        unexcused = num(raw.get('Unexcused', 0)); excused = num(raw.get('Excused', 0)); total = unexcused + excused
        d = {
            'school': school, 'source_file': os.path.basename(path), 'source_title': title, 'source_report_date': '2026-06-15',
            'jmtes': float(jmtes), 'student_id': clean(raw.get('Student Id', '')), 'grade': clean(raw.get('Student Grade', '')),
            'female': 1.0 if clean(raw.get('Gender', '')).lower() == 'female' else 0.0, 'gender': clean(raw.get('Gender', '')),
            'black': 1.0 if clean(raw.get('Ethnic Name', '')).lower() == 'black' else 0.0, 'race_ethnicity': clean(raw.get('Ethnic Name', '')),
            'age': num(raw.get('Student Age', 0)), 'meal_status': clean(raw.get('Meal Status Code', '')), 'entry_code': clean(raw.get('Entry Code - E/W', '')),
            'report_school_days': 170.0, 'full_school_year_days': 170.0,
            'unexcused_absences': unexcused, 'excused_absences': excused, 'total_absences': total,
            'unexcused_pct': unexcused / 170.0 * 100.0, 'excused_pct': excused / 170.0 * 100.0, 'total_pct': total / 170.0 * 100.0,
        }
        out.append(d)
    return out


def design(data, include_treatment=True):
    cat_terms = []
    for var in ['grade', 'meal_status', 'entry_code']:
        levels = sorted({d[var] for d in data}); cat_terms += [(var, l) for l in levels[1:]]
    names = ['Intercept', 'female', 'black', 'age']
    if include_treatment: names.insert(1, 'jmtes')
    names += [f'{v}:{l}' for v, l in cat_terms]
    X = []
    for d in data:
        row = [1.0, d['female'], d['black'], d['age']]
        if include_treatment: row.insert(1, d['jmtes'])
        row += [1.0 if d[v] == l else 0.0 for v, l in cat_terms]
        X.append(row)
    return names, X


def inv(A):
    n=len(A); M=[list(map(float,A[i]))+[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        piv=max(range(i,n), key=lambda r: abs(M[r][i])); M[i],M[piv]=M[piv],M[i]
        if abs(M[i][i]) < 1e-12: M[i][i] = 1e-12
        div=M[i][i]; M[i]=[v/div for v in M[i]]
        for r in range(n):
            if r == i: continue
            fac=M[r][i]
            if fac: M[r]=[M[r][c]-fac*M[i][c] for c in range(2*n)]
    return [row[n:] for row in M]


def logit_fit(data, yvar='jmtes'):
    names, X = design(data, include_treatment=False); p=len(names); beta=[0.0]*p
    y=[d[yvar] for d in data]
    for _ in range(100):
        A=[[0.0]*p for _ in range(p)]; s=[0.0]*p
        for xi, yi in zip(X,y):
            xb=sum(xi[j]*beta[j] for j in range(p)); pr=1/(1+math.exp(-max(min(xb,35),-35))); pr=min(max(pr,1e-8),1-1e-8)
            for j in range(p):
                s[j]+=xi[j]*(yi-pr)
                for k in range(p): A[j][k]+=pr*(1-pr)*xi[j]*xi[k]
        Ai=inv(A); delta=[sum(Ai[j][k]*s[k] for k in range(p)) for j in range(p)]; beta=[beta[j]+delta[j] for j in range(p)]
        if max(abs(v) for v in delta)<1e-8: break
    return names, beta


def wls(data, yvar, weights, adjusted):
    names, X = design(data, include_treatment=adjusted)
    if not adjusted:
        names=['Intercept','jmtes']; X=[[1.0,d['jmtes']] for d in data]
    y=[d[yvar] for d in data]; n=len(data); p=len(names)
    XtWX=[[sum(weights[i]*X[i][j]*X[i][k] for i in range(n)) for k in range(p)] for j in range(p)]
    XtWy=[sum(weights[i]*X[i][j]*y[i] for i in range(n)) for j in range(p)]
    bread=inv(XtWX); beta=[sum(bread[j][k]*XtWy[k] for k in range(p)) for j in range(p)]
    resid=[y[i]-sum(X[i][j]*beta[j] for j in range(p)) for i in range(n)]
    # HC0 sandwich robust SEs for weighted linear model.
    meat=[[sum((weights[i]**2)*(resid[i]**2)*X[i][j]*X[i][k] for i in range(n)) for k in range(p)] for j in range(p)]
    tmp=[[sum(bread[j][l]*meat[l][k] for l in range(p)) for k in range(p)] for j in range(p)]
    vcov=[[sum(tmp[j][l]*bread[l][k] for l in range(p)) for k in range(p)] for j in range(p)]
    j=names.index('jmtes'); est=beta[j]; se=math.sqrt(max(vcov[j][j],0)); t=est/se if se else float('nan'); pval=math.erfc(abs(t)/math.sqrt(2))
    return est,se,t,pval,est-1.96*se,est+1.96*se


def fmtp(p): return '<0.001' if p < .001 else f'{p:.3f}'
def write_csv(path, rows):
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)



def significance_label(p):
    if p < 0.01:
        return '*** p < 0.01'
    if p < 0.05:
        return '** p < 0.05'
    return 'n.s.'


def svg_escape(x):
    return str(x).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def make_attendance_coefficient_plot(results, path):
    """Write a self-contained SVG coefficient plot for attendance outcomes."""
    outcomes = ['Unexcused absence percentage', 'Excused absence percentage', 'Total absence percentage']
    outcome_labels = {
        'Unexcused absence percentage': 'Unexcused absence %',
        'Excused absence percentage': 'Excused absence %',
        'Total absence percentage': 'Total absence %',
    }
    model_labels = {
        'Overlap weighted': 'OW',
        'Overlap weighted + covariates': 'OW + covariates',
    }
    colors = {'Overlap weighted': '#1b9e77', 'Overlap weighted + covariates': '#d95f02'}
    # Axis chosen to include all CIs with clean percentage-point ticks.
    xmin, xmax = -4.5, 1.5
    ticks = [-4, -3, -2, -1, 0, 1]
    width, height = 1900, 920
    left, right, top, bottom = 320, 80, 140, 230
    plot_w, plot_h = width - left - right, height - top - bottom
    row_gap = plot_h / (len(outcomes) - 1)
    offsets = {'Overlap weighted': -22, 'Overlap weighted + covariates': 22}

    def xmap(v):
        return left + (float(v) - xmin) / (xmax - xmin) * plot_w

    def ybase(outcome):
        return top + outcomes.index(outcome) * row_gap

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222}.title{font-size:42px;font-weight:700}.axis{font-size:28px}.tick{font-size:24px;fill:#444}.legend{font-size:25px}.note{font-size:20px;fill:#555}</style>',
        '<text class="title" x="320" y="62">GROW-Associated Differences in Attendance Outcomes</text>',
    ]

    # Grid and labels.
    for t in ticks:
        x = xmap(t)
        parts.append(f'<line x1="{x:.1f}" y1="{top-50}" x2="{x:.1f}" y2="{top+plot_h+50}" stroke="#e5e5e5" stroke-width="3"/>')
        parts.append(f'<text class="tick" x="{x:.1f}" y="{top+plot_h+90}" text-anchor="middle">{t}</text>')
    parts.append(f'<line x1="{xmap(0):.1f}" y1="{top-50}" x2="{xmap(0):.1f}" y2="{top+plot_h+50}" stroke="#777" stroke-width="3" stroke-dasharray="10 10"/>')
    for outcome in outcomes:
        y = ybase(outcome)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#e8e8e8" stroke-width="3"/>')
        parts.append(f'<text class="axis" x="{left-25}" y="{y+10:.1f}" text-anchor="end">{outcome_labels[outcome]}</text>')

    # Coefficients.
    for r in results:
        outcome = r['outcome']; model = r['model']; color = colors[model]
        y = ybase(outcome) + offsets[model]
        x, lo, hi = xmap(r['estimate']), xmap(r['conf_low']), xmap(r['conf_high'])
        sig = significance_label(float(r['p_value']))
        fill = color if sig != 'n.s.' else 'white'
        parts.append(f'<line x1="{lo:.1f}" y1="{y:.1f}" x2="{hi:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="5"/>')
        parts.append(f'<line x1="{lo:.1f}" y1="{y-9:.1f}" x2="{lo:.1f}" y2="{y+9:.1f}" stroke="{color}" stroke-width="5"/>')
        parts.append(f'<line x1="{hi:.1f}" y1="{y-9:.1f}" x2="{hi:.1f}" y2="{y+9:.1f}" stroke="{color}" stroke-width="5"/>')
        if sig == '** p < 0.05':
            pts = f'{x:.1f},{y-14:.1f} {x-13:.1f},{y+11:.1f} {x+13:.1f},{y+11:.1f}'
            parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{color}" stroke-width="3"/>')
        else:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="{fill}" stroke="{color}" stroke-width="3"/>')

    parts.append(f'<text class="axis" x="{left+plot_w/2:.1f}" y="{height-95}" text-anchor="middle">JMTES absence percentage points - JES absence percentage points</text>')

    # Legend modeled after supplied plot: significance then attendance model.
    ly = height - 42
    x0 = 285
    parts.append(f'<text class="legend" x="{x0}" y="{ly}">Statistical significance</text>')
    x = x0 + 335
    parts.append(f'<circle cx="{x}" cy="{ly-8}" r="11" fill="black"/><text class="legend" x="{x+35}" y="{ly}">*** p &lt; 0.01</text>')
    x += 205
    parts.append(f'<polygon points="{x},{ly-22} {x-13},{ly+3} {x+13},{ly+3}" fill="black"/><text class="legend" x="{x+35}" y="{ly}">** p &lt; 0.05</text>')
    x += 190
    parts.append(f'<circle cx="{x}" cy="{ly-8}" r="11" fill="white" stroke="black" stroke-width="3"/><text class="legend" x="{x+35}" y="{ly}">n.s.</text>')
    x += 160
    parts.append(f'<text class="legend" x="{x}" y="{ly}">Attendance model</text>')
    x += 245
    for model in ['Overlap weighted', 'Overlap weighted + covariates']:
        color = colors[model]
        parts.append(f'<line x1="{x}" y1="{ly-8}" x2="{x+48}" y2="{ly-8}" stroke="{color}" stroke-width="5"/>')
        parts.append(f'<circle cx="{x+24}" cy="{ly-8}" r="11" fill="{color}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text class="legend" x="{x+62}" y="{ly}">{svg_escape(model_labels[model])}</text>')
        x += 225

    parts.append('</svg>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))


def main():
    jmtes=load_school(JMTES,'JMTES',1); jes=load_school(JES,'JES',0); data=jmtes+jes
    audit=[{'school':'JMTES','source_file':os.path.basename(JMTES),'source_report_date':'2026-06-15','students_loaded':len(jmtes),'workbook_title':jmtes[0]['source_title']}, {'school':'JES','source_file':os.path.basename(JES),'source_report_date':'2026-06-15','students_loaded':len(jes),'workbook_title':jes[0]['source_title']}]
    names,b=logit_fit(data); _,Xps=design(data, include_treatment=False)
    for i,d in enumerate(data):
        xb=sum(Xps[i][j]*b[j] for j in range(len(b))); ps=1/(1+math.exp(-max(min(xb,35),-35)))
        d['propensity']=ps; d['overlap_weight']=1-ps if d['jmtes']==1.0 else ps
    weights=[d['overlap_weight'] for d in data]
    outcomes=[('unexcused_pct','Unexcused absence percentage'),('excused_pct','Excused absence percentage'),('total_pct','Total absence percentage')]
    results=[]
    for y,label in outcomes:
        for model,adj in [('Overlap weighted',False),('Overlap weighted + covariates',True)]:
            est,se,t,p,lo,hi=wls(data,y,weights,adj)
            results.append({'outcome':label,'model':model,'estimate':est,'std_error':se,'t_value':t,'p_value':p,'conf_low':lo,'conf_high':hi,'p_value_formatted':fmtp(p),'estimate_label':f'{est:.3f} (SE = {se:.3f}), 95% CI [{lo:.3f}, {hi:.3f}], p = {fmtp(p)}'})
    desc=[]
    for y,label in outcomes:
        for school in ['JMTES','JES']:
            vals=[d[y] for d in data if d['school']==school]
            desc.append({'outcome':label,'school':school,'n':len(vals),'mean':statistics.mean(vals),'sd':statistics.stdev(vals),'median':statistics.median(vals),'min':min(vals),'max':max(vals)})
    write_csv(os.path.join(BASE,'jmtes_jes_attendance_data_source_audit.csv'),audit)
    write_csv(os.path.join(BASE,'jmtes_jes_overlap_weighted_attendance_results.csv'),[{k:v for k,v in r.items() if k!='estimate_label'} for r in results])
    write_csv(os.path.join(BASE,'jmtes_jes_overlap_weighted_attendance_regression_table.csv'),results)
    make_attendance_coefficient_plot(results, os.path.join(BASE, 'jmtes_jes_overlap_weighted_attendance_coefficient_plot.svg'))
    write_csv(os.path.join(BASE,'jmtes_jes_attendance_descriptive_statistics.csv'),desc)
    write_csv(os.path.join(BASE,'jmtes_jes_overlap_weighted_attendance_student_data.csv'),data)

    weighted_means = []
    for y, label in outcomes:
        for school, group in [('JES', 0.0), ('JMTES', 1.0)]:
            rows = [d for d in data if d['jmtes'] == group]
            sw = sum(d['overlap_weight'] for d in rows)
            weighted_means.append({'outcome': label, 'school': school, 'weighted_mean': sum(d['overlap_weight'] * d[y] for d in rows) / sw, 'sum_overlap_weight': sw, 'n': len(rows)})
    write_csv(os.path.join(BASE, 'jmtes_jes_overlap_weighted_attendance_weighted_means.csv'), weighted_means)

    def wm(vals, ws): return sum(v * w for v, w in zip(vals, ws)) / sum(ws)
    def wvar(vals, ws):
        m = wm(vals, ws)
        return sum(w * (v - m) ** 2 for v, w in zip(vals, ws)) / sum(ws)
    def smd_numeric(var, weighted=False):
        d1 = [d for d in data if d['jmtes'] == 1.0]; d0 = [d for d in data if d['jmtes'] == 0.0]
        w1 = [d['overlap_weight'] if weighted else 1.0 for d in d1]; w0 = [d['overlap_weight'] if weighted else 1.0 for d in d0]
        x1 = [float(d[var]) for d in d1]; x0 = [float(d[var]) for d in d0]
        den = math.sqrt((wvar(x1, w1) + wvar(x0, w0)) / 2)
        return (wm(x1, w1) - wm(x0, w0)) / den if den else ''
    def smd_indicator(var, level, weighted=False):
        d1 = [d for d in data if d['jmtes'] == 1.0]; d0 = [d for d in data if d['jmtes'] == 0.0]
        w1 = [d['overlap_weight'] if weighted else 1.0 for d in d1]; w0 = [d['overlap_weight'] if weighted else 1.0 for d in d0]
        x1 = [1.0 if d[var] == level else 0.0 for d in d1]; x0 = [1.0 if d[var] == level else 0.0 for d in d0]
        p = (wm(x1, w1) + wm(x0, w0)) / 2
        den = math.sqrt(p * (1 - p)) if p * (1 - p) > 0 else 0
        return (wm(x1, w1) - wm(x0, w0)) / den if den else ''
    balance = []
    for var in ['age', 'female', 'black']:
        balance.append({'variable': var, 'unweighted_smd': smd_numeric(var), 'weighted_smd': smd_numeric(var, True)})
    for var in ['grade', 'meal_status', 'entry_code']:
        for level in sorted({d[var] for d in data}):
            balance.append({'variable': f'{var}: {level}', 'unweighted_smd': smd_indicator(var, level), 'weighted_smd': smd_indicator(var, level, True)})
    for row in balance:
        row['abs_unweighted_smd'] = abs(row['unweighted_smd']) if row['unweighted_smd'] != '' else ''
        row['abs_weighted_smd'] = abs(row['weighted_smd']) if row['weighted_smd'] != '' else ''
    balance.sort(key=lambda row: row['abs_unweighted_smd'] if row['abs_unweighted_smd'] != '' else -1, reverse=True)
    write_csv(os.path.join(BASE, 'jmtes_jes_overlap_weighted_attendance_balance.csv'), balance)

    checks = [
        {'check': 'source_files', 'value': f'{os.path.basename(JMTES)}; {os.path.basename(JES)}'},
        {'check': 'observations', 'value': len(data)},
        {'check': 'jmtes_students', 'value': len(jmtes)},
        {'check': 'jes_students', 'value': len(jes)},
    ]
    write_csv(os.path.join(BASE, 'jmtes_jes_overlap_weighted_attendance_model_comparison_check.csv'), checks)
    print(f'Loaded {len(jmtes)} JMTES and {len(jes)} JES students; wrote overlap-weighted attendance outputs.')

if __name__ == '__main__': main()
