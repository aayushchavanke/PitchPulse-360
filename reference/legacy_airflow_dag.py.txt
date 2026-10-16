"""
PitchPulse 360 - Apache Airflow Production DAG (CO4 & Lab 12)
Orchestrates the entire football telemetry data lifecycle:
1. Extract StatsBomb match events
2. Validate Quality & Observability constraints
3. Ingest into Bronze Delta Lake
4. Transform via DuckDB / PySpark into Silver schema
5. Build Gold analytical metrics & Star Schema
6. Publish to Serving layer & trigger alerts
"""

from datetime import datetime, timedelta
import os
import sys

# Add project root to sys.path for operator execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.empty import EmptyOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

default_args = {
    "owner": "pitchpulse_data_engineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2026, 1, 1),
}

def task_extract_events(**context):
    from ingestion.fetch_statsbomb import download_statsbomb_match
    path = download_statsbomb_match()
    return path

def task_validate_quality(**context):
    from ingestion.fetch_statsbomb import download_statsbomb_match
    from quality.expectations_suite import DataQualitySuite
    import json
    
    path = download_statsbomb_match()
    with open(path, "r", encoding="utf-8") as f:
        events = json.load(f)
    suite = DataQualitySuite()
    report = suite.validate_events(events)
    suite.generate_html_report(report)
    print(f"[Airflow Task] Data Quality check completed. Pass Rate: {report['pass_rate_percentage']}%")
    return report

def task_stage_bronze_and_silver(**context):
    from storage.lakehouse_manager import LakehouseManager
    from ingestion.fetch_statsbomb import download_statsbomb_match
    import json
    
    path = download_statsbomb_match()
    with open(path, "r", encoding="utf-8") as f:
        events = json.load(f)
    
    lm = LakehouseManager()
    lm.write_bronze(events, match_id="3869685")
    lm.process_silver(events, match_id="3869685")
    print("[Airflow Task] Bronze & Silver Delta Lake tables updated successfully.")

def task_build_gold_kpis(**context):
    from spark.duckdb_processor import DuckDBProcessor
    processor = DuckDBProcessor()
    gold_kpis = processor.run_analytical_pipeline()
    print(f"[Airflow Task] Gold metrics produced for {len(gold_kpis)} teams.")

if AIRFLOW_AVAILABLE:
    with DAG(
        "pitchpulse_football_telemetry_pipeline",
        default_args=default_args,
        description="End-to-End Football Data Engineering Pipeline (StatsBomb -> Delta Lake -> DuckDB -> Serving)",
        schedule_interval="@hourly",
        catchup=False,
    ) as dag:

        start = EmptyOperator(task_id="start_pipeline")
        
        extract = PythonOperator(
            task_id="extract_statsbomb_events",
            python_callable=task_extract_events
        )

        validate = PythonOperator(
            task_id="validate_data_quality",
            python_callable=task_validate_quality
        )

        stage_lakehouse = PythonOperator(
            task_id="stage_bronze_silver_delta",
            python_callable=task_stage_bronze_and_silver
        )

        build_gold = PythonOperator(
            task_id="build_gold_analytical_kpis",
            python_callable=task_build_gold_kpis
        )

        end = EmptyOperator(task_id="end_pipeline")

        start >> extract >> validate >> stage_lakehouse >> build_gold >> end
else:
    print("[Airflow Note] Apache Airflow environment not detected. Use pipeline_runner.py for standalone execution.")
