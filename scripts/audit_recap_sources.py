"""Recount saved recap facts directly from the seeded feeds, separately from prose review."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app import matchday


def check(row):
    snapshot=row['snapshot']
    profile=next(p for p in matchday.PROFILES if p['role']==row['role'])
    feed=matchday.library_fixture(profile,snapshot['match_id'],row['variant_id']-1)
    events=[e for e in feed if e['sequence']<=snapshot['through_sequence'] and e['match_second']<=snapshot['match_second']]
    by_id={e['event_id']:e for e in events}
    goals=[e for e in events if e['type']=='goal']
    score={side:sum(e['team_id']==side for e in goals) for side in ('home','away')}
    assert [e['event_id'] for e in goals]==[e['event_id'] for e in row['source_goals']], 'goal chronology'
    facts=row['evidence']['facts']
    assert next(f['data']['score'] for f in facts if f['fact_id']=='score')==score, 'score recount'
    for fact in facts:
        assert set(fact['evidence_event_ids'])<=by_id.keys(), 'unobserved evidence'
    kinds=[]
    for story in row['selected_stories']:
        kind=story['kind']; kinds.append(kind)
        assert set(story['evidence_event_ids'])<=by_id.keys(), 'unobserved story'
        metric=story.get('metric',{})
        if kind=='recovery_shot':
            recovery,shot=by_id[metric['recovery_event_id']],by_id[metric['shot_event_id']]
            assert shot['match_second']-recovery['match_second']==metric['elapsed_seconds'], 'elapsed time'
            assert recovery['possession_id']==shot['possession_id'], 'possession continuity'
            link=metric.get('goal_link')
            if link:
                goal=by_id[link['goal_event_id']]
                assert goal['related_event_id']==shot['event_id'] and shot['outcome']=='goal', 'goal shot linkage'
                assert link['recoverer']==recovery['player_name'] and link['scorer']==goal['player_name'], 'linked actors'
                passes=[e for e in events if recovery['sequence']<e['sequence']<shot['sequence']
                        and e['possession_id']==shot['possession_id'] and e['type']=='pass' and e['outcome']=='complete']
                assert len(passes)==link['completed_pass_count'], 'team pass count'
                before={side:sum(e['team_id']==side and e['sequence']<goal['sequence'] for e in goals) for side in score}
                after={**before,goal['team_id']:before[goal['team_id']]+1}
                assert before==link['score_before'] and after==link['score_after'], 'goal score transition'
        elif kind.startswith('player_'):
            def in_window(e):
                return (e['team_id']==metric['team_id'] and e['period']==metric['period'] and
                        (e['match_second']>=metric['start_second'] if metric['start_inclusive'] else e['match_second']>metric['start_second']) and
                        (e['match_second']<=metric['end_second'] if metric['end_inclusive'] else e['match_second']<metric['end_second']))
            window=[e for e in events if in_window(e)]
            shots=[e for e in window if e['type']=='shot']
            if kind=='player_shot_creation':
                assert len(shots)==metric['team_total'], 'team shot denominator'
                assert len(metric['links'])==metric['count'], 'creator count'
                for link in metric['links']:
                    before,shot=by_id[link['pass_event_id']],by_id[link['shot_event_id']]
                    assert in_window(before) and in_window(shot), 'creator window'
                    assert before['type']=='pass' and before['outcome']=='complete' and shot['type']=='shot', 'creator actions'
                    assert before['player_id']==metric['player_id'] and before['recipient_player_id']==shot['player_id'], 'creator actors'
                    assert before['sequence']+1==shot['sequence'] and before['possession_id']==shot['possession_id'], 'creator continuity'
            elif kind=='player_shooting':
                own=[e for e in shots if e['player_id']==metric['player_id']]
                assert len(shots)==metric['team_total'] and len(own)==metric['count'], 'player shot count'
            elif kind=='player_forward_passing':
                direction=1 if metric['team_id']=='home' else -1
                passes=[e for e in window if e['type']=='pass' and e['outcome']=='complete' and
                        direction*(e['end_x']-e['x'])>=metric['min_gain']]
                assert len(passes)==metric['team_total'], 'forward pass denominator'
                assert sum(e['player_id']==metric['player_id'] for e in passes)==metric['count'], 'forward pass count'
        elif kind!='goal':
            raise AssertionError('Metric recount not implemented for '+kind)
    return kinds


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports',nargs='+',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result={'scope':'Source facts and selected contribution recount; not a proof of model prose correctness','reports':[]}
    for path in args.reports:
        data=json.loads(path.read_text(encoding='utf-8'))
        rows=[]; kinds=Counter()
        for row in data['cases']:
            item={k:row.get(k) for k in ('case','audience','role','variant_id','writer_mode')}
            try:
                kinds.update(check(row)); item['source_check']='pass'
            except (AssertionError,KeyError) as error:
                item.update(source_check='fail',issue=str(error))
            rows.append(item)
        result['reports'].append({'file':path.name,'complete':data['complete'],'checked_cases':len(rows),
                                 'selected_kinds':dict(kinds),'failures':sum(r['source_check']=='fail' for r in rows),'cases':rows})
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k!='cases'} for r in result['reports']]))
    sys.exit(1 if any(r['failures'] for r in result['reports']) else 0)
