"""Actual false rejection plus corruptions of its source-backed shot list."""
import copy
import json
from pathlib import Path

import pytest
from app import recap_quality, story_writer

CAPTURE=json.loads((Path(__file__).parent/'fixtures/v19-enumerated-shot-rejection.json').read_text(encoding='utf-8'))


def test_actual_bilingual_revision_accepts_exact_shot_list_without_repeating_window():
    story_writer.validate_draft(CAPTURE['draft'],CAPTURE['packet'])


@pytest.mark.parametrize('language,before,after',[
    ('en','two saved shots','three saved shots'),
    ('es','dos remates detenidos','tres remates detenidos'),
    ('en','18:40','18:41'),('es','18:40','18:41'),
    ('en','18:40','16:40'),('es','18:40','16:40'),
    ('en','two saved shots','two blocked shots'),
    ('es','dos remates detenidos','dos remates bloqueados'),
    ('en','18:40','15:10'),('es','18:40','15:10'),
    ('en','Mbeumo had two','Fernandes had two'),
    ('es','Mbeumo tuvo dos','Fernandes tuvo dos'),
])
def test_wrong_count_clock_outcome_or_actor_is_rejected(language,before,after):
    value=copy.deepcopy(CAPTURE['draft'])
    value[language]=value[language].replace(before,after)
    with pytest.raises(recap_quality.RecapQualityError) as caught:
        story_writer.validate_draft(value,CAPTURE['packet'])
    assert any(issue['code']=='wrong_enumerated_shots' for issue in caught.value.details['issues'])


@pytest.mark.parametrize('language,sentence',[
    ('en','Mbeumo had two saved shots at 16:40 and 18:40.'),
    ('es','Mbeumo tuvo dos remates detenidos a los 16:40 y 18:40.'),
    ('en','Mbeumo had 2 saved shots at 16:40 and at 18:40.'),
    ('es','Mbeumo tuvo 2 remates detenidos a los 16:40 y a los 18:40.'),
])
def test_named_recorded_points_support_count_in_words_or_digits(language,sentence):
    facts=CAPTURE['packet']['facts']
    assert recap_quality.enumerated_shot_points(sentence,facts,CAPTURE['packet'])


@pytest.mark.parametrize('before,after',[
    ('two saved shots at 16:40 and 18:40','two saved shots between 16:40 and 18:40'),
    ('18:40, but','18:40 between 20:00 and 25:00, but'),
    ('18:40, but','18:40 and three passes, but'),
    ('between 15:00 and 25:00','between 20:00 and 25:00'),
])
def test_event_list_cannot_supply_an_unrelated_window_or_pass_count(before,after):
    value=copy.deepcopy(CAPTURE['draft'])
    value['en']=value['en'].replace(before,after)
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,CAPTURE['packet'])


def test_bad_outcome_is_rejected_even_when_the_list_carries_a_valid_window():
    value=copy.deepcopy(CAPTURE['draft'])
    value['en']=value['en'].replace('two saved shots','two missed shots').replace('18:40, but','18:40 between 15:00 and 25:00, but')
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_enumerated_shots'):
        story_writer.validate_draft(value,CAPTURE['packet'])


def test_uncited_or_missing_shot_evidence_cannot_grant_the_exception():
    packet=copy.deepcopy(CAPTURE['packet'])
    facts=[fact for fact in packet['facts'] if not fact.get('chronology')]
    sentence='Mbeumo had two saved shots at 16:40 and 18:40.'
    assert not recap_quality.enumerated_shot_points(sentence,facts,packet)
    fact=next(f for f in packet['facts'] if f.get('chronology'))
    fact['chronology']['actions'].pop()
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_enumerated_shots'):
        recap_quality.enumerated_shot_points(sentence,packet['facts'],packet)


ATTEMPT=json.loads((Path(__file__).parent/'fixtures/v20-spanish-attempt-rejection.json').read_text(encoding='utf-8'))


def test_actual_spanish_goal_attempt_uses_shot_time_not_goal_time():
    story_writer.validate_draft(ATTEMPT['draft'],ATTEMPT['packet'])


@pytest.mark.parametrize('replacement,code',[
    ('intento de gol a los 15:11','wrong_explicit_shot_clock'),
    ('gol a los 15:10','wrong_explicit_goal_clock')])
def test_shot_attempt_exception_cannot_change_a_shot_or_goal_clock(replacement,code):
    value=copy.deepcopy(ATTEMPT['draft'])
    value['es']=value['es'].replace('intento de gol a los 15:10',replacement)
    with pytest.raises(recap_quality.RecapQualityError,match=code):
        story_writer.validate_draft(value,ATTEMPT['packet'])


SINGLE_PASS=json.loads((Path(__file__).parent/'fixtures/v21-single-pass-rejection.json').read_text(encoding='utf-8'))


def test_captured_single_pass_is_identified_by_unique_recipient_and_clock():
    story_writer.validate_draft(SINGLE_PASS['draft'],SINGLE_PASS['packet'])


@pytest.mark.parametrize('replacement',['a pass at 15:10','a pass from Haaland at 15:09'])
def test_single_pass_exception_rejects_wrong_clock_or_competing_actor(replacement):
    value=copy.deepcopy(SINGLE_PASS['draft'])
    value['en']=value['en'].replace('a pass at 15:09',replacement)
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,SINGLE_PASS['packet'])


def test_single_pass_exception_requires_unique_source_action():
    packet=copy.deepcopy(SINGLE_PASS['packet'])
    fact=next(f for f in packet['facts'] if f.get('chronology'))
    duplicate=copy.deepcopy(fact['chronology']['actions'][0])
    duplicate['pass_event_id']='another-recorded-pass'
    fact['chronology']['actions'].append(duplicate)
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(SINGLE_PASS['draft'],packet)


LATER_SHOTS=json.loads((Path(__file__).parent/'fixtures/v22-shot-list-wording-rejection.json').read_text(encoding='utf-8'))


def test_actual_later_shots_by_named_player_preserve_bilingual_event_scope():
    story_writer.validate_draft(LATER_SHOTS['draft'],LATER_SHOTS['packet'])


@pytest.mark.parametrize('language,before,after',[
    ('en','two later saved shots by Mbeumo','three later saved shots by Mbeumo'),
    ('en','two later saved shots by Mbeumo','two later blocked shots by Mbeumo'),
    ('en','two later saved shots by Mbeumo','two later saved shots by Fernandes'),
    ('en','18:40','18:41'),
    ('es','dos remates detenidos de Mbeumo','tres remates detenidos de Mbeumo'),
    ('es','dos remates detenidos de Mbeumo','dos remates bloqueados de Mbeumo'),
    ('es','dos remates detenidos de Mbeumo','dos remates detenidos de Fernandes'),
    ('es','18:40','18:41'),
])
def test_postposed_shooter_cannot_hide_wrong_count_outcome_actor_or_clock(language,before,after):
    value=copy.deepcopy(LATER_SHOTS['draft'])
    value[language]=value[language].replace(before,after)
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_enumerated_shots'):
        story_writer.validate_draft(value,LATER_SHOTS['packet'])
