"""Experiments 2/3: real PostgreSQL schema, transactional ETL, windows and plans."""
import json
import uuid
import pandas as pd
import psycopg
from psycopg import sql
from .config import PG_DSN, ROOT, RESULTS, save_json

def connect():
    return psycopg.connect(PG_DSN,connect_timeout=10)

def initialize(con):
    con.execute((ROOT/'models/postgres_schema.sql').read_text(encoding='utf-8'))
    for code in ['1819','1920','2021','2122','2223','2324']:
        con.execute(sql.SQL('CREATE TABLE IF NOT EXISTS analytics.{} PARTITION OF analytics.match_facts FOR VALUES IN ({})').format(
            sql.Identifier('match_facts_'+code),sql.Literal(code)))

def native(value):
    if pd.isna(value): return None
    if isinstance(value,pd.Timestamp): return value.date()
    if hasattr(value,'item'): return value.item()
    return value

def load(clean_path):
    df=pd.read_parquet(clean_path)
    columns=['match_id','match_date','home_team','away_team','home_goals','away_goals','result',
        'home_shots','away_shots','home_shots_target','away_shots_target','home_yellows',
        'away_yellows','home_reds','away_reds','league_name','country','season','season_code','source_file','source_row']
    with connect() as con:
        initialize(con)
        # Shared with the consumer: only one batch may replace warehouse facts at a time.
        con.execute('SELECT pg_advisory_xact_lock(3602026)')
        con.execute('CREATE TEMP TABLE incoming ('+','.join(f'{c} '+('INTEGER' if c in columns[4:6]+columns[7:15]+['source_row'] else 'DATE' if c=='match_date' else 'TEXT') for c in columns)+') ON COMMIT DROP')
        with con.cursor().copy('COPY incoming ('+','.join(columns)+') FROM STDIN') as copy:
            for row in df[columns].itertuples(index=False,name=None): copy.write_row(tuple(native(v) for v in row))
        statements=[
          'INSERT INTO football.countries(country_name) SELECT DISTINCT country FROM incoming ON CONFLICT DO NOTHING',
          'INSERT INTO football.leagues(league_name,country_id) SELECT DISTINCT i.league_name,c.country_id FROM incoming i JOIN football.countries c ON c.country_name=i.country ON CONFLICT DO NOTHING',
          'INSERT INTO football.seasons(season_code,season_label) SELECT DISTINCT season_code,season FROM incoming ON CONFLICT DO NOTHING',
          'INSERT INTO football.league_seasons(league_id,season_id) SELECT DISTINCT l.league_id,s.season_id FROM incoming i JOIN football.leagues l USING(league_name) JOIN football.seasons s USING(season_code) ON CONFLICT DO NOTHING',
          'INSERT INTO football.teams(team_name) SELECT home_team FROM incoming UNION SELECT away_team FROM incoming ON CONFLICT DO NOTHING',
        ]
        for statement in statements: con.execute(statement)
        # Full snapshot replacement is atomic. Event staging remains independent.
        con.execute('DELETE FROM football.matches')
        con.execute('''INSERT INTO football.matches
          SELECT i.match_id,ls.league_season_id,i.match_date,ht.team_id,at.team_id,
            i.home_goals,i.away_goals,i.home_shots,i.away_shots,
            i.home_shots_target,i.away_shots_target,i.home_yellows,i.away_yellows,
            i.home_reds,i.away_reds,i.source_file,i.source_row
          FROM incoming i JOIN football.leagues l USING(league_name)
          JOIN football.seasons s USING(season_code)
          JOIN football.league_seasons ls USING(league_id,season_id)
          JOIN football.teams ht ON ht.team_name=i.home_team
          JOIN football.teams at ON at.team_name=i.away_team''')
        con.execute('DELETE FROM analytics.match_facts')
        con.execute('INSERT INTO analytics.match_facts SELECT match_id,season_code,match_date,league_name,result,total_goals FROM analytics.match_enriched')
        rejected=len(pd.read_csv(RESULTS/'rejected_matches.csv'))
        con.execute('INSERT INTO football.etl_runs(run_id,accepted_rows,rejected_rows) VALUES(%s,%s,%s)',(str(uuid.uuid4()),len(df),rejected))
        count=con.execute('SELECT count(*) FROM football.matches').fetchone()[0]
        if count!=len(df): raise AssertionError('PostgreSQL count mismatch')
    return dict(matches=count,rejected_rows=rejected)

def export_query(con,name,query):
    with con.cursor() as cur:
        cur.execute(query)
        frame=pd.DataFrame(cur.fetchall(),columns=[d.name for d in cur.description])
    directory=RESULTS/'postgres'; directory.mkdir(exist_ok=True)
    frame.to_csv(directory/(name+'.csv'),index=False)
    return len(frame)

def analyze():
    with connect() as con:
        con.execute('ANALYZE football.matches'); con.execute('ANALYZE analytics.match_facts')
        count=export_query(con,'team_season_rank','SELECT * FROM analytics.team_season_rank ORDER BY league_name,season,rank,team')
        export_query(con,'season_progression','''SELECT *,
          LAG(points) OVER(PARTITION BY league_name,team ORDER BY season) AS previous_season_points,
          LEAD(points) OVER(PARTITION BY league_name,team ORDER BY season) AS next_season_points
          FROM analytics.team_season_rank ORDER BY league_name,team,season''')
        export_query(con,'cumulative_points','''SELECT *, SUM(points) OVER(
          PARTITION BY league_name,season,team ORDER BY match_date,match_id
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_points
          FROM analytics.team_match_points ORDER BY league_name,season,team,match_date,match_id''')
        date_query="SELECT * FROM football.matches WHERE match_date=DATE '2024-05-19'"
        plan=con.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+date_query).fetchone()[0]
        # Transaction-local planner toggles are teaching comparisons; never claim a forced scan is faster.
        con.execute('SET LOCAL enable_indexscan=off'); con.execute('SET LOCAL enable_bitmapscan=off')
        sequential=con.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+date_query).fetchone()[0]
        con.execute('SET LOCAL enable_indexscan=on'); con.execute('SET LOCAL enable_bitmapscan=on')
        partition=con.execute("EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT sum(total_goals) FROM analytics.match_facts WHERE season_code='2324'").fetchone()[0]
        all_partitions=con.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT sum(total_goals) FROM analytics.match_facts').fetchone()[0]
        save_json('postgres/index_and_partition_plans.json',dict(normal_index_plan=plan,forced_sequential_plan=sequential,
            filtered_partition_plan=partition,all_partitions_plan=all_partitions))
        stats=dict(matches=con.execute('SELECT count(*) FROM football.matches').fetchone()[0],
          goals=con.execute('SELECT sum(home_goals+away_goals) FROM football.matches').fetchone()[0],
          teams=con.execute('SELECT count(*) FROM football.teams').fetchone()[0],team_seasons=count,
          partitions=con.execute("SELECT count(*) FROM pg_inherits WHERE inhparent='analytics.match_facts'::regclass").fetchone()[0])
    save_json('postgres/summary.json',stats)
    return stats
