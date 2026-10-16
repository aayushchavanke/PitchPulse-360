import argparse
import json
import os
from .config import ROOT

def main():
    os.chdir(ROOT)
    p=argparse.ArgumentParser(description='PitchPulse complete experiments')
    p.add_argument('command',choices=['run','eda','postgres','olap','mongo','stream','verify','metrics','delta','benchmark','quality'])
    args=p.parse_args()
    from .config import RESULTS
    if args.command=='run':
        from .flow import football_flow
        result=football_flow()
    elif args.command=='eda':
        from .cleaning import extract,clean_and_report
        result={'clean_file':clean_and_report(extract())}
    elif args.command=='postgres':
        from .postgres import load,analyze
        load(RESULTS/'clean_matches.parquet'); result=analyze()
    elif args.command=='olap':
        from .olap import run
        result=run(RESULTS/'clean_matches.parquet')
    elif args.command=='mongo':
        from .mongo import sync_raw,demonstrate_crud
        result={**sync_raw(RESULTS/'raw_snapshot.parquet'),**demonstrate_crud()}
    elif args.command=='stream':
        from .streaming import demo
        result=demo()
    elif args.command in ['metrics','delta','benchmark','quality']:
        import importlib
        names={'metrics':'metrics','delta':'delta_experiment','benchmark':'benchmark','quality':'expectations'}
        module=importlib.import_module('platform_lab.'+names[args.command])
        result=module.run() if args.command=='delta' else module.run(RESULTS/'clean_matches.parquet')
    else:
        from .verification import verify
        result=verify()
    print(json.dumps(result,indent=2,default=str))

if __name__=='__main__': main()
