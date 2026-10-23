import copy
import json

import httpx
import pytest

from app import recap_quality, story_writer, main
from app.matchday import fixture, PROFILES
from app.models import MatchEvent, CatchUpRequest
from test_story_writer import configured, inputs, provider, DRAFT


EN = ('Manchester United lead Manchester City 1 to 0 at 25:00. United recorded three shots in '
      '15:00–20:00, compared with zero in 10:00–15:00. In 20:00–25:00 United completed ten of ten passes.')
ES = ('Manchester United gana a Manchester City 1 a 0 a los 25:00. United registró tres remates en '
      '15:00–20:00, frente a cero en 10:00–15:00. En 20:00–25:00 United completó diez de diez pases.')


def packet():
    return {'editorial_plan': {'status': 'change_detected'}, 'required_fact_ids': ['score', 'trajectory', 'phase'],
            'facts': [{'fact_id': name, 'data': {}, 'window_labels': []} for name in ('score', 'trajectory', 'phase')]
            + [{'fact_id': 'story:shots:home:1200', 'data': {'kind': 'shot_activity'}, 'window_labels': ['10:00–15:00', '15:00–20:00']},
               {'fact_id': 'passing', 'data': {}, 'window_labels': ['20:00–25:00']}]}


def draft():
    return {'en': EN, 'es': ES, 'fact_ids': [fact['fact_id'] for fact in packet()['facts']]}


def test_precise_bilingual_windows_and_limitations_pass():
    value = draft()
    value['en'] += ' These counts do not establish control or chance quality.'
    value['es'] += ' Estos datos no demuestran control ni calidad de las ocasiones.'
    story_writer.validate_draft(value, packet())


@pytest.mark.parametrize('phrase', [' These counts do not prove dominance.', ' Estos datos no demuestran dominio.'])
def test_explicit_limitations_are_not_positive_dominance_claims(phrase):
    recap_quality.validate(phrase, {'editorial_plan': None}, set())


