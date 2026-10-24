import copy
import json
from pathlib import Path
from xml.etree import ElementTree as ET
import pytest
from app import main, narration, recap_quality, story_writer
from app.models import MatchEvent, CatchUpRequest
from app.intelligence import match_stories, story_graph
from test_story_writer import configured, provider


def feed(now=3750):
    # Fixed observed examples keep the bilingual contracts independent of generator changes.
    rows = json.loads((Path(__file__).parent/'fixtures/linked_scoring_reference.json').read_text())
    return [MatchEvent(**raw) for raw in rows if raw['match_second'] <= now]


def transition(events):
    return next(story for story in match_stories(events) if story['kind']=='recovery_shot' and story['match_second']==3610)


def test_exact_scoring_sequence_links_recovery_passes_shot_and_equalizer():
    events = feed()
    story = transition(events)
    link = story['metric']['goal_link']
    assert link['recoverer']=='Takehiro Tomiyasu' and link['scorer']=='Ismaila Sarr'
    assert link['completed_pass_count']==3 and story['metric']['elapsed_seconds']==10
    assert link['shot_clock']=='60:10' and link['goal_clock']=='60:11'
    assert link['score_change']=='equalization' and link['score_after']=={'home':1,'away':1}
    assert story['sequence']==link['goal_sequence']
    assert set(link['evidence_event_ids']) <= set(story['evidence_event_ids'])
    graph = story_graph(events)
    assert {'source':link['goal_event_id'],'target':story['story_id'],'type':'supports'} in graph['edges']


@pytest.mark.parametrize('field,value', [('related_event_id',None),('team_id','away'),('player_id','other'),
    ('period',1),('possession_id','different'),('match_id','another'),('match_second',3650)])
def test_nearby_or_invalid_goal_is_not_attached_to_the_shot(field,value):
    events = [event.model_copy(update={field:value}) if event.type=='goal' and event.match_second==3611 else event for event in feed()]
    assert 'goal_link' not in transition(events)['metric']


def test_future_goal_and_non_goal_shot_do_not_produce_scoring_context():
    assert 'goal_link' not in transition(feed(3610))['metric']
    altered = [event.model_copy(update={'outcome':'saved'}) if event.type=='shot' and event.match_second==3610 else event for event in feed()]
    assert 'goal_link' not in transition(altered)['metric']


def test_goal_arriving_after_shot_cursor_still_explains_the_build_up():
    events = feed()
    story = transition(events)
    result = main.build_catch_up(events,CatchUpRequest(since_sequence=story['metric']['shot_sequence']))
    plan = result['fan_briefing']['story_plan']
    assert plan['change_story_id']==story['story_id']
    for language in ('en','es'):
        text=result['fan_briefing']['spoken_recap'][language]
        assert 'Tomiyasu' in text and 'Sarr' in text and '60:10' in text and '60:11' in text
        assert ''.join(ET.fromstring(narration.build_ssml(result['fan_briefing'],language,'matchday')[0]).itertext())==text


def drafted():
    events=feed()
    fan=main.build_catch_up(events,CatchUpRequest())['fan_briefing']
    packet=story_writer.evidence_packet(fan,events)
    value={'en':"At 62:30, Crystal Palace and Newcastle United are level 1–1. Harvey Barnes scored for Newcastle at 15:11. After Takehiro Tomiyasu's recovery and 3 completed passes, Ismaila Sarr shot at 60:10, 10 seconds later, and that shot became Palace's equalizer at 60:11.",
           'es':'A los 62:30, Crystal Palace y Newcastle United están empatados 1–1. Harvey Barnes marcó para Newcastle a los 15:11. Tras la recuperación de Takehiro Tomiyasu y 3 pases completados, Ismaila Sarr remató a los 60:10, 10 segundos después, y ese remate terminó en el gol del empate a los 60:11.',
           'fact_ids':packet['required_fact_ids']}
    return fan,events,packet,value


def test_connected_bilingual_draft_passes_and_disconnected_list_is_rejected():
    _,_,packet,value=drafted()
    story_writer.validate_draft(value,packet)
    value['es']=('A los 62:30, Crystal Palace y Newcastle United están empatados 1–1. Harvey Barnes marcó a los 15:11. '
                 'Ismaila Sarr marcó a los 60:11. Takehiro Tomiyasu recuperó el balón y Sarr remató a los 60:10, 10 segundos después.')
    with pytest.raises(recap_quality.RecapQualityError,match='missing_recovery_goal_connection'):
        story_writer.validate_draft(value,packet)


def test_invented_pass_count_is_rejected():
    _,_,packet,value=drafted()
    value['en']=value['en'].replace('3 completed passes','2 completed passes')
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_scoring_sequence_pass_count'):
        story_writer.validate_draft(value,packet)


def test_live_model_failure_cannot_credit_team_passes_to_the_recoverer():
    _,_,packet,value=drafted()
    value['en']=value['en'].replace("After Takehiro Tomiyasu's recovery and 3 completed passes",
                                  'After Takehiro Tomiyasu recovered and completed 3 passes')
    with pytest.raises(recap_quality.RecapQualityError,match='wrong_scoring_sequence_pass_credit'):
        story_writer.validate_draft(value,packet)


