import copy
import json
from pathlib import Path
import pytest
from app import recap_quality,story_writer

SAMPLES=json.loads((Path(__file__).parent/'fixtures/recap-v16-rejected-drafts.json').read_text(encoding='utf-8'))


def sample(case,audience):
    return next(row for row in SAMPLES if row['case']==case and row['audience']==audience)


def draft(row,stage):
    return next(trace['draft'] for trace in row['evaluation_trace'] if trace['stage']==stage)


@pytest.mark.parametrize('case,audience',[
    ('quiet_brighton','casual'),('quiet_brighton','advanced'),('first_half_exchange','advanced')])
def test_actual_source_correct_revisions_are_accepted(case,audience):
    row=sample(case,audience)
    story_writer.validate_draft(draft(row,'revision'),row['evidence'])


def test_actual_individual_pass_error_stays_rejected():
    row=sample('first_half_exchange','advanced')
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_scoring_sequence_pass_credit'):
        story_writer.validate_draft(draft(row,'draft'),row['evidence'])


def test_actual_wrong_single_pass_clock_stays_rejected():
    row=sample('early_derby_contribution','advanced')
    with pytest.raises(recap_quality.RecapQualityError) as caught:
        story_writer.validate_draft(draft(row,'draft'),row['evidence'])
    assert any(issue['code']=='wrong_creation_pass_clock' for issue in caught.value.details['issues'])


def test_one_verified_pass_does_not_need_a_rolling_window_but_aggregate_still_does():
    row=sample('early_derby_contribution','advanced')
    packet=row['evidence']
    value={'en':"Manchester United lead Manchester City 1-0 at 25:00. Bryan Mbeumo scored at 15:11 after a pass from Bruno Fernandes at 15:09. Between 15:00 and 25:00, Fernandes completed 3 passes to Mbeumo; the goal attempt was followed by saved shots at 16:40 and 18:40.",
           'es':"Manchester United gana 1-0 a Manchester City a los 25:00. Bryan Mbeumo marcó a los 15:11 tras un pase de Bruno Fernandes a los 15:09. Entre 15:00 y 25:00, Fernandes completó 3 pases a Mbeumo; después del remate que terminó en gol llegaron los remates detenidos a los 16:40 y 18:40.",
           'fact_ids':packet['required_fact_ids']}
    story_writer.validate_draft(value,packet)
    wrong_clock={**value,'en':value['en'].replace('pass from Bruno Fernandes at 15:09','pass from Bruno Fernandes at 15:10')}
    with pytest.raises(recap_quality.RecapQualityError): story_writer.validate_draft(wrong_clock,packet)
    wrong_window={**value,'en':value['en'].replace('Between 15:00 and 25:00','Between 20:00 and 25:00')}
    with pytest.raises(recap_quality.RecapQualityError): story_writer.validate_draft(wrong_window,packet)


@pytest.mark.parametrize('replacement',['31-second threshold','30-shot threshold','outside the 30-second threshold'])
def test_rule_explanation_exception_cannot_hide_wrong_limits_or_action_counts(replacement):
    row=sample('quiet_brighton','advanced')
    value=copy.deepcopy(draft(row,'revision'))
    value['en']=value['en'].replace('within the 30-second threshold',replacement)
    with pytest.raises(recap_quality.RecapQualityError): story_writer.validate_draft(value,row['evidence'])


def test_captured_hype_is_not_accepted_as_a_quiet_match_fact():
    row=sample('quiet_brighton','casual')
    with pytest.raises(recap_quality.RecapQualityError,match='unsupported_interpretation'):
        story_writer.validate_draft(draft(row,'draft'),row['evidence'])
