# PitchPulse360: the complete walkthrough

A plain-language explanation of the current football project. The presentation has 11 slides: an introduction, nine content slides and a thank-you slide. The PowerPoint includes detailed speaker notes. Counts below describe the supplied saved run, rather than a fresh pipeline execution for this presentation.

## 1. The project in one sentence

PitchPulse360 takes football match files, checks whether the numbers make sense, puts the useful data into organized storage, and lets you explore it through a dashboard and an API. It also demonstrates the engineering around that journey: automated runs, database relationships, reusable SQL, event queues, version history and performance measurements.

Think of a match as one entry in a football notebook. The original notebook contains the date, the two teams, goals, shots and cards. The project makes several useful copies: an original copy for inspection, a clean copy for calculations, and a smaller summary containing each team's season totals. Each copy has a specific purpose.

The supplied history contains 10,781 matches across five leagues and six seasons, from 2018/2019 through 2023/2024. The leagues are the Premier League, La Liga, Serie A, Bundesliga and Ligue 1. Five leagues multiplied by six seasons gives 30 input files. The saved warehouse result contains 140 distinct team names, 586 team-season records and 30,186 goals.

Those are the counts in the project's saved execution evidence. They describe the included files. They do not mean the application contains every football match ever played, every competition, or current live results.

## 2. The two routes through the platform

There are two connected but separate routes.

The batch route processes a collection of historical files. It reads all 30 files, cleans them, applies the quality checklist, loads PostgreSQL, creates metric views, preserves raw records in MongoDB, compares analytical SQL, builds the Delta layers, runs the Delta feature experiment, measures the local benchmark and checks streaming behavior. Prefect controls this ordered run. The dashboard reads the prepared lakehouse tables.

The event route handles one JSON message at a time. A client submits an event to FastAPI. FastAPI validates it and publishes it to RabbitMQ. A consumer reads the queued message, validates it again and commits it to a PostgreSQL staging table. GET /lab/events lets a client inspect recent staged events.

Staging is a waiting area. An accepted event does not automatically become a historical match in the warehouse or change the league table. A later promotion step would need to resolve whether the event is a new match, a correction or a duplicate of an existing match. That promotion step is a useful future improvement, rather than a behavior the current application already provides.

Docker Compose starts the services together. PostgreSQL, MongoDB, RabbitMQ and Prefect provide the supporting services. The API, dashboard, scheduler and consumer run as separate application services. Keeping them separate makes it easier to restart the dashboard without resetting the databases.

## 3. Reading and identifying the source data

The active extractor lives in platform_lab/cleaning.py and calls the file-reading function in ingestion/fetch_leagues.py. The reader first checks data/raw_leagues for a usable cached CSV. If a file is missing, it attempts to download that league-season file from football-data.co.uk. A full active run fails if any required league-season is empty. It does not quietly report success with reduced coverage.

Extraction selects a common set of fields and gives them readable names. For example, FTHG becomes home_goals, FTAG becomes away_goals and FTR becomes result. It adds the league, country, season label and season code. It also records the original filename and source row number. These last two fields are provenance: they let you trace a suspicious output back to the exact input record.

The original selected rows go into results/raw_snapshot.parquet. Parquet is a file format that stores values by column. That makes it useful when an analysis needs only a few columns from a large table. This snapshot preserves the selected source fields before cleaning. MongoDB later receives this raw snapshot, rather than the repaired clean table.

The reader has caching, but the current full pipeline still rebuilds a complete prepared snapshot. It does not use an incremental checkpoint to process only newly arrived matches. Keeping that distinction clear explains why reruns are safe but still repeat work.

## 4. Cleaning the data without inventing football facts

Cleaning first removes extra spaces from team and league names. It normalizes a few known aliases, such as Bayern to Bayern Munich. It parses dates using day-first interpretation and turns numeric fields into actual numbers. Nullable integer types let an unknown shot count remain unknown while still keeping the column numeric.

Essential fields need to be usable. A match needs a date, distinct teams, a league and season, and valid goal counts. Impossible goals, missing essential values and duplicate fixture keys receive rejection reasons. The pipeline writes rejected rows to a separate CSV instead of quietly mixing them into the accepted table.

