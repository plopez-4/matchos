import json
import time
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from app import security
from app.main import app, store
from app.simulation import generate
from app.explanations import explain

HEADERS = {"X-MatchOS-Client": "replay"}


def browser():
    client = TestClient(app, headers=HEADERS)
    assert client.post('/api/session', json={}).status_code == 200
    return client


def start(client, mid='private', scenario='united-city-90'):
    return client.post('/api/replay/start', json={'match_id':mid, 'scenario_id':scenario})


def test_untrusted_writes_and_cross_session_tampering_are_denied():
    owner, other = browser(), browser()
    events = start(owner).json()
    assert other.post('/api/events', json=events[0]).status_code == 401
    assert start(other).status_code == 403
    assert other.post('/api/matches/private/advance', json={'sequence':1}).status_code == 403
    assert owner.post('/api/matches/private/advance', json={**events[0], 'sequence':1}).status_code == 422
    assert owner.post('/api/matches/private/advance', json={'sequence':2}).status_code == 409
    assert owner.post('/api/matches/private/advance', json={'sequence':1}).status_code == 201
    assert owner.post('/api/matches/private/advance', json={'sequence':1}).json()['accepted'] is False
    assert owner.get('/api/matches/private/events').json() == events[:1]
    # Public synthetic match reads are deliberate; they carry no private user data.
    assert other.get('/api/matches/private/events').json() == events[:1]


def test_disabled_ingestion_and_missing_session(monkeypatch):
    monkeypatch.delenv('MATCHOS_INGEST_TOKEN')
    client = TestClient(app, headers=HEADERS)
    assert client.post('/api/events', json=next(generate())).status_code == 401
    assert start(client).status_code == 401


def test_csrf_host_body_and_security_headers():
    client = TestClient(app)
    assert client.post('/api/session', json={}).status_code == 403
    assert client.post('/api/session', json={}, headers={**HEADERS,'Origin':'https://evil.example'}).status_code == 403
    assert client.get('/api/health', headers={'Host':'evil.example'}).status_code == 400
    assert client.post('/api/session', content='x'*8193, headers={**HEADERS,'Content-Type':'application/json'}).status_code == 413
    response = client.get('/api/health')
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['cache-control'] == 'no-store'


def test_chunked_body_limit_without_content_length():
    client = TestClient(app, headers=HEADERS)
    assert client.post('/api/session', content=iter([b'x'*5000, b'x'*5000]), headers={'Content-Type':'application/json'}).status_code == 413


def test_expiry_and_capacity_are_enforced(monkeypatch):
    client = browser()
    assert start(client).status_code == 200
    security.matches['private']['expires'] = time.monotonic()-1
    assert client.get('/api/matches/private/events').json() == []
    assert 'private' not in store
    monkeypatch.setattr(security, 'MAX_MATCHES', 1)
    assert start(client, 'one').status_code == 200
    assert start(client, 'two').status_code == 503
    security.sessions[next(iter(security.sessions))] = time.monotonic()-1
    assert client.post('/api/matches/one/advance', json={'sequence':1}).status_code == 401


def test_event_limit_and_ai_cache(monkeypatch):
    client = browser()
    start(client)
    monkeypatch.setattr(security, 'MAX_EVENTS', 1)
    assert client.post('/api/matches/private/advance', json={'sequence':1}).status_code == 201
    assert client.post('/api/matches/private/advance', json={'sequence':2}).status_code == 429
    with patch('app.main.explain', return_value={'text':'', 'selected_story_ids':[]}) as mocked:
        a = client.post('/api/matches/private/catch-up', json={})
        b = client.post('/api/matches/private/catch-up', json={})
        assert a.status_code == b.status_code == 200
        assert a.json() == b.json()
        assert mocked.call_count == 1
    assert client.post('/api/matches/private/catch-up', json={'since_sequence':999}).status_code == 422


