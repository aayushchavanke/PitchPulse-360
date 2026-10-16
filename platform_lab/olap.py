"""Experiment 5: execute all three OLAP forms on both engines; compare outputs and plans."""
import time
import statistics
import duckdb
import pandas as pd
from .config import RESULTS, save_json
from .postgres import connect

GROUPS={'rollup':'ROLLUP(league_name,season_code)',
        'cube':'CUBE(league_name,season_code)',
        'grouping_sets':'GROUPING SETS ((league_name,season_code),(league_name),(season_code),())'}

def query(table,group):
    return f'''SELECT league_name,season_code,COUNT(*) AS matches,SUM(total_goals) AS goals,
      GROUPING(league_name) AS all_leagues,GROUPING(season_code) AS all_seasons
      FROM {table} GROUP BY {group}
      ORDER BY all_leagues,all_seasons,league_name,season_code'''

def run(clean_path):
    directory=RESULTS/'olap'; directory.mkdir(exist_ok=True)
    duck=duckdb.connect(str(RESULTS/'football.duckdb'))
    duck.execute('SET threads=4')
    frame=pd.read_parquet(clean_path)
    duck.register('incoming_matches',frame)
    duck.execute('CREATE OR REPLACE TABLE matches AS SELECT * FROM incoming_matches')
    reports={}
    with connect() as pg:
        for name,group in GROUPS.items():
            dq=query('matches',group); pq=query('analytics.match_facts',group)
            result=duck.execute(dq).df()
            with pg.cursor() as cur:
                cur.execute(pq)
                pg_rows=cur.fetchall()
                other=pd.DataFrame(pg_rows,columns=[d.name for d in cur.description])
            pd.testing.assert_frame_equal(result,other,check_dtype=False)
            grand=result[(result.all_leagues==1)&(result.all_seasons==1)].iloc[0]
            assert int(grand.matches)==len(frame) and int(grand.goals)==int(frame.total_goals.sum())
            result.to_csv(directory/(name+'.csv'),index=False)
            (directory/(name+'_duckdb_plan.txt')).write_text(duck.execute('EXPLAIN ANALYZE '+dq).fetchone()[1],encoding='utf-8')
            plan=pg.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+pq).fetchone()[0]
            save_json('olap/'+name+'_postgres_plan.json',plan)
            # Warm both queries; report medians from five runs, not one lucky measurement.
            times={}
            for engine,func in [('DuckDB',lambda:duck.execute(dq).fetchall()),('PostgreSQL',lambda:pg.execute(pq).fetchall())]:
                func(); samples=[]
                for _ in range(5):
                    start=time.perf_counter(); func(); samples.append(1000*(time.perf_counter()-start))
                times[engine]=dict(median_ms=round(statistics.median(samples),3),runs=5)
            reports[name]=dict(rows=len(result),grand_total_matches=int(grand.matches),
                grand_total_goals=int(grand.goals),engines_match=True,timing=times,
                postgres_execution_ms=plan[0]['Execution Time'])
    duck.close()
    save_json('olap/comparison.json',reports)
    return reports
