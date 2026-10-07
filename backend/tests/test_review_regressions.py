import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app, store
from app.models import MatchEvent
from app.simulation import generate
from app.intelligence import match_stories, progressive_pass_windows
from app.explanations import explain, select_candidates


def test_legacy_matches_original_evidence_and_retries_without_conflicts():
    original = json.loads((Path(__file__).parent / 'fixtures/legacy-seed7.json').read_text())
    assert list(generate()) == original
    store.clear()
    with TestClient(app) as client:
        for event in original:
            assert client.post('/api/events', json=event).json()['accepted']
        for event in generate():
            result = client.post('/api/events', json=event)
            assert result.status_code == 201
            assert result.json()['accepted'] is False


@pytest.mark.parametrize('team', ['home', 'away'])
@pytest.mark.parametrize('missing', ['end_x', 'end_y'])
def test_progressive_pass_requires_both_end_coordinates(team, missing):
    start, end = (50, 70) if team == 'home' else (50, 30)
    events = [MatchEvent(event_id='kickoff', match_id='m', sequence=1, match_second=0,
                         team_id=team, player_id='player', type='kickoff', x=50, y=50)]
    for index in range(3):
        payload = dict(event_id=f'pass-{index}', match_id='m', sequence=index+2,
                       match_second=100+index*10, team_id=team, player_id='player',
                       type='pass', x=start, y=50, end_x=end, end_y=50, outcome='complete')
        payload.pop(missing)
        events.append(MatchEvent(**payload))
    events.append(MatchEvent(event_id='end', match_id='m', sequence=5, match_second=300,
                             team_id=team, player_id='player', type='recovery', x=50, y=50))
    windows = progressive_pass_windows(events)
    assert all(window['pass_count'] == 0 for window in windows)
    assert not any(story['kind'] == 'progressive_pass' for story in match_stories(events))


def configure_azure(monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'test-placeholder')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'fixture-deployment')


@pytest.mark.parametrize('goal_count,with_change', [(9, False), (8, True)])
def test_candidate_overflow_preserves_all_facts_without_provider(monkeypatch, goal_count, with_change):
    configure_azure(monkeypatch)
    stories = [dict(story_id=f'goal-{i}', kind='goal', sequence=i+1,
                    text=f'Goal {i}.', evidence_event_ids=[f'event-{i}'], rule_version='goal-v1')
               for i in range(goal_count)]
    if with_change:
        stories.append(dict(story_id='change', kind='shot_activity', sequence=20,
                            text='Home recorded increased shooting activity.',
                            evidence_event_ids=['shot-1'], rule_version='shot-frequency-v1'))
    with pytest.raises(ValueError, match='budget'):
        select_candidates(stories)
    def unexpected_request(request):
        pytest.fail('Overflow must skip the provider')
    with httpx.Client(transport=httpx.MockTransport(unexpected_request)) as client:
        result = explain(stories, 'casual', client)
    assert result['mode'] == 'deterministic'
    assert result['fallback_reason'] == 'candidate_budget_or_identity_failure'
    assert result['selected_story_ids'] == [s['story_id'] for s in stories]
    assert result['sections'][0]['story_ids'] == [s['story_id'] for s in stories if s['kind'] == 'goal']
    if with_change:
        assert result['sections'][1]['story_ids'] == ['change']


def test_duplicate_candidate_ids_are_rejected():
    story = dict(story_id='same', kind='goal', sequence=1)
    with pytest.raises(ValueError, match='Duplicate'):
        select_candidates([story, dict(story, sequence=2)])


def test_quiet_scenario_skips_azure_entirely(monkeypatch):
    configure_azure(monkeypatch)
    stories = match_stories([MatchEvent(**e) for e in generate(scenario_id='quiet-match')])
    assert stories == []
    def unexpected_request(request):
        pytest.fail('Quiet fixture must skip the provider')
    with httpx.Client(transport=httpx.MockTransport(unexpected_request)) as client:
        result = explain(stories, 'advanced', client)
    assert result['sections'] == []
    assert result['text'] == ''
