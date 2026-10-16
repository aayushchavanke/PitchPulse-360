"""Experiment 13: explicit suite, per-expectation results, HTML and failing-data demonstration."""
import html
import json
import pandas as pd
from pandas.api import types as types
from .config import ROOT,RESULTS,save_json

def validate(frame,suite=None):
    if suite is None: suite=json.loads((ROOT/'quality/football_expectations.json').read_text())
    checks=[]
    def add(name,mask=None,passed=None,details=''):
        failed=frame.index[mask.fillna(False)].tolist() if mask is not None else []
        good=(not failed) if passed is None else bool(passed)
        samples=frame.loc[failed[:5]].astype(object).where(pd.notna(frame.loc[failed[:5]]),None).to_dict('records') if failed else []
        checks.append(dict(expectation=name,passed=good,failed_rows=len(failed),sample_indices=failed[:5],samples=samples,details=details))
    missing=sorted(set(suite['required_columns'])-set(frame.columns))
    add('required_columns',passed=not missing,details='Missing: '+str(missing)+'; extra provenance fields allowed')
    add('minimum_row_count',passed=len(frame)>=suite['minimum_rows'],details=f'{len(frame)} rows; minimum {suite["minimum_rows"]}')
    for col in suite['not_null']:
        if col not in frame: add('not_null:'+col,passed=False,details='Column missing'); continue
        blank=frame[col].isna() | frame[col].astype('string').str.strip().eq('').fillna(False)
        add('not_null:'+col,blank)
    for col in suite['unique']:
        add('unique:'+col,frame[col].duplicated(keep=False)) if col in frame else add('unique:'+col,passed=False,details='Column missing')
    for col,expected in suite['types'].items():
        if col not in frame: add('dtype:'+col,passed=False,details='Column missing'); continue
        dtype=frame[col].dtype
        good=types.is_datetime64_any_dtype(dtype) if expected=='datetime' else types.is_integer_dtype(dtype) if expected=='integer' else types.is_string_dtype(frame[col].dropna())
        add('dtype:'+col,passed=good,details=f'Expected {expected}; actual {dtype}')
    for col,(low,high) in suite['ranges'].items():
        if col not in frame: add('range:'+col,passed=False,details='Column missing'); continue
        numeric=pd.to_numeric(frame[col],errors='coerce')
        invalid=frame[col].notna() & (numeric.isna() | ~numeric.between(low,high))
        add('range:'+col,invalid,details=f'Inclusive [{low}, {high}]; unknown optional values permitted')
    for col,allowed in suite['allowed'].items():
        add('allowed:'+col,~frame[col].isin(allowed)) if col in frame else add('allowed:'+col,passed=False,details='Column missing')
    required={'home_goals','away_goals','result','home_team','away_team','home_shots','away_shots','home_shots_target','away_shots_target'}
    if required<=set(frame.columns):
        hg=pd.to_numeric(frame.home_goals,errors='coerce'); ag=pd.to_numeric(frame.away_goals,errors='coerce')
        expected=pd.Series('D',index=frame.index).mask(hg>ag,'H').mask(hg<ag,'A')
        add('result_matches_score',frame.result.ne(expected) | hg.isna() | ag.isna())
        add('different_teams',frame.home_team.eq(frame.away_team))
        for side in ['home','away']:
            total=pd.to_numeric(frame[side+'_shots'],errors='coerce'); target=pd.to_numeric(frame[side+'_shots_target'],errors='coerce')
            add(side+'_target_not_above_total',total.notna() & target.notna() & (target>total))
    else:
        for name in suite['business_rules']: add(name,passed=False,details='Required business-rule columns missing')
    failed=sum(not c['passed'] for c in checks)
    return dict(suite=suite['name'],status='PASSED' if failed==0 else 'FAILED',rows=len(frame),
      expectations=len(checks),passed_expectations=len(checks)-failed,failed_expectations=failed,
      expectation_pass_pct=round(100*(len(checks)-failed)/len(checks),2),checks=checks,notes=suite['notes'])

def render(report,path):
    def esc(value): return html.escape(str(value))
    rows=''.join(f'<tr><td>{esc(c["expectation"])}</td><td>{"PASS" if c["passed"] else "FAIL"}</td><td>{c["failed_rows"]}</td><td>{esc(c["details"])}</td><td><pre>{esc(json.dumps(c["samples"],default=str,ensure_ascii=False))}</pre></td></tr>' for c in report['checks'])
    text=f'''<!doctype html><html><head><meta charset="utf-8"><title>Football expectation suite</title>
    <style>body{{font:15px system-ui;margin:32px;color:#173047}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #bbcbd6;padding:8px;text-align:left}}pre{{white-space:pre-wrap;max-width:420px}}th{{background:#e5eff4}}</style></head>
    <body><h1>Football data-quality validation: {report['status']}</h1>
    <p>{report['rows']:,} rows; {report['passed_expectations']}/{report['expectations']} expectations passed. {report['failed_expectations']} failed.</p>
    <p>{esc(report['notes'])}</p><p>The percentage counts expectations, not individual records. Dtype/schema failures can be table-level with zero row samples.</p>
    <table><tr><th>Expectation</th><th>Result</th><th>Failed rows</th><th>Interpretation</th><th>Examples (maximum five)</th></tr>{rows}</table></body></html>'''
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')

def run(clean_path):
    frame=pd.read_parquet(clean_path)
    actual=validate(frame)
    save_json('quality/validation.json',actual); render(actual,RESULTS/'quality/validation_report.html')
    (ROOT/'data/quality_audit_report.html').write_text((RESULTS/'quality/validation_report.html').read_text(),encoding='utf-8')
    dirty=frame.head(8).copy().reset_index(drop=True)
    if len(dirty)<6: raise ValueError('Failure demonstration needs at least six records')
    dirty['home_goals']=dirty.home_goals.astype('string')
    dirty.loc[0,'home_goals']='-1'; dirty.loc[0,'match_date']=pd.NaT
    dirty.loc[1,'home_team']=None; dirty.loc[2,'match_id']=dirty.loc[1,'match_id']
    dirty.loc[3,'result']='X'; dirty.loc[4,'away_shots_target']=999
    dirty.to_csv(RESULTS/'quality/intentional_bad_sample.csv',index=False)
    demo=validate(dirty)
    assert demo['status']=='FAILED' and demo['failed_expectations']>=6
    save_json('quality/intentional_failure.json',demo); render(demo,RESULTS/'quality/intentional_failure_report.html')
    if actual['status']!='PASSED': raise ValueError('Expectation suite failed; warehouse loading is blocked. Inspect results/quality/validation_report.html')
    result=dict(status='passed',expectations=actual['expectations'],clean_passed=actual['passed_expectations'],
      deliberate_failure_detected=demo['failed_expectations'],interpretation='Clean data passed the gate. Separate intentionally damaged rows failed; they were never loaded into the warehouse.')
    save_json('quality/summary.json',result)
    return result