Optional measurements receive more cautious treatment. A missing shot count does not make a score unusable. Invalid optional numbers become unknown and receive an audit note. The program also checks that shots on target cannot exceed total shots. Filling an unknown count with zero would claim that no shots happened, so the cleaner deliberately avoids that shortcut.

There is a real example in this dataset: Newcastle lost 2–4 to West Ham on 15 August 2021. The source row says West Ham had 8 shots and 9 shots on target. That combination is impossible. The cleaner keeps the score, which is internally valid, and clears both away-shot measurements. results/repaired_measurements.csv records the reason. The saved run repaired one row's optional measurements and rejected zero complete matches.

Cleaning also derives useful fields. total_goals is home_goals plus away_goals. A home win gives the home team 3 points and the away team 0. A draw gives each team 1. goal_diff is the home goals minus away goals. The result code is reconstructed from valid scores. A deterministic 24-character hash identifies each fixture using its league, season, date and team names. The same fixture receives the same ID on another run.

Unusual values need a separate decision from impossible values. The project flags matches with more than 7 total goals using an interquartile-range rule. It retains 69 such matches because a high-scoring result can be real. The EDA report shows distributions, missing values, data types and before/after counts. This implements experiment 1.

## 5. The quality gate

Cleaning makes repairs. Validation asks whether the resulting table meets an explicit contract. Experiment 13 stores that contract in quality/football_expectations.json. A custom Pandas validator reads it and checks required columns, nulls, types, ranges, allowed values, uniqueness and football consistency.

Examples include a unique match_id, a real date, integer goals between 0 and 20, an allowed H/D/A result and different home and away teams. Business checks confirm that the result agrees with the score and that target shots do not exceed total shots. Optional measurement nulls are allowed because the cleaning policy deliberately preserves uncertainty.

The saved clean dataset passes all 45 checks. A separate damaged sample triggers 9 failed expectations, proving that the validator can detect mistakes. Nine failed expectations do not necessarily mean nine bad rows, because one bad row can break several rules. The damaged sample never goes into the historical warehouse.

If the clean table fails, the flow raises an error before PostgreSQL loading. HTML reports show passed and failed checks with explanations and examples. This is a custom expectation-suite implementation. The project does not depend on the Great Expectations library.

This checklist covers the rules that were written. It cannot establish that every source fact is true. A wrong but plausible score could pass these checks. Independent source reconciliation would strengthen that part of the project.

## 6. The PostgreSQL model and ETL

PostgreSQL is the relational warehouse. Relational means the information lives in connected tables with rules about which rows may refer to other rows. The football schema contains countries, leagues, seasons, league_seasons, teams and matches.

The country name lives in countries. A league refers to a country. A season describes a year pair. league_seasons connects a league to a season. A team has a reusable ID. Each match refers to a league-season and two team IDs. This avoids repeating every descriptive fact in every match row. It demonstrates normalization through third normal form for the core football tables.

A primary key identifies one row. A foreign key points to an existing row in another table. A UNIQUE constraint prevents a repeated fixture combination. CHECK constraints reject values such as negative goals or the same home and away team. Database rules provide another layer of protection after the Pandas validation.

The loader reads clean_matches.parquet, opens a transaction and acquires a PostgreSQL advisory lock. It uses COPY to transfer rows efficiently into a temporary incoming table. It inserts missing dimension values, joins their IDs to the incoming records and refreshes the match snapshot. It also refreshes a separate analytical fact table and records an ETL audit row.

A transaction groups the database work into one unit. If a step fails before commit, PostgreSQL rolls back that transaction. The warehouse avoids exposing a half-loaded batch. The whole multi-service pipeline is not one shared transaction, however. A later MongoDB or Delta failure does not undo an already committed PostgreSQL load.

This loader replaces the historical snapshot rather than appending the same matches again. Stable fixture IDs and unique keys help make repeated runs safe. The staging tables remain separate. The saved result is 10,781 matches and 30,186 goals.

For analytical work, analytics.match_facts deliberately repeats some labels and partitions rows into six season groups. This denormalized table serves a different purpose from the normalized core: convenient scans and partition demonstrations. Indexes on date, home team/date and league-season help selected lookups. PostgreSQL still chooses whether an index is worthwhile. EXPLAIN ANALYZE records the actual plan, including filtered partition scans. These functions implement experiments 2 and 3.

