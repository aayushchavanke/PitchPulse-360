"""
PitchPulse 360 - High-Speed Columnar Analytical Engine (CO5 & Lab 11)
Processes 10,780+ Top 5 European League Matches + 14,500+ Player Spatial Telemetry Events:
- League Standings with Champions, UCL, UEL, Relegation Zones
- Multi-Year Relegation & Promotion Tracking across 6 seasons
- Team Multi-Year Trajectories (rise and fall)
- Head-to-Head Clash Analytics & Records
- Individual Player Analytics, Tactical Heatmaps & Attribute Radars
"""

import os
import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional

class DuckDBProcessor:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = duckdb.connect(db_path)
        self.conn.execute("SET threads TO 4;")

    def register_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        self.conn.register(table_name, df)

    def load_silver_matches(self, silver_path: str = "data/lakehouse/silver_leagues") -> int:
        from deltalake import DeltaTable
        if os.path.exists(silver_path):
            dt = DeltaTable(silver_path)
            df = dt.to_pandas()
            self.register_dataframe("silver_matches", df)
            return len(df)
        return 0

    def load_gold_standings(self, gold_path: str = "data/lakehouse/gold_standings") -> pd.DataFrame:
        from deltalake import DeltaTable
        if os.path.exists(gold_path):
            dt = DeltaTable(gold_path)
            df = dt.to_pandas()
            self.register_dataframe("gold_standings", df)
            return df
        return pd.DataFrame()

    def load_player_spatial_data(self, parquet_path: str = "data/lakehouse/player_spatial_telemetry.parquet") -> int:
        if os.path.exists(parquet_path):
            df = pd.read_parquet(parquet_path)
            self.register_dataframe("player_actions", df)
            return len(df)
        return 0

    def get_standings(self, league_name: str, season: str) -> pd.DataFrame:
        query = f"""
        SELECT position, team, played, won, drawn, lost, goals_for, goals_against, goal_diff, points, status
        FROM gold_standings
        WHERE league_name = ? AND season = ?
        ORDER BY position ASC;
        """
        return self.conn.execute(query, [league_name, season]).df()

    def get_all_champions(self) -> pd.DataFrame:
        query = """
        SELECT league_name, season, team AS champion, points, won, drawn, lost, goal_diff
        FROM gold_standings
        WHERE position = 1
        ORDER BY league_name ASC, season DESC;
        """
        return self.conn.execute(query).df()

    def get_relegation_history(self, league_name: str) -> pd.DataFrame:
        query = f"""
        SELECT season, position, team, points, goal_diff, status
        FROM gold_standings
        WHERE league_name = ? AND status LIKE '%Relegated%'
        ORDER BY season DESC, position ASC;
        """
        return self.conn.execute(query, [league_name]).df()

    def get_team_trajectory(self, team_name: str) -> pd.DataFrame:
        query = f"""
        SELECT season, league_name, position, points, won, drawn, lost, goals_for, goals_against, goal_diff, status
        FROM gold_standings
        WHERE team = ?
        ORDER BY season ASC;
        """
        return self.conn.execute(query, [team_name]).df()

    def get_head_to_head(self, team1: str, team2: str) -> Dict[str, Any]:
        query = f"""
        SELECT 
            match_date, season, league_name,
            home_team, away_team, home_goals, away_goals, result,
            home_shots, away_shots
        FROM silver_matches
        WHERE (home_team = ? AND away_team = ?)
           OR (home_team = ? AND away_team = ?)
        ORDER BY season DESC, match_date DESC;
        """
        df_matches = self.conn.execute(query, [team1, team2, team2, team1]).df()

        if df_matches.empty:
            return {"matches": pd.DataFrame(), "summary": {}}

        t1_wins = len(df_matches[((df_matches["home_team"] == team1) & (df_matches["result"] == "H")) |
                                 ((df_matches["away_team"] == team1) & (df_matches["result"] == "A"))])
        t2_wins = len(df_matches[((df_matches["home_team"] == team2) & (df_matches["result"] == "H")) |
                                 ((df_matches["away_team"] == team2) & (df_matches["result"] == "A"))])
        draws = len(df_matches[df_matches["result"] == "D"])

        t1_goals = df_matches[df_matches["home_team"] == team1]["home_goals"].sum() + \
                   df_matches[df_matches["away_team"] == team1]["away_goals"].sum()
        t2_goals = df_matches[df_matches["home_team"] == team2]["home_goals"].sum() + \
                   df_matches[df_matches["away_team"] == team2]["away_goals"].sum()

        summary = {
            "total_matches": len(df_matches),
            "team1": team1,
            "team1_wins": t1_wins,
            "team1_goals": int(t1_goals),
            "draws": draws,
            "team2": team2,
            "team2_wins": t2_wins,
            "team2_goals": int(t2_goals)
        }
        return {"matches": df_matches, "summary": summary}

    def get_top_scoring_matches(self, limit: int = 10) -> pd.DataFrame:
        query = f"""
        SELECT match_date, season, league_name, home_team, away_team, 
               home_goals, away_goals, total_goals,
               CONCAT(home_goals, ' - ', away_goals) AS scoreline
        FROM silver_matches
        ORDER BY total_goals DESC, (home_goals + away_goals) DESC
        LIMIT {limit};
        """
        return self.conn.execute(query).df()

    # ==========================================
    # PLAYER SPATIAL & TACTICAL ANALYTICS
    # ==========================================
    def get_top_players_list(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Returns top players by action volume and goal threat."""
        query = f"""
        SELECT 
            player_name,
            team_name,
            COUNT(*) AS total_actions,
            SUM(is_shot) AS total_shots,
            SUM(is_goal) AS total_goals,
            ROUND(SUM(xg), 2) AS total_xg
        FROM player_actions
        GROUP BY player_name, team_name
        ORDER BY total_goals DESC, total_actions DESC
        LIMIT {limit};
        """
        return self.conn.execute(query).df().to_dict(orient="records")

    def get_player_spatial_events(self, player_name: str) -> pd.DataFrame:
        """Returns all spatial coordinates for a player."""
        query = f"""
        SELECT x, y, event_type, minute, xg, shot_outcome, is_pass, is_shot, is_goal
        FROM player_actions
        WHERE player_name = ?
        ORDER BY minute;
        """
        return self.conn.execute(query, [player_name]).df()

    def get_player_radar_attributes(self, player_name: str) -> Dict[str, float]:
        """
        Calculates 5-dimensional football tactical profile (0-100 scale):
        1. Finishing (Goals vs xG Conversion)
        2. Threat (Cumulative xG Index)
        3. Playmaking (Passing Volume & Distribution)
        4. Pitch Incursion (Final Third Penetration, X >= 80)
        5. Work Rate (Total Touches & Spatial Dispersion)
        """
        query = f"""
        SELECT 
            COUNT(*) AS actions,
            SUM(is_shot) AS shots,
            SUM(is_goal) AS goals,
            SUM(xg) AS total_xg,
            SUM(is_pass) AS passes,
            SUM(CASE WHEN x >= 80 THEN 1 ELSE 0 END) AS final_third_touches
        FROM player_actions
        WHERE player_name = ?;
        """
        res = self.conn.execute(query, [player_name]).df().iloc[0]
        
        actions = float(res["actions"])
        shots = float(res["shots"])
        goals = float(res["goals"])
        xg = float(res["total_xg"])
        passes = float(res["passes"])
        ft = float(res["final_third_touches"])

        # Normalized scoring (benchmarked against elite international profiles)
        finishing = min(round((goals * 22) + ((goals - xg) * 15) + (shots * 2), 1), 99.0)
        threat = min(round((xg * 25) + (shots * 4), 1), 99.0)
        playmaking = min(round((passes / max(actions, 1)) * 120, 1), 95.0)
        incursion = min(round((ft / max(actions, 1)) * 150, 1), 98.0)
        workrate = min(round((actions / 600.0) * 90.0, 1), 99.0)

        return {
            "Finishing": max(finishing, 40.0),
            "Goal Threat (xG)": max(threat, 35.0),
            "Playmaking": max(playmaking, 45.0),
            "Final Third Incursion": max(incursion, 40.0),
            "Spatial Work Rate": max(workrate, 50.0)
        }

if __name__ == "__main__":
    p = DuckDBProcessor()
    p.load_player_spatial_data()
    print("DuckDB engine ready.")
