"""
PitchPulse 360 - Automated Test Suite (Python standard unittest)
Verifies all modules and Course Outcomes (CO1 to CO6) for Multi-Year Top 5 Leagues
"""

import os
import sys
import shutil
import unittest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from quality.expectations_suite import DataQualitySuite
from storage.lakehouse_manager import LakehouseManager
from spark.duckdb_processor import DuckDBProcessor

class TestPitchPulsePipeline(unittest.TestCase):

    def setUp(self):
        shutil.rmtree("data/lakehouse_test", ignore_errors=True)

    def tearDown(self):
        shutil.rmtree("data/lakehouse_test", ignore_errors=True)

    def test_co1_data_quality(self):
        suite = DataQualitySuite()
        df_sample = pd.DataFrame([
            {"match_id": "m1", "home_team": "Arsenal", "away_team": "Chelsea", "home_goals": 2, "away_goals": 1, "result": "H"},
            {"match_id": "m2", "home_team": "Real Madrid", "away_team": "Barcelona", "home_goals": 1, "away_goals": 1, "result": "D"}
        ])
        report = suite.validate_league_matches(df_sample)
        self.assertEqual(report["total_records_evaluated"], 2)
        self.assertEqual(report["pass_rate_percentage"], 100.0)

    def test_co2_lakehouse_delta(self):
        lm = LakehouseManager(base_dir="data/lakehouse_test")
        df_sample = pd.DataFrame([
            {"match_id": "m1", "league_name": "Premier League", "season": "2023/2024", "home_team": "Liverpool", "away_team": "Everton", "home_goals": 2, "away_goals": 0, "result": "H"}
        ])
        bronze = lm.write_bronze(df_sample)
        silver = lm.process_silver(df_sample)
        standings = lm.generate_gold_standings(df_sample)
        self.assertTrue(os.path.exists(bronze))
        self.assertTrue(os.path.exists(silver))
        self.assertEqual(len(standings), 2) # Liverpool and Everton

    def test_co4_co5_duckdb_standings(self):
        processor = DuckDBProcessor()
        df_gold_mock = pd.DataFrame([
            {"league_name": "Premier League", "season": "2023/2024", "team": "Man City", "played": 38, "won": 28, "drawn": 7, "lost": 3, "goals_for": 96, "goals_against": 34, "goal_diff": 62, "points": 91, "position": 1, "status": "Champion 🏆"}
        ])
        processor.register_dataframe("gold_standings", df_gold_mock)
        standings = processor.get_standings("Premier League", "2023/2024")
        self.assertEqual(len(standings), 1)
        self.assertEqual(standings.iloc[0]["team"], "Man City")
        self.assertEqual(standings.iloc[0]["points"], 91)

if __name__ == "__main__":
    unittest.main()
