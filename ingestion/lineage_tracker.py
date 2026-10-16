"""Accurate lineage for the complete historical football and event-staging paths."""
import json
from pathlib import Path
from datetime import datetime, timezone

class LineageTracker:
    def __init__(self, lineage_file='data/lineage_metadata.json'):
        self.lineage_file=lineage_file
        definitions=[('CSV','Historical league CSVs','Source'),('CLEAN','Pandas profile and clean','Transform'),
          ('MONGO','MongoDB original documents','Storage'),('PG','PostgreSQL normalized matches','Storage'),
          ('OLAP','PostgreSQL and DuckDB OLAP','Compute'),('BRONZE','Delta Bronze raw snapshot','Storage'),
          ('SILVER','Delta Silver clean matches','Storage'),('GOLD','Delta Gold calculated standings','Storage'),
          ('PLAYERS','Simulated player positions','Demonstration'),('UI','Streamlit football and engineering pages','Serving'),
          ('API','FastAPI event capture and reads','Serving'),('RABBIT','RabbitMQ durable queues','Messaging'),
          ('STAGING','PostgreSQL event staging and rejections','Storage'),('PREFECT','Prefect scheduled task workflow','Orchestration')]
        self.nodes=[dict(id=i,label=l,type=t) for i,l,t in definitions]
        self.edges=[('CSV','CLEAN','profile and validate'),('CSV','MONGO','preserve source documents'),
          ('CSV','BRONZE','raw snapshot'),('CLEAN','PG','transactional ETL'),('CLEAN','SILVER','clean snapshot'),
          ('SILVER','GOLD','calculate standings'),('PG','OLAP','aggregate and compare'),('GOLD','UI','football charts'),
          ('OLAP','UI','saved lab evidence'),('PLAYERS','UI','generated heatmaps'),('GOLD','API','read summaries'),
          ('API','RABBIT','validated event publication'),('RABBIT','STAGING','validate, commit, acknowledge'),
          ('STAGING','UI','live staging table'),('PREFECT','CLEAN','schedule and track tasks')]

    def generate_mermaid_diagram(self):
        lines=['graph TD']
        lines += [f'    {n["id"]}["{n["label"]}"]' for n in self.nodes]
        lines += [f'    {a} -->|{label}| {b}' for a,b,label in self.edges]
        return '\n'.join(lines)

    def save_lineage_metadata(self):
        path=Path(self.lineage_file); path.parent.mkdir(parents=True,exist_ok=True)
        data=dict(generated_at=datetime.now(timezone.utc).isoformat(),pipeline='PitchPulse360-complete',
          nodes=self.nodes,edges=[{'from':a,'to':b,'transformation':l} for a,b,l in self.edges],
          mermaid=self.generate_mermaid_diagram())
        path.write_text(json.dumps(data,indent=2),encoding='utf-8')
        return str(path)
