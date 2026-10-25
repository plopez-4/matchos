"""Nine reproducible inputs, legal elevens and discovery from observed events only."""
import itertools
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import matchday, security, main, story_writer
from app.models import MatchEvent, CatchUpRequest
from app.rosters import club_for_name


@pytest.mark.parametrize('profile', matchday.PROFILES, ids=lambda p:p['role'])
@pytest.mark.parametrize('variant', range(4))
def test_each_library_match_has_legal_elevens_and_connected_varied_actions(profile, variant):
    mid = 'library-'+profile['role']
    raw = matchday.library_fixture(profile, mid, variant)
    assert raw == matchday.library_fixture(profile, mid, variant)
    assert 500 < len(raw) < security.MAX_EVENTS
    active = {side:{f'{side}-{slot}' for slot in club_for_name(profile[side])['demo_lineup']}
              for side in ('home','away')}
    starters = {side:players.copy() for side,players in active.items()}
    assert all(sum(player['position']=='GK' for player in
                   [matchday.player_for_slot(profile[side],slot)
                    for slot in club_for_name(profile[side])['demo_lineup']])==1
               for side in active)
    passing = {side:set() for side in active}
    chains, previous = {}, None
    cfg = matchday.versioned_profile(profile, variant)
    card_cfg = cfg.get('red_card')
    for index, row in enumerate(raw, 1):
        event = MatchEvent(**row)
        assert event.sequence == index
        assert event.player_id in active[event.team_id]
        if previous:
            assert event.match_second >= previous.match_second
            assert event.period >= previous.period
            if previous.type == 'pass' and event.type in ('pass','shot'):
                assert previous.outcome == 'complete'
                assert event.player_id == previous.recipient_player_id
                assert (event.x,event.y) == (previous.end_x,previous.end_y)
                assert event.possession_id == previous.possession_id
        if event.type == 'substitution':
            assert event.recipient_player_id not in active[event.team_id]
            active[event.team_id].remove(event.player_id)
            active[event.team_id].add(event.recipient_player_id)
        if event.type == 'red_card':
            assert event.player_id in active[event.team_id]
            active[event.team_id].remove(event.player_id)
        if event.type == 'pass':
            assert event.recipient_player_id in active[event.team_id]
            assert event.recipient_player_id != event.player_id
            if event.match_second < 2700:
                passing[event.team_id].update((event.player_id,event.recipient_player_id))
            chains[event.possession_id] = chains.get(event.possession_id,0)+1
        if event.type == 'shot':
            assert event.player_position != 'GK'
        if event.type == 'goal':
            assert previous.type == 'shot' and previous.outcome == 'goal'
            assert event.related_event_id == previous.event_id
        carded_side = card_cfg['team'] if card_cfg and event.match_second >= card_cfg['second'] else None
        assert all(len(players) == (10 if side == carded_side else 11) for side, players in active.items())
        previous = event
    assert all(starters[side] <= passing[side] for side in starters)
    assert {2,3,4} <= set(chains.values())
    assert sum(e['type']=='half_end' for e in raw)==1
    assert raw[-1]['type']=='match_end' and raw[-1]['match_second']==5580


def test_library_versions_change_stories_not_just_names():
    for profile in matchday.PROFILES:
        feeds=[matchday.library_fixture(profile,'same',v) for v in range(3)]
        signatures=[[(e['type'],e['match_second'],e['team_id']) for e in feed
                     if e['type'] in ('shot','goal')] for feed in feeds]
        assert len({json.dumps(s) for s in signatures})==3
        routes=[[(e['player_id'],e['recipient_player_id']) for e in feed if e['type']=='pass'] for feed in feeds]
        assert len({json.dumps(r) for r in routes})==3


