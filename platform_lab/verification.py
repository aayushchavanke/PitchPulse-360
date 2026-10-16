import json
import pandas as pd
import requests
import time
from .config import RESULTS,save_json
from .postgres import connect
from .mongo import client

def verify():
    frame=pd.read_parquet(RESULTS/'clean_matches.parquet')
    report=json.loads((RESULTS/'last_run.json').read_text())
    with connect() as pg:
        row=pg.execute('SELECT count(*),sum(home_goals+away_goals) FROM football.matches').fetchone()
        assert row==(len(frame),int(frame.total_goals.sum()))
        assert pg.execute('SELECT count(*) FROM analytics.match_facts').fetchone()[0]==len(frame)
        assert pg.execute('SELECT count(*) FROM football.league_seasons').fetchone()[0]==30
        constraints=pg.execute("SELECT count(*) FROM pg_constraint WHERE conrelid='football.matches'::regclass").fetchone()[0]
        assert constraints>=10
    with client() as mongo:
        documents=mongo.pitchpulse.raw_matches.count_documents({})
        assert documents==len(pd.read_parquet(RESULTS/'raw_snapshot.parquet'))
    for name in ['rollup','cube','grouping_sets']:
        assert report['olap'][name]['engines_match']
    assert report['streaming']['staged_unique']==report['streaming']['published_valid']
    assert report['streaming']['rejection_records']>=1
    assert report['streaming']['duplicate_retry']=='ignored'
    assert report['quality']['clean_passed']==report['quality']['expectations']
    assert report['quality']['deliberate_failure_detected']>=6
    assert all(item['answers_match'] for item in report['metrics']['comparisons'].values())
    assert report['delta_features']['version_unchanged_after_rejections'] and len(report['delta_features']['rejected_writes'])==2
    assert report['benchmark']['all_answers_match'] and len(report['benchmark']['modes'])==6
    assert report['benchmark']['benchmark_rows']>=250000
    # Query the actual orchestration server, not just a local success flag.
    import os
    url=os.environ['PREFECT_API_URL'].rstrip('/')
    # Prefect persists task events asynchronously; wait for their recorded states,
    # rather than declaring failure in the brief interval after a completed flow.
    deadline=time.monotonic()+45
    while True:
        response=requests.get(url+'/flow_runs/'+report['prefect_run_id'],timeout=15)
        response.raise_for_status(); flow=response.json()
        tasks=requests.post(url+'/task_runs/filter',json={'flow_runs':{'id':{'any_':[report['prefect_run_id']]}}},timeout=15)
        tasks.raise_for_status(); task_rows=tasks.json()
        if flow['state_type']=='COMPLETED' and len(task_rows)==11 and all(t['state_type']=='COMPLETED' for t in task_rows):
            break
        if time.monotonic()>deadline:
            raise AssertionError(f'Prefect state verification failed: flow={flow["state_type"]}, tasks={[t["state_type"] for t in task_rows]}')
        time.sleep(2)
    result=dict(status='passed',postgres_matches=row[0],goals=row[1],postgres_constraints=constraints,
        mongo_documents=documents,completed_prefect_tasks=len(task_rows),prefect_run_id=report['prefect_run_id'],
        tests=['PostgreSQL reconciliation','MongoDB reconciliation','OLAP engine equality',
          'stream deduplication and rejection','metric view/raw equality','Delta old-version reads and schema rejections',
          'six-mode equal-result benchmark','quality gate and intentional failures','actual Prefect completed flow and eleven tasks'])
    save_json('verification.json',result)
    return result
