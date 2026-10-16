# All 15 experiments — implementation and evidence

This is the current syllabus map for the football project. These are executable features, not just module names. The new completion report records their actual tests. Financial orders and benchmark scaling data are explicitly synthetic; historical match records remain sourced from the supplied files.

| No. | Experiment | What is implemented | Where to show it |
|---|---|---|---|
| 1 | EDA and cleaning | CSV ingestion, type conversion, null/duplicate/domain checks, audited repairs/rejections, outlier inspection, statistics and charts | saved experiment reports; results/eda/report.html |
| 2 | Relational schema and SQL | Actual PostgreSQL 3NF tables, ER diagram and normalization explanation, keys/constraints, sample records, joins, DENSE_RANK/LAG/LEAD/running SUM, indexes and partition/query-plan comparisons | models/postgres_schema.sql; WORKFLOW_GUIDE.md; results/postgres/ |
| 3 | CSV → PostgreSQL ETL | Extract/transform/validate/COPY load, transactional snapshot refresh, stable IDs, provenance and rerunnable CLI with ETL audit | platform_lab/postgres.py; football.etl_runs |
| 4 | Reusable SQL business metrics | Daily revenue, monthly sales growth and repeat-customer percentage on labeled football ticket orders; football daily-goals and team-win-rate views; view versus direct SQL equality, timings and plans | models/metric_views.sql; saved experiment reports; results/metrics/ |
| 5 | Data cubes | Actual ROLLUP/CUBE/GROUPING SETS, PostgreSQL/DuckDB equality, saved result tables and execution-plan comparisons | saved experiment reports; results/olap/ |
| 6 | BI dashboard | Warehouse-backed standings, head-to-head, records and player demonstrations; charts answering football questions; theme/league/season controls plus engineering evidence pages | http://127.0.0.1:8502 |
| 7 | MongoDB CRUD | Actual source documents, nested flexible scout reports, insert/find/project/update/delete, compound indexes and indexed plan evidence | saved experiment reports; results/mongo/ |
| 8 | Delta Lake features | Create, append, update and delete to produce versions 0–3; actual reader query of version 0; incompatible columns and wrong types rejected with errors recorded and no new commit | saved experiment reports; results/delta_lab/summary.json |
| 9 | REST data capture | FastAPI POST/GET, required JSON/schema/business validation, real RabbitMQ ingestion into PostgreSQL staging, recent-event reads and error responses | http://127.0.0.1:8002/docs; results/http_checks.json |
| 10 | Event-driven ingestion | Real RabbitMQ producer/consumer, durable queues, persistent messages, broker confirms, commit-before-ACK, unique event-ID insertion and rejected-message handling | saved experiment reports; staging tables; RabbitMQ UI |
| 11 | Parallel local processing | 250,000 replayed football rows; CSV, partitioned ZSTD Parquet and native DuckDB; actual one/four-thread settings; warm-up plus five timings per mode; equal-result assertions, scan plans and partition pruning | saved experiment reports; results/benchmark/ |
| 12 | Orchestration | Real Prefect flow with 11 dependent tasks, retries, logs, concurrency protection, active deployment and hourly schedule; actual future automatic run checked | http://127.0.0.1:4201; results/prefect/ |
| 13 | Expectation suite | Explicit versioned JSON suite for columns/nulls/types/ranges/uniqueness/allowed values/business consistency; clean and deliberate-failure sample validation; detailed HTML pass/fail reports; failed clean data blocks loading | quality/football_expectations.json; saved experiment reports|
| 14 | End-to-end batch | Connected ingestion → cleaning → validation gate → transformation → PostgreSQL/Delta/Parquet outputs, provenance, logs and rejected/repair files | run_pipeline.py; platform_lab/flow.py; results/last_run.json |
| 15 | Combined mini platform | APIs, SQL and NoSQL modeling, validation, ETL, storage, analytics, event staging and dashboards run together through Docker Compose | Start.cmd; compose.yaml; results/verification.json |

## The four additions, in baby words

**4 — Save the calculation once.** A SQL view is a saved question. “What was each day's revenue?” is defined once and reused. A separate raw query calculates the same result; the code compares them. An ordinary view mainly improves consistency/readability, not guaranteed speed. The 6,000 ticket orders are generated teaching data linked to real fixture IDs. They are not real club revenue or real people.

Monthly growth includes calendar months with zero sales, rather than skipping the summer gaps. Growth is unknown for the first month or when the previous month's revenue is zero. Repeat customers are customers with more than one paid order; refunded orders do not count as realized revenue or paid purchases.

**8 — Open the table's earlier edit history.** A separate tiny Delta table starts with two rows. Another row is added, one goal value changes and one row is deleted. The program uses DeltaTable(version=0) to read the original table. It attempts two bad writes and records the errors; the table's version stays unchanged. Real historical match tables are not damaged for this demonstration.

**11 — Run the same race with different settings.** The same prepared 250,000 rows are stored in CSV, Parquet and DuckDB. Each query runs with one and four DuckDB thread limits. Every result must match before its timing is accepted. The rows repeat historical fixtures only to create a larger controlled workload. Four threads do not mean four computers, and four threads are not promised to win every time.

Repeated fixture rows compress unusually well. The saved file-size ratios should not be presented as a prediction for independent, newly observed matches. Timing includes reading from the configured local container/bind-mounted storage.

**13 — Give the data an explicit checklist.** The JSON suite says which columns are required, which values cannot be missing, which fields must be integers/dates, which values/ranges are allowed, and whether scores/shots make sense. The real clean data must pass before warehouse loading. A separate damaged sample proves the checks catch mistakes. Both runs have HTML reports with per-check results and examples. This is a custom Pandas expectation-suite implementation, not a claim that the Great Expectations library is installed; the supplied syllabus does not require that particular library.

## Commands for the additions

From the extracted project folder after Start.cmd succeeds:

```powershell
docker compose run --rm pipeline metrics
docker compose run --rm pipeline delta
docker compose run --rm pipeline benchmark
docker compose run --rm pipeline quality
.\Start.ps1 -Action Run
.\Start.ps1 -Action Test
```

The four single-experiment commands are useful for demonstrations. The full Run command connects all experiments, runs the quality gate before loading and verifies the completed Prefect flow. A synthetic dataset is not evidence of real financial performance, and benchmark timings are local measurements. Official league rules and generated player heatmaps retain the limitations described in WORKFLOW_GUIDE.md.