def test_live_model_failure_cannot_call_a_current_tie_a_lead():
    _,_,packet,value=drafted()
    bad=value['es'].replace('están empatados 1–1','va por delante 1–1')
    with pytest.raises(recap_quality.RecapQualityError,match='contradictory_current_score'):
        recap_quality.validate_selected_claims(bad,packet)


def test_live_model_failure_cannot_substitute_recovery_for_the_shot_action():
    _,_,packet,_=drafted()
    bad=('At 62:30, Crystal Palace and Newcastle United are tied 1-1. Harvey Barnes scored at 15:11. '
         'Then at 60:10, Takehiro Tomiyasu recovered possession and completed three passes within 10 seconds '
         'before Ismaila Sarr scored the equalizer at 60:11.')
    with pytest.raises(recap_quality.RecapQualityError,match='missing_recovery_goal_connection'):
        recap_quality.validate_selected_claims(bad,packet)


def test_linked_goal_does_not_end_with_a_generic_restatement():
    _,_,packet,value=drafted()
    value['en']+=' This recovery-shot pattern shows how the goal was set up.'
    with pytest.raises(recap_quality.RecapQualityError,match='repeated_linked_goal_explanation'):
        story_writer.validate_draft(value,packet)


@pytest.mark.parametrize('language,ending', [
    ('en', ' This chain of play shows how Palace responded.'),
    ('es', ' Esta jugada muestra la respuesta de Crystal Palace.'),
])
def test_live_v12_closing_restatements_are_rejected(language,ending):
    _,_,packet,value=drafted()
    value[language]+=ending
    with pytest.raises(recap_quality.RecapQualityError,match='repeated_linked_goal_explanation'):
        story_writer.validate_draft(value,packet)


@pytest.mark.parametrize('language,extra', [
    ('en', ' Barnes scored, setting the tone early.'),
    ('en', ' This was sharp build-up.'),
    ('es', ' Barnes marcó, marcando el ritmo temprano.'),
])
def test_live_v12_unmeasured_quality_is_rejected(language,extra):
    _,_,packet,value=drafted()
    value[language]+=extra
    with pytest.raises(recap_quality.RecapQualityError,match='unsupported_interpretation'):
        story_writer.validate_draft(value,packet)


def test_natural_adjacent_sentences_can_connect_the_same_observed_move():
    _,_,packet,value=drafted()
    value['en']=("At 62:30, Crystal Palace and Newcastle United are level 1–1. Harvey Barnes scored at 15:11. "
                 "Takehiro Tomiyasu recovered the ball and Palace completed 3 passes. Ismaila Sarr shot at 60:10, "
                 "10 seconds after the recovery. That shot became Sarr's equalizer at 60:11.")
    story_writer.validate_draft(value,packet)


def test_observed_passing_path_is_valid_without_repeating_elapsed_seconds():
    _,_,packet,value=drafted()
    value['en']=('At 62:30, Crystal Palace and Newcastle United are tied 1-1. Harvey Barnes scored at 15:11. '
                 'Takehiro Tomiyasu recovered the ball at 60:00 and completed a pass to Adam Wharton, who passed '
                 'to Jean-Philippe Mateta, then to Ismaila Sarr, who scored the equalizer at 60:11 after three '
                 'completed passes in the 60:00-60:10 window.')
    story_writer.validate_draft(value,packet)


def test_passing_path_can_explain_the_goal_across_sentences_without_shot_timestamp():
    _,_,packet,value=drafted()
    value['en']=("At 62:30, Crystal Palace and Newcastle United are level 1–1. Harvey Barnes scored at 15:11. "
                 "Takehiro Tomiyasu recovered the ball at 60:00, and Palace completed 3 passes. "
                 "That move ended with Ismaila Sarr scoring the equalizer at 60:11.")
    story_writer.validate_draft(value,packet)
    value['en']=value['en'].replace('at 60:00,','in the 60:00–60:30 window,')
    with pytest.raises(recap_quality.RecapQualityError,match='ambiguous_statistic_window'):
        story_writer.validate_draft(value,packet)


def test_writer_receives_ordered_observations_not_a_pre_authored_commentary():
    _,_,packet,_=drafted()
    compact=story_writer.writer_evidence(packet)
    sequence=next(fact['data'] for fact in compact['facts'] if fact['data'].get('kind')=='verified_scoring_sequence')
    assert [row['action'] for row in sequence['ordered_actions']]==['recovery','completed_pass','completed_pass','completed_pass','shot','goal']
    passes=[row['passer'] for row in sequence['ordered_actions'] if row['action']=='completed_pass']
    assert passes==['Takehiro Tomiyasu','Adam Wharton','Jean-Philippe Mateta']
    assert sequence['ordered_actions'][0]['clock']=='60:00'
    assert sequence['ordered_actions'][-2]['clock']=='60:10'
    assert sequence['team_completed_passes']==3
    assert not any(key in sequence for key in ('text','commentary','canonical_text'))


def test_whole_ai_paragraph_is_reviewed_and_preserved(configured,monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE','off')
    fan,events,_,value=drafted()
    monkeypatch.setenv('MATCHOS_AI_MODE','azure')
    model,requests=provider(value)
    with model:
        written=story_writer.write(fan,events,model)
    assert written['mode']=='azure' and len(requests)==2
    assert written['text']=={language:value[language] for language in ('en','es')}
