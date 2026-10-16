"""Experiment 10: persistent RabbitMQ messages -> validated PostgreSQL staging."""
import argparse
import json
import logging
import time
import uuid
from datetime import date
from typing import Literal
import pandas as pd
import pika
from pydantic import BaseModel, Field, model_validator, ConfigDict
from psycopg.types.json import Jsonb
from .config import AMQP_URL, QUEUE, DEAD_QUEUE, RESULTS, save_json
from .postgres import connect, initialize

LOG=logging.getLogger('pitchpulse.consumer')

class MatchEvent(BaseModel):
    model_config=ConfigDict(extra='forbid')
    event_id: str=Field(min_length=1,max_length=128)
    demo_run: str=Field(min_length=1,max_length=128)
    match_id: str=Field(min_length=1,max_length=128)
    match_date: date
    home_team: str=Field(min_length=1,max_length=100)
    away_team: str=Field(min_length=1,max_length=100)
    home_goals: int=Field(ge=0,le=20,strict=True)
    away_goals: int=Field(ge=0,le=20,strict=True)
    result: Literal['H','D','A']

    @model_validator(mode='after')
    def consistent(self):
        expected='H' if self.home_goals>self.away_goals else 'A' if self.home_goals<self.away_goals else 'D'
        if self.result!=expected: raise ValueError('result conflicts with score')
        if self.home_team.strip()==self.away_team.strip(): raise ValueError('teams must differ')
        if not self.home_team.strip() or not self.away_team.strip(): raise ValueError('blank team')
        return self

def broker():
    params=pika.URLParameters(AMQP_URL)
    params.heartbeat=60
    params.blocked_connection_timeout=20
    params.socket_timeout=10
    return pika.BlockingConnection(params)

def declare(channel):
    channel.queue_declare(queue=QUEUE,durable=True)
    channel.queue_declare(queue=DEAD_QUEUE,durable=True)
    channel.confirm_delivery()

def publish(payload,validate=True):
    event=MatchEvent.model_validate(payload).model_dump(mode='json') if validate else payload
    with broker() as connection:
        channel=connection.channel(); declare(channel)
        channel.basic_publish(exchange='',routing_key=QUEUE,body=json.dumps(event).encode(),mandatory=True,
          properties=pika.BasicProperties(content_type='application/json',delivery_mode=2,
            message_id=str(payload.get('event_id','invalid'))))

def persist(payload):
    event=MatchEvent.model_validate_json(payload)
    with connect() as pg:
        inserted=pg.execute('''INSERT INTO staging.match_events(event_id,demo_run,match_id,payload)
          VALUES(%s,%s,%s,%s) ON CONFLICT(event_id) DO NOTHING RETURNING event_id''',
          (event.event_id,event.demo_run,event.match_id,Jsonb(event.model_dump(mode='json')))).fetchone()
    return 'inserted' if inserted else 'duplicate'

def handle(channel,method,properties,body):
    # Validation failure is permanent; database/network failures are retried.
    try:
        MatchEvent.model_validate_json(body)
    except ValueError as error:
        try:
            text=body.decode('utf-8',errors='replace')
            try: run=json.loads(text).get('demo_run','unknown')
            except (ValueError,AttributeError): run='unknown'
            # Rejection evidence is committed before the original delivery is acknowledged.
            with connect() as pg:
                pg.execute('INSERT INTO staging.rejected_events(demo_run,payload,reason) VALUES(%s,%s,%s)',
                    (run,text,str(error)))
            channel.basic_publish(exchange='',routing_key=DEAD_QUEUE,body=body,mandatory=True,
                properties=pika.BasicProperties(delivery_mode=2,content_type='application/json'))
            channel.basic_ack(method.delivery_tag)
            return 'rejected'
        except Exception:
            channel.basic_nack(method.delivery_tag,requeue=True)
            raise
    try:
        result=persist(body)
    except Exception:
        channel.basic_nack(method.delivery_tag,requeue=True)
        raise
    channel.basic_ack(method.delivery_tag)  # Commit happened in persist() before ACK.
    return result

def consume_forever():
    with connect() as pg: initialize(pg)
    while True:
        try:
            with broker() as connection:
                channel=connection.channel(); declare(channel)
                channel.basic_qos(prefetch_count=10)
                def callback(ch,method,properties,body):
                    LOG.info('delivery=%s outcome=%s',method.delivery_tag,handle(ch,method,properties,body))
                channel.basic_consume(queue=QUEUE,on_message_callback=callback,auto_ack=False)
                LOG.info('Consuming %s',QUEUE); channel.start_consuming()
        except KeyboardInterrupt: return
        except Exception:
            LOG.exception('Consumer reconnecting in 3 seconds'); time.sleep(3)

def drain(max_seconds=30):
    counts={'inserted':0,'duplicate':0,'rejected':0}
    deadline=time.monotonic()+max_seconds
    with broker() as connection:
        channel=connection.channel(); declare(channel)
        while time.monotonic()<deadline:
            method,props,body=channel.basic_get(QUEUE,auto_ack=False)
            if method is None: break
            outcome=handle(channel,method,props,body); counts[outcome]+=1
    return counts

def demo(n=20):
    run=str(uuid.uuid4())
    data=pd.read_parquet(RESULTS/'clean_matches.parquet').head(n)
    n=len(data)
    for i,row in enumerate(data.to_dict('records')):
        payload={key:row[key] for key in ['match_id','home_team','away_team','home_goals','away_goals','result']}
        payload.update(event_id=run+f':{i}',demo_run=run,match_date=str(pd.Timestamp(row['match_date']).date()))
        publish(payload)
        if i==0: publish(payload)  # Deliberate redelivery with the same ID.
    publish({'event_id':run+':bad','demo_run':run,'broken':'payload'},validate=False)
    counts=drain()
    # Works with either our bounded consumer or the continuously running consumer service.
    deadline=time.monotonic()+30
    while True:
        with connect() as pg:
            stored=pg.execute('SELECT count(*) FROM staging.match_events WHERE demo_run=%s',(run,)).fetchone()[0]
            rejected=pg.execute('SELECT count(*) FROM staging.rejected_events WHERE demo_run=%s',(run,)).fetchone()[0]
        if stored==n and rejected>=1: break
        if time.monotonic()>deadline: raise AssertionError(f'Stream demo incomplete: {stored}/{n}, rejected={rejected}')
        time.sleep(.5)
    # Direct retry confirms idempotency independently of which consumer received the duplicate.
    with connect() as pg:
        first=pg.execute('SELECT payload FROM staging.match_events WHERE demo_run=%s LIMIT 1',(run,)).fetchone()[0]
    assert persist(json.dumps(first).encode())=='duplicate'
    with broker() as connection:
        queue_state=connection.channel().queue_declare(queue=DEAD_QUEUE,durable=True).method.message_count
    result=dict(run=run,published_valid=n,published_duplicate=1,published_invalid=1,staged_unique=stored,
        rejection_records=rejected,dead_queue_messages=queue_state,duplicate_retry='ignored',bounded_consumer_counts=counts)
    save_json('streaming/demo.json',result)
    return result

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['consume','demo']); args=p.parse_args()
    if args.command=='consume': consume_forever()
    else: print(json.dumps(demo(),indent=2))