def test_bundled_exports_match_all_nine_prepared_versions():
    output=Path(__file__).resolve().parents[2]/'data/synthetic'
    manifest=json.loads((output/'manifest.json').read_text())
    assert len(manifest['scenarios'])==9
    for row in manifest['scenarios']:
        metadata=next(item for item in matchday.DEMO_FIXTURES if item['id']==row['fixture_id'])
        profile=next(p for p in matchday.PROFILES if p['role']==metadata['role'])
        rows=[json.loads(line) for line in (output/row['file']).read_text().splitlines()]
        assert len(rows)==row['event_count']
        assert rows==matchday.library_fixture(profile,row['id'],row['variant_id']-1)


def test_selection_covers_all_64_combinations_and_reopening_does_not_reroll():
    combinations={tuple(matchday.selected_variant(f'day-{i}-{p["role"]}') for p in matchday.PROFILES)
                  for i in range(1000)}
    assert combinations==set(itertools.product(range(4),repeat=3))
    with TestClient(main.app, headers={'X-MatchOS-Client':'replay'}) as client:
        client.post('/api/session',json={}).raise_for_status()
        first=client.post('/api/matchdays/start',json={'matchday_id':'library-session'}).json()
        selections={entry['match_id']:entry['variant_id'] for entry in first['matches']}
        fingerprints={mid:json.dumps(security.matches[mid]['fixture']) for mid in selections}
        assert all(entry['event_count']==1 for entry in first['matches'])
        assert all(len(lineup)==11 for entry in first['matches'] for lineup in entry['starting_lineups'].values())
        for tick in (1,2):
            client.post('/api/matchdays/library-session/tick',json={'tick':tick}).raise_for_status()
        reopened=client.post('/api/matchdays/start',json={'matchday_id':'library-session'}).json()
        assert reopened['tick']==2
        assert {e['match_id']:e['variant_id'] for e in reopened['matches']}==selections
        assert {mid:json.dumps(security.matches[mid]['fixture']) for mid in selections}==fingerprints
        assert all(e['pulse']['score']=={'home':0,'away':0} for e in reopened['matches'])
        assert all('fixture' not in entry and 'seed' not in entry for entry in reopened['matches'])


def test_all_combinations_rank_observed_action_allow_quiet_and_each_fixture_can_lead():
    pulses={}
    for profile in matchday.PROFILES:
        for variant in range(3):
            events=[MatchEvent(**e) for e in matchday.library_fixture(profile,profile['role'],variant)]
            for now in range(0,5581,30):
                pulses[profile['role'],variant,now]=matchday.pulse(events,now)
            for now in (900,1200,3600,4530,5580):
                assert matchday.pulse(events,now)==matchday.pulse([e for e in events if e.match_second<=now],now)
    leaders=set()
    quiet_combination=(1,2,0)
    for combination in itertools.product(range(3),repeat=3):
        for now in range(0,5581,30):
            entries=[{'match_id':p['role'],'pulse':pulses[p['role'],v,now]}
                     for p,v in zip(matchday.PROFILES,combination)]
            ranked=matchday.rank(entries)
            assert all(e['pulse']['eligible'] for e in ranked)
            if combination==quiet_combination:
                assert ranked==[]
            if ranked:
                leaders.add(ranked[0]['match_id'])
    assert leaders=={p['role'] for p in matchday.PROFILES}


@pytest.mark.parametrize('profile', matchday.PROFILES, ids=lambda p:p['role'])
@pytest.mark.parametrize('variant', range(4))
def test_new_library_keeps_recap_evidence_bounded_and_source_linked(profile,variant):
    events=[MatchEvent(**e) for e in matchday.library_fixture(profile,'recap-'+profile['role'],variant)]
    for now in (1200,2700,4530,5580):
        observed=[e for e in events if e.match_second<=now]
        fan=main.build_catch_up(observed,CatchUpRequest())['fan_briefing']
        assert set(fan['evidence_event_ids']) <= {e.event_id for e in observed}
        packet=story_writer.evidence_packet(fan,observed)
        assert len(json.dumps(packet,ensure_ascii=False).encode())<=32768
