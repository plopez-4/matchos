"""Bounded nine-match recap audit; live mode uses the running backend, never its keys.

Records each request once. A fallback is preserved, not retried into a passing result.
Reports contain public synthetic evidence only and require a separate editorial review.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
import uuid
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import matchday, main, story_writer
from app.models import MatchEvent, CatchUpRequest

SITUATIONS = [
    (0, 'featured', 1500, 0, 'early_derby_contribution'),
    (0, 'featured', 2700, 1200, 'halftime_goal_connection'),
    (0, 'comeback', 3750, 3300, 'palace_equalizer_build_up'),
    (0, 'comeback', 4530, 3300, 'palace_repeated_replies'),
    (0, 'quiet', 4500, 2700, 'quiet_brighton'),
    (1, 'featured', 3750, 2700, 'quiet_derby'),
    (1, 'comeback', 2250, 1500, 'first_half_exchange'),
    (1, 'quiet', 1350, 600, 'open_brighton'),
    (2, 'featured', 4530, 3900, 'late_derby_equalizer'),
    (2, 'comeback', 4500, 2700, 'no_new_goal_palace'),
    (2, 'quiet', 4800, 3900, 'late_fulham_turnaround_and_reply'),
]


def fingerprint():
    names = ['backend/app/'+name for name in (
        'matchday.py','story_writer.py','recap_context.py','recap_quality.py','story_plan.py',
        'data/match_variants.json','data/players_2026.json')]
    return {name:sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def report(kind):
    return {'evaluation':kind,'started_utc':datetime.now(timezone.utc).isoformat(),
            'writer_version':story_writer.VERSION,'generator_version':matchday.VERSION,
            'source_hashes':fingerprint(), 'cases':[], 'complete':False,
            'independent_fan_study':'not_run','editorial_verdict':'pending_source_review'}


def save(result, path):
    result['mode_counts']=dict(Counter(row['writer_mode'] for row in result['cases']))
    result['fallback_counts']=dict(Counter(row.get('fallback_reason') for row in result['cases'] if row.get('fallback_reason')))
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def source_record(events, fan):
    return {'snapshot':fan['snapshot'],'text':fan['spoken_recap'],
            'selected_stories':fan.get('story_plan',{}).get('stories',[]),
            'evidence':story_writer.evidence_packet(fan,events),
            'source_goals':[{'event_id':e.event_id,'second':e.match_second,'team':e.team_name,
                             'scorer':e.player_name,'shot_id':e.related_event_id}
                            for e in events if e.type=='goal'],
            'editorial_review':'pending'}


def offline(path):
    os.environ['MATCHOS_AI_MODE']='off'
    result=report('Nine versions x four snapshots x two audiences; deterministic source audit')
    for profile in matchday.PROFILES:
        for variant in range(3):
            feed=[MatchEvent(**e) for e in matchday.library_fixture(profile,'offline-'+profile['role'],variant)]
            for now in (1200,2700,4530,5580):
                events=[e for e in feed if e.match_second<=now]
                for audience in ('casual','advanced'):
                    fan=main.build_catch_up(events,CatchUpRequest(audience=audience))['fan_briefing']
                    known={e.event_id for e in events}
                    assert set(fan['evidence_event_ids']) <= known
                    packet=story_writer.evidence_packet(fan,events)
                    assert len(json.dumps(packet,ensure_ascii=False).encode())<=32768
                    result['cases'].append({'case':f"{profile['role']}-v{variant+1}-{now}",
                        'role':profile['role'],'variant_id':variant+1,'audience':audience,
                        'writer_mode':'deterministic',**source_record(events,fan)})
    result['complete']=True
    result['finished_utc']=datetime.now(timezone.utc).isoformat()
    save(result,path)
    print(f"Saved {len(result['cases'])} deterministic EN/ES pairs",flush=True)


def live(path, base_url, cooldown, case_names=None, capture_rejections=False):
    result=report('Eleven situations across nine versions x two audiences; both languages per request')
    situations=[s for s in SITUATIONS if not case_names or s[4] in case_names]
    if case_names and set(case_names)-{s[4] for s in SITUATIONS}:
        raise ValueError('Unknown evaluation case')
    result['selected_cases']=[s[4] for s in situations]
    coverage={(s[0]+1,s[1]) for s in situations}
    result['version_coverage']=[{'variant_id':v,'role':role} for v,role in sorted(coverage)]
    result['planned_requests']=len(situations)*2
    if case_names: result['evaluation']='Focused follow-up: '+str(len(situations))+' situations x two audiences; both languages'
    if len(coverage)==9: result['evaluation']=f'All nine versions; {len(situations)} situations x two audiences; both languages'
    result['temporary_groups']=[]
    result['capture_rejections']=capture_rejections
    last_request=None
    prefix='library-audit-'+uuid.uuid4().hex[:8]
    with httpx.Client(base_url=base_url,headers={'X-MatchOS-Client':'replay'},timeout=120) as browser:
        status=browser.get('/api/ai/status').raise_for_status().json()
        if not status['configured'] or status['writer_version']!=result['writer_version']:
            raise RuntimeError('Configured backend writer does not match the frozen source')
        browser.post('/api/session',json={}).raise_for_status()
        try:
            for variant in range(3):
                if not any(s[0]==variant for s in situations): continue
                # Select an ordinary random-ID-compatible session with a known combination.
                # No public API override, provider keys or future schedule are sent to Radar.
                day=next(f'{prefix}-{i}' for i in range(10000)
                         if all(matchday.selected_variant(f'{prefix}-{i}-{p["role"]}')==variant
                                for p in matchday.PROFILES))
                view=browser.post('/api/matchdays/start',json={'matchday_id':day}).raise_for_status().json()
                if any(e.get('variant_id')!=variant+1 for e in view['matches']):
                    raise RuntimeError('Backend library does not match the frozen source')
                group={'id':day,'variant_id':variant+1,'released':False}
                result['temporary_groups'].append(group)
                save(result,path)
                try:
                    tick=view['tick']
                    for _,role,now,cursor_second,name in sorted((s for s in situations if s[0]==variant),key=lambda s:s[2]):
                        while tick<now//30:
                            tick+=1
                            browser.post(f'/api/matchdays/{day}/tick',json={'tick':tick}).raise_for_status()
                        mid=f'{day}-{role}'
                        rows=browser.get(f'/api/matches/{mid}/events').raise_for_status().json()
                        profile=next(p for p in matchday.PROFILES if p['role']==role)
                        expected=[e for e in matchday.library_fixture(profile,mid,variant) if e['match_second']<=now]
                        if rows!=expected:
                            raise RuntimeError('Observed backend feed differs from frozen library')
                        events=[MatchEvent(**e) for e in rows]
                        cursor=max((e.sequence for e in events if e.match_second<=cursor_second),default=0)
                        for audience in ('casual','advanced'):
                            if fingerprint()!=result['source_hashes']:
                                raise RuntimeError('Frozen evaluation sources changed')
                            if last_request is not None:
                                wait=cooldown-(time.monotonic()-last_request)
                                if wait>0: time.sleep(wait)
                            started=time.monotonic()
                            route=f'/api/development/matches/{mid}/catch-up' if capture_rejections else f'/api/matches/{mid}/catch-up'
                            response=browser.post(route,json={'since_sequence':cursor,'audience':audience})
                            last_request=time.monotonic()
                            row={'case':name,'role':role,'variant_id':variant+1,'second':now,
                                 'cursor_second':cursor_second,'audience':audience,'http_status':response.status_code,
                                 'seconds':round(last_request-started,2)}
                            if response.is_success:
                                body=response.json()
                                if capture_rejections:
                                    row['evaluation_trace']=body['evaluation_trace']
                                    body=body['result']
                                fan=body['fan_briefing']
                                narrative=fan['narrative']
                                if narrative.get('version')!=result['writer_version']:
                                    raise RuntimeError('Backend writer changed during evaluation')
                                row.update(source_record(events,fan))
                                row.update(writer_mode=narrative['mode'],fallback_reason=narrative.get('fallback_reason'),
                                    validation_stage=narrative.get('validation_stage'),validation_details=narrative.get('validation_details'),
                                    model_review=narrative.get('review'),revision_used=narrative.get('revision_used',False),
                                    prompt_hash=narrative.get('prompt_hash'))
                            else:
                                row.update(writer_mode='http_failure',fallback_reason=f'http_{response.status_code}')
                            result['cases'].append(row)
                            save(result,path)
                            print(len(result['cases']),name,audience,row['writer_mode'],row.get('fallback_reason'),flush=True)
                finally:
                    released=browser.request('DELETE',f'/api/matchdays/{day}',json={})
                    group['released']=released.status_code==200
                    save(result,path)
            result['complete']=len(result['cases'])==result['planned_requests']
        finally:
            result['finished_utc']=datetime.now(timezone.utc).isoformat()
            save(result,path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--cooldown',type=float,default=30)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',action='append',dest='case_names')
    parser.add_argument('--capture-rejections',action='store_true',help='Opt-in loopback-only owned-session developer trace; never a fan response')
    args=parser.parse_args()
    if not 0<=args.cooldown<=60: parser.error('cooldown must be within 0..60 seconds')
    (live(args.output,args.base_url,args.cooldown,args.case_names,args.capture_rejections) if args.live else offline(args.output))
