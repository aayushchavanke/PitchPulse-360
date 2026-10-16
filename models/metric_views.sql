CREATE SCHEMA IF NOT EXISTS business;
CREATE TABLE IF NOT EXISTS business.ticket_orders (
 order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL,
 match_id TEXT NOT NULL REFERENCES football.matches ON DELETE CASCADE,
 order_date DATE NOT NULL, quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 6),
 unit_price_eur NUMERIC(10,2) NOT NULL CHECK(unit_price_eur>0),
 status TEXT NOT NULL CHECK(status IN ('Paid','Refunded')),
 synthetic BOOLEAN NOT NULL DEFAULT true CHECK(synthetic));

CREATE OR REPLACE VIEW business.vw_ticket_sales AS
SELECT *, quantity*unit_price_eur AS gross_amount_eur,
 CASE WHEN status='Paid' THEN quantity*unit_price_eur ELSE 0 END AS revenue_eur
FROM business.ticket_orders;

CREATE OR REPLACE VIEW business.vw_daily_revenue AS
SELECT order_date,SUM(revenue_eur) AS revenue_eur,COUNT(*) AS orders
FROM business.vw_ticket_sales GROUP BY order_date;

CREATE OR REPLACE VIEW business.vw_monthly_sales_growth AS
WITH amounts AS (
 SELECT date_trunc('month',order_date)::DATE AS month,SUM(revenue_eur) AS revenue_eur
 FROM business.vw_ticket_sales GROUP BY 1
), calendar AS (
 SELECT generate_series(date_trunc('month',MIN(order_date)),date_trunc('month',MAX(order_date)),INTERVAL '1 month')::DATE AS month
 FROM business.ticket_orders
), monthly AS (
 SELECT calendar.month,COALESCE(amounts.revenue_eur,0) AS revenue_eur
 FROM calendar LEFT JOIN amounts USING(month)
), previous AS (
 SELECT *,LAG(revenue_eur) OVER(ORDER BY month) AS previous_revenue_eur FROM monthly
)
SELECT *,100.0*(revenue_eur-previous_revenue_eur)/NULLIF(previous_revenue_eur,0) AS growth_pct
FROM previous;

CREATE OR REPLACE VIEW business.vw_repeat_customer_percentage AS
WITH customers AS (
 SELECT customer_id,COUNT(*) AS paid_orders FROM business.ticket_orders
 WHERE status='Paid' GROUP BY customer_id
)
SELECT COUNT(*) AS purchasing_customers,
 COUNT(*) FILTER(WHERE paid_orders>1) AS repeat_customers,
 100.0*COUNT(*) FILTER(WHERE paid_orders>1)/NULLIF(COUNT(*),0) AS repeat_customer_pct
FROM customers;

CREATE OR REPLACE VIEW analytics.vw_daily_goals AS
SELECT match_date,league_name,COUNT(*) AS matches,SUM(total_goals) AS goals,
 AVG(total_goals) AS goals_per_match FROM analytics.match_enriched GROUP BY match_date,league_name;

CREATE OR REPLACE VIEW analytics.vw_team_win_percentage AS
SELECT league_name,season,team,COUNT(*) AS played,
 COUNT(*) FILTER(WHERE points=3) AS wins,
 100.0*COUNT(*) FILTER(WHERE points=3)/COUNT(*) AS win_percentage
FROM analytics.team_match_points GROUP BY league_name,season,team;
