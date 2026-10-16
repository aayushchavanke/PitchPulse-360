"""Experiment 12: a real Prefect task graph, retries, logs, deployment and schedule."""
import argparse
import os
import time
from prefect import flow, task, get_run_logger
from prefect.cache_policies import NO_CACHE
from prefect.runtime import flow_run
from .config import ROOT, RESULTS, save_json

@task(retries=2,retry_delay_seconds=3,cache_policy=NO_CACHE)
def extract_task():
    from .cleaning import extract
    get_run_logger().info('Reading all 30 league-season files; incomplete coverage fails the run')
    return extract()

@task(retries=1,retry_delay_seconds=3,cache_policy=NO_CACHE)
def clean_task(raw):
    from .cleaning import clean_and_report
    return clean_and_report(raw)

@task(retries=0,cache_policy=NO_CACHE)
def expectations_task(clean):
    from .expectations import run
    return run(clean)

@task(retries=1,retry_delay_seconds=3,cache_policy=NO_CACHE)
def metrics_task(clean):
    from .metrics import run
    return run(clean)

@task(retries=1,retry_delay_seconds=3,cache_policy=NO_CACHE)
def delta_features_task():
    from .delta_experiment import run
    return run()

@task(retries=1,retry_delay_seconds=3,cache_policy=NO_CACHE)
def benchmark_task(clean):
    from .benchmark import run
    return run(clean)

@task(retries=2,retry_delay_seconds=3,cache_policy=NO_CACHE)
def postgres_task(clean):
    from .postgres import load,analyze
    load(clean)
    return analyze()

@task(retries=2,retry_delay_seconds=3,cache_policy=NO_CACHE)
def mongo_task(raw):
    from .mongo import sync_raw,demonstrate_crud
    return dict(**sync_raw(raw),**demonstrate_crud())

@task(retries=1,retry_delay_seconds=3,cache_policy=NO_CACHE)
def olap_task(clean):
    from .olap import run
    return run(clean)

@task(retries=1,retry_delay_seconds=3,cache_policy=NO_CACHE)
def lakehouse_task(clean):
    import pandas as pd
    from storage.lakehouse_manager import LakehouseManager
    from ingestion.build_player_database import build_player_lakehouse_data
    from ingestion.lineage_tracker import LineageTracker
    df=pd.read_parquet(clean)
    lm=LakehouseManager()
    lm.write_bronze(pd.read_parquet(RESULTS/'raw_snapshot.parquet'))
    lm.process_silver(df)
    gold=lm.generate_gold_standings(df)
    players,events=build_player_lakehouse_data()
    LineageTracker().save_lineage_metadata()
    return dict(matches=len(df),team_seasons=len(gold),player_profiles=len(players),simulated_player_actions=len(events))

@task(retries=1,retry_delay_seconds=3,cache_policy=NO_CACHE)
def streaming_task():
    from .streaming import demo
    return demo()

@flow(name='pitchpulse-football-platform',log_prints=True)
def football_flow():
    # Relative paths in the original dashboard/lakehouse modules resolve consistently.
    os.chdir(ROOT)
    # A filesystem lock prevents scheduled and manual runs from replacing outputs together.
    from filelock import FileLock
    with FileLock(str(RESULTS/'.pipeline.lock'),timeout=1800):
        started=time.perf_counter()
        raw=extract_task()
        clean=clean_task(raw)
        quality=expectations_task(clean)
        pg=postgres_task(clean)
        metrics=metrics_task(clean)
        mongo=mongo_task(raw)
        olap=olap_task(clean)
        lake=lakehouse_task(clean)
        delta_features=delta_features_task()
        benchmark=benchmark_task(clean)
        stream=streaming_task()
        result=dict(status='completed',prefect_run_id=flow_run.id,postgres=pg,mongo=mongo,
            olap=olap,lakehouse=lake,streaming=stream,quality=quality,metrics=metrics,
            delta_features=delta_features,benchmark=benchmark,
            duration_seconds=round(time.perf_counter()-started,3))
        save_json('last_run.json',result)
        get_run_logger().info('Completed: %s matches, real PostgreSQL/MongoDB/RabbitMQ checks passed',pg['matches'])
        return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--serve',action='store_true'); args=p.parse_args()
    if args.serve:
        football_flow.serve(name='football-hourly',interval=int(os.getenv('PITCHPULSE_SCHEDULE_SECONDS','3600')),
            limit=1,pause_on_shutdown=True)
    else: football_flow()
