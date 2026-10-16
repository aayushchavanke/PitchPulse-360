"""
PitchPulse 360 - Lakehouse Storage & Delta Architecture for Top 5 Leagues (CO2 & Lab 8)
Implements:
- Bronze Layer: Raw match rows with ingestion provenance
- Silver Layer: Cleaned, schema-enforced, with match points & goal metrics, partitioned by [league_name]
- Gold Layer: Pre-computed League Standings, Champions, European spots, Relegation zones
- Delta Lake ACID transactions & Time Travel
"""

import os
import json
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List
from deltalake import DeltaTable, write_deltalake

class LakehouseManager:
    def __init__(self, base_dir: str = "data/lakehouse"):
        self.base_dir = base_dir
        self.bronze_path = os.path.join(base_dir, "bronze_leagues")
        self.silver_path = os.path.join(base_dir, "silver_leagues")
        self.gold_standings_path = os.path.join(base_dir, "gold_standings")
        self.gold_path = self.gold_standings_path
        os.makedirs(self.bronze_path, exist_ok=True)
        os.makedirs(self.silver_path, exist_ok=True)
        os.makedirs(self.gold_standings_path, exist_ok=True)

    def write_bronze(self, df: pd.DataFrame) -> str:
        """Stores raw match rows into Bronze Delta Lake."""
        df_bronze = df.copy()
        df_bronze["ingestion_ts"] = datetime.now(timezone.utc).isoformat()
        write_deltalake(
            self.bronze_path,
            df_bronze,
            mode="overwrite",
            schema_mode="overwrite",
            partition_by=["league_name"]
        )
        print(f"[Lakehouse] Bronze Delta Table populated with {len(df_bronze):,} match records.")
        return self.bronze_path

    def process_silver(self, df: pd.DataFrame) -> str:
        """
        Cleans and enriches data with point allocations and goal differentials.
        """
        df_silver = df.copy()

        # Calculate points for home and away
        df_silver["home_points"] = df_silver["result"].map({"H": 3, "D": 1, "A": 0}).fillna(0).astype(int)
        df_silver["away_points"] = df_silver["result"].map({"A": 3, "D": 1, "H": 0}).fillna(0).astype(int)
        df_silver["goal_diff"] = df_silver["home_goals"] - df_silver["away_goals"]
        df_silver["processed_ts"] = datetime.now(timezone.utc).isoformat()

        write_deltalake(
            self.silver_path,
            df_silver,
            mode="overwrite",
            schema_mode="overwrite",
            partition_by=["league_name"]
        )
        print(f"[Lakehouse] Silver Delta Table synchronized ({len(df_silver):,} clean matches).")
        return self.silver_path

    def generate_gold_standings(self, silver_df: pd.DataFrame) -> pd.DataFrame:
        """
        Gold Layer: Generates final season standings for each league & season:
        Calculates: Played, Won, Drawn, Lost, Goals For (GF), Goals Against (GA),
        Goal Difference (GD), Points, and Qualification / Relegation Status.
        """
        standings_list = []

        for (league, season), matches in silver_df.groupby(["league_name", "season"]):
            teams = set(matches["home_team"]).union(set(matches["away_team"]))
            table = []

            for team in teams:
                home_m = matches[matches["home_team"] == team]
                away_m = matches[matches["away_team"] == team]

                p = len(home_m) + len(away_m)
                w = (home_m["result"] == "H").sum() + (away_m["result"] == "A").sum()
                d = (home_m["result"] == "D").sum() + (away_m["result"] == "D").sum()
                l = (home_m["result"] == "A").sum() + (away_m["result"] == "H").sum()

                gf = home_m["home_goals"].sum() + away_m["away_goals"].sum()
                ga = home_m["away_goals"].sum() + away_m["home_goals"].sum()
                gd = gf - ga
                pts = (w * 3) + (d * 1)

                table.append({
                    "league_name": league,
                    "season": season,
                    "team": team,
                    "played": p,
                    "won": w,
                    "drawn": d,
                    "lost": l,
                    "goals_for": gf,
                    "goals_against": ga,
                    "goal_diff": gd,
                    "points": pts
                })

            df_t = pd.DataFrame(table).sort_values(by=["points", "goal_diff", "goals_for"], ascending=False).reset_index(drop=True)
            df_t["position"] = df_t.index + 1
            
            # Assign status (Top 4 = UCL, 5-6 = UEL/UECL, Bottom 3 = Relegated)
            total_teams = len(df_t)
            status_col = []
            for pos in df_t["position"]:
                if pos == 1:
                    status_col.append("Champion 🏆")
                elif pos <= 4:
                    status_col.append("Champions League 🔵")
                elif pos <= 6:
                    status_col.append("Europa League 🟠")
                elif pos >= total_teams - 2:
                    status_col.append("Relegated 🔴")
                else:
                    status_col.append("Mid Table ⚪")
            df_t["status"] = status_col
            standings_list.append(df_t)

        all_standings = pd.concat(standings_list, ignore_index=True)
        write_deltalake(
            self.gold_standings_path,
            all_standings,
            mode="overwrite",
            schema_mode="overwrite",
            partition_by=["league_name"]
        )
        print(f"[Lakehouse] Gold Standings Table built across {len(standings_list)} league-seasons!")
        return all_standings

    def demonstrate_time_travel(self) -> Dict[str, Any]:
        """Demonstrates Delta Lake Time Travel (CO2 & Lab 8)."""
        dt = DeltaTable(self.silver_path)
        history = dt.history()
        return {
            "current_version": dt.version(),
            "history_commits": len(history),
            "table_schema": [f.name for f in dt.schema().fields],
            "sample_commit": history[0] if history else {}
        }

if __name__ == "__main__":
    lm = LakehouseManager()
    print("Lakehouse ready.")
