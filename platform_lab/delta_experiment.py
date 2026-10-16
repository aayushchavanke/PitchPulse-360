"""Experiment 8: real writes, update/delete, versioned reads and rejected schemas."""
from pathlib import Path
import uuid
import pandas as pd
from deltalake import DeltaTable,write_deltalake
from .config import RESULTS,save_json

def run():
    directory=RESULTS/'delta_lab'/str(uuid.uuid4())
    table=directory/'table'; directory.mkdir(parents=True)
    initial=pd.DataFrame({'match_id':['demo-1','demo-2'],'goals':[2,1]})
    write_deltalake(str(table),initial)
    snapshots={}
    def capture(label):
        dt=DeltaTable(str(table)); frame=dt.to_pandas().sort_values('match_id').reset_index(drop=True)
        frame.to_csv(directory/(label+'.csv'),index=False)
        snapshots[label]=dict(version=dt.version(),rows=frame.to_dict('records'))
        return dt.version()
    v0=capture('created')
    write_deltalake(str(table),pd.DataFrame({'match_id':['demo-3'],'goals':[0]}),mode='append')
    capture('inserted')
    DeltaTable(str(table)).update(updates={'goals':'3'},predicate="match_id = 'demo-1'")
    capture('updated')
    DeltaTable(str(table)).delete("match_id = 'demo-2'")
    before=capture('deleted')
    # Read old version through the Delta reader, not by manually opening old files.
    old=DeltaTable(str(table),version=v0).to_pandas().sort_values('match_id').reset_index(drop=True)
    pd.testing.assert_frame_equal(old,initial.sort_values('match_id').reset_index(drop=True))
    old.to_csv(directory/'time_travel_version_0.csv',index=False)
    failures=[]
    for name,bad in [('wrong_columns',pd.DataFrame({'match_id':['bad'],'unexpected':[7]})),
                     ('wrong_type',pd.DataFrame({'match_id':['bad'],'goals':['not-a-number']}))]:
        try: write_deltalake(str(table),bad,mode='append')
        except Exception as error:
            failures.append(dict(case=name,error_type=type(error).__name__,message=str(error)))
        else: raise AssertionError('Incompatible write unexpectedly accepted: '+name)
    current=DeltaTable(str(table))
    assert current.version()==before,'Rejected schema write changed table version'
    assert len(failures)==2 and len(current.to_pandas())==2
    result=dict(status='passed',table=str(table),snapshots=snapshots,
        old_version_read=v0,old_rows=old.to_dict('records'),rejected_writes=failures,
        version_unchanged_after_rejections=True,history=current.history(),
        interpretation='Insert adds demo-3; update changes demo-1 from 2 to 3 goals; delete removes demo-2. Version 0 still contains original rows. Schema errors created no commit.')
    save_json('delta_lab/summary.json',result)
    return result
