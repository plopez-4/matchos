import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app import matchday, main, story_writer, recap_quality
from app.discipline import card_facts, card_text, REASONS
from app.fan_briefing import fan_briefing
from app.models import MatchEvent, CatchUpRequest


def seaside():
    return [MatchEvent(**e) for e in matchday.library_fixture(matchday.PROFILES[2], 'discipline-check', 3)]


def test_authored_reasons_reach_event_evidence_in_both_languages():
    for profile, code in zip(matchday.PROFILES, ['serious_foul_play', 'violent_punch', 'violent_push']):
        feed = [MatchEvent(**e) for e in matchday.library_fixture(profile, 'reason-check', 3)]
        card = next(e for e in feed if e.type == 'red_card')
        assert card.card_reason == code
        observed = [e for e in feed if e.sequence <= card.sequence]
        recap = main.build_catch_up(observed, CatchUpRequest())['fan_briefing']
        for language in ('en', 'es'):
            assert REASONS[code][language] in recap['spoken_recap'][language]
        packet = story_writer.evidence_packet(recap, observed)
        fact = next(f for f in packet['facts'] if f['fact_id'] == f'red_card:{card.event_id}')
        assert fact['data']['reason_text'] == REASONS[code]
        assert fact['evidence_event_ids'] == [card.event_id]


def test_post_match_abuse_is_losing_team_only_and_does_not_reduce_playing_numbers():
    feed = seaside()
    card = feed[-1]
    assert card.type == 'red_card' and card.card_phase == 'post_match'
    assert feed[-2].type == 'match_end'
    assert card.card_reason == 'abusive_language'
    assert card.match_second == feed[-2].match_second == matchday.DURATION
    score = {t: sum(e.type == 'goal' and e.team_id == t for e in feed) for t in ('home','away')}
    assert score[card.team_id] < score['home' if card.team_id == 'away' else 'away']
    facts = card_facts(card, feed)
    assert facts['players_remaining'] is None
    names = {e.team_id: e.team_name for e in feed}
    assert 'down to' not in card_text(facts, names)
    assert 'jugó con' not in card_text(facts, names, 'es')
    assert 'after the final whistle' in card_text(facts, names)
    assert 'después del pitido final' in card_text(facts, names, 'es')
    briefing = fan_briefing(feed, feed)
    assert briefing['locale_facts']['phase'] == 'finished'
    pulse = matchday.pulse(feed, matchday.DURATION)
    assert pulse['why_now']['post_match']
    assert pulse['why_now']['card_event_id'] == card.event_id
    assert not matchday.rank([{'match_id':'m', 'pulse':pulse}])


def test_post_match_card_cannot_be_ingested_before_final_whistle():
    card = seaside()[-1]
    previous = main.store.pop(card.match_id, None)
    try:
        with pytest.raises(HTTPException, match='Post-match discipline'):
            main.append_event(card)
    finally:
        main.store.pop(card.match_id, None)
        if previous is not None:
            main.store[card.match_id] = previous


def test_unknown_reason_rejected_and_legacy_missing_reason_stays_unknown():
    card = seaside()[0].model_dump()
    card.update(type='red_card', card_reason='made_up_foul')
    with pytest.raises(ValueError, match='Unknown recorded'):
        MatchEvent(**card)
    card['card_reason'] = None
    event = MatchEvent(**card)
    assert 'not recorded' in card_text(card_facts(event, [event]), {'home':'Home','away':'Away'})


def test_second_during_match_card_counts_to_nine_but_post_match_card_does_not():
    feed = seaside()
    first = next(e for e in feed if e.type == 'red_card')
    second = first.model_copy(update={'event_id':'second', 'sequence':first.sequence+1, 'player_id':'away-7'})
    assert card_facts(second, [first, second])['players_remaining'] == 9
    post = second.model_copy(update={'card_phase':'post_match'})
    assert card_facts(post, [first, post])['players_remaining'] is None


def test_final_tick_delivers_post_match_notification_and_finished_recap():
    with TestClient(main.app, headers={'X-MatchOS-Client':'replay'}) as client:
        client.post('/api/session', json={}).raise_for_status()
        day = 'test-v4-post-match-check'
        view = client.post('/api/matchdays/start', json={'matchday_id':day}).json()
        # Set up the already-observed penultimate tick without generating AI prose.
        for entry in view['matches']:
            mid = entry['match_id']
            for raw in main.security.matches[mid]['fixture']:
                if raw['match_second'] < matchday.DURATION:
                    main.append_event(MatchEvent(**raw))
        state = main.security.matches[view['matches'][0]['match_id']]
        state.update(clock=matchday.DURATION-30, tick=185)
        response = client.post(f'/api/matchdays/{day}/tick', json={'tick':186})
        response.raise_for_status()
        final = response.json()
        assert final['finished'] and final['recommendation'] is None
        assert final['notification']['match_id'].endswith('-quiet')
        assert 'after full time' in final['notification']['title']
        quiet = next(e for e in final['matches'] if e['role'] == 'quiet')
        assert quiet['briefing']['locale_facts']['phase'] == 'finished'
        assert quiet['pulse']['score'] == {'home':1,'away':0}
        assert quiet['briefing']['locale_facts']['red_cards'][-1]['players_remaining'] is None


def test_ai_card_validator_requires_post_match_phase_and_rejects_playing_number_claim():
    feed = seaside()
    recap = main.build_catch_up(feed, CatchUpRequest())['fan_briefing']
    packet = story_writer.evidence_packet(recap, feed)
    card = feed[-1]
    packet['required_fact_ids'] = [f'red_card:{card.event_id}']
    valid = f'{card.player_name} was sent off after full time at 93:00.'
    recap_quality.validate_selected_claims(valid, packet)
    with pytest.raises(recap_quality.RecapQualityError, match='missing_post_match_card_phase'):
        recap_quality.validate_selected_claims(valid.replace(' after full time', ''), packet)
    with pytest.raises(recap_quality.RecapQualityError, match='post_match_card_changed_playing_numbers'):
        recap_quality.validate_selected_claims(valid.replace(' at', ', leaving Fulham down to 9 men at'), packet)
