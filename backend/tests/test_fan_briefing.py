import pytest
from app.fan_briefing import fan_briefing
from app.models import MatchEvent
from app.matchday import fixture, PROFILES


def event(sequence, second, kind, team='home'):
    return MatchEvent(event_id=f'e{sequence}', match_id='m', sequence=sequence,
                      match_second=second, team_id=team, team_name='Palace' if team == 'home' else 'Newcastle',
                      player_id=f'{team}-9', type=kind, x=50, y=50)


def test_equalizer_and_two_way_burst_are_a_story_with_inspectable_facts():
    events = [event(1,0,'kickoff'), event(2,100,'goal','away')]
    events += [event(i+3,420+i*30,'shot','home' if i%2 else 'away') for i in range(4)]
    events += [event(7,590,'goal'),event(8,600,'pass')]
    result = fan_briefing(events,events[2:])
    assert result['headline'] == 'Palace have pulled level'
    assert result['scoreline'] == 'Palace 1–1 Newcastle'
    assert 'Compared with 0 total' in result['sections'][1]['text']
    assert result['sections'][2]['text'] == '80:00 until 90 minutes, plus added time.'
    assert 'e2' in result['evidence_event_ids']  # Earlier goal supports current score.
    assert set(result['evidence_event_ids']) <= {e.event_id for e in events}
    assert not any(word in result['sections'][1]['text'] for word in ('dominat', 'dangerous', 'pressure'))


@pytest.mark.parametrize('prior,team,phrase', [
    ([], 'home', 'taken the lead'),
    (['home'], 'home', 'extended their lead'),
    (['away','away'], 'home', 'pulled a goal back'),
])
def test_goal_headlines_follow_the_actual_score(prior,team,phrase):
    events = [event(i+1, i*30,'goal',side) for i,side in enumerate(prior)]
    newest = event(len(events)+1,120,'goal',team)
    result = fan_briefing(events+[newest],[newest])
    assert phrase in result['headline']


def test_incomplete_coverage_never_claims_a_comparison_or_looks_ahead():
    events = [event(i+1,500+i*20,'shot','home' if i%2 else 'away') for i in range(4)]
    last = event(5,600,'pass')
    result = fan_briefing(events+[last,event(6,900,'goal')],events+[last])
    assert 'comparison is unavailable' in result['sections'][1]['text']
    assert result['scoreline'] == 'Palace 0–0 Newcastle'
    assert 'e6' not in result['evidence_event_ids']


def test_quiet_and_finished_games_do_not_invent_live_drama():
    events = [event(1,0,'kickoff'),event(2,600,'pass')]
    quiet = fan_briefing(events,events)
    assert 'No shots recorded' in quiet['sections'][1]['text']
    assert '?' not in quiet['headline']
    finished = event(3,5580,'match_end')
    recap = fan_briefing(events+[finished],[finished])
    assert 'final whistle' in recap['headline']
    assert 'finished' in recap['sections'][2]['text']
    assert 'next goal' not in recap['sections'][2]['text']
    assert fan_briefing(events,[]) is None


def test_whole_match_keeps_every_goal_accessible_and_stays_concise():
    events = [MatchEvent(**raw) for raw in fixture(PROFILES[1], 'fan-test')]
    result = fan_briefing(events,events)
    goals = [e for e in events if e.type == 'goal']
    assert len(goals) == 4
    assert set(e.event_id for e in goals) <= set(result['evidence_event_ids'])
    assert len(result['trajectory']['transitions']) == 4
    assert sum(len(s['text'].split()) for s in result['sections']) < 100
