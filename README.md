# PitchPulse 360 — Complete Football Data Engineering Platform

Start with **Start.cmd** (Docker Desktop required). It builds and starts the services, executes and verifies the batch, then starts the dashboard, event consumer and scheduled Prefect deployment.

- Football dashboard: http://127.0.0.1:8502
- API documentation: http://127.0.0.1:8002/docs
- Prefect runs/schedule: http://127.0.0.1:4201
- RabbitMQ queues: http://127.0.0.1:15673

**Read [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)** for every functionality, each completed experiment, normalization/ER diagram, data flow, demonstration commands and limitations.

Use [DEMO_COMMANDS.md](DEMO_COMMANDS.md) for a classroom demonstration with copyable commands. Read COMPLETION_REPORT.md for measured validation results.

## Completed extension

All experiments **1–15** are now mapped to executable features in [ALL_15_EXPERIMENTS.md](ALL_15_EXPERIMENTS.md). Additions include reusable ticket/football metrics, actual Delta time travel/schema rejection, six-mode DuckDB benchmarks and an explicit quality suite with HTML reports.

Runtime evidence is generated under `results/`. Check `results/verification.json`, `results/last_run.json`, the detailed CSVs, plans and logs. The current completion report records what was actually tested. Read the syllabus map for exact evidence and the documented synthetic datasets/tool choices.

## Commands

```powershell
.\Start.ps1 -Action Start
.\Start.ps1 -Action Run
.\Start.ps1 -Action Test
.\Start.ps1 -Action Stream
.\Start.ps1 -Action Status
.\Start.ps1 -Action Stop
```

Stop preserves database volumes. All published ports are localhost only. Credentials in compose.yaml are local demonstration credentials, not production secrets. First startup requires internet for image/package downloads.

The scheduler defaults to one full run per hour while Docker is running. It replays historical fixtures for its streaming check; it is not a live sports feed. Player heatmaps are generated demonstration data. Historical standings use simplified rules and do not include all official deductions/tie-breaks.

## Code map

- `platform_lab/cleaning.py`: collection, profiling, cleaning and EDA artifacts.
- `models/postgres_schema.sql`, `platform_lab/postgres.py`: 3NF database, transactional load, analytical views, windows and plans.
- `platform_lab/olap.py`: ROLLUP/CUBE/GROUPING SETS, answer equality, timing and plans.
- `platform_lab/mongo.py`: original documents, actual CRUD, projections and index evidence.
- `platform_lab/streaming.py`: durable RabbitMQ producer/consumer, validation, deduplication and rejection handling.
- `platform_lab/flow.py`: Prefect flow, eleven tasks, retries, deployment and interval schedule.
- `platform_lab/metrics.py`, `models/metric_views.sql`: football views and explicitly synthetic ticket-sales metrics.
- `platform_lab/delta_experiment.py`: Delta changes, old-version reads and schema-error evidence.
- `platform_lab/benchmark.py`: six-mode equal-data storage/thread benchmark.
- `platform_lab/expectations.py`, `quality/football_expectations.json`: declarative checks, HTML reports and a load gate.
- `platform_lab/verification.py`: verifies actual database counts and Prefect task completion.
- `dashboard/app.py`: football dashboard; `results/`: saved execution evidence.
- `serving/api.py`, `platform_lab/api.py`: read endpoints and event capture.
- `tests/test_platform.py`: defect and service-integration tests.
- `compose.yaml`, `Dockerfile`, `requirements-platform.txt`: portable service setup.

`README-original.md`, `PROJECT_REPORT.md`, the original PDF reports, `reference/`, and `run_legacy_pipeline.py` are historical source material. They are not evidence of the current platform and may contain inaccurate claims. The active orchestrator is Prefect, not the archived Airflow example.


### Dashboard appearance

Use the top-right **⋮ → Settings → Theme** to choose **Light**, **Dark**, or the system setting. This is the single appearance control for both dashboard pages, including tables, dropdowns and charts. Custom metric cards inherit that theme. The football pitch stays green in either theme.

### Desktop launcher

Double-click `Install_Desktop_Launcher.cmd` to add **Start PitchPulse360 Football.cmd** to your Windows Desktop. Double-click that desktop file to start the project and open its dashboard. Keep the extracted project folder in place; if you move it, run the installer again from the new location.

The launcher starts Docker Desktop if needed, waits for the engine and required services, builds the application image if missing, initializes absent warehouse/lakehouse data, and opens the dashboard after both it and the API respond. Existing prepared data is reused for quick startup. The services continue running when the launcher window closes. Use `.\Start.ps1 -Action Stop` to stop them, or `.\Start.ps1 -Action Run` for a fresh full pipeline run. Use `Open_Football.cmd` to launch directly from the project folder. `Start_Football_Platform.ps1 -Rebuild` also rebuilds the application image when necessary.

## Dashboard appearance

The football dashboard uses a forest-green visual style, stadium header, clearer navigation and responsive cards. Tables and charts follow Streamlit native Light/Dark appearance. Open the top-right menu, select Settings, then Theme. Additional standings columns are available through the table column menu. The stadium image is bundled locally; static serving is enabled in `.streamlit/config.toml`.

UI regression results are saved in `results/ui_checks.json`; responsive, theme and wording checks are recorded in `results/ui_redesign_checks.json`.
