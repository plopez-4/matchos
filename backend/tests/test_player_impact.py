import json
from xml.etree import ElementTree as ET

import pytest

from app import main, story_writer, narration
from app.models import MatchEvent, CatchUpRequest
from app.intelligence import match_stories, story_graph
from app.explanations import strongest_change, select_candidates
from app import recap_quality
from app.player_impact import player_impact_stories, direct_shot_pass, KINDS
from app.matchday import fixture, PROFILES
from test_story_writer import configured, provider


def event(sequence, second, kind, **fields):
    return MatchEvent(event_id=f'e{sequence}', match_id='player-test', sequence=sequence,
                      match_second=second, type=kind, team_id='home', team_name='United',
                      player_id=fields.pop('player_id', 'home-7'), player_name=fields.pop('player_name', 'Bruno'),
                      possession_id=fields.pop('possession_id', 'p1'),
                      x=fields.pop('x', 45), y=fields.pop('y', 40), **fields)


def creator_feed():
    return [event(1, 0, 'kickoff'),
            event(2, 610, 'pass', end_x=75, end_y=40, outcome='complete', recipient_player_id='home-9'),
            event(3, 615, 'shot', player_id='home-9', player_name='Amad', x=75, end_x=100, end_y=50, outcome='saved'),
            event(4, 800, 'recovery', possession_id='p2'),
            event(5, 805, 'pass', possession_id='p2', end_x=75, end_y=40, outcome='complete', recipient_player_id='home-9'),
            event(6, 810, 'shot', possession_id='p2', player_id='home-9', player_name='Amad', x=75,
                  end_x=100, end_y=50, outcome='blocked'),
            event(7, 1200, 'recovery', possession_id='p3')]


@pytest.mark.parametrize('change', [
    {'outcome':'intercepted'}, {'recipient_player_id':'home-8'}, {'possession_id':None},
    {'team_id':'away'}, {'match_id':'other'}, {'period':2}, {'end_x':None}, {'end_x':70},
    {'end_y':50}, {'sequence':1}, {'match_second':604}, {'match_second':616},
])
def test_shot_creation_rejects_unproved_or_mismatched_links(change):
    feed = creator_feed()
    before, shot = feed[1], feed[2]
    assert direct_shot_pass(before, shot)
    assert not direct_shot_pass(before.model_copy(update=change), shot)


def test_player_creation_and_shooting_have_exact_events_windows_and_denominators():
    feed = creator_feed()
    players = player_impact_stories(feed)
    creator = next(story for story in players if story['kind'] == 'player_shot_creation' and story['metric']['window_mode']=='snapshot')
    shooting = next(story for story in players if story['kind'] == 'player_shooting')
    assert (creator['metric']['count'], creator['metric']['team_total']) == (2, 2)
    assert (creator['metric']['start_second'], creator['metric']['end_second']) == (600, 1200)
    assert creator['evidence_event_ids'] == ['e2','e3','e5','e6']
    assert creator['sequence'] == 6 and creator['available_second'] == 1200
    assert creator['metric']['links'][0]['elapsed_seconds'] == 5
    assert shooting['metric']['player_name'] == 'Amad'
    assert shooting['metric']['outcomes']['saved'] == shooting['metric']['outcomes']['blocked'] == 1
    assert strongest_change(players) == creator
    assert creator in select_candidates(players, limit=1)
    graph = story_graph(feed)
    edges = {(edge['source'], edge['target']) for edge in graph['edges']}
    metric_id = f'metric:{creator["story_id"]}'
    assert (metric_id, creator['story_id']) in edges
    assert all((eid, metric_id) in edges for eid in creator['evidence_event_ids'])


def test_unobserved_windows_and_cursor_never_invent_or_repeat_old_player_activity():
    feed = creator_feed()
    # The second observed shot can qualify immediately, before a five-minute checkpoint.
    live = player_impact_stories(feed[:-1])
    assert any(s['kind']=='player_shot_creation' and s['available_second']==810 for s in live)
    assert not player_impact_stories(feed[:-2])
    assert all(s['available_second']<=810 for s in live)
    # A pass just before the window may not create a shot-creation claim for that window.
    outside = list(feed)
    outside[1] = outside[1].model_copy(update={'match_second':599})
    outside[2] = outside[2].model_copy(update={'match_second':605})
    assert not any(s['kind']=='player_shot_creation' and s['available_second']==1200 for s in player_impact_stories(outside))
    assert not player_impact_stories(feed[1:])  # Missing the observed start of the window.
    advanced = feed + [event(8, 1500, 'recovery', possession_id='p4')]
    stories = player_impact_stories(advanced)
    assert all(story['sequence'] == 6 for story in stories)
    caught = main.build_catch_up(advanced, CatchUpRequest(since_sequence=7))
    assert not any(story['kind'] in KINDS for story in caught['stories'])


