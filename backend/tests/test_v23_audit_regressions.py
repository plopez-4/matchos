"""Full-matrix findings: actual good drafts and accepted ownership ambiguity."""
import copy
import json
from pathlib import Path

import pytest
from app import recap_quality, story_writer

ROWS=json.loads((Path(__file__).parent/'fixtures/v23-nine-match-review.json').read_text(encoding='utf-8'))


def row(case,audience):
    return next(r for r in ROWS if r['case']==case and r['audience']==audience)


def captured(record,stage):
    return next(t['draft'] for t in record['evaluation_trace'] if t['stage']==stage)


@pytest.mark.parametrize('case,audience,stage',[
    ('palace_repeated_replies','casual','revision'),
    ('quiet_derby','casual','revision'),
    ('quiet_derby','advanced','draft'),
    ('quiet_derby','advanced','revision'),
    ('no_new_goal_palace','advanced','draft'),
])
def test_actual_source_correct_drafts_pass(case,audience,stage):
    record=row(case,audience)
    story_writer.validate_draft(captured(record,stage),record['evidence'])


@pytest.mark.parametrize('language',['en','es'])
def test_actual_accepted_multiple_recipient_ownership_is_rejected(language):
    record=row('no_new_goal_palace','casual')
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_pass_route_recipient'):
        recap_quality.validate(record['text'][language],record['evidence'],set(record['evidence']['required_fact_ids']))


@pytest.mark.parametrize('record',[r for r in ROWS if r['writer_mode']=='azure'
    and r['case']!='no_new_goal_palace'],ids=lambda r:r['case']+'-'+r['audience'])
def test_other_reviewed_ai_outputs_keep_existing_acceptance(record):
    story_writer.validate_draft({**record['text'],'fact_ids':record['evidence']['required_fact_ids']},record['evidence'])


@pytest.mark.parametrize('language,text',[
    ('en','Yoane Wissa passed to Joe Willock, who then found Tino Livramento. Livramento passed to Anthony Elanga, who passed to Harvey Barnes.'),
    ('es','Yoane Wissa pasó a Joe Willock, quien encontró a Tino Livramento. Livramento pasó a Anthony Elanga, que pasó a Harvey Barnes.'),
    ('en','Yoane Wissa passed to Joe Willock, and Joe Willock passed to Tino Livramento. Tino Livramento passed to Anthony Elanga, and Anthony Elanga passed to Harvey Barnes.'),
    ('en','Yoane Wissa passed to Joe Willock, then the ball went through Tino Livramento and Anthony Elanga to Harvey Barnes.'),
    ('es','Yoane Wissa pasó a Joe Willock, luego el balón pasó por Tino Livramento y Anthony Elanga hasta Harvey Barnes.'),
    ('en','Yoane Wissa passed to Joe Willock, continuing through Tino Livramento and Anthony Elanga before reaching Harvey Barnes.'),
])
def test_correct_subject_changes_and_collective_routes_remain_valid(language,text):
    facts=row('no_new_goal_palace','casual')['evidence']['facts']
    for sentence in text.split('. '):
        recap_quality.validate_pass_route_recipients(sentence,facts)


def test_one_player_can_have_multiple_verified_direct_recipients():
    facts=row('open_brighton','casual')['evidence']['facts']
    recap_quality.validate_pass_route_recipients('Calvin Bassey passed to Sander Berge and Emile Smith Rowe.',facts)


def test_full_bilingual_recap_can_describe_the_verified_route_clearly():
    record=row('no_new_goal_palace','casual')
    value={'fact_ids':record['evidence']['required_fact_ids'],
        'en':"Crystal Palace lead Newcastle United 2-0 at 75:00. At 55:00, Yoane Wissa recovered the ball and passed to Joe Willock, who found Tino Livramento; Livramento passed to Anthony Elanga. Elanga passed to Harvey Barnes, who shot at 55:10. No goal followed.",
        'es':"Crystal Palace gana 2-0 a Newcastle United a los 75:00. A los 55:00, Yoane Wissa recuperó el balón y pasó a Joe Willock, quien encontró a Tino Livramento; Livramento pasó a Anthony Elanga. Elanga pasó a Harvey Barnes, quien remató a los 55:10. No hubo gol."}
    story_writer.validate_draft(value,record['evidence'])