## 7. Reusable SQL, metrics and OLAP

A SQL view is a saved query. The project defines a useful question once and gives it a name, so the dashboard and analysts can reuse the same calculation. An ordinary view does not store a finished result by itself, so creating a view does not automatically make a query faster.

Football views reconstruct enriched match records, create one points row per team per match and calculate team-season rankings. DENSE_RANK assigns equal ranks to equal ordered values. LAG and LEAD retrieve the previous and next available season values for a team. A running SUM accumulates points in match order. A team's previous available season can be several calendar seasons earlier if it was absent from this dataset in between.

Experiment 4 also implements the syllabus's exact business measures. Since historical match files have no real sales data, the project creates 6,000 clearly labeled synthetic ticket orders linked to real fixture IDs. Daily revenue sums paid quantity multiplied by price. Refunded orders contribute no realized revenue. Monthly growth compares the current calendar month's revenue with the previous month and includes months with zero sales. Growth is unknown when no meaningful previous denominator exists. Repeat-customer percentage counts customers with more than one paid order out of customers with at least one paid order. The saved synthetic example gives 46.4%, which says nothing about real club customers.

For each metric, a view query and a direct SQL query must return equal answers. The program also saves their timings and plans. The point is consistent definitions and measured behavior, rather than a promise that a view wins a speed race.

OLAP means examining summaries from different angles. Here the dimensions are league and season, while the measures are match count and total goals. GROUP BY gives detailed league-season totals. ROLLUP adds each league's subtotal and the overall total. CUBE also adds season totals across all leagues. GROUPING SETS requests the exact grouping combinations the programmer wants. GROUPING flags distinguish a subtotal marker from an ordinary missing value.

The same queries run in PostgreSQL and DuckDB. Their results must match. In the saved run, ROLLUP returns 36 rows: 30 league-season combinations, 5 league subtotals and 1 grand total. CUBE and the chosen GROUPING SETS each return 42 rows by adding 6 season subtotals. The grand total remains 10,781 matches and 30,186 goals. These operations implement experiment 5.

## 8. Delta Lake and the three prepared layers

The project also keeps a lakehouse: file-based analytical tables with versioned metadata. Delta Lake uses Parquet data files plus a transaction log that records table changes. Pandas supplies the dataframes, and the local deltalake library writes and reads the tables. The application does not need a Spark cluster for these operations.

Bronze stores the selected raw snapshot. Silver stores cleaned matches with derived points and processing metadata. Gold stores one summary per team, league and season. Gold combines each team's home and away appearances, calculates played/won/drawn/lost, goals for, goals against, goal difference and points, and then sorts the table. The simple points formula is 3 multiplied by wins plus draws. Sorting uses points, goal difference and goals scored.

The dashboard reads Silver and Gold Delta tables into Pandas, then registers dataframes with DuckDB for analysis. It does not fetch every chart directly from PostgreSQL. PostgreSQL and the lakehouse are separate prepared outputs of the same batch. The dashboard's data-loading cache has a 60-second TTL, so the browser can briefly show a previous snapshot after a rebuild until the cache expires and the page reruns.

Experiment 8 uses a separate tiny Delta table so the historical data stays intact. Version 0 starts with two rows. Version 1 appends a third. Version 2 changes one goal value from 2 to 3. Version 3 deletes another row. Reading version 0 still returns the original two rows. That operation demonstrates time travel: opening the table as it looked before later edits.

The demonstration then attempts a write with incompatible columns and another with an invalid value type. Both fail, and the table version stays unchanged. The rejected writes prove that these incompatible writes could not commit. They do not prove every possible write mode will reject schema changes: the pipeline deliberately uses schema-overwrite settings for its full snapshot rebuilds. Gold's qualification and relegation labels also use simplified rules rather than every league's official exceptions.

## 9. The local performance experiment

Experiment 11 prepares 250,000 rows by repeating cleaned historical fixtures. It stores the same prepared rows as CSV, partitioned compressed Parquet and a native DuckDB table. These are 250,000 benchmark rows, not 250,000 newly observed football matches.

