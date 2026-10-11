import pytest
from fastapi.testclient import TestClient
from app import security, matchday
from app.main import app, store
from app.models import MatchEvent

HEADERS = {"X-MatchOS-Client":"replay"}


def client():
    result = TestClient(app, headers=HEADERS)
    assert result.post('/api/session', json={}).status_code == 200
    return result


def start(c, day='test-day'):
    response = c.post('/api/matchdays/start', json={'matchday_id':day})
    assert response.status_code == 200
    return response.json()


def tick_to(c, view, second):
    while view['clock_second'] < second:
        response = c.post(f'/api/matchdays/{view["matchday_id"]}/tick', json={'tick':view['tick']+1})
        assert response.status_code == 200, response.text
        view = response.json()
    return view


@pytest.mark.parametrize('profile', matchday.PROFILES, ids=lambda p:p['role'])
def test_authored_feed_is_reproducible_and_valid(profile):
    raw = matchday.fixture(profile, 'fixture')
    assert raw == matchday.fixture(profile, 'fixture')
    events = [MatchEvent(**e) for e in raw]
    assert len(events) < security.MAX_EVENTS
    assert events[-1].match_second == 5580 and events[-1].type == 'match_end'
    assert sum(e.type == 'half_end' for e in events) == 1
    assert [e.sequence for e in events] == list(range(1,len(events)+1))
    for previous, event in zip(events, events[1:]):
        assert previous.match_second <= event.match_second
        assert previous.period <= event.period
        if previous.type == 'pass' and event.type in ('pass','shot'):
            assert (event.player_id,event.x,event.y) == (previous.recipient_player_id,previous.end_x,previous.end_y)
        if previous.type == 'goal':
            assert event.type == 'kickoff' and event.team_id != previous.team_id
        if event.type == 'goal':
            assert previous.type == 'shot' and previous.outcome == 'goal'
            assert event.related_event_id == previous.event_id


def test_shared_clock_future_blind_recommendation_and_quiet_restraint():
    c = client()
    view = start(c)
    assert len(view['matches']) == 3 and view['recommendation'] is None
    assert all(item['event_count'] == 1 for item in view['matches'])
    assert not any('fixture' in item for item in view['matches'])
    # A prominent match can legitimately win: no hardcoded smaller-club boost.
    view = tick_to(c, view, 1200)
    assert view['recommendation']['role'] == 'featured'
    assert view['recommendation']['pulse']['rating'] >= 65
    # At 69 minutes the authored late burst has not happened: no future inference.
    view = tick_to(c, view, 4140)
    assert view['recommendation'] is None
    assert all(e.match_second <= 4140 for feed in store.values() for e in feed.values())
    view = tick_to(c, view, 4530)
    assert view['recommendation']['role'] == 'comeback'
    assert view['recommendation']['pulse']['score'] == {'home':2,'away':2}
    assert not next(item for item in view['matches'] if item['role'] == 'quiet')['pulse']['eligible']
    for entry in view['matches']:
        received = store[entry['match_id']]
        assert set(entry['pulse']['evidence_event_ids']) <= received.keys()
        assert all(e['match_second'] <= view['clock_second'] for e in entry['pulse']['evidence_events'])
    # Quiet finishes do not keep a stale exciting recommendation alive.
    view = tick_to(c, view, 5100)
    assert view['recommendation'] is None
    view = tick_to(c, view, 5580)
    assert view['finished'] and view['recommendation'] is None


def test_ownership_retry_sequence_and_no_individual_clock_bypass():
    c, stranger = client(), client()
    view = start(c)
    assert stranger.post('/api/matchdays/start', json={'matchday_id':'test-day'}).status_code == 403
    assert stranger.post('/api/matchdays/test-day/tick', json={'tick':1}).status_code == 403
    assert c.post('/api/matchdays/test-day/tick', json={'tick':2}).status_code == 409
    first = c.post('/api/matchdays/test-day/tick', json={'tick':1}).json()
    assert c.post('/api/matchdays/test-day/tick', json={'tick':1}).json() == first
    mid = view['matches'][0]['match_id']
    assert c.post(f'/api/matches/{mid}/advance', json={'sequence':2}).status_code == 409
    assert stranger.get('/api/matchdays/test-day').status_code == 200


