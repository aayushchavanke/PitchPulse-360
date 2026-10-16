"""Observe a genuinely auto-scheduled completed run; never fabricate schedule evidence."""
import os
import time
import requests
from datetime import datetime,timezone
from .config import save_json

def check(timeout=180):
    base=os.environ['PREFECT_API_URL'].rstrip('/')
    deadline=time.monotonic()+timeout
    after=datetime.now(timezone.utc) if os.getenv('PITCHPULSE_ONLY_NEW_SCHEDULE')=='1' else None
    deployment=None
    while time.monotonic()<deadline:
        r=requests.get(base+'/deployments/name/pitchpulse-football-platform/football-hourly',timeout=10)
        if r.ok:
            deployment=r.json()
            response=requests.post(base+'/flow_runs/filter',json={
              'deployments':{'id':{'any_':[deployment['id']]}},
              'flow_runs':{'state':{'type':{'any_':['COMPLETED']}}}},timeout=10)
            response.raise_for_status()
            runs=[run for run in response.json() if run.get('auto_scheduled') and
                (after is None or datetime.fromisoformat(run['start_time'].replace('Z','+00:00'))>after)]
            if runs:
                run=runs[0]
                tasks=requests.post(base+'/task_runs/filter',json={'flow_runs':{'id':{'any_':[run['id']]}}},timeout=10)
                tasks.raise_for_status(); task_rows=tasks.json()
                if len(task_rows)!=11 or not all(t['state_type']=='COMPLETED' for t in task_rows):
                    time.sleep(3)
                    continue
                evidence=dict(status='passed',deployment_id=deployment['id'],
                    schedules=deployment.get('schedules'),run_id=run['id'],auto_scheduled=True,
                    state=run['state_type'],start_time=run['start_time'],end_time=run['end_time'],
                    observed_after=str(after) if after else None,completed_tasks=len(task_rows))
                save_json('prefect/scheduled_run_evidence.json',evidence)
                return evidence
        time.sleep(3)
    raise TimeoutError('No completed automatically scheduled run observed; inspect Prefect logs')

if __name__=='__main__':
    import json
    print(json.dumps(check(),indent=2))
