"""
PitchPulse 360 - Data Serving Layer & Governance (CO6 & Lab 9)
Provides RESTful endpoints for Multi-Year Top 5 European Leagues:
- GET /api/v1/leagues/standings?league={league}&season={season}
- GET /api/v1/leagues/champions
- GET /api/v1/teams/{team_name}/trajectory
- GET /api/v1/governance/contracts-masked (RBAC & Principle of Least Privilege)
"""

from fastapi import FastAPI, Depends, HTTPException, Security, Query, status
from fastapi.security import APIKeyHeader
from typing import Dict, Any, List, Optional
import pandas as pd
import os
from storage.lakehouse_manager import LakehouseManager
from spark.duckdb_processor import DuckDBProcessor

app = FastAPI(
    title="PitchPulse 360 - Top 5 European Leagues API",
    description="Enterprise Data Serving & Governance Layer for Multi-Year European Football (CO6 Compliant)",
    version="2.0.0"
)

API_KEY_NAME = "X-PitchPulse-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

API_ROLES = {
    "coach_secret_2026": "Coach",
    "analyst_secret_2026": "Analyst",
    "public_guest_key": "Public"
}

def authenticate_client(api_key: str = Security(api_key_header)) -> str:
    if not api_key:
        return "Public"
    if api_key in API_ROLES:
        return API_ROLES[api_key]
    raise HTTPException(status_code=401, detail="Invalid API Key.")

@app.get("/")
def root():
    return {
        "platform": "PitchPulse 360 - European Football Intelligence",
        "total_matches_indexed": "10,780+",
        "leagues_covered": ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"],
        "seasons_covered": ["2018/19", "2019/20", "2020/21", "2021/22", "2022/23", "2023/24"],
        "status": "ONLINE"
    }

@app.get("/api/v1/leagues/standings")
def get_league_standings(
    league: str = Query(default="Premier League"),
    season: str = Query(default="2023/2024"),
    role: str = Depends(authenticate_client)
):
    proc = DuckDBProcessor()
    proc.load_gold_standings()
    df = proc.get_standings(league, season)
    return {
        "league": league,
        "season": season,
        "requested_by_role": role,
        "count": len(df),
        "standings": df.to_dict(orient="records")
    }

@app.get("/api/v1/leagues/champions")
def get_all_champions(role: str = Depends(authenticate_client)):
    proc = DuckDBProcessor()
    proc.load_gold_standings()
    df = proc.get_all_champions()
    return {
        "requested_by_role": role,
        "count": len(df),
        "champions": df.to_dict(orient="records")
    }

@app.get("/api/v1/teams/{team_name}/trajectory")
def get_team_trajectory(team_name: str, role: str = Depends(authenticate_client)):
    proc = DuckDBProcessor()
    proc.load_gold_standings()
    df = proc.get_team_trajectory(team_name)
    return {
        "team": team_name,
        "requested_by_role": role,
        "history": df.to_dict(orient="records")
    }

@app.get("/api/v1/governance/contracts-masked")
def get_sensitive_club_contracts(role: str = Depends(authenticate_client)):
    """Demonstrates Data Masking & Principle of Least Privilege (CO6)."""
    raw_data = [
        {"club": "Real Madrid", "wage_bill_millions_eur": 450.5, "debt_eur": "120M", "transfer_budget_eur": "200M"},
        {"club": "Manchester City", "wage_bill_millions_eur": 420.0, "debt_eur": "0M", "transfer_budget_eur": "180M"}
    ]
    if role == "Coach":
        return {"access_level": "PRIVILEGED", "records": raw_data}
    else:
        masked = []
        for r in raw_data:
            masked.append({
                "club": r["club"],
                "wage_bill_millions_eur": "CONFIDENTIAL [MASKED]",
                "debt_eur": "CLASSIFIED [MASKED]",
                "transfer_budget_eur": "CONFIDENTIAL [MASKED]"
            })
        return {"access_level": "RESTRICTED (DATA MASKED)", "records": masked}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("serving.api:app", host="127.0.0.1", port=8000, reload=True)
