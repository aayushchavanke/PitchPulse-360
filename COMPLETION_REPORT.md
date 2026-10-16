# Completion report — all 15 football experiments

**Experiments 1–15 are implemented and mapped to executable behavior and evidence.** Read ALL_15_EXPERIMENTS.md for the complete mapping, tool choices and synthetic-data notes. Original reports supplied in the ZIP describe an older implementation.

## Final verification

- **30 automated tests passed**; plotting/UI libraries emit non-failing deprecation warnings.
- **10,781 historical matches**, **30,186 goals**, 140 teams, 30 league-seasons and 586 team-season summaries remain reconciled.
- Real PostgreSQL, MongoDB and RabbitMQ integrations passed. Actual index use and partition pruning were recorded.
- **11 Prefect tasks** completed. A newly observed future automatically scheduled run completed all 11 tasks. The final active schedule was restored to **3,600 seconds**.
- Startup through the supplied Start.ps1 command passed. The football dashboard and HTTP experiment-report endpoints passed checks.

## Experiment 4 — reusable metrics

Actual PostgreSQL views produce daily revenue, calendar-month sales growth and repeat-customer percentage. They use **6,000 explicitly synthetic football ticket orders** linked to actual fixture IDs. Refunds do not count as realized revenue/paid purchases; zero-sales months remain in the monthly calendar; growth is undefined for the first month or a zero previous-month denominator.

Equivalent direct SQL returns the same values. Both forms have saved plans and five-run median timings. Ordinary views centralize definitions; they are not materialized and do not promise a speed gain. Additional views report daily football goals and team win percentage on historical results.

Evidence: results/metrics/, models/metric_views.sql, saved experiment reports.

## Experiment 8 — real Delta versioning

An isolated demonstration table was created, appended, updated and deleted, producing versions 0–3. The actual Delta reader retrieved version 0 and verified its original values. Two incompatible writes—wrong columns and nonnumeric goal values—were rejected. Their errors were recorded and the current version remained unchanged. Historical match tables were not corrupted for the demonstration.

Evidence: results/delta_lab/summary.json and the referenced table/log/snapshot files; saved experiment reports.

## Experiment 11 — measured storage/thread comparison

The same prepared **250,000 replayed rows** are stored in CSV, partitioned ZSTD Parquet and native DuckDB. Each mode receives a warm-up and five measured queries. Every measured result is checked for equality. Settings of one/four are verified DuckDB thread limits on one computer, not guaranteed simultaneous worker use or four computers. The filtered Parquet plan reads **1 of 5 files**.

| Storage | Thread limit | Median ms |
|---|---:|---:|
| CSV | 1 | 167.156 |
| Parquet | 1 | 152.962 |
| DuckDB | 1 | 9.515 |
| CSV | 4 | 166.694 |
| Parquet | 4 | 120.000 |
| DuckDB | 4 | 9.037 |

These are local warm-cache observations, including configured container/bind-mounted storage. Repeated fixtures compress unusually well. Do not generalize file-size ratios or assume four threads must be faster; the recorded values are retained even when parallel overhead loses.

Evidence: results/benchmark/timings.csv, comparison.png, six plans, partition_pruning_plan.txt and summary.json; saved experiment reports.

## Experiment 13 — explicit expectations and HTML

The versioned JSON suite defines required columns, null/blank checks, uniqueness, datatypes, numeric bounds, allowed values and cross-field business rules. **45/45 expectations passed** on the actual cleaned data. A separate intentionally damaged sample correctly failed **9 expectations**. Neither that sample nor its deliberately invalid values was loaded into the warehouse.

Both validations produce HTML with per-expectation results, counts, interpretation and example violations. Percentages refer to expectations, not records. The main suite is a load gate: failed clean data stops the flow before PostgreSQL loading. This is a custom Pandas suite; the syllabus asks for expectation-suite behavior, not a mandatory particular vendor library.

Evidence: quality/football_expectations.json; results/quality/validation_report.html; intentional_failure_report.html; saved experiment reports.

## Product and workflow

Start Docker Desktop, extract the ZIP, and double-click **Start.cmd**. Open http://127.0.0.1:8502. The main flow is:

**Extract → clean/profile → expectation gate → PostgreSQL → metric views → MongoDB → OLAP → lakehouse/dashboard → Delta feature lab → benchmark → streaming verification.**

The live event path remains API → RabbitMQ → validation → PostgreSQL staging → recent-event API. It does not automatically rewrite historical standings. Use `.\Start.ps1 -Action Stop` to stop the product while preserving database volumes.

Full instructions: WORKFLOW_GUIDE.md. All-15 map and additions: ALL_15_EXPERIMENTS.md. Demonstration commands: DEMO_COMMANDS.md. Detailed evidence: results/verification.json, completion_summary.json and the all15_*.log files.

## Boundaries

This is a local teaching platform with demonstration credentials. Historical fixtures cover 2018/19–2023/24. Ticket orders are generated data, benchmark rows are replays, player heatmaps are generated, and the event demonstration is not a licensed live football feed. Official league deductions/tie-breaks/qualification exceptions are not fully modeled. These domain limits are distinct from implementing the syllabus experiments.

The ZIP contains source, inputs and evidence. Docker images/volumes are not embedded; Start.cmd rebuilds/populates services on another computer and needs internet for initial downloads. Package versions are locked. Scheduled runs require Docker and the services to remain running.
