import json
from pathlib import Path
import pandas as pd
import pytest
from deltalake import DeltaTable
from platform_lab.config import RESULTS
from platform_lab.expectations import validate,render
from platform_lab.postgres import connect

@pytest.fixture
def clean_sample():
    return pd.read_parquet(RESULTS/'clean_matches.parquet').head(8).reset_index(drop=True)

def test_exp4_paid_revenue_and_repeat_customer_definition():
    with connect() as pg:
        paid=pg.execute("SELECT SUM(quantity*unit_price_eur) FROM business.ticket_orders WHERE status='Paid'").fetchone()[0]
        assert pg.execute('SELECT SUM(revenue_eur) FROM business.vw_daily_revenue').fetchone()[0]==paid
        assert pg.execute('SELECT SUM(revenue_eur) FROM business.vw_monthly_sales_growth').fetchone()[0]==paid
        first=pg.execute('SELECT previous_revenue_eur,growth_pct FROM business.vw_monthly_sales_growth ORDER BY month LIMIT 1').fetchone()
        assert first==(None,None)
        bad_gaps=pg.execute('''WITH dates AS (SELECT month,LAG(month) OVER(ORDER BY month) AS previous
          FROM business.vw_monthly_sales_growth)
          SELECT COUNT(*) FROM dates WHERE previous IS NOT NULL AND month<>(previous+INTERVAL '1 month')::DATE''').fetchone()[0]
        assert bad_gaps==0,'Monthly growth must compare adjacent calendar months, including zero-sales months'
        assert pg.execute('SELECT bool_and(synthetic),COUNT(*) FROM business.ticket_orders').fetchone()==(True,6000)
        row=pg.execute('SELECT purchasing_customers,repeat_customers,repeat_customer_pct FROM business.vw_repeat_customer_percentage').fetchone()
        assert float(row[2])==pytest.approx(100*row[1]/row[0])

def test_exp8_actual_current_and_historical_delta_rows():
    report=json.loads((RESULTS/'delta_lab/summary.json').read_text())
    current=DeltaTable(report['table']).to_pandas().set_index('match_id')
    old=DeltaTable(report['table'],version=0).to_pandas().set_index('match_id')
    assert old.loc['demo-1','goals']==2 and current.loc['demo-1','goals']==3
    assert 'demo-2' in old.index and 'demo-2' not in current.index
    assert 'demo-3' not in old.index and 'demo-3' in current.index
    assert DeltaTable(report['table']).version()==3

def test_exp11_benchmark_contains_all_six_modes_and_actual_rows():
    import duckdb
    report=json.loads((RESULTS/'benchmark/summary.json').read_text())
    assert {(m['storage'],m['threads']) for m in report['modes']}=={(s,t) for s in ['CSV','Parquet','DuckDB'] for t in [1,4]}
    with duckdb.connect(str(RESULTS/'benchmark/benchmark.duckdb'),read_only=True) as db:
        assert db.execute('SELECT COUNT(*) FROM benchmark_matches').fetchone()[0]==250000
    assert all(m['runs']==5 and m['answers_match'] and m['min_ms']<=m['median_ms']<=m['max_ms'] for m in report['modes'])

def test_exp13_clean_data_passes(clean_sample):
    assert validate(clean_sample)['status']=='PASSED'

@pytest.mark.parametrize('defect',['missing_column','missing_value','duplicate','bad_dtype','bad_range','bad_result','bad_shots'])
def test_exp13_each_required_failure_is_detected(clean_sample,defect):
    frame=clean_sample.copy()
    if defect=='missing_column': frame=frame.drop(columns='home_team')
    elif defect=='missing_value': frame.loc[0,'home_team']=None
    elif defect=='duplicate': frame.loc[1,'match_id']=frame.loc[0,'match_id']
    elif defect=='bad_dtype': frame['home_goals']=frame.home_goals.astype('string')
    elif defect=='bad_range': frame.loc[0,'home_goals']=-1
    elif defect=='bad_result': frame.loc[0,'result']='X'
    else: frame.loc[0,'away_shots_target']=999
    assert validate(frame)['status']=='FAILED'

def test_exp13_html_escapes_untrusted_values(clean_sample,tmp_path):
    frame=clean_sample.copy(); frame.loc[0,'result']='<script>alert(1)</script>'
    report=validate(frame); path=tmp_path/'report.html'; render(report,path)
    content=path.read_text()
    assert '<script>alert(1)</script>' not in content and '&lt;script&gt;' in content

def test_exp13_empty_table_fails(clean_sample):
    assert validate(clean_sample.iloc[:0])['status']=='FAILED'
