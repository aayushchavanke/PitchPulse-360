-- ====================================================================
-- PitchPulse 360 - Analytical SQL & Window Transformations (CO4 & Lab 4)
-- Implements:
-- - Window functions (SUM OVER, DENSE_RANK, LAG/LEAD)
-- - Cumulative team Expected Goals (xG) progression
-- - 10-Minute Rolling Momentum & Event Intensity Index
-- ====================================================================

-- 1. Cumulative Team xG by Match Timeline (Window Function)
CREATE OR REPLACE VIEW view_cumulative_team_xg AS
SELECT 
    match_id,
    period,
    minute,
    team_name,
    player_name,
    event_type,
    xg,
    shot_outcome,
    SUM(xg) OVER (
        PARTITION BY match_id, team_name 
        ORDER BY period, minute, second
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_xg
FROM silver_events
WHERE event_type = 'Shot';

-- 2. Player Threat Ranking within Match (Dense Rank & Aggregate)
CREATE OR REPLACE VIEW view_player_threat_ranking AS
SELECT 
    team_name,
    player_name,
    COUNT(CASE WHEN event_type = 'Shot' THEN 1 END) AS total_shots,
    COUNT(CASE WHEN shot_outcome = 'Goal' THEN 1 END) AS goals_scored,
    ROUND(SUM(xg), 3) AS total_expected_goals,
    DENSE_RANK() OVER (
        PARTITION BY team_name 
        ORDER BY SUM(xg) DESC
    ) AS team_threat_rank
FROM silver_events
WHERE player_name != 'Unknown'
GROUP BY team_name, player_name;

-- 3. 10-Minute Rolling Match Momentum Index
CREATE OR REPLACE VIEW view_match_momentum AS
SELECT 
    match_id,
    (minute / 10) * 10 AS minute_bucket,
    team_name,
    COUNT(*) AS action_count,
    ROUND(SUM(xg), 3) AS bucket_xg,
    ROUND(AVG(pass_length), 2) AS avg_pass_depth
FROM silver_events
WHERE team_name != 'Unknown'
GROUP BY match_id, (minute / 10) * 10, team_name
ORDER BY minute_bucket ASC, action_count DESC;
