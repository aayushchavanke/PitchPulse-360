"""Experiment 7: real MongoDB documents, CRUD, projections and indexed query evidence."""
import json
import uuid
import pandas as pd
from pymongo import MongoClient, UpdateOne, ASCENDING, DESCENDING
from .config import MONGO_URI, RESULTS, save_json

def client():
    return MongoClient(MONGO_URI,serverSelectionTimeoutMS=10000)

def sync_raw(raw_path):
    raw=pd.read_parquet(raw_path)
    # JSON conversion preserves nulls instead of writing NaN into source documents.
    records=json.loads(raw.to_json(orient='records',date_format='iso'))
    operations=[]
    for row in records:
        key=f'{row["source_file"]}:{row["source_row"]}'
        operations.append(UpdateOne({'_id':key},{'$set':row},upsert=True))
    with client() as connection:
        collection=connection.pitchpulse.raw_matches
        collection.create_index([('league_name',ASCENDING),('season_code',ASCENDING)],name='league_season')
        collection.create_index([('home_team',ASCENDING),('match_date',DESCENDING)],name='home_date')
        for i in range(0,len(operations),1000): collection.bulk_write(operations[i:i+1000],ordered=False)
        current=collection.count_documents({})
        if current!=len(raw): raise AssertionError(f'Mongo source document count {current} != snapshot {len(raw)}')
    return dict(raw_documents=current)

def demonstrate_crud():
    token=str(uuid.uuid4())
    with client() as connection:
        db=connection.pitchpulse
        collection=db.scout_reports
        collection.create_index([('team',ASCENDING),('rating',DESCENDING)],name='team_rating')
        # Separate demonstration document never changes historical match results.
        report={'_id':token,'team':'Arsenal','rating':7,'notes':{'strength':'passing'},'tags':['demo']}
        collection.insert_one(report)
        read=collection.find_one({'_id':token},{'_id':0,'team':1,'rating':1,'notes':1})
        assert read['rating']==7
        changed=collection.update_one({'_id':token},{'$set':{'rating':8,'notes.reviewed':True},'$push':{'tags':'updated'}})
        updated=collection.find_one({'_id':token},{'_id':0})
        assert changed.modified_count==1 and updated['notes']['reviewed']
        deleted=collection.delete_one({'_id':token})
        assert deleted.deleted_count==1 and collection.find_one({'_id':token}) is None
        filters={'league_name':'Premier League','season_code':'2324'}
        matches=list(db.raw_matches.find(filters,{'_id':0,'home_team':1,'away_team':1,'home_goals':1,'away_goals':1}).limit(3))
        plan=db.raw_matches.find(filters,{'_id':0,'home_team':1,'away_team':1}).explain()
        index_names=list(db.raw_matches.index_information())
        result=dict(create='inserted',read_projection=read,update=updated,delete='deleted and absence checked',
            filtered_examples=matches,indexes=index_names,query_plan=plan)
        save_json('mongo/crud_and_index_evidence.json',result)
    return dict(crud_passed=True,indexes=index_names,filtered_examples=len(matches))
