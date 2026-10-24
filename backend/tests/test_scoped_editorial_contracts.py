import copy
import json
from pathlib import Path

import httpx
import pytest

from app import main, recap_quality, story_writer
from app.matchday import PROFILES, fixture
from app.models import CatchUpRequest, MatchEvent
from test_linked_scoring_sequence import drafted
from test_recap_editorial import briefing
from test_story_writer import configured, REVIEW


def test_single_scoring_move_does_not_receive_a_rolling_metric_contract():
    fan, _, _, _ = drafted()
    prompt = story_writer.writer_prompt(fan)
    assert 'SELECTED CONTRIBUTION: a verified_scoring_sequence' in prompt
    assert 'NO analysis window or extra rule threshold is needed' in prompt
    assert 'SELECTED CONTRIBUTION: a measured pattern' not in prompt
    assert 'Put its named player/team' not in prompt
    assert 'level means tied/empatados' in prompt
    assert 'not a claim of dominance' not in prompt  # No pre-authored commentary supplied.
    assert 'Sarr' not in prompt and '60:11' not in prompt


def test_repeated_creator_keeps_window_and_goal_chronology_requirements():
    fan, _ = briefing()
    prompt = story_writer.writer_prompt(fan)
    assert 'SELECTED CONTRIBUTION: a measured pattern' in prompt
    assert 'exact MM:SS window in the SAME sentence' in prompt
    assert 'later shots is not the build-up' in prompt
    assert 'SELECTED CONTRIBUTION: a verified_scoring_sequence' not in prompt
    advanced = story_writer.writer_prompt({**copy.deepcopy(fan), 'audience': 'advanced'})
    assert 'Audience: analyst' in advanced and 'shot quality is not measured' in advanced


def test_natural_team_sequence_is_accepted_without_a_shot_clock_or_countdown():
    _, _, packet, value = drafted()
    value['en']=("At 62:30, Crystal Palace and Newcastle United are level at 1–1. Harvey Barnes put Newcastle ahead "
                 "at 15:11. Takehiro Tomiyasu recovered at 60:00; Palace then completed 3 passes, ending with "
                 "Ismaila Sarr's equalizer at 60:11.")
    value['es']=('A los 62:30, Crystal Palace y Newcastle United están empatados 1–1. Harvey Barnes adelantó '
                 'a Newcastle a los 15:11. Takehiro Tomiyasu recuperó el balón a los 60:00; Palace completó '
                 '3 pases y la jugada terminó en el gol del empate de Ismaila Sarr a los 60:11.')
    assert story_writer.compose_draft(value, packet) is value


def test_spanish_validation_failure_reports_language_without_rewriting_either_paragraph():
    _, _, packet, value = drafted()
    value['es']+=' Esta jugada muestra la respuesta de Palace.'
    original = copy.deepcopy(value)
    with pytest.raises(recap_quality.RecapQualityError) as error:
        story_writer.validate_draft(value, packet)
    assert error.value.details['language'] == 'es'
    assert value == original


CAPTURE = json.loads((Path(__file__).parent/'fixtures/v13-multiple-editorial-issues.json').read_text(encoding='utf-8'))


def test_captured_failure_reports_all_independent_defects_and_actual_expected_facts():
    original = copy.deepcopy(CAPTURE['draft'])
    with pytest.raises(recap_quality.RecapQualityError) as failure:
        story_writer.validate_draft(original, CAPTURE['packet'])
    issues = failure.value.details['issues']
    assert {'unsupported_interpretation','missing_selected_goal','wrong_scoring_sequence_pass_credit'} <= {row['code'] for row in issues}
    for language in ('en','es'):
        goal = next(row['details'] for row in issues if row['code']=='missing_selected_goal' and row['details']['language']==language)
        credit = next(row['details'] for row in issues if row['code']=='wrong_scoring_sequence_pass_credit' and row['details']['language']==language)
        assert goal['required_scorer']=='Erling Haaland' and goal['required_goal_clock']=='40:11'
        assert credit['player']=='Rico Lewis' and credit['individual_completed_passes']==1
        assert credit['team_completed_passes']==3
    assert original == CAPTURE['draft']