DuckDB runs the workload with thread limits of 1 and 4. This creates six combinations: three storage formats multiplied by two thread settings. Each mode receives one warm-up and five measured executions. The report records the median, minimum and maximum time. It accepts a timing only when the query answer matches the comparison answer. A filtered Parquet query also checks partition pruning against the native table's answer.

In the saved local run, CSV medians were 167.156 ms with one thread and 166.694 ms with four. Parquet medians were 152.962 ms and 120.000 ms. Native DuckDB medians were 9.515 ms and 9.037 ms. These are observations from the supplied local environment and workload, including its storage path and warm cache. They do not establish a universal ranking of database products or prove that four workers always execute or always improve a query.

Columnar formats can avoid reading irrelevant columns, and partitions can avoid reading irrelevant groups of files. A native database can also reuse its storage organization. Repeated fixture rows compress especially well, so the unusually small Parquet file is not a realistic prediction for independent new match data. This experiment demonstrates parallel local processing on one machine, rather than a distributed Spark/Hadoop deployment.

## 10. MongoDB and flexible documents

MongoDB stores documents with nested fields. It is useful when an incoming record or a scout report does not fit one rigid table shape. In this project, raw_matches preserves the selected source snapshot, including suspect original shot measurements. The clean PostgreSQL copy can therefore differ from the raw document without losing the original evidence.

The sync uses a source-file and source-row identity to upsert records. Upsert means update the document when that identity already exists, otherwise insert it. This keeps repeated syncs from creating another copy of the same source row. The saved run contains 10,781 raw match documents.

A separate scout_reports collection demonstrates CRUD. Create inserts a report with nested notes and tags. Read filters it and returns only selected fields, called a projection. Update changes its rating and nested review information and adds a tag. Delete removes the demonstration report and checks that it is gone. The example does not delete the historical match collection.

Compound indexes organize lookup keys such as league plus season or home team plus date. The program saves a MongoDB query plan so you can examine the selected access path. An index existing is different from the optimizer actually using it. Together, these functions implement experiment 7.

## 11. FastAPI, RabbitMQ and safe event handling

FastAPI provides a structured door into the application. GET endpoints return information. POST /lab/events accepts a match-event JSON body. Pydantic validates the required fields, date, strict integer goal counts, allowed result code and cross-field consistency. Extra unexpected fields are forbidden. Invalid API input returns 422 before the producer sends anything to RabbitMQ.

A valid producer sends a persistent message to a durable RabbitMQ queue and requests broker confirmation. The API returns 202 Accepted after publication is confirmed. Accepted means the queue received it. It does not promise that the consumer has already stored it. If RabbitMQ cannot confirm publication, the API returns a service-unavailable response instead of claiming success.

The consumer reads queued messages and validates them again. That second check matters because a different producer could bypass the API. It inserts valid payloads into staging.match_events using event_id as the primary key. An ON CONFLICT rule ignores another delivery with the same ID. The same match with a new event ID is still a different staged event, so event deduplication is not full match reconciliation.

The consumer acknowledges a valid message only after the database transaction commits. If the database is unavailable, it negatively acknowledges and requeues the delivery. Suppose the database commits and the process crashes before ACK. RabbitMQ can deliver that message again. The unique event ID stops it from creating another valid staging row. This is at-least-once delivery with an idempotent write.

Invalid payloads receive a recorded rejection reason and go to a separate durable rejected queue. The consumer acknowledges the original only after that handling succeeds. A crash during rejection handling may repeat audit evidence, so the project does not claim exactly-once processing for every side effect.

The saved full workflow publishes 20 valid events, one duplicate and one malformed payload. It checks 20 unique staged events, an ignored retry and a recorded rejection. These events replay included historical records. They are not a licensed live football feed. Some standalone integration tests run a smaller three-event case and overwrite the single-experiment demo file, so the full-run report is the appropriate source for the 20-event claim.

The original read API also provides standings, champions and team trajectories through DuckDB and Gold. A small role/masking endpoint illustrates how some fields can be hidden. Its example finance figures and hardcoded role keys are classroom demonstrations. These API and queue functions implement experiments 9 and 10.

## 12. Prefect, scheduling and recovery

