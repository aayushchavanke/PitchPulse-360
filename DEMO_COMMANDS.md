# Classroom demonstration, step by step

Run these in PowerShell from the extracted project folder after Start.cmd succeeds. The web screens are easier for explaining; the commands let you show that the databases and queues are real.

## 1. Exploration and cleaning

Open `results/eda/report.html` in a browser. Explain the before/after counts, missing measurements, goals histogram and the 69 unusual high-scoring matches that were retained. Open `results/repaired_measurements.csv` to show the audited Newcastle–West Ham shot inconsistency.

Rebuild this step:

```powershell
docker compose run --rm pipeline eda
```

## 2. The actual PostgreSQL tables and SQL

```powershell
docker compose exec postgres psql -U pitchpulse -d pitchpulse -c "\dt football.*"
docker compose exec postgres psql -U pitchpulse -d pitchpulse -c "SELECT COUNT(*) AS matches FROM football.matches;"
docker compose exec postgres psql -U pitchpulse -d pitchpulse -c "SELECT * FROM analytics.team_season_rank WHERE league_name='Premier League' AND season='2023/2024' ORDER BY rank LIMIT 5;"
```

Show the ER diagram in WORKFLOW_GUIDE.md. Open `results/postgres/cumulative_points.csv` and `season_progression.csv` for SUM OVER, LAG and LEAD. Open `index_and_partition_plans.json`: the date lookup uses `idx_matches_date`; the selected-season plan reads one partition, while the unrestricted plan reads six. The comparison also records a deliberately forced sequential scan.

## 3. Rerunnable CSV → PostgreSQL ETL

```powershell
docker compose run --rm pipeline postgres
docker compose exec postgres psql -U pitchpulse -d pitchpulse -c "SELECT * FROM football.etl_runs ORDER BY finished_at DESC LIMIT 5;"
```

Run it again and show that the match count stays 10,781. It refreshes the snapshot transactionally instead of appending duplicates. Do not edit real source rows during the demonstration; the automated tests already exercise dirty input and constraint failures.

## 5. ROLLUP, CUBE and GROUPING SETS

```powershell
docker compose run --rm pipeline olap
```

Open the saved `results/olap/` tables and plans. ROLLUP produces detail plus league subtotals and the grand total. CUBE also produces season-only subtotals. The explicit GROUPING SETS request returns the same groups as this two-dimension CUBE. This is why ROLLUP has 36 rows and the other two have 42. PostgreSQL and DuckDB equality assertions run before timings are accepted.

## 7. MongoDB

```powershell
docker compose exec mongo mongosh pitchpulse --quiet --eval "db.raw_matches.countDocuments({})"
docker compose exec mongo mongosh pitchpulse --quiet --eval "db.raw_matches.getIndexes()"
docker compose run --rm pipeline mongo
```

The last command performs actual create/read/update/delete on a separate scout document and verifies each result. It deletes only its own temporary demonstration document. Show `results/mongo/crud_and_index_evidence.json`, including the projected fields, nested update and `IXSCAN` in the winning query plan.

## 10. RabbitMQ → consumer → PostgreSQL staging

```powershell
.\Start.ps1 -Action Stream
docker compose exec postgres psql -U pitchpulse -d pitchpulse -c "SELECT event_id,match_id,received_at FROM staging.match_events ORDER BY received_at DESC LIMIT 5;"
docker compose exec postgres psql -U pitchpulse -d pitchpulse -c "SELECT demo_run,reason FROM staging.rejected_events ORDER BY rejected_at DESC LIMIT 2;"
```

Open RabbitMQ at http://127.0.0.1:15673, login `pitchpulse` / `pitchpulse_local_demo`, then Queues. The main queue often has zero ready messages because the running consumer has already committed and acknowledged them. That is expected; use staging rows and the rejected queue as evidence, rather than expecting the valid queue to stay full.

Open http://127.0.0.1:8002/docs, expand POST `/lab/events`, select Try it out, and use the JSON example in WORKFLOW_GUIDE.md. A valid event returns 202 and appears through GET `/lab/events` after consumption. Reuse its event ID to demonstrate deduplication. Change its result to A while keeping a 2–1 score to demonstrate HTTP 422 validation.

## 12. Prefect

Open http://127.0.0.1:4201. Select Deployments → football-hourly to see the active hourly interval. Select a completed run and inspect its eleven tasks and logs.

For an immediate demonstration without waiting an hour:

```powershell
docker compose exec scheduler prefect deployment run pitchpulse-football-platform/football-hourly
```

That command requests a run; watch it complete in the UI. The automatic schedule was also tested with a temporary 60-second interval; `results/prefect/scheduled_run_evidence.json` records a new automatically scheduled completed run. The delivered configuration is restored to 3,600 seconds.

## Final verification and shutdown

```powershell
docker compose run --rm pipeline verify
.\Start.ps1 -Action Test
.\Start.ps1 -Action Stop
```

Verification queries the actual services. Test runs include deliberately bad input, an actual PostgreSQL CHECK failure, MongoDB CRUD and real RabbitMQ delivery. Stop keeps database volumes. Use Start.cmd again to rebuild/restart the product.

## 4, 8, 11 and 13 — newly completed demonstrations

Use the saved reports under `results/metrics/`, `results/delta_lab/`, `results/benchmark/` and `results/quality/`. ALL_15_EXPERIMENTS.md explains each result and includes commands to rerun the demonstrations. The ticket data is synthetic and the benchmark repeats fixtures for scaling. The quality failure report is deliberately damaged sample data, not a failed production batch.

```powershell
docker compose run --rm pipeline metrics
docker compose run --rm pipeline delta
docker compose run --rm pipeline benchmark
docker compose run --rm pipeline quality
```
