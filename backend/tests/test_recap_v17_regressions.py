"""Captured model outputs: source-correct partitions and actual accepted defects."""
import copy
import json
from pathlib import Path

import pytest
from app import recap_quality, story_writer

ROWS=json.loads((Path(__file__).parent/'fixtures/recap-v17-observed-drafts.json').read_text(encoding='utf-8'))


def sample(case,audience):
    return next(row for row in ROWS if row['case']==case and row['audience']==audience)


def revision(row):
    return next(trace['draft'] for trace in row['evaluation_trace'] if trace['stage']=='revision')


@pytest.mark.parametrize('case,audience',[
    ('first_half_exchange','casual'),('first_half_exchange','advanced'),
    ('late_derby_equalizer','casual'),('quiet_derby','advanced')])
def test_actual_source_correct_revisions_are_not_false_rejections(case,audience):
    row=sample(case,audience)
    story_writer.validate_draft(revision(row),row['evidence'])


@pytest.mark.parametrize('case,audience,code',[
    ('early_derby_contribution','advanced','wrong_explicit_goal_clock'),
    ('late_fulham_turnaround_and_reply','casual','wrong_equalizer_clock'),
    ('quiet_derby','casual','unsupported_interpretation')])
def test_actual_accepted_errors_are_now_rejected(case,audience,code):
    row=sample(case,audience)
    value={**row['text'],'fact_ids':row['evidence']['required_fact_ids']}
    with pytest.raises(recap_quality.RecapQualityError) as caught:
        story_writer.validate_draft(value,row['evidence'])
    assert any(issue['code']==code for issue in caught.value.details['issues'])


@pytest.mark.parametrize('audience',['casual','advanced'])
def test_partition_cannot_accept_a_wrong_remainder(audience):
    row=sample('first_half_exchange',audience)
    value=copy.deepcopy(revision(row))
    value['en']=value['en'].replace('two more team passes','three more team passes').replace('two others by teammates','three others by teammates')
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,row['evidence'])


def test_continuation_cannot_hide_wrong_duration():
    row=sample('first_half_exchange','advanced')
    value=copy.deepcopy(revision(row))
    value['en']=value['en'].replace('10 seconds','11 seconds')
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,row['evidence'])


def test_fully_timed_quiet_route_requires_each_recorded_clock():
    row=sample('quiet_derby','advanced')
    value=copy.deepcopy(revision(row))
    value['en']=value['en'].replace('62:04','62:05')
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,row['evidence'])


def test_captured_genuine_individual_pass_errors_stay_rejected():
    for case in ('first_half_exchange','late_derby_equalizer'):
        row=sample(case,'casual')
        value=next(trace['draft'] for trace in row['evaluation_trace'] if trace['stage']=='draft')
        with pytest.raises(recap_quality.RecapQualityError):
            story_writer.validate_draft(value,row['evidence'])


def test_joint_subject_cannot_claim_the_entire_team_total():
    row=sample('late_derby_equalizer','casual')
    value=copy.deepcopy(revision(row))
    value['en']=value['en'].replace('then completed two more passes','then completed three more passes')
    with pytest.raises(recap_quality.RecapQualityError):
        story_writer.validate_draft(value,row['evidence'])