Prefect is the conductor for the batch route. The active flow contains eleven tasks in this order: extract, clean/profile, expectation validation, PostgreSQL load and analysis, metric views, MongoDB sync and CRUD, OLAP comparison, lakehouse/dashboard preparation, Delta feature demonstration, local benchmark and streaming verification.

The code invokes these tasks in sequence. Several tasks have retries for temporary failures. Extraction and PostgreSQL/MongoDB tasks retry twice, cleaning and several demonstrations retry once, and a failed clean-data expectation gate has no retry. A permanent error eventually fails the flow and appears in the logs.

The scheduler registers football-hourly with a default 3,600-second interval. The deployment allows one concurrent run. A shared filesystem lock also prevents a manual run and a scheduled run from replacing the same output files simultaneously. PostgreSQL uses a transaction advisory lock around its snapshot load. These controls prevent different kinds of overlap, rather than making all storage systems one atomic transaction.

The project checked an actual completed scheduled run through the Prefect API and found all eleven tasks completed. This is stronger evidence than merely having a deployment configuration file. Scheduled work still requires Docker, the scheduler and the other services to remain running. Turning the computer off stops local processing.

The batch writes last_run.json and per-experiment reports. Verification reconciles database counts, checks SQL-engine equality, confirms the queue behavior and queries Prefect for the real run/task states. The recorded test suite has 30 passing tests. UI smoke checks exercise both dashboard pages, including league/season and metric selections. The recent appearance fix also checked actual rendered light and dark widgets in the browser. These mechanisms support experiments 12, 14 and 15.

## 13. What each dashboard page actually does

The main dashboard is a Streamlit application. A league selector and season selector choose the slice of data. The appearance setting comes from Streamlit's top-right menu, Settings, Theme. This single native control keeps canvas tables, dropdowns, chart text and custom metric cards consistent in light and dark mode.

Standings and title race shows the calculated league table and points distribution. A scatter plot compares goals scored with goals conceded. A team with more points receives a larger bubble. These calculations reflect the included score records. Official point deductions and every league's tie-break or qualification exception are not fully modeled.

Player analytics combines 34 manually entered player profiles with 5,741 generated spatial actions in the saved run. A Gaussian KDE heatmap spreads individual generated action locations into a smooth density surface. A brighter region means more generated actions occurred near that area. Filters can separate types such as shots and goals. The radar chart rescales selected summary measures into bounded profile scores. Those scores are project-defined visual indices, rather than official player ratings. The visual is a demonstration of the method, not evidence of measured player movement.

Relegation dynamics compares lower-table points and a simplified survival line. The bottom-three rule is an approximation and does not model every league's changing formats or playoffs. Head-to-head selects two clubs and summarizes their included domestic league meetings. It also shows season point/rank trajectories. All-time records actually covers records within the six included seasons. It should be read as records within this dataset.

The Engineering Lab page has ten tabs: Explore & clean, PostgreSQL, OLAP, MongoDB CRUD, Streaming, Workflow, Metric views, Delta history, Parallel benchmark and Quality suite. It lets you show the engineering evidence behind the football charts. This is experiment 6's dashboard and experiment 15's combined platform interface.

## 14. How to run and demonstrate the project

From the extracted project folder, Start.cmd launches the PowerShell helper. Its Start action builds the application image, starts and checks the supporting services, executes the complete flow, verifies it, and starts the application services. On another computer, the first build needs internet to download dependencies and images. The ZIP includes source, data and evidence, rather than a complete Docker installation or running database volumes.

Useful commands from the project folder:

```powershell
.\Start.ps1 -Action Start
.\Start.ps1 -Action Run
.\Start.ps1 -Action Test
.\Start.ps1 -Action Stop
```

Start brings up and initializes the product. Run repeats the full batch and verification. Test executes the project's tests. Stop shuts down services while preserving database volumes. The ports are dashboard 8502, API 8002, Prefect 4201 and RabbitMQ management 15673. These are local teaching services.

A sensible classroom demonstration starts with the dashboard's league/season filters. Then open Engineering Lab and show the real repaired shot record and the quality report. Show a PostgreSQL ranking query and the equal PostgreSQL/DuckDB OLAP totals. Read Delta version 0 after showing its later edits. In the API docs, submit an event and show it in staging, then submit the same event ID and explain why no second valid row appears. Finish with the Prefect run and the benchmark's equal-result checks.