def test_ai_paraphrase_reaches_reviewer_screen_and_voice_unchanged(configured, monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    feed = [MatchEvent(**raw) for raw in fixture(PROFILES[0], 'authored-quality') if raw['match_second'] <= 1500]
    fan = main.build_catch_up(feed, CatchUpRequest())['fan_briefing']
    evidence = story_writer.evidence_packet(fan, feed)
    value = {
        'en': 'Manchester United lead Manchester City 1–0 at 25:00. Bryan Mbeumo scored for United at 15:11. Bruno Fernandes kept picking out Bryan Mbeumo in 15:00–25:00: 3 completed deliveries, each followed by a shot.',
        'es': 'Manchester United gana a Manchester City 1–0 a los 25:00. Bryan Mbeumo marcó para United a los 15:11. Bruno Fernandes encontró una y otra vez a Bryan Mbeumo en 15:00–25:00: 3 pases completados, cada uno seguido de un remate.',
        'fact_ids': evidence['required_fact_ids']}
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    model, requests = provider(value)
    with model:
        result = story_writer.write(fan, feed, model)
    assert result['mode'] == 'azure' and result['metric_rendering'] == 'model_reviewed'
    reviewed = json.loads(requests[1]['messages'][1]['content'])['draft']
    for language in ('en', 'es'):
        assert value[language] == reviewed[language] == result['text'][language]
    story_writer.apply(fan, result)
    from app.narration import build_ssml
    from xml.etree import ElementTree as ET
    for language in ('en', 'es'):
        ssml, _, _ = build_ssml(fan, language, 'matchday')
        assert ''.join(ET.fromstring(ssml).itertext()) == result['text'][language]


@pytest.mark.parametrize('problem', ['unknown_reference', 'unsupported_interpretation', 'markup'])
def test_composition_does_not_sanitize_invalid_context_into_an_accepted_draft(problem):
    evidence = packet()
    value = draft()
    if problem == 'unknown_reference':
        value['fact_ids'].append('invented')
    elif problem == 'unsupported_interpretation':
        value['en'] += ' More shots increased their threat.'
    else:
        value['en'] += ' <script>shots</script>'
    with pytest.raises(ValueError):
        story_writer.compose_draft(value, evidence)


def test_equivalent_clock_connectors_and_anchored_relative_windows_pass():
    evidence = packet()
    evidence['facts'][2]['data']['match_second'] = 1500
    evidence['facts'][3]['data']['metric'] = {
        'previous': {'start_second': 600, 'end_second': 900},
        'current': {'start_second': 900, 'end_second': 1200}}
    value = draft()
    value['en'] = EN.replace('15:00–20:00', '15:00 to 20:00').replace('10:00–15:00', 'the preceding five minutes').replace('In 20:00–25:00', 'In the last five minutes')
    value['es'] = ES.replace('15:00–20:00', '15:00 a 20:00').replace('10:00–15:00', 'los cinco minutos anteriores').replace('En 20:00–25:00', 'En los últimos cinco minutos')
    story_writer.validate_draft(value, evidence)


@pytest.mark.parametrize('text', ['15:00 hasta el 25:00', '15:00 until the 25:00', '15:00 a los 25:00'])
def test_natural_articles_in_clock_ranges(text):
    assert recap_quality.clock_ranges(text) == {(900, 1500)}


@pytest.mark.parametrize('language,phrase', [
    ('en', ' United increased their threat.'), ('en', ' United dominated the match.'),
    ('en', ' United took control.'), ('es', ' United aumentó la amenaza.'),
    ('es', ' United generó mayor presión.'), ('es', ' United dominó el partido.'),
])
def test_count_based_positive_interpretations_are_rejected(language, phrase):
    value = draft()
    value[language] += phrase
    with pytest.raises(recap_quality.RecapQualityError, match='unsupported_interpretation'):
        story_writer.validate_draft(value, packet())


@pytest.mark.parametrize('language', ['en', 'es'])
def test_missing_or_borrowed_passing_scope_is_rejected(language):
    value = draft()
    # Keep the real passing window elsewhere, then wrongly attach the shooting window to passes.
    value[language] = ('At 20:00–25:00. ' if language == 'en' else 'A los 20:00–25:00. ') + value[language].replace(
        'In 20:00–25:00', 'In 15:00–20:00').replace('En 20:00–25:00', 'En 15:00–20:00')
    with pytest.raises(recap_quality.RecapQualityError, match='ambiguous_statistic_window'):
        story_writer.validate_draft(value, packet())
    value = draft()
    value[language] = value[language].replace('20:00–25:00', 'this period' if language == 'en' else 'este período')
    with pytest.raises(recap_quality.RecapQualityError, match='missing_metric_window'):
        story_writer.validate_draft(value, packet())


@pytest.mark.parametrize('audience', ['casual', 'advanced'])
def test_provider_failure_preserves_selected_bilingual_rule_recap(audience, monkeypatch):
    feed = [MatchEvent(**raw) for raw in fixture(PROFILES[0], 'quality-failure') if raw['match_second'] <= 1500]
    fan = main.build_catch_up(feed, CatchUpRequest(audience=audience))['fan_briefing']
    expected = copy.deepcopy(fan['spoken_recap'])
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    monkeypatch.setenv('AZURE_OPENAI_BASE_URL', 'https://fixture.openai.azure.com/openai/v1')
    monkeypatch.setenv('AZURE_OPENAI_DEPLOYMENT', 'test-deployment')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'fake-test-credential')
    def unavailable(request):
        return httpx.Response(503, text='private-provider-diagnostic')
    with httpx.Client(transport=httpx.MockTransport(unavailable)) as provider:
        result = story_writer.write(fan, feed, provider)
    assert result['mode'] == 'deterministic' and result['text'] == expected
    assert fan['story_plan']['player_story_id'] == fan['story_plan']['change_story_id']
    assert fan['story_plan']['stories'][-1]['kind'] == 'player_shot_creation'
    assert 'private-provider-diagnostic' not in json.dumps(result)


def test_rejected_interpretation_falls_back_before_model_review(configured):
    value = copy.deepcopy(DRAFT)
    value['en'] += ' They increased their threat.'
    model, requests = provider(value)
    with model:
        result = story_writer.write(*inputs(), model)
    assert result['mode'] == 'deterministic'
    assert result['fallback_reason'] == 'unsupported_interpretation'
    assert len(requests) == 1


@pytest.mark.parametrize('audience', ['casual', 'advanced'])
def test_quiet_selection_does_not_call_writer_even_when_azure_is_configured(audience, configured, monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    feed = [MatchEvent(**raw) for raw in fixture(PROFILES[2], 'quiet-quality') if raw['match_second'] <= 2400]
    cursor = max(event.sequence for event in feed if event.match_second <= 1800)
    fan = main.build_catch_up(feed, CatchUpRequest(since_sequence=cursor, audience=audience))['fan_briefing']
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    def forbidden(request):
        pytest.fail('An empty quiet selection must not invoke the prose writer')
    with httpx.Client(transport=httpx.MockTransport(forbidden)) as model:
        result = story_writer.write(fan, feed, model)
    assert result['mode'] == 'deterministic' and result['fallback_reason'] == 'no_selected_story'
    assert result['text'] == fan['spoken_recap']
