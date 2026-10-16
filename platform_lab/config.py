import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
RESULTS.mkdir(exist_ok=True)
PG_DSN = os.getenv('PITCHPULSE_POSTGRES_DSN', 'postgresql://pitchpulse:pitchpulse_local_demo@127.0.0.1:55432/pitchpulse')
MONGO_URI = os.getenv('PITCHPULSE_MONGO_URI', 'mongodb://127.0.0.1:57017')
AMQP_URL = os.getenv('PITCHPULSE_AMQP_URL', 'amqp://pitchpulse:pitchpulse_local_demo@127.0.0.1:5673/%2F')
QUEUE = 'pitchpulse.match.events'
DEAD_QUEUE = QUEUE + '.rejected'

def save_json(name, value):
    import json
    path = RESULTS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str, ensure_ascii=False), encoding='utf-8')
    return str(path)
