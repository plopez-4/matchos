from app.fan_briefing import fan_briefing
from app.historical_context import historical_precedent
from app.models import MatchEvent
from app.matchday import fixture, PROFILES
import pytest


def event(sequence, second, kind, team='home'):
    return MatchEvent(event_id=f'h{sequence}', match_id='history-test', sequence=sequence,
                      match_second=second, team_id=team, player_id='p1', type=kind, x=50, y=50)


@pytest.mark.parametrize('goals,phase,expected', [
    (['home'], 'half_end', True), (['away'], 'half_end', True),
    ([], 'half_end', False), (['home','home'], 'half_end', False),
    (['home'], 'pass', False), (['home'], 'match_end', False),
])
def test_benchmark_only_at_observed_halftime_with_one_goal_lead(goals, phase, expected):
    events = [event(1, 0, 'kickoff')]
    events += [event(i+2, 600+i*60, 'goal', team) for i,team in enumerate(goals)]
    boundary = event(len(events)+1, 2700, phase)
    result = fan_briefing(events+[boundary], [boundary])
    assert bool(result['historical_precedent']) is expected
    if expected:
        benchmark = result['historical_precedent']
        assert benchmark['sample_size'] == 156
        assert benchmark['wins'] == 113
        assert 'not a prediction' in benchmark['caveat']['en']
        assert benchmark['wins'] + benchmark['draws'] + benchmark['losses'] == benchmark['sample_size']
        assert benchmark['win_percentage'] == round(100 * benchmark['wins'] / benchmark['sample_size'], 1)
        assert '2016–17' in benchmark['text']['en']
        assert '2016–17' in benchmark['text']['es']
        assert benchmark['source'] not in result['evidence_event_ids']


def test_future_halftime_does_not_trigger_context_and_second_half_clears_it():
    events = [event(1,0,'kickoff'), event(2,600,'goal'), event(3,2700,'half_end')]
    assert fan_briefing(events, events[:2], now=2699)['historical_precedent'] is None
    restarted = event(4,2700,'kickoff')
    assert fan_briefing(events+[restarted], [restarted])['historical_precedent'] is None
    assert historical_precedent('finished', {'home':1,'away':0}) is None


def test_real_matchday_fixture_exposes_halftime_then_second_half():
    events = [MatchEvent(**raw) for raw in fixture(PROFILES[1], 'history-day')]
    halftime = fan_briefing(events, events, now=2700)
    assert halftime['historical_precedent']['sample_size'] == 156
    assert halftime['locale_facts']['phase'] == 'halftime'
    assert 'final whistle' not in halftime['headline']
    second_half = fan_briefing(events, events, now=2701)
    assert second_half['historical_precedent'] is None
    assert second_half['locale_facts']['phase'] == 'playing'