def test_one_ai_revision_receives_all_issues_then_its_entire_paragraph_is_reviewed(configured,monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE','off')
    feed = [MatchEvent(**row) for row in fixture(PROFILES[0], 'editorial-eval-0e634f5e05-featured') if row['match_second']<=2700]
    cursor = max(event.sequence for event in feed if event.match_second<=2400)
    fan = main.build_catch_up(feed,CatchUpRequest(since_sequence=cursor))['fan_briefing']
    packet = story_writer.evidence_packet(fan,feed)
    fixed = {
        'en': 'At half-time, Manchester United and Manchester City are level at 1–1. Rico Lewis recovered the ball at 40:00 and City completed 3 passes, ending with Erling Haaland scoring the equalizer at 40:11. Shot quality is not measured.',
        'es': 'Al descanso, Manchester United y Manchester City están empatados 1–1. Rico Lewis recuperó el balón a los 40:00 y City completó 3 pases, que terminaron en el gol del empate de Erling Haaland a los 40:11. No se mide la calidad del remate.',
        'fact_ids':packet['required_fact_ids'],
    }
    assert fixed['fact_ids']==CAPTURE['draft']['fact_ids']
    calls=[]
    def respond(request):
        body=json.loads(request.content)
        calls.append(body)
        kind=body['response_format']['json_schema']['name']
        value=CAPTURE['draft'] if kind=='match_recap' else fixed if kind=='match_recap_revision' else REVIEW
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(value)}}]})
    monkeypatch.setenv('MATCHOS_AI_MODE','azure')
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result=story_writer.write(fan,feed,client)
    assert result['mode']=='azure' and result['revision_used']
    assert len(calls)==3 and result['text']=={language:fixed[language] for language in ('en','es')}
    feedback=json.loads(calls[1]['messages'][1]['content'])['validation']['details']['issues']
    assert {'missing_selected_goal','wrong_scoring_sequence_pass_credit','unsupported_interpretation'} <= {row['code'] for row in feedback}
    assert json.loads(calls[2]['messages'][1]['content'])['draft']==fixed


ACCEPTED_BAD = json.loads((Path(__file__).parent/'fixtures/v13-accepted-pass-credit-error.json').read_text(encoding='utf-8'))


def test_captured_generic_momentum_claim_is_rejected_in_both_languages():
    record = json.loads((Path(__file__).parent/'fixtures/oct24-momentum-embellishment.json').read_text(encoding='utf-8'))
    with pytest.raises(recap_quality.RecapQualityError) as failure:
        story_writer.validate_draft(record['draft'],record['packet'])
    issues=failure.value.details['issues']
    assert {row['details']['language'] for row in issues if row['code']=='unsupported_interpretation'}=={'en','es'}


def test_model_reviewed_pass_credit_error_is_rejected_in_both_languages():
    for language in ('en','es'):
        with pytest.raises(recap_quality.RecapQualityError,match='wrong_scoring_sequence_pass_credit'):
            recap_quality.validate_selected_claims(ACCEPTED_BAD['draft'][language],ACCEPTED_BAD['packet'])
        with pytest.raises(recap_quality.RecapQualityError,match='unsupported_interpretation'):
            recap_quality.validate(ACCEPTED_BAD['draft'][language],ACCEPTED_BAD['packet'],set(ACCEPTED_BAD['draft']['fact_ids']))


@pytest.mark.parametrize('language,clause', [
    ('en', 'Rico Lewis recovered for Manchester City and completed three passes'),
    ('en', 'Rico Lewis recovered for City and completed three passes'),
    ('en', 'Rico Lewis of Manchester City recovered, completing three passes'),
    ('es', 'Rico Lewis recuperó para Manchester City y completó tres pases'),
    ('es', 'Rico Lewis recuperó para City, completando tres pases'),
])
def test_prepositional_team_name_cannot_steal_the_players_pass_claim(language,clause):
    sentence = (clause+' after the recovery at 40:00, ending with Erling Haaland equalizing at 40:11.' if language=='en'
                else clause+' tras recuperar a los 40:00, hasta el gol del empate de Erling Haaland a los 40:11.')
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_scoring_sequence_pass_credit'):
        recap_quality.validate_selected_claims(sentence,CAPTURE['packet'])


@pytest.mark.parametrize('sentence', [
    'At 40:00, Rico Lewis recovered for Manchester City, who completed three passes before Erling Haaland equalized at 40:11.',
    'At 40:00, Rico Lewis recovered and City completed three passes before Erling Haaland equalized at 40:11.',
    'At 40:00, Rico Lewis recovered for City and the team completed three passes before Erling Haaland equalized at 40:11.',
    'A los 40:00, Rico Lewis recuperó para Manchester City, que completó tres pases antes del gol del empate de Erling Haaland a los 40:11.',
    'A los 40:00, Rico Lewis recuperó y City completó tres pases antes del gol del empate de Erling Haaland a los 40:11.',
])
def test_explicit_team_subject_and_relative_clauses_preserve_correct_collective_credit(sentence):
    recap_quality.validate_selected_claims(sentence,CAPTURE['packet'])
