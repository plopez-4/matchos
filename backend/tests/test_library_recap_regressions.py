import json
from pathlib import Path
import pytest
from app import recap_quality, story_writer, main, matchday
from app.models import MatchEvent,CatchUpRequest

CAPTURE=json.loads((Path(__file__).parent/'fixtures/library-v14-accepted-errors.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('sample',CAPTURE['samples'],ids=lambda r:r['case']+'-'+r['audience'])
@pytest.mark.parametrize('language',['en','es'])
def test_captured_accepted_library_defects_are_rejected(sample,language):
    packet=sample['packet']
    with pytest.raises(recap_quality.RecapQualityError,match=sample['expected_error']):
        recap_quality.validate(sample['text'][language],packet,set(packet['required_fact_ids']))
        recap_quality.validate_selected_claims(sample['text'][language],packet)


@pytest.mark.parametrize('text',[
    'At 55:10, Rodrigo Muniz shot 10 seconds after he recovered the ball.',
    'Rodrigo Muniz recovered the ball at 55:00 and shot 10 seconds later at 55:10.',
    'At 55:10, 10 seconds after Rodrigo Muniz recovered the ball, he shot.',
    'At 55:10, Rodrigo Muniz took a shot after recovering the ball 10 seconds earlier.',
    'A los 55:10, Rodrigo Muniz remató 10 segundos después de recuperar el balón.',
    'Rodrigo Muniz recuperó el balón a los 55:00 y remató 10 segundos después, a los 55:10.',
    'A los 55:10, 10 segundos después de recuperar el balón, Rodrigo Muniz remató.',
])
def test_correct_relative_and_explicit_action_clocks_remain_valid(text):
    packet=CAPTURE['samples'][0]['packet']
    recap_quality.validate(text,packet,set(packet['required_fact_ids']))
    recap_quality.validate_selected_claims(text,packet)


def test_single_shot_writer_gets_actual_ordered_actions_and_both_clocks():
    profile=matchday.PROFILES[2]
    events=[MatchEvent(**row) for row in matchday.library_fixture(profile,'clock-test',0) if row['match_second']<=4500]
    fan=main.build_catch_up(events,CatchUpRequest(since_sequence=max(e.sequence for e in events if e.match_second<=2700)))['fan_briefing']
    packet=story_writer.evidence_packet(fan,events)
    fact=next(f for f in story_writer.writer_evidence(packet)['facts'] if f['data'].get('kind')=='recovery_shot')
    assert fact['action_clocks']=={'recovery':'55:00','shot':'55:10'}
    assert fact['ordered_actions'][0]=={'action':'recovery','player':'Rodrigo Muniz','clock':'55:00'}
    assert fact['ordered_actions'][-1]=={'action':'shot','player':'Rodrigo Muniz','clock':'55:10'}
    assert len([a for a in fact['ordered_actions'] if a['action']=='completed_pass'])==3


RELATIONSHIPS=json.loads((Path(__file__).parent/'fixtures/library-v15-relationship-errors.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('language',['en','es'])
def test_actual_v15_self_recipient_is_rejected(language):
    sample=RELATIONSHIPS['palace']
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_scoring_sequence_pass_recipient'):
        recap_quality.validate_selected_claims(sample['text'][language],sample['packet'])


@pytest.mark.parametrize('language',['en','es'])
def test_correct_individual_recipients_remain_valid(language):
    sample=RELATIONSHIPS['halftime']
    recap_quality.validate_selected_claims(sample['text'][language],sample['packet'])


def test_balanced_half_is_not_inferred_from_tied_score():
    sample=RELATIONSHIPS['halftime']
    with pytest.raises(recap_quality.RecapQualityError,match='unsupported_interpretation'):
        recap_quality.validate(sample['text']['en'],sample['packet'],set(sample['packet']['required_fact_ids']))


@pytest.mark.parametrize('text',[
    'Rodrigo Muniz recovered the ball at 55:00 and shot at 55:10.',
    'At 55:00 Rodrigo Muniz recovered the ball. He shot at 55:10.',
    'Rodrigo Muniz recuperó el balón a los 55:00 y remató a los 55:10.',
    'A los 55:00 Rodrigo Muniz recuperó el balón. Remató a los 55:10.',
])
def test_both_verified_clocks_express_duration_without_requiring_repetition(text):
    packet=CAPTURE['samples'][0]['packet']
    recap_quality.validate(text,packet,set(packet['required_fact_ids']))
    recap_quality.validate_selected_claims(text,packet)
