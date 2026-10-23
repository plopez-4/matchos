import copy
import json
from collections import Counter
from xml.etree import ElementTree as ET

import pytest

from app import main, story_plan, story_writer, narration
from app.explanations import render
from app.intelligence import match_stories
from app.matchday import fixture, PROFILES
from app.models import CatchUpRequest, MatchEvent
from test_matchday import client, start, tick_to
from test_story_writer import inputs, provider, DRAFT


def observed(profile=0, now=1500):
    return [MatchEvent(**raw) for raw in fixture(PROFILES[profile], 'plan-test') if raw['match_second'] <= now]


def test_quiet_feed_has_circulation_and_missed_passes_without_repeated_activity_claims():
    feed = observed(2, 5580)
    kinds = Counter(story['kind'] for story in match_stories(feed))
    assert not any(kinds[kind] for kind in ('shot_activity', 'progressive_pass', 'high_recovery'))
    # Two authored chances remain honest observed transitions, not a fabricated pressure shift.
    assert kinds['recovery_shot'] == 2
    assert any(event.outcome == 'intercepted' for event in feed if event.type == 'pass')
    assert len({event.y for event in feed}) > 3
    for audience in ('casual', 'advanced'):
        snapshot = [event for event in feed if event.match_second <= 2400]
        cursor = max(event.sequence for event in snapshot if event.match_second <= 1800)
        result = main.build_catch_up(snapshot, CatchUpRequest(since_sequence=cursor, audience=audience))
        plan = result['fan_briefing']['story_plan']
        assert plan['status'] == 'no_qualifying_change' and plan['story_ids'] == []
        assert 'No qualifying change' in result['fan_briefing']['spoken_recap']['en']
        assert 'No se detectó un cambio' in result['fan_briefing']['spoken_recap']['es']


def test_selected_change_controls_bilingual_paragraph_packet_and_voice(monkeypatch):
    feed = observed()
    cursor = max(event.sequence for event in feed if event.match_second <= 900)
    # Deliberately choose Away's supported comparison, not the globally strongest Home comparison.
    def select(stories, audience):
        chosen = [story for story in stories if story['kind'] == 'goal' or story['story_id'] == 'shots:away:1200']
        return {'selected_story_ids': [story['story_id'] for story in chosen],
                'sections': render(chosen, audience), 'text': '', 'mode': 'deterministic'}
    monkeypatch.setattr(main, 'explain', select)
    for audience in ('casual', 'advanced'):
        result = main.build_catch_up(feed, CatchUpRequest(since_sequence=cursor, audience=audience))
        fan = result['fan_briefing']
        plan = fan['story_plan']
        assert plan['change_story_id'] == 'shots:away:1200'
        packet = story_writer.evidence_packet(fan, feed)
        assert packet['editorial_plan']['story_ids'] == plan['story_ids']
        assert 'story:shots:away:1200' in packet['required_fact_ids']
        assert not any(fact['fact_id'] == 'story:shots:home:1200' for fact in packet['facts'])
        assert 'Manchester City recorded 3 shots, compared with 1' in fan['spoken_recap']['en']
        assert 'Manchester City registró 3 remates, frente a 1' in fan['spoken_recap']['es']
        assert 'No shots recorded in the last five minutes' in fan['spoken_recap']['en']
        for language in ('en', 'es'):
            ssml, _, _ = narration.build_ssml(fan, language, 'matchday')
            assert ''.join(ET.fromstring(ssml).itertext()) == fan['spoken_recap'][language]


def test_limited_coverage_does_not_assert_a_full_quiet_comparison():
    fan = main.build_catch_up(observed(now=60), CatchUpRequest())['fan_briefing']
    assert fan['story_plan']['status'] == 'limited_coverage'
    assert 'coverage is limited' in fan['spoken_recap']['en']


def test_writer_rejects_omitted_selected_change_before_review(monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'test-model')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'fake-test-credential')
    fan, events = inputs()
    selected = [story for story in match_stories([event for event in events if event.match_second <= 4530])
                if story['kind'] == 'shot_activity']
    assert selected
    story_plan.bind(fan, selected, 'casual')
    original = copy.deepcopy(fan['spoken_recap'])
    model, requests = provider(DRAFT)  # Existing prose references score/phase/shots, omitting the selected story ID.
    with model:
        result = story_writer.write(fan, events, model)
    assert len(requests) == 1
    assert result['mode'] == 'deterministic' and result['text'] == original
    packet = json.loads(requests[0]['messages'][1]['content'])
    assert packet['editorial_plan']['story_ids'] == fan['story_plan']['story_ids']


def test_narration_reconstructs_exact_selected_plan_and_rejects_unknown_ids(monkeypatch):
    heard = []
    monkeypatch.setattr(narration, 'synthesize', lambda fan, *args: (
        heard.append(fan) or b'ID3mock', 'test-voice', 'measured'))
    with client() as browser:
        tick_to(browser, start(browser, 'voice-plan'), 1500)
        mid = 'voice-plan-featured'
        response = browser.post(f'/api/matches/{mid}/catch-up', json={'audience': 'advanced'})
        assert response.status_code == 200
        fan = response.json()['fan_briefing']
        payload = {**fan['snapshot'], 'audience': 'advanced', 'language': 'es',
                   'selected_story_ids': fan['story_plan']['story_ids']}
        assert browser.post('/api/narration', json=payload).status_code == 200
        assert heard[-1]['spoken_recap'] == fan['spoken_recap']
        assert browser.post('/api/narration', json={**payload, 'selected_story_ids': ['invented']}).status_code == 422
        assert len(heard) == 1


def test_reviewed_writer_caches_the_selected_plan_not_an_independent_pattern(monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'test-model')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'fake-test-credential')
    fan, events = inputs()
    candidates = [story for story in match_stories([event for event in events if event.match_second <= 4530])
                  if story['kind'] == 'shot_activity']
    story_plan.bind(fan, [candidates[0]], 'casual')
    packet = story_writer.evidence_packet(fan, events)
    canonical = {lang:story_plan.change_text(candidates[0], fan['locale_facts']['names'], 'casual', lang) for lang in ('en','es')}
    draft = {'en': 'Crystal Palace and Newcastle United are level at 2 to 2. ' + canonical['en'],
             'es': 'Crystal Palace y Newcastle United están empatados 2 a 2. ' + canonical['es'],
             'fact_ids': packet['required_fact_ids']}
    model, requests = provider(draft)
    with model:
        written = story_writer.write(fan, events, model)
    assert written['mode'] == 'azure' and len(requests) == 2
    assert story_writer.cached(fan, events) == written
    assert 'editorial-plan story' in requests[1]['messages'][0]['content']
    other = copy.deepcopy(fan)
    story_plan.bind(other, [candidates[-1]], 'casual')
    assert story_writer.identity(other, events) != written['id']
    assert story_writer.cached(other, events) is None
