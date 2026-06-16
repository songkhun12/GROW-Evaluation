#!/usr/bin/env python3
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import csv, math, statistics, os

BASE=os.path.dirname(__file__)
JES=os.path.join(BASE,'JES At Risk Report_Updated 6.15.26 (PW_ #JES2026).xlsx')
JMTES=os.path.join(BASE,'JMTES At Risk Report_Updated 6.15.26 (PW_ #MTE2026).xlsx')
NS={'a':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def colidx(ref):
    letters=''.join(ch for ch in ref if ch.isalpha()); n=0
    for ch in letters: n=n*26+ord(ch.upper())-64
    return n-1

def read_xlsx(path):
    z=ZipFile(path); ss=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        root=ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall('a:si',NS): ss.append(''.join(t.text or '' for t in si.findall('.//a:t',NS)))
    root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    rows=[]
    for row in root.findall('.//a:sheetData/a:row',NS):
        vals={}
        for c in row.findall('a:c',NS):
            v=c.find('a:v',NS); val='' if v is None else v.text
            if c.get('t')=='s' and val!='': val=ss[int(val)]
            vals[colidx(c.get('r','A1'))]=val
        if vals:
            mx=max(vals); rows.append([vals.get(i,'') for i in range(mx+1)])
    title=rows[0][0]; header=rows[1]
    return title,[dict(zip(header,r+['']*(len(header)-len(r)))) for r in rows[2:]]

def num(x):
    s=str(x).strip()
    try: return float(s) if s!='' else 0.0
    except: return 0.0

def clean(x): return str(x).strip()

def load(path, school, jmtes):
    title, rows=read_xlsx(path); out=[]
    for r in rows:
        if not clean(r.get('Student Id','')): continue
        l1,l2,l3,l4=[num(r.get(c,0)) for c in ['L-1','L-2','L-3','L-4']]
        local,b1,b2,b3=[num(r.get(c,0)) for c in ['Local','Transportation 1','Transportation 2','Transportation 3']]
        d={'school':school,'jmtes':jmtes,'student_id':clean(r.get('Student Id','')),
           'grade':clean(r.get('Student Grade','')),'female':1 if clean(r.get('Gender','')).lower()=='female' else 0,
           'black':1 if clean(r.get('Ethnic Name','')).lower()=='black' else 0,'age':num(r.get('Student Age',0)),
           'meal_status':clean(r.get('Meal Status Code','')),'entry_code':clean(r.get('Entry Code - E/W','')),
           'enrollment_days':170.0,'classroom_l1':l1,'classroom_l2':l2,'classroom_l3':l3,'classroom_l4':l4,
           'bus_l1':local+b1,'bus_l2':b2,'bus_l3':b3}
        d['classroom_total']=l1+l2+l3+l4; d['classroom_severity_points']=l1+2*l2+3*l3+4*l4
        d['bus_total']=local+b1+b2+b3; d['bus_severity_points']=local+b1+2*b2+3*b3
        d['any_school_referral']=1 if d['classroom_total']>0 else 0; d['any_bus_referral']=1 if d['bus_total']>0 else 0
        d['any_referral']=1 if d['classroom_total']>0 or d['bus_total']>0 else 0
        out.append(d)
    return title,out



def write_outputs():
    import csv, math, statistics
    title_j, jes = load(JES, 'JES', 0)
    title_m, jmtes = load(JMTES, 'JMTES', 1)
    data = jmtes + jes

    labels = [
        ('classroom_total', 'Total school referrals'), ('classroom_l1', 'School Level I referrals'),
        ('classroom_l2', 'School Level II referrals'), ('classroom_l3', 'School Level III referrals'),
        ('classroom_l4', 'School Level IV referrals'), ('bus_total', 'Total bus referrals'),
        ('bus_l1', 'Bus Level I referrals'), ('bus_l2', 'Bus Level II referrals'), ('bus_l3', 'Bus Level III referrals')]
    desc=[]
    for y,label in labels:
        for school in ['JMTES','JES']:
            vals=[d[y] for d in data if d['school']==school]
            desc.append({'outcome':label,'school':school,'n':len(vals),'mean':statistics.mean(vals),
                         'sd':statistics.stdev(vals),'median':statistics.median(vals),'min':min(vals),'max':max(vals)})
    with open(os.path.join(BASE,'jmtes_jes_referral_descriptive_statistics.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,desc[0].keys()); w.writeheader(); w.writerows(desc)

    def star(p): return '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else ''
    outcomes=[('classroom_total','Classroom referrals'),('classroom_severity_points','Classroom severity-weighted frequency'),
              ('bus_total','Bus referrals'),('bus_severity_points','Bus severity-weighted frequency'),
              ('classroom_l1','Classroom L-I'),('classroom_l2','Classroom L-II'),('classroom_l3','Classroom L-III'),
              ('classroom_l4','Classroom L-IV'),('bus_l1','Bus L-I'),('bus_l2','Bus L-II'),('bus_l3','Bus L-III')]
    rows=[]
    for y,label in outcomes:
        e1=sum(d[y] for d in jmtes); e0=sum(d[y] for d in jes); r1=e1/len(jmtes); r0=e0/len(jes)
        if e1>0 and e0>0:
            coef=math.log(r1/r0); se=math.sqrt(1/e1+1/e0); p=math.erfc(abs(coef/se)/math.sqrt(2)); irr=math.exp(coef)
        else:
            coef=se=p=irr=float('nan')
        rows.append({'outcome':y,'label':label,'coefficient':coef,'robust_se':se,'p_value':p,
                     'stars':'' if math.isnan(p) else star(p),'irr':irr,
                     'percent_difference':100*(irr-1) if not math.isnan(irr) else float('nan'),
                     'jes_weighted_rate_per_170_days':r0,'jmtes_weighted_rate_per_170_days':r1,
                     'observations':len(data),'events':e1+e0})
    with open(os.path.join(BASE,'jmtes_jes_referral_poisson_results.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys()); w.writeheader(); w.writerows(rows)

    logrows=[]
    for y,label in [('any_school_referral','Any school referral'),('any_bus_referral','Any bus referral'),('any_referral','Any school or bus referral')]:
        a=sum(d[y] for d in jmtes); b=len(jmtes)-a; c=sum(d[y] for d in jes); dd=len(jes)-c
        coef=math.log((a/b)/(c/dd)); se=math.sqrt(1/a+1/b+1/c+1/dd); p=math.erfc(abs(coef/se)/math.sqrt(2)); orr=math.exp(coef)
        logrows.append({'outcome':y,'label':label,'coefficient':coef,'robust_se':se,'p_value':p,'stars':star(p),
                        'odds_ratio':orr,'jes_weighted_probability':c/len(jes),'jmtes_weighted_probability':a/len(jmtes),
                        'observations':len(data),'events':a+c})
    with open(os.path.join(BASE,'jmtes_jes_referral_any_referral_logit_robustness_results.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,logrows[0].keys()); w.writeheader(); w.writerows(logrows)
    with open(os.path.join(BASE,'jmtes_jes_referral_student_data.csv'),'w',newline='') as f:
        w=csv.DictWriter(f,data[0].keys()); w.writeheader(); w.writerows(data)
    print(f'Loaded {len(jmtes)} JMTES and {len(jes)} JES students; wrote updated referral outputs.')

if __name__ == '__main__':
    write_outputs()
