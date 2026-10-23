import copy
import json
from pathlib import Path

import pytest

from app import main, recap_quality, story_writer
from app.matchday import fixture, PROFILES
from app.models import CatchUpRequest, MatchEvent
from app.recap_context import creator_chronology
from test_story_writer import configured, REVIEW


def briefing(now=1500, cursor_second=900):
    feed = [MatchEvent(**row) for row in fixture(PROFILES[0], 'editorial-case') if row['match_second'] <= now]
    cursor = max(event.sequence for event in feed if event.match_second <= cursor_second)
    return main.build_catch_up(feed, CatchUpRequest(since_sequence=cursor))['fan_briefing'], feed


def test_chronology_separates_goal_attempt_from_later_attempts_without_mutating_plan():
    fan, feed = briefing()
    before = copy.deepcopy(fan['story_plan'])
    packet = story_writer.evidence_packet(fan, feed)
    contribution = next(f for f in packet['facts'] if f.get('chronology'))
    chronology = contribution['chronology']
    relationship = chronology['goal_relationships'][0]
    assert relationship['goal_clock'] == '15:11'
    assert relationship['goal_attempt_count'] == 1
    assert relationship['other_earlier_count'] == 0
    assert relationship['later_count'] == 2
    assert not relationship['whole_pattern_precedes_goal']
    assert chronology['missing_link_count'] == 0
    assert sum(relationship[key] for key in ('goal_attempt_count', 'other_earlier_count', 'later_count')) == contribution['data']['metric']['count']
    assert fan['story_plan'] == before
    assert not any('canonical_text' in fact or 'text' in fact['data'] for fact in packet['facts'])


@pytest.mark.parametrize('prefix', ['Behind that goal, ', 'Detrás de ese gol, '])
def test_mixed_window_cannot_be_described_as_behind_an_earlier_goal(prefix):
    fan, feed = briefing()
    packet = story_writer.evidence_packet(fan, feed)
    text = prefix + 'Bruno Fernandes supplied Bryan Mbeumo with the final pass for 3 shots in 15:00–25:00.'
    with pytest.raises(recap_quality.RecapQualityError, match='goal_pattern_chronology'):
        recap_quality.validate(text, packet, set(packet['required_fact_ids']))


def test_explicit_goal_and_recurring_pattern_can_be_explained_without_rewriting():
    fan, feed = briefing()
    packet = story_writer.evidence_packet(fan, feed)
    value = {
        'en': 'Manchester United lead Manchester City 1–0 at 25:00. Bryan Mbeumo scored at 15:11. In 15:00–25:00, Bruno Fernandes supplied Bryan Mbeumo with the final pass for 3 shots, one producing the goal and two following it.',
        'es': 'Manchester United gana a Manchester City 1–0 a los 25:00. Bryan Mbeumo marcó a los 15:11. En 15:00–25:00, Bruno Fernandes dio el último pase para 3 remates de Bryan Mbeumo: uno produjo el gol y dos llegaron después.',
        'fact_ids': packet['required_fact_ids'],
    }
    assert story_writer.compose_draft(value, packet) is value
    repeated = {**value, 'en':value['en']+' This pattern shows Fernandes consistently setting up Mbeumo for shooting opportunities.'}
    with pytest.raises(recap_quality.RecapQualityError, match='repeated_player_contribution'):
        story_writer.validate_draft(repeated, packet)


def test_spanish_score_verb_does_not_imply_tactical_dominance():
    recap_quality.validate('Manchester United domina 1–0 a Manchester City.', {'editorial_plan':None}, set())
    with pytest.raises(recap_quality.RecapQualityError, match='unsupported_interpretation'):
        recap_quality.validate('Manchester United domina el partido.', {'editorial_plan':None}, set())


def test_old_accepted_casual_and_analyst_embellishment_is_now_rejected():
    root = Path(__file__).resolve().parents[2]
    casual = json.loads((root/'docs/live-ai-authorship-casual.json').read_text(encoding='utf-8'))
    for text in casual['narrative']['text'].values():
        with pytest.raises(recap_quality.RecapQualityError):
            recap_quality.validate(text, {'editorial_plan': None}, set())


def test_prompt_fingerprint_changes_with_prompt_even_without_version_bump(monkeypatch):
    fan, feed = briefing()
    old_hash = story_writer.prompt_fingerprint(fan)
    old_identity = story_writer.identity(fan, feed)
    original = story_writer.writer_prompt
    monkeypatch.setattr(story_writer, 'writer_prompt', lambda fan: original(fan)+' Extra editorial condition.')
    assert story_writer.prompt_fingerprint(fan) != old_hash
    assert story_writer.identity(fan, feed) != old_identity


