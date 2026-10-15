"""
PitchPulse 360 - Multi-Year Top 5 European Leagues Ingestion Module (CO1 & CO3)
Downloads official historical match data across the Top 5 European Leagues:
- Premier League (England - E0)
- La Liga (Spain - SP1)
- Serie A (Italy - I1)
- Bundesliga (Germany - D1)
- Ligue 1 (France - F1)
Across 5+ seasons (2018/19 through 2023/24).
"""

import os
import io
import urllib.request
import pandas as pd
from typing import Dict, List, Tuple

LEAGUES = {
    "Premier League": {"code": "E0", "country": "England"},
    "La Liga": {"code": "SP1", "country": "Spain"},
    "Serie A": {"code": "I1", "country": "Italy"},
    "Bundesliga": {"code": "D1", "country": "Germany"},
    "Ligue 1": {"code": "F1", "country": "France"}
}

SEASONS = [
    {"label": "2023/2024", "code": "2324"},
    {"label": "2022/2023", "code": "2223"},
    {"label": "2021/2022", "code": "2122"},
    {"label": "2020/2021", "code": "2021"},
    {"label": "2019/2020", "code": "1920"},
    {"label": "2018/2019", "code": "1819"}
]

DATA_DIR = "data/raw_leagues"

def ensure_directory(path: str = DATA_DIR):
    os.makedirs(path, exist_ok=True)

def fetch_league_season(league_name: str, season_label: str, season_code: str) -> pd.DataFrame:
    """
    Downloads or reads cached CSV for a specific league and season.
    """
    ensure_directory()
    league_code = LEAGUES[league_name]["code"]
    cache_path = os.path.join(DATA_DIR, f"{league_code}_{season_code}.csv")

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
        try:
            return pd.read_csv(cache_path, encoding="utf-8-sig")
        except Exception:
            return pd.read_csv(cache_path, encoding="latin1")

    url = f"https://www.football-data.co.uk/mmz4281/{season_code}/{league_code}.csv"
    print(f"[Ingestion] Fetching {league_name} ({season_label}) from {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read()
        
        # Save cache
        with open(cache_path, "wb") as f:
            f.write(content)

        try:
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
        except Exception:
            df = pd.read_csv(io.BytesIO(content), encoding="latin1")

        print(f"  -> Ingested {len(df)} matches.")
        return df
    except Exception as e:
        print(f"[Ingestion Warning] Could not download {url}: {e}")
        return pd.DataFrame()

def ingest_all_top5_leagues() -> pd.DataFrame:
    """
    Batch ingests all Top 5 leagues for all 6 seasons and normalizes schema.
    Returns unified DataFrame containing thousands of matches.
    """
    ensure_directory()
    all_frames = []

    for l_name, l_info in LEAGUES.items():
        for s in SEASONS:
            df = fetch_league_season(l_name, s["label"], s["code"])
            if df.empty:
                continue

            # Ensure essential columns exist
            cols = {
                "Date": "match_date",
                "HomeTeam": "home_team",
                "AwayTeam": "away_team",
                "FTHG": "home_goals",
                "FTAG": "away_goals",
                "FTR": "result", # H, D, A
                "HS": "home_shots",
                "AS": "away_shots",
                "HST": "home_shots_target",
                "AST": "away_shots_target",
                "HY": "home_yellows",
                "AY": "away_yellows",
                "HR": "home_reds",
                "AR": "away_reds"
            }

            # Filter and rename available columns
            matched_cols = {orig: new for orig, new in cols.items() if orig in df.columns}
            sub_df = df[list(matched_cols.keys())].rename(columns=matched_cols).copy()

            # Clean rows with missing team names or scores
            sub_df = sub_df.dropna(subset=["home_team", "away_team", "home_goals", "away_goals"])

            # Cast goals to int
            sub_df["home_goals"] = sub_df["home_goals"].astype(int)
            sub_df["away_goals"] = sub_df["away_goals"].astype(int)
            sub_df["total_goals"] = sub_df["home_goals"] + sub_df["away_goals"]

            # Add lineage metadata
            sub_df["league_name"] = l_name
            sub_df["country"] = l_info["country"]
            sub_df["season"] = s["label"]
            sub_df["season_code"] = s["code"]
            sub_df["match_id"] = [
                f"{l_info['code']}_{s['code']}_{i+1:03d}" for i in range(len(sub_df))
            ]

            all_frames.append(sub_df)

    if all_frames:
        master_df = pd.concat(all_frames, ignore_index=True)
        print(f"[Ingestion Success] Consolidated master dataset: {len(master_df):,} matches across Top 5 leagues!")
        return master_df
    return pd.DataFrame()

if __name__ == "__main__":
    df = ingest_all_top5_leagues()
    print("Sample output:")
    print(df.head(3))