def test_forward_passing_is_player_specific_completed_and_direction_aware():
    feed = [event(1, 0, 'kickoff')]
    for seq, second in enumerate((610, 620, 630), 2):
        feed.append(event(seq, second, 'pass', end_x=65, end_y=40, outcome='complete', recipient_player_id='home-9'))
    feed.append(event(5, 1200, 'recovery'))
    story = next(s for s in player_impact_stories(feed) if s['kind']=='player_forward_passing')
    assert story['metric']['count'] == 3 and story['metric']['min_gain'] == 15
    backward = [e.model_copy(update={'team_id':'away'}) for e in feed]
    assert not player_impact_stories(backward)
    backward = [e.model_copy(update={'x':75}) for e in backward]
    assert not player_impact_stories(backward)  # Only ten units forward for Away.
    backward = [e.model_copy(update={'x':85}) for e in backward]
    assert any(s['kind']=='player_forward_passing' for s in player_impact_stories(backward))
    feed[2] = feed[2].model_copy(update={'outcome':'intercepted'})
    assert not player_impact_stories(feed)


@pytest.mark.parametrize('claim', ['Amad beat his man.', 'Haaland had three headers.',
                                  'Bruno had three assists.', 'Bruno dio tres asistencias.',
                                  'Bruno made line-breaking passes.', 'Amad ganó dos regates.',
                                  'Haaland tuvo tres remates de cabeza.'])
def test_unrecorded_player_action_types_are_not_added_by_the_writer(claim):
    with pytest.raises(recap_quality.RecapQualityError, match='unsupported_interpretation'):
        recap_quality.validate(claim, {'editorial_plan':None}, set())


@pytest.mark.parametrize('claim', ['El marcador sigue 1-0 a falta de 25 minutos.',
                                  'There are 25 minutes remaining.', 'Quedan 25 minutos.'])
def test_ai_countdown_cannot_be_confused_with_elapsed_clock(claim):
    with pytest.raises(recap_quality.RecapQualityError, match='ambiguous_match_clock'):
        recap_quality.validate(claim, {'editorial_plan':{},'facts':[]}, set())


def test_omitted_selected_goal_is_rejected_rather_than_inserted(configured, monkeypatch):
    monkeypatch.setenv('MATCHOS_AI_MODE','off')
    feed = [MatchEvent(**raw) for raw in fixture(PROFILES[0],'goal-retained') if raw['match_second']<=1500]
    fan = main.build_catch_up(feed,CatchUpRequest())['fan_briefing']
    packet = story_writer.evidence_packet(fan,feed)
    draft = {
        'en': 'Manchester United lead Manchester City 1 to 0 at 25:00. Bruno Fernandes kept finding Bryan Mbeumo, supplying 3 shots in 15:00–25:00.',
        'es': 'Manchester United gana a Manchester City 1 a 0 a los 25:00. Bruno Fernandes conectó con Bryan Mbeumo para 3 remates en 15:00–25:00.',
        'fact_ids':packet['required_fact_ids']}
    with pytest.raises(recap_quality.RecapQualityError, match='missing_selected_goal'):
        story_writer.compose_draft(draft,packet)
    monkeypatch.setenv('MATCHOS_AI_MODE','azure')
    model, requests = provider(draft)
    with model:
        written = story_writer.write(fan,feed,model)
    assert written['mode']=='deterministic' and len(requests)==2
    assert written['text']==fan['spoken_recap']


def test_current_window_includes_the_latest_shot_and_keeps_boundaries_explicit():
    feed = creator_feed()[:-1]
    creator = next(s for s in player_impact_stories(feed) if s['kind']=='player_shot_creation')
    metric = creator['metric']
    assert (metric['start_second'], metric['end_second']) == (210, 810)
    assert metric['end_inclusive'] and not metric['start_inclusive']
    assert 'e6' in metric['evidence_event_ids']
    assert creator['available_second']==feed[-1].match_second
    assert '3:30–13:30' in creator['text']


def test_snapshot_identity_and_raw_provenance_survive_narration_reconstruction(monkeypatch):
    from fastapi.testclient import TestClient
    heard = []
    monkeypatch.setattr(narration,'synthesize',lambda fan,*args:(heard.append(fan) or b'ID3mock','test','measured'))
    with TestClient(main.app, headers={'X-MatchOS-Client':'replay'}) as browser:
        browser.post('/api/session',json={}).raise_for_status()
        view = browser.post('/api/matchdays/start',json={'matchday_id':'player-voice'}).json()
        for tick in range(1,51):
            browser.post('/api/matchdays/player-voice/tick',json={'tick':tick}).raise_for_status()
        fan = browser.post('/api/matches/player-voice-featured/catch-up',json={}).json()['fan_briefing']
        assert fan['story_plan']['player_story_id']
        browser.post('/api/narration', json={**fan['snapshot'], 'selected_story_ids':fan['story_plan']['story_ids'],
                                            'audience':'casual','language':'es'}).raise_for_status()
        assert heard[-1]['spoken_recap']==fan['spoken_recap']


