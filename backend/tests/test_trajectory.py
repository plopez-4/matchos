import pytest
from app.intelligence import score_trajectory
from app.fan_briefing import fan_briefing
from test_fan_briefing import event


@pytest.mark.parametrize('teams,kinds', [
    (['home','home','home'], ['lead_acquisition','lead_extension','lead_extension']),
    (['away','away','home'], ['lead_acquisition','lead_extension','deficit_reduction']),
    (['away','home','away','home'], ['lead_acquisition','equalization','lead_acquisition','equalization']),
    (['away','home','home'], ['lead_acquisition','equalization','lead_reversal']),
])
def test_transition_categories_and_evidence(teams,kinds):
    goals = [event(i+1,100+i*60,'goal',team) for i,team in enumerate(teams)]
    result = score_trajectory(list(reversed(goals)))
    assert [t['type'] for t in result['transitions']] == kinds
    assert result['evidence_event_ids'] == [e.event_id for e in goals]
    for index,transition in enumerate(result['transitions']):
        assert sum(transition['before'].values()) == index
        assert sum(transition['after'].values()) == index+1
    if teams == ['away','home','away','home']:
        assert result['equalizers']['home'] == 2
        assert result['lead_acquisitions']['away'] == 2


def test_response_requires_opponent_goal_and_ten_minute_boundary():
    same = score_trajectory([event(1,0,'goal'),event(2,100,'goal')])
    assert same['transitions'][-1]['rapid_response'] is None
    for elapsed,qualifies in [(600,True),(601,False)]:
        result = score_trajectory([event(1,0,'goal','away'),event(2,elapsed,'goal')])
        assert bool(result['transitions'][-1]['rapid_response']) == qualifies


def test_exact_trajectory_window_clock_and_no_future_goal():
    from app.matchday import PROFILES, fixture
    from app.models import MatchEvent
    events = [MatchEvent(**raw) for raw in fixture(PROFILES[1],'trajectory')]
    early = fan_briefing(events,[e for e in events if e.match_second <= 4500],now=4500)
    later = fan_briefing(events,[e for e in events if e.match_second <= 4530],now=4530)
    assert early['trajectory']['score'] == {'home':1,'away':2}
    assert len(early['trajectory']['transitions']) == 3
    assert later['headline'] == 'Newcastle United led twice. Crystal Palace have answered twice.'
    assert 'Compared with 1 total' in early['sections'][1]['text']
    assert 'Compared with 2 total' in later['sections'][1]['text']
    assert later['window'] == {'start_exclusive':4230,'end_inclusive':4530}
    assert later['sections'][2]['text'] == '14:30 until 90 minutes, plus added time.'
    assert '?' not in ' '.join(s['text'] for s in later['sections'])
    assert score_trajectory([])['transitions'] == []
