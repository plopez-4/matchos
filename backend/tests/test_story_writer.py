import copy
import json
import httpx
import pytest
from app import security, story_writer
from app.fan_briefing import fan_briefing
from app.matchday import fixture, PROFILES
from app.models import MatchEvent
from app.narration import build_ssml
from xml.etree import ElementTree as ET

EN = ('Newcastle United have led twice, but Crystal Palace have answered both times to leave the match level at 2–2. '
      'There have been six shots in the last five minutes, with fourteen minutes and thirty seconds until ninety, plus added time.')
ES = ('Newcastle United se adelantó dos veces, pero Crystal Palace respondió en ambas ocasiones para dejar el partido empatado 2–2. '
      'Se registraron seis remates en los últimos cinco minutos y faltan catorce minutos y treinta segundos para los noventa, más el añadido.')
DRAFT = {'en': EN, 'es': ES, 'fact_ids': ['score', 'trajectory', 'phase', 'shots']}
REVIEW = {'supported': True, 'same_facts_both_languages': True, 'score_and_phase_correct': True,
          'chronology_correct': True, 'non_redundant': True}


def inputs(now=4530):
    events = [MatchEvent(**e) for e in fixture(PROFILES[1], 'writer-test')]
    observed = [e for e in events if e.match_second <= now]
    return fan_briefing(events, observed, now=now), events


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'matchos-explainer')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'fake-test-credential')


def provider(draft=None, review=None):
    requests = []
    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        value = (draft if draft is not None else DRAFT) if len(requests) % 2 else (review if review is not None else REVIEW)
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(value)}}]})
    return httpx.Client(transport=httpx.MockTransport(handler)), requests


def test_disabled_writer_uses_fallback_without_any_provider_call():
    briefing, events = inputs()
    result = story_writer.write(briefing, events)
    assert result['mode'] == 'deterministic'
    assert result['text'] == briefing['spoken_recap']
    assert security.ai_calls == 0
    assert story_writer.write(None, []) is None


def test_writer_and_separate_reviewer_use_bounded_structured_output_and_cache(configured):
    briefing, events = inputs()
    client, requests = provider()
    with client:
        result = story_writer.write(briefing, events, client)
        assert result['mode'] == 'azure' and result['text'] == {'en': EN, 'es': ES}
        assert len(requests) == 2 and security.ai_calls == 2 and security.ai_active == 0
        assert all(r['response_format']['json_schema']['strict'] for r in requests)
        assert all(r['max_completion_tokens'] == 1400 for r in requests)
        assert requests[1]['messages'][0]['content'].startswith('Independently check BOTH')
        again = story_writer.write(briefing, events, client)
        assert again == result and len(requests) == 2
    packet = json.loads(requests[0]['messages'][1]['content'])
    assert max(e['match_second'] for e in packet['events']) <= 4530
    assert 'pass' in {e['type'] for e in packet['events']}
    assert 'recipient_player_name' in packet['events'][0]
    passing = next(fact for fact in packet['facts'] if fact['fact_id'] == 'passing')
    actual_passes = [e for e in events if 4230 < e.match_second <= 4530 and e.type == 'pass']
    assert sum(value['attempted'] for value in passing['data']['teams'].values()) == len(actual_passes)
    assert set(passing['evidence_event_ids']) == {e.event_id for e in actual_passes}
    assert len(packet['events']) <= 60
    assert set(result['evidence_event_ids']) <= {e.event_id for e in events if e.match_second <= 4530}


@pytest.mark.parametrize('change', ['unknown-id', 'missing-score', 'duplicate-id', 'markup', 'too-long', 'wrong-shape'])
def test_invalid_drafts_never_reach_review_or_display(configured, change):
    draft = copy.deepcopy(DRAFT)
    if change == 'unknown-id': draft['fact_ids'].append('imaginary-red-card')
    if change == 'missing-score': draft['fact_ids'].remove('score')
    if change == 'duplicate-id': draft['fact_ids'].append('score')
    if change == 'markup': draft['en'] += ' <script>bad</script>'
    if change == 'too-long': draft['en'] = 'word ' * 101
    if change == 'wrong-shape': draft['unsupported'] = True
    client, requests = provider(draft)
    with client:
        result = story_writer.write(*inputs(), client)
    assert result['mode'] == 'deterministic' and len(requests) == 1
    assert not story_writer.CACHE and security.ai_active == 0


@pytest.mark.parametrize('field', list(REVIEW))
def test_failed_semantic_or_bilingual_review_falls_back(configured, field):
    client, requests = provider(review={**REVIEW, field: False})
    with client: result = story_writer.write(*inputs(), client)
    assert result['mode'] == 'deterministic' and len(requests) == 2
    assert not story_writer.CACHE


def test_missing_config_and_budget_never_forward_credentials(configured, monkeypatch):
    client, requests = provider()
    with client:
        monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://attacker.example/openai/v1')
        assert story_writer.write(*inputs(), client)['mode'] == 'deterministic'
        monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
        monkeypatch.setenv('MATCHOS_AI_CALL_BUDGET', '1')
        assert story_writer.write(*inputs(), client)['fallback_reason'] == 'ai_budget_or_concurrency_limit'
    assert requests == []


@pytest.mark.parametrize('failure', ['timeout', 'oversize', 'refusal', 'malformed', 'provider-error'])
def test_provider_failures_are_bounded_and_private(configured, failure):
    def handler(request):
        if failure == 'timeout': raise httpx.ReadTimeout('private-provider-details')
        if failure == 'oversize': return httpx.Response(200, content=b'x'*32769)
        if failure == 'refusal': return httpx.Response(200, json={'choices': [{'message': {'refusal': 'private-provider-details'}}]})
        if failure == 'provider-error': return httpx.Response(401, text='private-provider-details')
        return httpx.Response(200, json={'choices': []})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = story_writer.write(*inputs(), client)
    assert result['mode'] == 'deterministic'
    assert 'private-provider-details' not in json.dumps(result)
    assert security.ai_active == 0


