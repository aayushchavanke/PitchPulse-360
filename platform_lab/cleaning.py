"""Experiment 1: preserve input, profile defects, clean deterministically, quarantine."""
import hashlib
import html
import json
import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .config import ROOT, RESULTS, save_json
from ingestion.fetch_leagues import LEAGUES, SEASONS, fetch_league_season

NAMES = {'Date':'match_date','HomeTeam':'home_team','AwayTeam':'away_team',
    'FTHG':'home_goals','FTAG':'away_goals','FTR':'result','HS':'home_shots',
    'AS':'away_shots','HST':'home_shots_target','AST':'away_shots_target',
    'HY':'home_yellows','AY':'away_yellows','HR':'home_reds','AR':'away_reds'}
NUMERIC = list(NAMES.values())[3:5] + list(NAMES.values())[6:]
ALIASES = {'Bayern':'Bayern Munich','Inter Milan':'Inter','AC Milan':'Milan'}

def extract():
    frames=[]
    for league, info in LEAGUES.items():
        for season in SEASONS:
            original=fetch_league_season(league, season['label'], season['code'])
            if original.empty:
                raise ValueError(f'Missing league-season: {league} {season["label"]}')
            # Reindex retains missing fields for validation, rather than hiding them.
            frame=original.reindex(columns=NAMES).rename(columns=NAMES)
            frame=frame.assign(league_name=league,country=info['country'],
                season=season['label'],season_code=season['code'],
                source_file=f'{info["code"]}_{season["code"]}.csv',
                source_row=range(2,len(frame)+2))
            frames.append(frame)
    raw=pd.concat(frames,ignore_index=True)
    raw.to_parquet(RESULTS/'raw_snapshot.parquet',index=False)
    return str(RESULTS/'raw_snapshot.parquet')

def profile(df):
    return dict(rows=len(df), columns=len(df.columns),
        types={c:str(t) for c,t in df.dtypes.items()},
        nulls={c:int(v) for c,v in df.isna().sum().items()},
        exact_duplicate_rows=int(df.drop(columns=['source_row'],errors='ignore').duplicated().sum()),
        numeric_summary=json.loads(df.describe(include='number').to_json()) if len(df.select_dtypes('number').columns) else {})

def clean_frame(raw):
    df=raw.copy()
    reasons=pd.Series('',index=df.index,dtype='object')
    measurement_notes=pd.Series('',index=df.index,dtype='object')
    def flag(mask,reason):
        nonlocal reasons
        reasons.loc[mask.fillna(False)] += reason+'; '
    for col in ['home_team','away_team','league_name','country','season','season_code']:
        if col not in df: df[col]=pd.NA
        df[col]=df[col].astype('string').str.strip().str.replace(r'\s+',' ',regex=True).replace('',pd.NA)
        flag(df[col].isna(),f'missing {col}')
    for col in ['home_team','away_team']:
        df[col]=df[col].replace(ALIASES)
    dates=df.get('match_date',pd.Series(pd.NaT,index=df.index)).astype('string')
    df['match_date']=pd.to_datetime(dates,format='mixed',dayfirst=True,errors='coerce')
    flag(df['match_date'].isna(),'invalid date')
    for col in NUMERIC:
        if col not in df: df[col]=np.nan
        numeric=pd.to_numeric(df[col],errors='coerce')
        maximum=20 if 'goals' in col else 80 if 'shots' in col else 30
        invalid=numeric.notna() & (~numeric.between(0,maximum) | numeric.mod(1).ne(0))
        invalid_text=df[col].notna() & numeric.isna()
        if 'goals' in col:
            flag(invalid,f'invalid {col}')
            flag(numeric.isna(),f'missing {col}')
        else:
            measurement_notes.loc[invalid|invalid_text] += f'{col} invalid: set unknown; '
        df[col]=numeric.where(~invalid & numeric.mod(1).eq(0)).astype('Int64')
    for side in ['home','away']:
        inconsistent=(df[f'{side}_shots_target']>df[f'{side}_shots']).fillna(False)
        measurement_notes.loc[inconsistent] += f'{side} target shots exceed shots: both measurements set unknown; '
        df.loc[inconsistent,[f'{side}_shots',f'{side}_shots_target']]=pd.NA
    flag(df.home_team.eq(df.away_team),'same home and away team')
    df['result']=df.get('result',pd.Series(pd.NA,index=df.index)).astype('string').str.strip().str.upper()
    expected=pd.Series(np.where(df.home_goals.fillna(-1)>df.away_goals.fillna(-1),'H',
        np.where(df.home_goals.fillna(-1)<df.away_goals.fillna(-1),'A','D')),index=df.index)
    # Result can be safely repaired from valid scores; record repair count separately.
    repair=df.result.ne(expected).fillna(True)
    df['result']=expected
    keys=['league_name','season','match_date','home_team','away_team']
    flag(df.duplicated(keys,keep='first'),'duplicate fixture')
    df['rejection_reason']=reasons.str.rstrip('; ')
    df['measurement_repair_notes']=measurement_notes.str.rstrip('; ')
    rejected=df[df.rejection_reason.ne('')].copy()
    clean=df[df.rejection_reason.eq('')].drop(columns='rejection_reason').copy()
    clean['match_id']=[hashlib.sha256('|'.join(map(str,row)).encode()).hexdigest()[:24]
        for row in clean[keys].itertuples(index=False,name=None)]
    clean['total_goals']=clean.home_goals+clean.away_goals
    clean['home_points']=clean.result.map({'H':3,'D':1,'A':0}).astype('int64')
    clean['away_points']=clean.result.map({'H':0,'D':1,'A':3}).astype('int64')
    clean['goal_diff']=clean.home_goals-clean.away_goals
    assert clean.match_id.is_unique
    return clean,rejected,int(repair.sum())