def test_capacity_is_atomic_and_expiry_cleans_matchday(monkeypatch):
    c = client()
    monkeypatch.setattr(security, 'MAX_MATCHES', 2)
    assert c.post('/api/matchdays/start', json={'matchday_id':'too-big'}).status_code == 429
    assert store == {} and security.matches == {}
    monkeypatch.setattr(security, 'MAX_MATCHES', 64)
    view = start(c)
    for entry in view['matches']:
        security.matches[entry['match_id']]['expires'] = 0
    assert c.get('/api/matchdays/test-day').status_code == 404
    assert store == {}


def test_only_owner_can_release_group_and_capacity_is_reusable():
    c, other = client(), client()
    start(c)
    assert other.request('DELETE', '/api/matchdays/test-day',json={}).status_code == 403
    assert c.request('DELETE', '/api/matchdays/test-day',json={}).status_code == 200
    assert store == {} and security.matches == {}
    start(c, 'another-day')


def test_partial_group_release_preserves_ownership_and_other_matches():
    owner, other = client(), client()
    view = start(owner)
    other_view = start(other, 'other-day')
    store.pop(view['matches'][0]['match_id'])
    assert owner.get('/api/matchdays/test-day').status_code == 404
    assert other.request('DELETE', '/api/matchdays/test-day', json={}).status_code == 403
    assert owner.request('DELETE', '/api/matchdays/test-day', json={}).status_code == 200
    assert set(store) == {item['match_id'] for item in other_view['matches']}
    assert set(security.matches) == set(store)
    start(owner, 'replacement')


def test_window_metadata_matches_zero_and_exact_boundary():
    zero = MatchEvent(event_id='zero', match_id='m', sequence=1, match_second=0,
                      team_id='home', player_id='home-9', type='shot', x=50, y=50)
    early = matchday.pulse([zero], 120)
    assert early['window'] == {'start_exclusive':-1,'end_inclusive':120}
    assert early['shots_last_five']['home'] == 1
    boundary = matchday.pulse([zero], 300)
    assert boundary['window']['start_exclusive'] == 0
    assert boundary['shots_last_five']['home'] == 0


def test_notifications_are_transition_based_and_idempotent():
    c = client()
    view = start(c)
    alerts = []
    while not view['finished']:
        response = c.post('/api/matchdays/test-day/tick', json={'tick':view['tick']+1})
        assert response.status_code == 200
        view = response.json()
        if view['notification']:
            assert c.post('/api/matchdays/test-day/tick', json={'tick':view['tick']}).json()['notification'] == view['notification']
            alerts.append(view['notification'])
    assert len(alerts) >= 2
    assert len({alert['id'] for alert in alerts}) == len(alerts)
    for a,b in zip(alerts,alerts[1:]):
        if a['match_id'] == b['match_id']:
            assert b['clock_second']-a['clock_second'] >= 600


def test_ranking_rejects_one_sided_volume_and_is_deterministic():
    def event(seq, team, kind, second=4400):
        return MatchEvent(event_id=f'e{seq}',match_id='m',sequence=seq,match_second=second,
                          team_id=team,player_id=f'{team}-9',type=kind,x=80,y=50)
    unilateral = [event(i,'home','shot') for i in range(1,11)]
    assert not matchday.pulse(unilateral,4500)['eligible']
    balanced = [event(i, 'home' if i%2 else 'away', 'shot') for i in range(1,5)]
    pulse = matchday.pulse(balanced,4500)
    assert pulse['eligible']
    entries = [{'match_id':mid,'pulse':pulse} for mid in ('b','a')]
    assert [e['match_id'] for e in matchday.rank(entries)] == ['a','b']
    assert matchday.pulse(balanced,5580)['suppression_reason'] == 'finished'


def test_window_boundary_no_future_inputs_and_briefing(monkeypatch):
    profile = matchday.PROFILES[1]
    feed = [MatchEvent(**e) for e in matchday.fixture(profile,'m')]
    assert matchday.pulse(feed,4140) == matchday.pulse([e for e in feed if e.match_second <= 4140],4140)
    now = 4510
    result = matchday.pulse(feed,now)
    shots = [e for e in feed if now-300 < e.match_second <= now and e.type == 'shot']
    assert sum(result['shots_last_five'].values()) == len(shots)
    monkeypatch.setenv('MATCHOS_AI_MODE','off')
    c = client()
    view = tick_to(c,start(c),4530)
    mid = view['recommendation']['match_id']
    briefing = c.post(f'/api/matches/{mid}/catch-up',json={})
    assert briefing.status_code == 200
    assert 'Crystal Palace' in briefing.json()['match_briefing']['text']