@pytest.mark.parametrize('replacement',['11 seconds','30 seconds'])
def test_rule_continuation_rejects_wrong_duration(replacement):
    record=row('quiet_derby','advanced')
    value=copy.deepcopy(captured(record,'revision'))
    value['en']=value['en'].replace('lasted 10 seconds','lasted '+replacement)
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,record['evidence'])


@pytest.mark.parametrize('before,after',[
    ('30-second threshold','31-second threshold'),
    ('30-second threshold','30-shot threshold'),
    ('within the 30-second threshold','outside the 30-second threshold'),
])
def test_rule_continuation_rejects_wrong_threshold_units_or_relation(before,after):
    record=row('quiet_derby','advanced')
    value=copy.deepcopy(captured(record,'revision'))
    value['en']=value['en'].replace(before,after)
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,record['evidence'])


def test_new_pass_partition_wording_cannot_hide_wrong_remainder():
    record=row('palace_repeated_replies','casual')
    value=copy.deepcopy(captured(record,'revision'))
    value['en']=value['en'].replace('two more passes','three more passes')
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,record['evidence'])


def test_clock_passes_exception_cannot_hide_a_football_pass_count():
    record=row('quiet_derby','casual')
    value=copy.deepcopy(captured(record,'revision'))
    value['en']=value['en'].replace('as the match passes 62 minutes','after three passes as the match passes 62 minutes')
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,record['evidence'])


@pytest.mark.parametrize('language',['en','es'])
def test_actual_original_wrong_individual_credit_remains_rejected(language):
    record=row('palace_repeated_replies','casual')
    value=captured(record,'draft')[language]
    with pytest.raises(recap_quality.RecapQualityError):
        recap_quality.validate(value,record['evidence'],set(record['evidence']['required_fact_ids']))
        recap_quality.validate_selected_claims(value,record['evidence'])


def test_spanish_after_recovery_wording_keeps_the_two_actual_action_times():
    record=row('quiet_derby','casual')
    text='A los 62:10, Erling Haaland realizó un remate tras la recuperación de Enzo Fernandez a los 62:00.'
    recap_quality.validate_selected_claims(text,record['evidence'])
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_recovery_clock'):
        recap_quality.validate_selected_claims(text.replace('62:00','62:10'),record['evidence'])


CONFIRMATION=json.loads((Path(__file__).parent/'fixtures/v24-confirmation-regressions.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('record',[r for r in CONFIRMATION if r['writer_mode']=='azure'],ids=lambda r:r['case']+'-'+r['audience'])
def test_fresh_reviewed_ai_outputs_keep_acceptance(record):
    story_writer.validate_draft({**record['text'],'fact_ids':record['evidence']['required_fact_ids']},record['evidence'])


def test_captured_ordinal_clock_wording_does_not_claim_football_passes():
    record=next(r for r in CONFIRMATION if r['case']=='quiet_derby' and r['audience']=='casual')
    story_writer.validate_draft(captured(record,'revision'),record['evidence'])


def test_following_goal_scorer_is_not_a_second_recipient():
    facts=row('palace_repeated_replies','casual')['evidence']['facts']
    recap_quality.validate_pass_route_recipients('Jefferson Lerma passed to Adam Wharton, and finally Jean-Philippe Mateta scored.',facts)
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_pass_route_recipient'):
        recap_quality.validate_pass_route_recipients('Jefferson Lerma passed to Jean-Philippe Mateta, who scored.',facts)
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_pass_route_recipient'):
        recap_quality.validate_pass_route_recipients('Jefferson Lerma passed to Jean-Philippe Mateta scored.',facts)