def clean_and_report(raw_path):
    raw=pd.read_parquet(raw_path)
    clean,rejected,repaired=clean_frame(raw)
    if clean.empty: raise ValueError('No valid fixtures after cleaning')
    clean.to_parquet(RESULTS/'clean_matches.parquet',index=False)
    rejected.to_csv(RESULTS/'rejected_matches.csv',index=False)
    repairs=clean[clean.measurement_repair_notes.ne('')]
    repairs.to_csv(RESULTS/'repaired_measurements.csv',index=False)
    missing=clean[NUMERIC].isna().sum().to_dict()
    # Missing optional measurements stay unknown; filling them with zero would invent data.
    q=clean.total_goals.quantile([.25,.75]); threshold=float(q.loc[.75]+1.5*(q.loc[.75]-q.loc[.25]))
    unusual=clean[clean.total_goals>threshold]
    unusual.to_csv(RESULTS/'high_scoring_outliers.csv',index=False)
    summary=dict(before=profile(raw),after=profile(clean),rejected_rows=len(rejected),
        result_codes_repaired=repaired,rows_with_measurement_repairs=len(repairs),optional_missing={k:int(v) for k,v in missing.items()},
        outlier_rule=f'total_goals > Q3 + 1.5 IQR ({threshold:g})',
        outliers_retained=len(unusual),outlier_policy='Flag unusual valid results; reject impossible values. Do not delete real high-scoring matches.')
    save_json('eda/summary.json',summary)
    chart_dir=RESULTS/'eda'; chart_dir.mkdir(exist_ok=True)
    fig,ax=plt.subplots(1,2,figsize=(12,4))
    clean.groupby('league_name').size().plot.barh(ax=ax[0],color='#168c87',title='Matches by league')
    clean.total_goals.astype(int).plot.hist(ax=ax[1],bins=range(12),color='#4474bc',title='Goals per match')
    fig.tight_layout(); fig.savefig(chart_dir/'overview.png',dpi=140); plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4))
    raw.isna().sum().plot.bar(ax=ax,color='#c88028',title='Missing values before cleaning')
    fig.tight_layout(); fig.savefig(chart_dir/'missing_values.png',dpi=140); plt.close(fig)
    report=f'''<html><head><meta charset="utf-8"><title>Football EDA</title></head><body>
    <h1>Football exploration and cleaning</h1><p>{len(raw):,} input rows; {len(clean):,} accepted; {len(rejected):,} rejected.</p>
    <p>Optional missing measurements stay unknown. Invalid optional measurements are logged and cleared; valid match scores remain. Valid high-scoring matches remain in the data.</p>
    <img width="900" src="overview.png"><img width="900" src="missing_values.png">
    <h2>Before</h2>{raw.describe(include='all').to_html()}
    <h2>After</h2>{clean.describe(include='all').to_html()}
    <h2>Rules and counts</h2><pre>{html.escape(json.dumps(summary,indent=2,default=str))}</pre></body></html>'''
    (chart_dir/'report.html').write_text(report,encoding='utf-8')
    return str(RESULTS/'clean_matches.parquet')
