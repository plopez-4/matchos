import json
import httpx
import pytest
from app.explanations import explain

STORIES = [
    {'story_id': 'goal:1', 'kind': 'goal', 'text': 'Home scored.', 'evidence_event_ids': ['shot-1', 'goal-1'], 'rule_version': 'goal-v1'},
    {'story_id': 'shots:home:600', 'kind': 'shot_activity', 'text': 'Home recorded four shots.', 'evidence_event_ids': ['shot-1'], 'rule_version': 'shot-frequency-v1'},
]

@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'fixture-deployment')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'test-placeholder')

def provider(selected):
    requests = []
    def handle(request):
        payload = json.loads(request.content)
        requests.append(payload)
        name = payload['tools'][0]['function']['name']
        arguments = {} if name == 'get_match_evidence' else {'story_ids': selected}
        return httpx.Response(200, json={'choices': [{'message': {'role': 'assistant', 'tool_calls': [
            {'id': f'call-{len(requests)}', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments)}}]}}]})
    return httpx.Client(transport=httpx.MockTransport(handle)), requests

@pytest.mark.parametrize('endpoint', ['https://fixture.openai.azure.com/openai/v1', 'https://fixture.services.ai.azure.com/openai/v1'])
def test_tool_flow_and_known_fact_rendering(configured, monkeypatch, endpoint):
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', endpoint)
    client, requests = provider(['shots:home:600', 'goal:1'])
    with client:
        result = explain(STORIES, 'advanced', client)
    assert result['mode'] == 'azure'
    assert result['text'] == 'What happened: Home scored. What changed: Home recorded four shots.'
    assert len(requests) == 2
    evidence = json.loads(requests[1]['messages'][-1]['content'])
    assert evidence[0]['evidence_event_ids'] == ['shot-1', 'goal-1']
    assert result['trace'][-1]['status'] == 'ok'

@pytest.mark.parametrize('ids', [['invented'], ['shots:home:600'], ['goal:1', 'goal:1'], []])
def test_unsupported_selection_falls_back(configured, ids):
    client, _ = provider(ids)
    with client:
        result = explain(STORIES, 'casual', client)
    assert result['mode'] == 'deterministic'
    assert result['text'] == 'What happened: Home scored. What changed: Home recorded four shots.'
    assert result['fallback_reason'] == 'provider_or_validation_failure'

def test_provider_timeout_falls_back(configured):
    def timeout(request):
        raise httpx.ReadTimeout('test timeout', request=request)
    with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
        result = explain(STORIES, 'casual', client)
    assert result['mode'] == 'deterministic'
    assert 'test timeout' not in json.dumps(result)

def test_bad_endpoint_never_sends_key(configured, monkeypatch):
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://untrusted.example/openai/v1')
    client, requests = provider(['goal:1'])
    with client:
        result = explain(STORIES, 'casual', client)
    assert result['fallback_reason'] == 'configuration_incomplete'
    assert requests == []

def test_disabled_and_empty_skip_provider(monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    assert explain(STORIES, 'casual')['fallback_reason'] == 'ai_disabled'
    assert explain([], 'casual')['text'] == ''

def test_goal_only_selection_adds_verified_change(configured):
    client, _ = provider(['goal:1'])
    with client:
        result = explain(STORIES, 'casual', client)
    assert result['mode'] == 'azure'
    assert result['selected_story_ids'] == ['goal:1', 'shots:home:600']
    assert [s['title'] for s in result['sections']] == ['What happened', 'What changed']
    assert any(t['step'] == 'complete_coverage' for t in result['trace'])

def test_casual_and_advanced_share_evidence(monkeypatch):
    from app.intelligence import match_stories
    from app.models import MatchEvent
    from simulator.run import generate
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    stories = match_stories([MatchEvent(**e) for e in generate()])
    casual = explain(stories, 'casual')
    advanced = explain(stories, 'advanced')
    assert 'took more shots' in casual['text']
    assert 'recorded 4 shots' in advanced['text']
    assert [s['evidence_event_ids'] for s in casual['sections']] == [s['evidence_event_ids'] for s in advanced['sections']]
