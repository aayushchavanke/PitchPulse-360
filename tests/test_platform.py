"""Meaningful defect, constraint and broker-path tests for requested experiments."""
import json
from pathlib import Path
import pandas as pd
import pytest
from platform_lab.cleaning import clean_frame
from platform_lab.streaming import MatchEvent,persist,demo
from platform_lab.postgres import connect
from platform_lab.config import RESULTS

def fixture(**changes):
    record=dict(match_date='19/05/2024',home_team=' Arsenal  ',away_team='Chelsea',
      home_goals='2',away_goals='1',result='A',home_shots='10',home_shots_target='4',
      away_shots='8',away_shots_target='2',league_name='Premier League',country='England',
      season='2023/2024',season_code='2324',source_file='test.csv',source_row=2)
    return {**record,**changes}

def test_cleaning_repairs_types_result_and_deduplicates():
    clean,bad,repairs=clean_frame(pd.DataFrame([fixture(),fixture()]))
    assert len(clean)==1 and len(bad)==1 and repairs==2
    assert clean.iloc[0].home_team=='Arsenal' and clean.iloc[0].result=='H'
    assert clean.iloc[0].match_date==pd.Timestamp('2024-05-19')
    assert 'duplicate fixture' in bad.iloc[0].rejection_reason

@pytest.mark.parametrize('changes',[
    {'home_goals':-1},{'match_date':'nonsense'},
    {'home_goals':1.5},{'away_team':'Arsenal'},{'home_team':None}])
def test_invalid_values_are_rejected(changes):
    clean,bad,_=clean_frame(pd.DataFrame([fixture(**changes)]))
    assert clean.empty and len(bad)==1

def test_missing_optional_measurement_stays_unknown():
    clean,_,_=clean_frame(pd.DataFrame([fixture(home_shots=None,home_shots_target=None)]))
    assert pd.isna(clean.iloc[0].home_shots)

def test_inconsistent_optional_shots_are_audited_and_cleared():
    clean,bad,_=clean_frame(pd.DataFrame([fixture(away_shots=8,away_shots_target=9)]))
    assert len(clean)==1 and bad.empty
    assert pd.isna(clean.iloc[0].away_shots) and pd.isna(clean.iloc[0].away_shots_target)
    assert 'away target shots exceed shots' in clean.iloc[0].measurement_repair_notes

def test_valid_high_score_is_retained():
    clean,bad,_=clean_frame(pd.DataFrame([fixture(home_goals=8,away_goals=2)]))
    assert len(clean)==1 and bad.empty

def test_real_postgres_counts_and_constraints():
    import psycopg
    with connect() as pg:
        assert pg.execute('SELECT count(*) FROM football.matches').fetchone()[0]==10781
        row=pg.execute('SELECT * FROM football.matches LIMIT 1').fetchone()
        # Bad mutation must fail a real database CHECK, then roll back the savepoint.
        with pytest.raises(psycopg.errors.CheckViolation):
            with pg.transaction():
                pg.execute('UPDATE football.matches SET home_goals=-1 WHERE match_id=%s',(row[0],))

def test_olap_outputs_equal_across_engines():
    report=json.loads((RESULTS/'olap/comparison.json').read_text())
    assert all(r['engines_match'] and r['grand_total_matches']==10781 for r in report.values())
    assert report['rollup']['rows']!=report['cube']['rows']

def test_mongo_real_crud_and_index():
    from platform_lab.mongo import demonstrate_crud
    assert demonstrate_crud()['crud_passed']

def test_real_broker_staging_and_deduplication():
    result=demo(3)
    assert result['staged_unique']==3 and result['duplicate_retry']=='ignored'
    assert result['rejection_records']>=1 and result['dead_queue_messages']>=1

def test_event_rejects_inconsistent_score():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        MatchEvent(event_id='x',demo_run='x',match_id='x',match_date='2024-05-19',
          home_team='A',away_team='B',home_goals=2,away_goals=0,result='A')
