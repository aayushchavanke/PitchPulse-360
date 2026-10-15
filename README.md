# ⚽ PitchPulse 360: European Football Intelligence Lakehouse

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Delta Lake](https://img.shields.io/badge/Storage-Delta%20Lake-00A4EF.svg)](https://delta.io/)
[![DuckDB](https://img.shields.io/badge/Engine-DuckDB%20Columnar-FFF000.svg)](https://duckdb.org/)
[![FastAPI](https://img.shields.io/badge/Serving-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)

> **An enterprise Data Engineering Lakehouse analyzing 10,780+ matches across the Top 5 European Leagues over 6 seasons (2018/19 to 2023/24).**
> Fully compliant with all **6 Course Outcomes (CO1 to CO6)** and Lab Experiments for **AIDSC502 & AIDSL502**.

---

## 🌍 Leagues & Seasons Covered (10,780+ Matches)

| League | Country | League Code | Seasons Indexed | Total Matches |
| :--- | :--- | :--- | :--- | :--- |
| **Premier League** | England 🏴󠁧󠁢󠁥󠁮󠁧󠁿 | `E0` | 2018/19 – 2023/24 (6 Seasons) | **2,280** matches |
| **La Liga** | Spain 🇪🇸 | `SP1` | 2018/19 – 2023/24 (6 Seasons) | **2,280** matches |
| **Serie A** | Italy 🇮🇹 | `I1` | 2018/19 – 2023/24 (6 Seasons) | **2,280** matches |
| **Bundesliga** | Germany 🇩🇪 | `D1` | 2018/19 – 2023/24 (6 Seasons) | **1,836** matches |
| **Ligue 1** | France 🇫🇷 | `F1` | 2018/19 – 2023/24 (6 Seasons) | **2,105** matches |
| **TOTAL** | **Europe** 🇪🇺 | **Top 5** | **6 Complete Seasons** | **10,781 Matches** |

---

## 🎯 100% Syllabus Course Outcome (CO) Mapping

| Course Outcome | Syllabus Module | Practical Implementation in PitchPulse 360 | Code Artifacts |
| :--- | :--- | :--- | :--- |
| **CO1** | **Foundations & Quality** | Full Data Lifecycle documentation; Data Quality Suite checking score bounds ($0 \le \text{Goals} \le 20$), result integrity ($FTHG > FTAG \implies 'H'$), non-null checks across 10,781 records; automated HTML report. | [`quality/expectations_suite.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/quality/expectations_suite.py)<br>[`data/quality_audit_report.html`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/data/quality_audit_report.html) |
| **CO2** | **Storage & Lakehouse** | Medallion Architecture on **Delta Lake** (Bronze raw records $\to$ Silver clean & typed partitioned by `league_name` $\to$ Gold Standings). ACID transactions and **Delta Time Travel** demonstration. | [`storage/lakehouse_manager.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/storage/lakehouse_manager.py)<br>`data/lakehouse/` |
| **CO3** | **Ingestion & Lineage** | High-throughput batch ingestion of 30 league-seasons; comprehensive **Data Lineage Graph** tracing flow from football-data raw sources $\to$ Delta Bronze $\to$ Silver $\to$ Gold $\to$ DuckDB $\to$ UI. | [`ingestion/fetch_leagues.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/ingestion/fetch_leagues.py)<br>[`ingestion/lineage_tracker.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/ingestion/lineage_tracker.py) |
| **CO4** | **Orchestration & Modeling** | Kimball Dimensional **Star Schema** (`Fact_League_Matches`, `Dim_Teams`, `Dim_Leagues`, `Dim_Seasons`). SQL window functions (`RANK()`, `SUM() OVER`, points progression). Airflow DAG pipeline definition. | [`models/star_schema.sql`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/models/star_schema.sql)<br>[`models/analytical_views.sql`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/models/analytical_views.sql)<br>[`airflow/dags/football_pipeline_dag.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/airflow/dags/football_pipeline_dag.py) |
| **CO5** | **Distributed Processing** | Vectorized multi-threaded columnar processing using **DuckDB**; sub-second aggregation across 10,780+ records for points tables, goal differences, and head-to-head clash histories. | [`spark/duckdb_processor.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/spark/duckdb_processor.py)<br>[`spark/spark_transform.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/spark/spark_transform.py) |
| **CO6** | **Serving, Security & BI** | **FastAPI Data Product** with Role-Based Access Control (RBAC) and confidential club wage bill data masking; **Interactive Streamlit Dashboard** with dynamic Plotly visualizations. | [`serving/api.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/serving/api.py)<br>[`dashboard/app.py`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/dashboard/app.py) |

---

## 📊 Peak Interactive Dashboard Highlights

Launch via:
```bash
python -m streamlit run dashboard/app.py
```
Open **`http://localhost:8501`** to explore:

1. **🏆 Interactive League Standings & Title Races**:
   * Switch between Premier League, La Liga, Serie A, Bundesliga, and Ligue 1 across any season (2018/19 through 2023/24).
   * Color-coded verdict badges: 🏆 Champion, 🔵 Champions League (Top 4), 🟠 Europa League, 🔴 Relegation.
   * Horizontal bar points distribution & Attack vs Defense Goal Quadrant scatter chart.
2. **🔻 Relegation & 🔺 Promotion Dynamics**:
   * "The Survival Line" Chart: Compares the points needed by the 17th-placed survivor vs the highest relegated club across all 6 years.
   * Multi-Year Relegation Board: Complete history of every relegated team.
   * "Yo-Yo Clubs" Chart: Teams that fluctuated between divisions over the 6-year period.
3. **⚔️ Head-to-Head & Team Deep Dive**:
   * Select ANY two clubs in Europe (e.g., *Real Madrid vs Barcelona*, *Man City vs Liverpool*, *Bayern vs Dortmund*).
   * Win/Draw/Loss pie chart and match-by-match scoreline log with shots and dates.
   * 6-Year Club Trajectory line charts showing points and league table finish rank year-by-year.
4. **📊 All-Time European Records & Fun Stats**:
   * 10-Goal Thrillers (e.g. Barcelona 8–2 Huesca, Atalanta 8–2 Salernitana).
   * Home vs Away Win advantage comparison across England, Spain, Italy, Germany, France.
   * Roll of Honor: Every champion across Europe from 2018 to 2024.
5. **Tactical Telemetry & 2D Gaussian KDE Pitch Heatmaps**:
   * Continuous 2D bivariate Gaussian kernel density estimation (`scipy.stats.gaussian_kde`) over a standard $120 \times 80$ meter pitch.
   * Player action spatial coordinates (goals, shots, assists, key passes) with transparent vector pitch overlay.
   * Calibrated 5-attribute player radar charts (Finishing, Playmaking, Possession, Dribbling, Pressing).
6. **Dynamic Theme Engine (Light / Dark Mode)**:
   * Real-time CSS and Plotly token switcher between nocturnal broadcast dark (`#070d19`) and daylight slate (`#f8fafc`).
   * Deep emerald pitch grass turf (`#0a3a24`) and high-contrast vector pitch markings.
7. **Comprehensive Academic & Technical Reports**:
   * 13-page publication-grade PDF report: [`PitchPulse_360_Project_Report.pdf`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/PitchPulse_360_Project_Report.pdf)
   * GitHub Markdown technical report: [`PROJECT_REPORT.md`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/PROJECT_REPORT.md)
   * Automated Great Expectations HTML audit: [`data/quality_audit_report.html`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/data/quality_audit_report.html)

---

## 🚀 Quickstart Commands

### 🌟 1-Click Windows Batch Launchers:
* **Double-click [`run.bat`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/run.bat)**: An interactive command menu to run the pipeline, start the dashboard, launch the API, or run tests.
* **Double-click [`run_dashboard.bat`](file:///c:/Users/Aayush/Downloads/DE%20Miniproject/run_dashboard.bat)**: Instantly opens the Streamlit dashboard in your default browser.

### Or Run via Terminal:
```bash
# 1. Run the entire Lakehouse pipeline (executes in ~2 seconds):
python run_pipeline.py

# 2. Launch the Streamlit Interactive Dashboard:
python -m streamlit run dashboard/app.py

# 3. Launch the FastAPI Serving API:
python -m uvicorn serving.api:app --reload

# 4. Run automated test suite:
python -m unittest tests/test_pipeline.py
```
