"""Experiment 11: equal prepared data, six storage/thread modes, actual timings."""
import statistics
import time
from urllib.parse import quote
import duckdb
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .config import RESULTS,save_json

def run(clean_path,rows=250000,runs=5):
    base=pd.read_parquet(clean_path)[['league_name','season_code','total_goals','result','match_date']]
    if base.empty: raise ValueError('Benchmark needs clean matches')
    copies=(rows+len(base)-1)//len(base)
    data=pd.concat([base.assign(replay_copy=i) for i in range(copies)],ignore_index=True).head(rows)
    directory=RESULTS/'benchmark'; directory.mkdir(exist_ok=True)
    csv=directory/'replayed_matches.csv'; data.to_csv(csv,index=False)
    parquet=directory/'partitioned_parquet'; parquet.mkdir(exist_ok=True)
    for league,group in data.groupby('league_name'):
        partition=parquet/('league_name='+quote(league,safe='')); partition.mkdir(exist_ok=True)
        group.drop(columns='league_name').to_parquet(partition/'data.parquet',compression='zstd',index=False)
    conn=duckdb.connect(str(directory/'benchmark.duckdb'))
    conn.register('prepared',data)
    conn.execute('CREATE OR REPLACE TABLE benchmark_matches AS SELECT * FROM prepared')
    def path(p): return p.as_posix().replace("'","''")
    tables={'CSV':f"read_csv('{path(csv)}',header=true,all_varchar=true)",
      'Parquet':f"read_parquet('{path(parquet)}/**/*.parquet',hive_partitioning=true)",
      'DuckDB':'benchmark_matches'}
    def query(table):
        return f'''SELECT league_name,CAST(season_code AS VARCHAR) AS season_code,
        COUNT(*) AS matches,SUM(CAST(total_goals AS BIGINT)) AS goals
        FROM {table} GROUP BY 1,2 ORDER BY 1,2'''
    expected=conn.execute(query('benchmark_matches')).fetchall()
    results=[]
    for threads in [1,4]:
        conn.execute(f'SET threads={threads}')
        assert int(conn.execute("SELECT current_setting('threads')").fetchone()[0])==threads
        for storage,table in tables.items():
            sql=query(table)
            assert conn.execute(sql).fetchall()==expected,(storage,threads,'answers differ')
            conn.execute(sql).fetchall()  # Warm-up is excluded from timings.
            samples=[]
            for _ in range(runs):
                started=time.perf_counter(); output=conn.execute(sql).fetchall()
                samples.append((time.perf_counter()-started)*1000)
                assert output==expected
            (directory/f'{storage.lower()}_{threads}_threads_plan.txt').write_text(conn.execute('EXPLAIN ANALYZE '+sql).fetchone()[1])
            results.append(dict(storage=storage,threads=threads,median_ms=round(statistics.median(samples),3),
              min_ms=round(min(samples),3),max_ms=round(max(samples),3),runs=runs,answers_match=True))
    filtered=f"SELECT COUNT(*),SUM(total_goals) FROM {tables['Parquet']} WHERE league_name='Premier League'"
    assert conn.execute(filtered).fetchall()==conn.execute("SELECT COUNT(*),SUM(total_goals) FROM benchmark_matches WHERE league_name='Premier League'").fetchall()
    (directory/'partition_pruning_plan.txt').write_text(conn.execute('EXPLAIN ANALYZE '+filtered).fetchone()[1])
    conn.execute('CHECKPOINT'); conn.close()
    frame=pd.DataFrame(results); frame.to_csv(directory/'timings.csv',index=False)
    ax=frame.pivot(index='storage',columns='threads',values='median_ms').reindex(['CSV','Parquet','DuckDB']).plot.bar(figsize=(9,4),rot=0)
    ax.set_ylabel('Median query time (ms; lower is better)'); ax.set_title(f'{len(data):,} replayed football rows; identical prepared data')
    plt.tight_layout(); plt.savefig(directory/'comparison.png',dpi=150); plt.close()
    sizes=dict(csv_bytes=csv.stat().st_size,parquet_bytes=sum(p.stat().st_size for p in parquet.rglob('*.parquet')),
        duckdb_bytes=(directory/'benchmark.duckdb').stat().st_size)
    summary=dict(status='passed',source='Clean historical fixtures repeated for scaling, not additional real matches',
      original_matches=len(base),benchmark_rows=len(data),warmups=1,runs_per_mode=runs,modes=results,sizes=sizes,
      all_answers_match=True,filtered_parquet_matches_native=True,
      interpretation='One machine; 1/4 are DuckDB thread limits, not computers or a guarantee every query uses four workers. CSV, Parquet and native tables contain identical prepared rows. Warm-cache medians are local observations; four threads may be slower. Native database size includes database metadata.')
    save_json('benchmark/summary.json',summary)
    return summary
