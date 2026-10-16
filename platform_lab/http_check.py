import time
import uuid
import requests
from .postgres import connect
from .config import save_json

def check():
    base='http://api:8000'
    token=str(uuid.uuid4())
    event=dict(event_id='http:'+token,demo_run='http:'+token,match_id='classroom-fixture',
      match_date='2024-05-19',home_team='Arsenal',away_team='Chelsea',home_goals=2,away_goals=1,result='H')
    for _ in range(2):
        response=requests.post(base+'/lab/events',json=event,timeout=15)
        assert response.status_code==202,response.text
    invalid=requests.post(base+'/lab/events',json={**event,'result':'A'},timeout=15)
    assert invalid.status_code==422
    deadline=time.monotonic()+20
    while True:
        with connect() as pg:
            count=pg.execute('SELECT count(*) FROM staging.match_events WHERE event_id=%s',(event['event_id'],)).fetchone()[0]
        if count==1: break
        if time.monotonic()>deadline: raise AssertionError('HTTP event never reached staging')
        time.sleep(.5)
    recent=requests.get(base+'/lab/events',timeout=15); assert recent.status_code==200
    standings=requests.get(base+'/api/v1/leagues/standings',timeout=15)
    assert standings.status_code==200 and standings.json()['count']==20
    experiment_status={}
    for name in ['metrics','delta','benchmark','quality']:
        response=requests.get(base+'/lab/experiments/'+name,timeout=15)
        assert response.status_code==200,(name,response.text)
        experiment_status[name]=response.status_code
    result=dict(status='passed',valid_post=202,duplicate_post=202,invalid_post=422,
        unique_staged_rows=count,recent_events_get=200,standings_get=200,event_id=event['event_id'],experiment_reports=experiment_status)
    save_json('http_checks.json',result)
    return result

if __name__=='__main__':
    import json
    print(json.dumps(check(),indent=2))
