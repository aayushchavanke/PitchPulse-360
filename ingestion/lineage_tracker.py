"""
PitchPulse 360 - Data Lineage & Pipeline Provenance (CO3)
Tracks data lineage from origin source -> ingestion -> Bronze -> Silver -> Gold -> Serving layer.
Generates an interactive Mermaid graph and JSON audit trace.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

class LineageTracker:
    def __init__(self, lineage_file: str = "data/lineage_metadata.json"):
        self.lineage_file = lineage_file
        os.makedirs(os.path.dirname(lineage_file), exist_ok=True)
        self.nodes = [
            {"id": "SRC_STATSBOMB", "label": "StatsBomb GitHub API", "type": "Source"},
            {"id": "SRC_STREAM", "label": "Kafka Live Match Events", "type": "Source"},
            {"id": "STAGE_INGEST", "label": "Ingestion & Dead Letter Queue (DLQ)", "type": "Ingestion"},
            {"id": "LAKE_BRONZE", "label": "Delta Lake: Bronze Layer (Raw Payloads)", "type": "Storage"},
            {"id": "VAL_QUALITY", "label": "Great Expectations Quality Suite", "type": "Validation"},
            {"id": "LAKE_SILVER", "label": "Delta Lake: Silver Layer (Cleaned & Schema Enforced)", "type": "Storage"},
            {"id": "PROC_DUCKDB", "label": "DuckDB / PySpark Distributed Engine", "type": "Compute"},
            {"id": "LAKE_GOLD", "label": "Delta Lake: Gold Star Schema & KPIs", "type": "Storage"},
            {"id": "SERV_FASTAPI", "label": "FastAPI Data Product & RBAC", "type": "Serving"},
            {"id": "BI_STREAMLIT", "label": "Streamlit Tactical Match Center", "type": "Analytics"}
        ]
        self.edges = [
            ("SRC_STATSBOMB", "STAGE_INGEST", "HTTP Batch Fetch"),
            ("SRC_STREAM", "STAGE_INGEST", "Real-Time Kafka Consumer"),
            ("STAGE_INGEST", "LAKE_BRONZE", "Append Raw JSON"),
            ("LAKE_BRONZE", "VAL_QUALITY", "Validate Constraints"),
            ("VAL_QUALITY", "LAKE_SILVER", "Filtered Clean Stream"),
            ("LAKE_SILVER", "PROC_DUCKDB", "Columnar SQL Transforms"),
            ("PROC_DUCKDB", "LAKE_GOLD", "Aggregate KPIs & Star Schema"),
            ("LAKE_GOLD", "SERV_FASTAPI", "Query Serving Layer"),
            ("SERV_FASTAPI", "BI_STREAMLIT", "Tactical Visualization")
        ]

    def generate_mermaid_diagram(self) -> str:
        """Produces a Mermaid representation of the complete pipeline lineage."""
        lines = ["graph TD"]
        for node in self.nodes:
            lines.append(f'    {node["id"]}["{node["label"]}"]')
        for src, dest, label in self.edges:
            lines.append(f'    {src} -->|{label}| {dest}')
        return "\n".join(lines)

    def save_lineage_metadata(self) -> str:
        metadata = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "pipeline": "PitchPulse-360-Full-Lifecycle",
            "nodes": self.nodes,
            "edges": [{"from": s, "to": d, "transformation": l} for s, d, l in self.edges],
            "mermaid": self.generate_mermaid_diagram()
        }
        with open(self.lineage_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        return self.lineage_file

if __name__ == "__main__":
    lt = LineageTracker()
    lt.save_lineage_metadata()
    print("Lineage metadata saved.")
    print(lt.generate_mermaid_diagram())