@pytest.mark.parametrize('audience', ['casual','advanced'])
def test_player_plan_drives_bilingual_display_evidence_and_voice(audience):
    feed = creator_feed()
    result = main.build_catch_up(feed, CatchUpRequest(audience=audience))
    fan = result['fan_briefing']
    assert fan['story_plan']['player_story_id'] == fan['story_plan']['change_story_id']
    assert "Bruno repeatedly found Amad" in fan['spoken_recap']['en']
    assert 'passes directly preceded 2' in fan['spoken_recap']['en']
    assert 'Bruno encontró repetidamente a Amad' in fan['spoken_recap']['es']
    assert '600' not in fan['spoken_recap']['en']
    assert '10:00–20:00' in fan['spoken_recap']['en']
    assert 'Across the last five minutes' not in fan['spoken_recap']['en']
    assert ('within ten seconds' in fan['spoken_recap']['en']) == (audience=='advanced')
    for lang in ('en','es'):
        ssml, _, _ = narration.build_ssml(fan,lang,'matchday')
        assert ''.join(ET.fromstring(ssml).itertext()) == fan['spoken_recap'][lang]


@pytest.mark.parametrize('phrase', [
    'Bruno kept picking out Amad in 10:00–20:00, supplying the final pass for 2 shots.',
    'In 10:00–20:00, Bruno and Amad combined again and again: 2 completed passes, with a shot following each one.',
    'In the last ten minutes, Bruno found Amad with the final pass for two shots. These passes led to the two attempts.',
])
def test_model_review_sees_exact_ai_authored_player_contribution(configured, monkeypatch, phrase):
    monkeypatch.setenv('MATCHOS_AI_MODE','off')
    feed = creator_feed()
    fan = main.build_catch_up(feed,CatchUpRequest())['fan_briefing']
    packet = story_writer.evidence_packet(fan,feed)
    draft = {'en':'United and Away remain level at 0 to 0 at 20:00. ' + phrase,
             'es':'United y Away siguen empatados 0 a 0 a los 20:00. Bruno encontró una y otra vez a Amad en 10:00–20:00 y dio el último pase para 2 remates.',
             'fact_ids':packet['required_fact_ids']}
    monkeypatch.setenv('MATCHOS_AI_MODE','azure')
    model, requests = provider(draft)
    with model:
        written = story_writer.write(fan,feed,model)
    assert written['mode']=='azure' and written['review']=='model_review_passed'
    assert written['text']=={lang:draft[lang] for lang in ('en','es')}
    assert 'repeatedly found' not in written['text']['en']
    assert all('canonical_text' not in fact and 'text' not in fact['data'] for fact in packet['facts'])
    assert not any(fact['fact_id'] == 'shots' for fact in packet['facts'])
    reviewed = json.loads(requests[1]['messages'][1]['content'])['draft']
    assert reviewed['en'] == written['text']['en']
    assert 'story:'+fan['story_plan']['player_story_id'] in written['fact_ids']


@pytest.mark.parametrize('change', ['count', 'player', 'recipient', 'scope'])
def test_ai_prose_cannot_omit_required_player_count_or_scope(configured, monkeypatch, change):
    monkeypatch.setenv('MATCHOS_AI_MODE', 'off')
    feed = creator_feed()
    fan = main.build_catch_up(feed, CatchUpRequest())['fan_briefing']
    packet = story_writer.evidence_packet(fan, feed)
    text = 'United and Away are level at 0–0 at 20:00. In 10:00–20:00, Bruno supplied Amad with the final pass for 2 shots.'
    text = text.replace(*{'count': ('2 shots', '99 shots'), 'player': ('Bruno', 'Someone'),
                         'recipient': ('Amad', 'Someone'), 'scope': ('10:00–20:00', '9:00–19:00')}[change])
    value = {'en': text, 'es': text, 'fact_ids': packet['required_fact_ids']}
    monkeypatch.setenv('MATCHOS_AI_MODE', 'azure')
    model, requests = provider(value)
    with model:
        written = story_writer.write(fan, feed, model)
    assert written['mode'] == 'deterministic' and len(requests) == 2
    assert written['text'] == fan['spoken_recap']


def test_synthetic_busy_spells_support_named_contributions_but_quiet_does_not():
    feed = [MatchEvent(**raw) for raw in fixture(PROFILES[0],'impact-fixture') if raw['match_second']<=1500]
    players = player_impact_stories(feed)
    bruno = [s for s in players if s['kind']=='player_shot_creation' and s['metric']['player_name']=='Bruno Fernandes']
    assert bruno and max(s['metric']['count'] for s in bruno)==3
    haaland = [s for s in players if s['kind']=='player_shooting' and s['metric']['player_name']=='Erling Haaland']
    assert haaland and max(s['metric']['count'] for s in haaland)>=3
    quiet = [MatchEvent(**raw) for raw in fixture(PROFILES[2],'quiet-impact')]
    assert not player_impact_stories(quiet)
