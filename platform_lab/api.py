from fastapi import APIRouter, HTTPException
from .streaming import MatchEvent,publish
from .postgres import connect
from typing import Literal

router=APIRouter(prefix='/lab',tags=['Completed data engineering labs'])

@router.post('/events',status_code=202)
def submit_event(event:MatchEvent):
    try: publish(event.model_dump(mode='json'))
    except Exception as error:
        raise HTTPException(503,'RabbitMQ is unavailable; event was not confirmed') from error
    return {'status':'accepted','event_id':event.event_id}

@router.get('/events')
def recent_events():
    with connect() as pg:
        with pg.cursor() as cur:
            cur.execute('SELECT event_id,match_id,payload,received_at FROM staging.match_events ORDER BY received_at DESC LIMIT 20')
            columns=[d.name for d in cur.description]
            return [dict(zip(columns,row)) for row in cur.fetchall()]

@router.get('/status')
def status():
    from .config import RESULTS
    import json
    path=RESULTS/'last_run.json'
    return json.loads(path.read_text()) if path.exists() else {'status':'not run'}

@router.get('/experiments/{name}')
def experiment_report(name:Literal['metrics','delta','benchmark','quality']):
    from .config import RESULTS
    import json
    folders={'metrics':'metrics','delta':'delta_lab','benchmark':'benchmark','quality':'quality'}
    path=RESULTS/folders[name]/'summary.json'
    if not path.exists(): raise HTTPException(404,'Run the full workflow first')
    return json.loads(path.read_text())