def test_unchanged_prompt_fingerprint_is_stable_and_audiences_differ():
    fan, _ = briefing()
    assert story_writer.prompt_fingerprint(fan) == story_writer.prompt_fingerprint(copy.deepcopy(fan))
    assert story_writer.prompt_fingerprint(fan) != story_writer.prompt_fingerprint({**fan, 'audience':'advanced'})


def test_missing_or_unlinked_goal_evidence_cannot_prove_goal_producing_combination():
    fan, feed = briefing()
    story = next(story for story in fan['story_plan']['stories'] if story['kind'] == 'player_shot_creation')
    altered = [event.model_copy(update={'related_event_id':None}) if event.type=='goal' else event for event in feed]
    relation = creator_chronology(story, altered)['goal_relationships'][0]
    assert relation['goal_attempt_count'] == 0
    assert relation['other_earlier_count'] == 1 and relation['later_count'] == 2
    incomplete = creator_chronology(story, [event for event in feed if event.event_id != story['metric']['links'][-1]['shot_event_id']])
    assert incomplete['missing_link_count'] == 1
    assert not incomplete['goal_relationships'][0]['whole_pattern_precedes_goal']


def test_repeated_identical_explanation_is_rejected():
    with pytest.raises(recap_quality.RecapQualityError, match='repeated_explanation'):
        recap_quality.validate('Bruno repeatedly found Amad. Bruno repeatedly found Amad.',
                               {'editorial_plan':{}, 'facts':[]}, set())


BASELINE = json.loads((Path(__file__).parent/'fixtures/editorial-interpretation-regressions.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('sample', BASELINE['samples'], ids=lambda sample: sample['case']+'-'+sample['audience'])
def test_known_accepted_but_unsupported_baseline_drafts_are_rejected(sample):
    with pytest.raises(recap_quality.RecapQualityError, match='unsupported_interpretation'):
        for text in sample['text'].values():
            recap_quality.validate(text, {'editorial_plan':None}, set())


def test_recovery_shot_uses_its_event_clock_not_an_invented_window():
    from app import story_plan
    from app.intelligence import match_stories
    fan, feed = briefing(now=960)
    candidates = match_stories(feed)
    transition = next(story for story in candidates if story['kind']=='recovery_shot' and story['match_second']==910)
    story_plan.bind(fan, [story for story in candidates if story['kind']=='goal']+[transition], 'casual')
    elapsed = transition['metric']['elapsed_seconds']
    packet = story_writer.evidence_packet(fan, feed)
    assert any(fact.get('point_clock') == '15:10' for fact in packet['facts'])
    value = {'en':f'Manchester United lead Manchester City 1–0 at 16:00. At 15:10, {elapsed} seconds after Kobbie Mainoo recovered the ball, Bryan Mbeumo shot and that shot became United’s go-ahead goal at 15:11.',
             'es':f'Manchester United gana a Manchester City 1–0 a los 16:00. A los 15:10, {elapsed} segundos después de la recuperación de Kobbie Mainoo, Bryan Mbeumo remató y ese remate terminó en el gol que puso a United por delante a los 15:11.',
             'fact_ids':packet['required_fact_ids']}
    assert story_writer.compose_draft(value, packet) is value
    wrong_time = {**value, 'en':value['en'].replace('At 15:10', 'At 15:20')}
    with pytest.raises(recap_quality.RecapQualityError, match='ambiguous_statistic_window'):
        story_writer.validate_draft(wrong_time, packet)
    wrong_elapsed = {**value, 'en':value['en'].replace(f'{elapsed} seconds', f'{elapsed+1} seconds')}
    with pytest.raises(recap_quality.RecapQualityError, match='missing_recovery_goal_connection'):
        story_writer.validate_draft(wrong_elapsed, packet)


def test_factual_fallback_keeps_selected_scorer_and_goal_time():
    fan, _ = briefing(now=960)
    for language in ('en','es'):
        text=fan['spoken_recap'][language]
        assert 'Bryan Mbeumo' in text and text.count('15:11')==1
        assert 'Kobbie Mainoo' in text and '15:10' in text


def test_writer_gets_selected_facts_without_unrelated_raw_rows():
    fan, feed = briefing()
    packet = story_writer.evidence_packet(fan, feed)
    brief = story_writer.writer_evidence(packet)
    assert 'events' not in brief
    assert brief['required_fact_ids'] == packet['required_fact_ids']
    creator = next(fact for fact in brief['facts'] if fact.get('chronology'))
    assert creator['chronology']['goal_relationships'][0]['later_count'] == 2
    assert 'evidence_event_ids' not in json.dumps(brief)
    assert len(json.dumps(brief)) < len(json.dumps(packet))


def test_insufficient_opening_coverage_deliberately_skips_writer(configured, monkeypatch):
    import httpx
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    fan, feed = briefing(now=60, cursor_second=0)
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail('Empty coverage must not call the writer'))) as client:
        result = story_writer.write(fan, feed, client)
    assert result['mode'] == 'deterministic' and result['fallback_reason'] == 'limited_coverage'


