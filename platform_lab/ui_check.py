import json
from pathlib import Path
from streamlit.testing.v1 import AppTest
from .config import save_json


def check():
    app=AppTest.from_file('dashboard/app.py',default_timeout=60).run()
    assert not app.exception, [e.message for e in app.exception]
    assert len(app.tabs)==5
    standings=app.dataframe[0].value
    assert standings['qualification'].eq('Champion').sum()==1
    assert standings['qualification'].eq('UEFA Champions League').sum()==3
    assert not Path('dashboard/pages/Engineering_Lab.py').exists()
    for league,season in [('Bundesliga','2018/2019'),('Premier League','2023/2024')]:
        app.sidebar.selectbox[0].select(league).run()
        app.sidebar.selectbox[1].select(season).run()
        assert not app.exception, [e.message for e in app.exception]
    results={'dashboard/app.py':'All five football tabs loaded; league/season interactions and standings classification passed','navigation':'Single football dashboard; removed evidence page is absent'}
    save_json('ui_checks.json',results)
    print(json.dumps(results,indent=2))

if __name__=='__main__': check()
