"""Two bounded live recap spot checks; uses server configuration without reading keys."""
import json
import argparse
from pathlib import Path
import sys
import uuid
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.story_writer import VERSION


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audience',choices=('casual','advanced','both'),default='both')
    args=parser.parse_args()
    mid='linked-goal-'+uuid.uuid4().hex[:10]
    folder=ROOT/'docs'
    report={'writer_version':VERSION,'match_id':mid,'cases':[],'scope':'Live integration spot checks, not a fan study or general accuracy benchmark.'}
    with httpx.Client(base_url='http://127.0.0.1:8000',headers={'X-MatchOS-Client':'replay'},timeout=90,trust_env=False) as client:
        status=client.get('/api/ai/status').raise_for_status().json()
        assert status['configured'] and status['writer_version']==VERSION, status
        client.post('/api/session',json={}).raise_for_status()
        feed=client.post('/api/replay/start',json={'match_id':mid,'scenario_id':'palace-newcastle-90'}).raise_for_status().json()
        observed=[event for event in feed if event['match_second']<=3750]
        for event in observed:
            client.post('/api/matches/'+mid+'/advance',json={'sequence':event['sequence']}).raise_for_status()
        for audience in (('casual','advanced') if args.audience=='both' else (args.audience,)):
            result=client.post('/api/matches/'+mid+'/catch-up',json={'audience':audience}).raise_for_status().json()
            fan=result['fan_briefing']
            plan=fan['story_plan']
            change=next(story for story in plan['stories'] if story['story_id']==plan['change_story_id'])
            assert change['metric']['goal_link']['score_change']=='equalization'
            assert change['metric']['goal_link']['scorer']=='Ismaila Sarr'
            assert all(name in fan['spoken_recap'][language] for name in ('Sarr','Tomiyasu') for language in ('en','es'))
            file=folder/f'linked-goal-{audience}-live.json'
            file.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
            narrative=fan['narrative']
            report['cases'].append({'audience':audience,'mode':narrative['mode'],'review':narrative.get('review'),
                                    'fallback_reason':narrative.get('fallback_reason'),'text':fan['spoken_recap']})
            print(json.dumps(report['cases'][-1],ensure_ascii=False),flush=True)
    (folder/'linked-goal-live-check.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':
    main()