def test_catch_cache_is_invalidated_by_revision_and_match_generation():
    client = browser()
    start(client)
    with patch('app.main.explain', return_value={'text':'', 'selected_story_ids':[]}) as mocked:
        assert client.post('/api/matches/private/catch-up', json={}).status_code == 200
        client.post('/api/matches/private/advance', json={'sequence':1})
        assert client.post('/api/matches/private/catch-up', json={}).status_code == 200
        # Reusing a display ID cannot serve a cached result from an older replay.
        security.matches['private']['generation'] = 'new-generation'
        assert client.post('/api/matches/private/catch-up', json={}).status_code == 200
        assert mocked.call_count == 3


def test_rate_limits_and_bounded_counters(monkeypatch):
    client = browser()
    for _ in range(20):
        assert client.post('/api/matches/none/catch-up', json={}).status_code == 200
    response = client.post('/api/matches/none/catch-up', json={})
    assert response.status_code == 429 and response.headers['retry-after'] == '60'
    security.rates.clear()
    for n in range(1024):
        assert security.allow_request(('address',n), 1)
    assert not security.allow_request(('overflow',), 1)


def test_provider_budget_payload_and_output_caps(monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'fixture')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'test-placeholder')
    story = {'story_id':'goal', 'kind':'goal', 'text':'Home scored.', 'rule_version':'v1', 'evidence_event_ids':['e1']}
    calls = []
    def fail(request):
        calls.append(json.loads(request.content))
        return httpx.Response(500)
    monkeypatch.setenv('MATCHOS_AI_CALL_BUDGET', '2')
    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        assert explain([story], 'casual', client)['fallback_reason'] == 'provider_or_validation_failure'
        result = explain([story], 'casual', client)
        assert result['fallback_reason'] == 'ai_budget_or_concurrency_limit'
        assert 'Home scored.' in result['text']
        assert len(calls) == 1 and calls[0]['max_completion_tokens'] == 512
        assert security.ai_active == 0
        oversized = {**story, 'evidence_event_ids':['x'*33000]}
        assert explain([oversized], 'casual', client)['fallback_reason'] == 'evidence_payload_limit'


def test_production_requires_https_and_secure_cookie(monkeypatch):
    monkeypatch.setenv('MATCHOS_ENV', 'production')
    assert TestClient(app).get('/api/health').status_code == 400
    client = TestClient(app, base_url='https://testserver', headers=HEADERS)
    response = client.post('/api/session', json={})
    assert response.status_code == 200
    cookie = response.headers['set-cookie']
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=strict' in cookie
    assert "script-src 'self'" in response.headers['content-security-policy']
    assert client.get('/docs').status_code == 404


def test_busy_catch_up_fails_fast_and_ai_concurrency_is_bounded(monkeypatch):
    from app.main import CATCH_LOCK
    client = browser()
    CATCH_LOCK.acquire()
    try:
        assert client.post('/api/matches/none/catch-up', json={}).status_code == 429
    finally:
        CATCH_LOCK.release()
    assert security.take_ai_budget()
    assert security.take_ai_budget()
    assert not security.take_ai_budget()
    security.release_ai()
    security.release_ai()


@pytest.mark.parametrize('scenario', ['united-city-90','palace-newcastle-90','brighton-fulham-90'])
def test_full_match_uses_only_canonical_replay_and_retains_briefing(scenario, monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    client = browser()
    fixture = start(client, scenario, scenario).json()
    for event in fixture:
        response = client.post(f'/api/matches/{scenario}/advance', json={'sequence':event['sequence']})
        assert response.status_code == 201 and response.json()['accepted']
    assert client.get(f'/api/matches/{scenario}/events').json() == fixture
    result = client.post(f'/api/matches/{scenario}/catch-up', json={})
    assert result.status_code == 200
    assert result.json()['through_sequence'] == len(fixture)
    assert fixture[0]['team_name'] in result.json()['match_briefing']['text']
