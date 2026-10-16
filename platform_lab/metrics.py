"""Experiment 4: exact business metrics on labeled synthetic football ticket orders."""
import random
import statistics
import time
from datetime import timedelta
from decimal import Decimal
import pandas as pd
from .postgres import connect
from .config import ROOT,RESULTS,save_json

RAW_QUERIES={
 'daily_revenue':"""SELECT order_date,SUM(CASE WHEN status='Paid' THEN quantity*unit_price_eur ELSE 0 END) AS revenue_eur,
 COUNT(*) AS orders FROM business.ticket_orders GROUP BY order_date ORDER BY order_date""",
 'monthly_sales_growth':"""WITH amounts AS (
 SELECT date_trunc('month',order_date)::DATE AS month,
 SUM(CASE WHEN status='Paid' THEN quantity*unit_price_eur ELSE 0 END) AS revenue_eur
 FROM business.ticket_orders GROUP BY 1), calendar AS (
 SELECT generate_series(date_trunc('month',MIN(order_date)),date_trunc('month',MAX(order_date)),INTERVAL '1 month')::DATE AS month
 FROM business.ticket_orders), monthly AS (
 SELECT calendar.month,COALESCE(amounts.revenue_eur,0) AS revenue_eur FROM calendar LEFT JOIN amounts USING(month)), previous AS (
 SELECT *,LAG(revenue_eur) OVER(ORDER BY month) AS previous_revenue_eur FROM monthly)
 SELECT *,100.0*(revenue_eur-previous_revenue_eur)/NULLIF(previous_revenue_eur,0) AS growth_pct
 FROM previous ORDER BY month""",
 'repeat_customer_percentage':"""WITH customers AS (
 SELECT customer_id,COUNT(*) AS paid_orders FROM business.ticket_orders WHERE status='Paid' GROUP BY customer_id)
 SELECT COUNT(*) AS purchasing_customers,COUNT(*) FILTER(WHERE paid_orders>1) AS repeat_customers,
 100.0*COUNT(*) FILTER(WHERE paid_orders>1)/NULLIF(COUNT(*),0) AS repeat_customer_pct FROM customers"""}

def run(clean_path):
    source=pd.read_parquet(clean_path).sort_values('match_id').reset_index(drop=True)
    rng=random.Random(42); rows=[]
    for i in range(6000):
        match=source.iloc[rng.randrange(len(source))]
        rows.append((f'DEMO-TICKET-{i:05}',f'DEMO-C{rng.randrange(5000):05}',match.match_id,
          match.match_date.date()-timedelta(days=rng.randrange(1,22)),rng.randint(1,6),
          Decimal(rng.choice([20,35,50,75,100])), 'Refunded' if i%17==0 else 'Paid',True))
    directory=RESULTS/'metrics'; directory.mkdir(exist_ok=True)
    pd.DataFrame(rows,columns=['order_id','customer_id','match_id','order_date','quantity','unit_price_eur','status','synthetic']).to_csv(directory/'synthetic_ticket_orders.csv',index=False)
    comparison={}
    with connect() as pg:
        pg.execute((ROOT/'models/metric_views.sql').read_text())
        pg.execute('DELETE FROM business.ticket_orders')
        with pg.cursor().copy('COPY business.ticket_orders FROM STDIN') as copy:
            for row in rows: copy.write_row(row)
        for name,raw in RAW_QUERIES.items():
            order=' ORDER BY order_date' if name=='daily_revenue' else ' ORDER BY month' if name=='monthly_sales_growth' else ''
            view='SELECT * FROM business.vw_'+name+order
            with pg.cursor() as cur:
                cur.execute(view); result=cur.fetchall(); columns=[d.name for d in cur.description]
                cur.execute(raw); assert result==cur.fetchall(),name+' view/raw results differ'
            pd.DataFrame(result,columns=columns).to_csv(directory/(name+'.csv'),index=False)
            times={}
            for mode,query in [('view',view),('raw_sql',raw)]:
                pg.execute(query).fetchall(); samples=[]
                for _ in range(5):
                    start=time.perf_counter(); pg.execute(query).fetchall(); samples.append((time.perf_counter()-start)*1000)
                times[mode]=round(statistics.median(samples),3)
                save_json(f'metrics/{name}_{mode}_plan.json',pg.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query).fetchone()[0])
            comparison[name]=dict(answers_match=True,rows=len(result),median_ms=times,view_sql=view,raw_sql=raw,
              interpretation='Views centralize the definition. Ordinary views are not precomputed and do not inherently speed up queries.')
        for name in ['daily_goals','team_win_percentage']:
            with pg.cursor() as cur:
                cur.execute('SELECT * FROM analytics.vw_'+name)
                pd.DataFrame(cur.fetchall(),columns=[d.name for d in cur.description]).to_csv(directory/(name+'.csv'),index=False)
        repeat=pg.execute('SELECT repeat_customer_pct FROM business.vw_repeat_customer_percentage').fetchone()[0]
    result=dict(source='SYNTHETIC football ticket orders; not real club finances',ticket_orders=len(rows),
      repeat_customer_pct=float(repeat),comparisons=comparison,football_views=['daily_goals','team_win_percentage'])
    save_json('metrics/summary.json',result)
    return result
