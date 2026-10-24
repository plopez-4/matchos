import copy
import json
from pathlib import Path

import pytest
from app import matchday, recap_context, recap_quality, story_writer
from app.models import MatchEvent

ROWS=json.loads((Path(__file__).parent/'fixtures/recap-v18-clock-errors.json').read_text(encoding='utf-8'))


def evidence(row):
    packet=copy.deepcopy(row['evidence'])
    profile=next(p for p in matchday.PROFILES if p['role']==row['role'])
    events=[MatchEvent(**event) for event in matchday.library_fixture(profile,row['snapshot']['match_id'],row['variant_id']-1)
            if event['match_second']<=row['snapshot']['match_second']]
    fact=next(f for f in packet['facts'] if f['fact_id']=='trajectory')
    names=next(f['data']['names'] for f in packet['facts'] if f['fact_id']=='score')
    fact['data']=recap_context.score_chronology(fact['data'],events,names)
    return packet


@pytest.mark.parametrize('row',ROWS,ids=lambda r:r['case']+'-'+r['audience'])
def test_actual_accepted_shot_clock_and_historical_scorer_errors_are_rejected(row):
    packet=evidence(row)
    expected='wrong_explicit_goal_scorer' if row['case']=='late_derby_equalizer' else 'wrong_explicit_shot_clock'
    with pytest.raises(recap_quality.RecapQualityError) as caught:
        story_writer.validate_draft({**row['text'],'fact_ids':packet['required_fact_ids']},packet)
    assert any(issue['code']==expected for issue in caught.value.details['issues'])


@pytest.mark.parametrize('row',ROWS,ids=lambda r:r['case']+'-'+r['audience'])
def test_correct_recorded_event_roles_and_names_remain_valid(row):
    packet=evidence(row)
    value={**row['text'],'fact_ids':packet['required_fact_ids']}
    value['en']=value['en'].replace('goal attempt at 15:11','goal attempt at 15:10').replace('shot and goal at 75:11','goal at 75:11').replace('10:11 with Erling Haaland scoring','10:11 with Jeremy Doku scoring')
    value['es']=value['es'].replace('remató y anotó a los 75:11','anotó a los 75:11').replace('10:11 con un gol de Erling Haaland','10:11 con un gol de Jeremy Doku')
    story_writer.validate_draft(value,packet)


def test_scoring_timeline_keeps_all_observed_goals_and_distinct_shots_without_mutating_source():
    row=next(row for row in ROWS if row['case']=='late_derby_equalizer')
    original=copy.deepcopy(row['evidence'])
    packet=evidence(row)
    transitions=next(f['data']['transitions'] for f in packet['facts'] if f['fact_id']=='trajectory')
    assert [(t['scorer'],t['goal_clock'],t['shot_clock']) for t in transitions]==[
        ('Jeremy Doku','10:11','10:10'),('Amad Diallo','50:11','50:10'),
        ('Erling Haaland','69:11','69:10'),('Bryan Mbeumo','75:11','75:10')]
    assert row['evidence']==original


def test_individual_pass_totals_recount_the_recorded_team_path():
    row=next(row for row in ROWS if row['case']=='palace_repeated_replies')
    packet=story_writer.writer_evidence(evidence(row))
    sequence=next(f['data'] for f in packet['facts'] if f['data'].get('kind')=='verified_scoring_sequence')
    assert sequence['team_completed_passes']==3
    assert sequence['individual_completed_passes']==[
        {'player':'Daichi Kamada','count':1},{'player':'Jefferson Lerma','count':1},{'player':'Adam Wharton','count':1}]