def test_cache_identity_cannot_cross_snapshot_scope_or_reused_match_feed(configured):
    briefing, events = inputs()
    original = story_writer.identity(briefing, events)
    changed = copy.deepcopy(briefing)
    changed['snapshot']['since_sequence'] += 1
    assert story_writer.identity(changed, events) != original
    changed_events = list(events)
    changed_events[0] = events[0].model_copy(update={'player_name': 'Different fictional player'})
    assert story_writer.identity(briefing, changed_events) != original
    # Future fixture entries are excluded from both provider packet and cache identity.
    assert story_writer.identity(briefing, events) == story_writer.identity(briefing, [e for e in events if e.match_second <= 4530])


def test_audio_reads_exact_displayed_reviewed_paragraph_and_keeps_all_goal_evidence(configured):
    briefing, events = inputs()
    client, _ = provider()
    with client: narrative = story_writer.write(briefing, events, client)
    goal_ids = set(briefing['trajectory']['evidence_event_ids'])
    story_writer.apply(briefing, narrative)
    for language in ('en', 'es'):
        ssml, _, delivery = build_ssml(briefing, language, 'matchday')
        assert ''.join(ET.fromstring(ssml).itertext()) == narrative['text'][language]
        assert delivery == 'measured'
        assert briefing['spoken_recap'][language] == narrative['text'][language]
    assert goal_ids <= set(briefing['evidence_event_ids'])


def test_catch_up_pipeline_attaches_writer_output_without_removing_legacy_evidence(monkeypatch):
    from app.main import build_catch_up
    from app.models import CatchUpRequest
    briefing, events = inputs()
    observed = [e for e in events if e.match_second <= 4530]
    called = []
    def writer(fan, items):
        called.append(fan['snapshot'])
        return {'mode': 'azure', 'id': 'a'*64, 'text': {'en': EN, 'es': ES},
                'evidence_event_ids': [observed[-1].event_id]}
    monkeypatch.setattr(story_writer, 'write', writer)
    result = build_catch_up(observed, CatchUpRequest())
    assert len(called) == 1
    assert result['fan_briefing']['narrative']['text']['en'] == EN
    assert result['fan_briefing']['spoken_recap']['es'] == ES
    assert result['stories'] and result['explanation'] and result['match_briefing']
    assert len(result['fan_briefing']['trajectory']['transitions']) == 4


def test_narration_requires_the_displayed_recap_identity_and_never_substitutes_text(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app, store
    with TestClient(app, headers={'X-MatchOS-Client': 'replay'}) as client:
        client.post('/api/session', json={}).raise_for_status()
        day = client.post('/api/matchdays/start', json={'matchday_id': 'writer-owned'}).json()
        match = day['matches'][0]
        snapshot = match['briefing']['snapshot']
        heard = []
        def synthesize(fan, language, profile):
            heard.append(fan)
            return b'ID3mock', 'test-voice', 'measured'
        monkeypatch.setattr('app.narration.synthesize', synthesize)
        written = {'mode': 'azure', 'id': 'a'*64, 'text': {'en': EN, 'es': ES},
                   'evidence_event_ids': list(store[snapshot['match_id']])}
        monkeypatch.setattr(story_writer, 'cached', lambda *args: written)
        # A rule-based card must still read its own wording, even if AI text exists for that snapshot.
        assert client.post('/api/narration', json=snapshot).status_code == 200
        assert 'narrative' not in heard[-1]
        response = client.post('/api/narration', json={**snapshot, 'narrative_id': 'a'*64, 'language': 'es'})
        assert response.status_code == 200 and heard[-1]['spoken_recap']['es'] == ES
        monkeypatch.setattr(story_writer, 'cached', lambda *args: None)
        assert client.post('/api/narration', json={**snapshot, 'narrative_id': 'a'*64}).status_code == 409
        assert len(heard) == 2

def test_audience_changes_depth_without_changing_snapshot_or_score():
    casual, events = inputs()
    analyst = copy.deepcopy(casual)
    story_writer.personalize(analyst, events, 'advanced')
    assert analyst['snapshot'] == casual['snapshot']
    assert analyst['trajectory'] == casual['trajectory']
    assert 'Recorded passes' in analyst['spoken_recap']['en']
    assert 'Pases registrados' in analyst['spoken_recap']['es']
    assert 'do not establish possession' in analyst['spoken_recap']['en']
    assert set(casual['evidence_event_ids']) <= set(analyst['evidence_event_ids'])
    assert all(e.match_second <= 4530 for e in events if e.event_id in analyst['evidence_event_ids'])
    fallback = story_writer.write(analyst, events)
    story_writer.apply(analyst, fallback)
    assert analyst['spoken_recap'] == fallback['text']


def test_audience_cache_and_prompts_are_isolated(configured):
    casual, events = inputs()
    analyst = copy.deepcopy(casual)
    story_writer.personalize(analyst, events, 'advanced')
    client, requests = provider()
    with client:
        casual_result = story_writer.write(casual, events, client)
        analyst_result = story_writer.write(analyst, events, client)
    assert len(requests) == 4
    assert casual_result['id'] != analyst_result['id']
    assert 'Audience: casual fan' in requests[0]['messages'][0]['content']
    assert 'Audience: analyst' in requests[2]['messages'][0]['content']
    assert story_writer.cached(casual, events) == casual_result
    assert story_writer.cached(analyst, events) == analyst_result