Use http://127.0.0.1:8502 for the dashboard, http://127.0.0.1:8002/docs for the API documentation, http://127.0.0.1:4201 for Prefect and http://127.0.0.1:15673 for RabbitMQ's management interface. They work when the services are running on this computer.

## 15. What the project proves and what to improve next

The existing evidence shows the connected local teaching platform works for its included workload: PostgreSQL and MongoDB reconcile to the source, SQL-engine answers agree, all clean expectations pass, the malformed sample triggers failures, old Delta data remains readable, incompatible writes fail, the six benchmark modes agree and the Prefect run completes eleven tasks.

The most useful next improvement is football correctness. Add season-specific point deductions, league-specific tie-breaks, changing relegation rules and qualification exceptions. A polished dashboard becomes more trustworthy when the rules match the official competition.

Next, replace generated player actions with a licensed observed event dataset if the goal is genuine player analysis. Keep a clear source label on every player chart. Replace synthetic ticket sales with authorized real order data only if a real revenue use case exists.

For ingestion, add an explicit event-to-warehouse promotion step with match reconciliation, correction handling and an audit history. Add incremental file checkpoints so an ordinary scheduled run handles changes without rebuilding the whole snapshot. Publish completed batch outputs together or attach a shared batch ID so the dashboard can avoid mixed versions during a partial multi-store failure.

For reliability, add bounded retry/backoff and alerting for repeated queue failures, plus monitoring for backlog size and stale dashboards. For deployment, move demonstration keys and passwords into managed secrets, add real authentication, TLS, backups and recovery checks. Those are future deployment improvements, not claims that the current local teaching stack already implements them.

For measurements, repeat benchmarks on larger, less repetitive data and report hardware, cold/warm cache conditions and storage paths. Keep equal-result assertions before interpreting performance. Add stronger regression cases for corrected league rules and a browser check that catches theme regressions.

## Where all 15 experiments appear

| Experiment | Functionality | Presentation slide |
|---|---|---|
| 1 | Data exploration and audited cleaning | 3 |
| 2 | Normalized relational model and SQL analysis | 4 |
| 3 | CSV to PostgreSQL ETL | 4 |
| 4 | Reusable business and football metric views | 5 |
| 5 | ROLLUP, CUBE and GROUPING SETS | 5 |
| 6 | Football dashboard and evidence pages | 9 |
| 7 | MongoDB documents, CRUD and indexes | 7 |
| 8 | Delta versions, time travel and incompatible-write checks | 6 |
| 9 | FastAPI POST/GET and JSON validation | 7 |
| 10 | RabbitMQ producer, consumer and PostgreSQL staging | 7 |
| 11 | Local DuckDB processing and format/thread benchmark | 6 |
| 12 | Prefect orchestration and hourly schedule | 8 |
| 13 | Declarative expectation suite and failure reports | 3 |
| 14 | Connected batch with logging and prepared outputs | 2, 8 |
| 15 | Combined platform and verified outcomes | 2, 10 |


## Important implementation files

The orchestration entry point is `platform_lab/flow.py`. `platform_lab/cleaning.py` performs active extraction and cleaning. `models/postgres_schema.sql` defines the relational model, and `platform_lab/postgres.py` loads and analyzes it. `models/metric_views.sql` defines metric formulas. The remaining labs live in `platform_lab/olap.py`, `mongo.py`, `streaming.py`, `delta_experiment.py`, `benchmark.py` and `expectations.py`.

`storage/lakehouse_manager.py` prepares Bronze, Silver and Gold. `dashboard/app.py` reads the lakehouse for the football interface. `dashboard/pages/Engineering_Lab.py` presents engineering evidence. `serving/api.py` contains the original read API, while `platform_lab/api.py` adds event capture and experiment reports. `compose.yaml` and `Start.ps1` wire the local product together.

The core evidence is in `results/last_run.json`, `results/verification.json`, `results/completion_summary.json` and the per-experiment results folders. The guide explains the inspected implementation and saved results. The original archive also contains historical examples and reports that should not override these active entry points.
