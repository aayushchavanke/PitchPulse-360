CREATE SCHEMA IF NOT EXISTS football;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE TABLE IF NOT EXISTS football.countries (
 country_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 country_name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS football.leagues (
 league_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 league_name TEXT NOT NULL UNIQUE,
 country_id INTEGER NOT NULL REFERENCES football.countries);
CREATE TABLE IF NOT EXISTS football.seasons (
 season_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 season_code TEXT NOT NULL UNIQUE, season_label TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS football.league_seasons (
 league_season_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 league_id INTEGER NOT NULL REFERENCES football.leagues,
 season_id INTEGER NOT NULL REFERENCES football.seasons,
 UNIQUE(league_id,season_id));
CREATE TABLE IF NOT EXISTS football.teams (
 team_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 team_name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS football.matches (
 match_id TEXT PRIMARY KEY,
 league_season_id INTEGER NOT NULL REFERENCES football.league_seasons,
 match_date DATE NOT NULL,
 home_team_id INTEGER NOT NULL REFERENCES football.teams,
 away_team_id INTEGER NOT NULL REFERENCES football.teams,
 home_goals SMALLINT NOT NULL CHECK(home_goals BETWEEN 0 AND 20),
 away_goals SMALLINT NOT NULL CHECK(away_goals BETWEEN 0 AND 20),
 home_shots SMALLINT, away_shots SMALLINT,
 home_shots_target SMALLINT, away_shots_target SMALLINT,
 home_yellows SMALLINT, away_yellows SMALLINT,
 home_reds SMALLINT, away_reds SMALLINT,
 source_file TEXT NOT NULL, source_row INTEGER NOT NULL,
 CHECK(home_team_id<>away_team_id),
 CHECK(home_shots>=0 AND away_shots>=0),
 CHECK(home_shots_target BETWEEN 0 AND home_shots),
 CHECK(away_shots_target BETWEEN 0 AND away_shots),
 UNIQUE(league_season_id,match_date,home_team_id,away_team_id));
CREATE INDEX IF NOT EXISTS idx_matches_date ON football.matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_home_date ON football.matches(home_team_id,match_date);
CREATE INDEX IF NOT EXISTS idx_matches_edition ON football.matches(league_season_id);

CREATE OR REPLACE VIEW analytics.match_enriched AS
SELECT m.*,l.league_name,l.league_id,c.country_name AS country,
 s.season_code,s.season_label AS season,ht.team_name AS home_team,at.team_name AS away_team,
 CASE WHEN m.home_goals>m.away_goals THEN 'H' WHEN m.home_goals<m.away_goals THEN 'A' ELSE 'D' END AS result,
 m.home_goals+m.away_goals AS total_goals,
 CASE WHEN m.home_goals>m.away_goals THEN 3 WHEN m.home_goals=m.away_goals THEN 1 ELSE 0 END AS home_points,
 CASE WHEN m.home_goals<m.away_goals THEN 3 WHEN m.home_goals=m.away_goals THEN 1 ELSE 0 END AS away_points
FROM football.matches m
JOIN football.league_seasons ls USING(league_season_id)
JOIN football.leagues l USING(league_id)
JOIN football.countries c USING(country_id)
JOIN football.seasons s USING(season_id)
JOIN football.teams ht ON ht.team_id=m.home_team_id
JOIN football.teams at ON at.team_id=m.away_team_id;

-- Deliberately denormalized analytical fact; the football schema above remains 3NF.
CREATE TABLE IF NOT EXISTS analytics.match_facts (
 match_id TEXT NOT NULL, season_code TEXT NOT NULL,
 match_date DATE NOT NULL, league_name TEXT NOT NULL,
 result CHAR(1) NOT NULL, total_goals INTEGER NOT NULL,
 PRIMARY KEY(match_id,season_code)
) PARTITION BY LIST(season_code);
CREATE INDEX IF NOT EXISTS idx_facts_league_date ON analytics.match_facts(league_name,match_date);

CREATE OR REPLACE VIEW analytics.team_match_points AS
SELECT match_id,league_name,season,match_date,home_team AS team,
 home_points AS points,home_goals AS goals_for,away_goals AS goals_against
FROM analytics.match_enriched
UNION ALL
SELECT match_id,league_name,season,match_date,away_team,
 away_points,away_goals,home_goals FROM analytics.match_enriched;

CREATE OR REPLACE VIEW analytics.team_season_rank AS
SELECT league_name,season,team,COUNT(*) AS played,SUM(points) AS points,
 SUM(goals_for) AS goals_for,SUM(goals_against) AS goals_against,
 DENSE_RANK() OVER(PARTITION BY league_name,season
 ORDER BY SUM(points) DESC,SUM(goals_for)-SUM(goals_against) DESC,SUM(goals_for) DESC) AS rank
FROM analytics.team_match_points GROUP BY league_name,season,team;

CREATE TABLE IF NOT EXISTS staging.match_events (
 event_id TEXT PRIMARY KEY, demo_run TEXT NOT NULL,
 match_id TEXT NOT NULL, payload JSONB NOT NULL,
 received_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS idx_staging_run ON staging.match_events(demo_run,received_at);
CREATE TABLE IF NOT EXISTS staging.rejected_events (
 rejection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 demo_run TEXT NOT NULL, payload TEXT NOT NULL, reason TEXT NOT NULL,
 rejected_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS football.etl_runs (
 run_id TEXT PRIMARY KEY, finished_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 accepted_rows INTEGER NOT NULL, rejected_rows INTEGER NOT NULL);