@pytest.mark.parametrize('failure', [None, 'invalid_revision', 'budget'])
def test_one_ai_revision_is_validated_then_reviewed_or_falls_back(configured, monkeypatch, failure):
    import httpx
    from app import security
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    fan, feed = briefing()
    packet = story_writer.evidence_packet(fan, feed)
    fixed = {'en':'Manchester United lead Manchester City 1–0 at 25:00. Bryan Mbeumo scored at 15:11. In 15:00–25:00, Bruno Fernandes supplied Bryan Mbeumo with 3 completed passes followed by shots, one producing the goal and two coming afterward.',
             'es':'Manchester United gana a Manchester City 1–0 a los 25:00. Bryan Mbeumo marcó a los 15:11. En 15:00–25:00, Bruno Fernandes dio 3 pases completados seguidos de remates de Bryan Mbeumo: uno produjo el gol y dos llegaron después.',
             'fact_ids':packet['required_fact_ids']}
    original = {**fixed, 'en':fixed['en']+' This combination shows Fernandes setting up Mbeumo for scoring opportunities.'}
    requests = []
    def reply(request):
        body = json.loads(request.content)
        name = body['response_format']['json_schema']['name']
        requests.append(name)
        value = original if name=='match_recap' or failure=='invalid_revision' else fixed if name=='match_recap_revision' else REVIEW
        return httpx.Response(200, json={'choices':[{'message':{'content':json.dumps(value)}}]})
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    if failure == 'budget':
        monkeypatch.setenv('MATCHOS_AI_CALL_BUDGET', '2')
    with httpx.Client(transport=httpx.MockTransport(reply)) as client:
        result = story_writer.write(fan, feed, client)
    assert security.ai_active == 0
    if failure is None:
        assert result['mode']=='azure' and result['revision_used']
        assert result['text']=={language:fixed[language] for language in ('en','es')}
        assert requests == ['match_recap', 'match_recap_revision', 'recap_review']
        assert security.ai_calls == 4
    else:
        assert result['mode']=='deterministic' and result['text']==fan['spoken_recap']
        assert len(requests)==(1 if failure=='budget' else 2)


CASES = json.loads((Path(__file__).resolve().parents[2]/'docs/recap-evaluation-cases.json').read_text())


@pytest.mark.parametrize('audience', ['casual', 'advanced'])
@pytest.mark.parametrize('case', CASES, ids=lambda case: case['case'])
def test_twenty_snapshot_audience_cases_have_consistent_evidence(case, audience):
    profile = next(profile for profile in PROFILES if profile['role'] == case['role'])
    feed = [MatchEvent(**row) for row in fixture(profile, 'matrix-'+case['case']) if row['match_second'] <= case['second']]
    cursor = max(event.sequence for event in feed if event.match_second <= case['cursor_second'])
    result = main.build_catch_up(feed, CatchUpRequest(since_sequence=cursor, audience=audience))
    fan = result['fan_briefing']
    assert fan and fan['audience'] == audience
    packet = story_writer.evidence_packet(fan, feed)
    observed_ids = {event.event_id for event in feed}
    assert all(set(fact['evidence_event_ids']) <= observed_ids for fact in packet['facts'])
    assert all(row['match_second'] <= case['second'] for row in packet['events'])
    for fact in packet['facts']:
        if not fact.get('chronology'):
            continue
        chronology = fact['chronology']
        assert chronology['missing_link_count'] == 0
        for relation in chronology['goal_relationships']:
            assert relation['goal_event_id'] in observed_ids
            assert relation['goal_attempt_count'] + relation['other_earlier_count'] + relation['later_count'] == fact['data']['metric']['count']
    assert len(fan['narrative']['prompt_hash']) == 64
