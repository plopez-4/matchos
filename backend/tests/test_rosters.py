import json
from pathlib import Path
import pytest
from jsonschema import validate
from app.rosters import ROSTER_DATA, player_for_slot, player_fields
from app.matchday import fixture, PROFILES


def test_shared_roster_has_unique_identities_and_resolvable_demo_slots():
    assert len(ROSTER_DATA['clubs']) == 20
    assert 'other clubs remain curated subsets' in ROSTER_DATA['scope']
    identities = []
    for club in ROSTER_DATA['clubs'].values():
        players = {p['id']:p for p in club['players']}
        assert len(players) == len(club['players'])
        assert len({p['number'] for p in players.values()}) == len(players)
        identities.extend(players)
        assert all(identity in players for identity in club.get('demo_slots', {}).values())
    assert len(identities) == len(set(identities)) == 155


def test_actor_slots_are_not_actual_shirt_numbers():
    city_midfielder = player_for_slot('Manchester City',7)
    assert city_midfielder['name'] == 'Enzo Fernandez'
    assert city_midfielder['number'] == 17
    wissa = player_for_slot('Newcastle United',10)
    assert wissa['name'] == 'Yoane Wissa' and wissa['number'] == 9
    assert player_fields('Unknown Club',7) == {'player_name':'Unknown Club Player 7'}
    assert player_for_slot('Brighton',2) == player_for_slot('Brighton & Hove Albion',2)


@pytest.mark.parametrize('profile',PROFILES, ids=lambda p:p['role'])
def test_generated_metadata_matches_one_reference_for_actor_and_recipient(profile):
    schema = json.loads((Path(__file__).resolve().parents[2]/'schemas/match-event.schema.json').read_text())
    events = fixture(profile,'roster-test')
    for event in events:
        slot = int(event['player_id'].rsplit('-',1)[1])
        player = player_for_slot(event['team_name'],slot)
        assert event['player_name'] == player['name']
        assert event['player_shirt_number'] == player['number']
        assert event['roster_version'] == ROSTER_DATA['version']
        if event['recipient_player_id']:
            recipient = player_for_slot(event['team_name'],int(event['recipient_player_id'].rsplit('-',1)[1]))
            assert event['recipient_player_name'] == recipient['name']
            assert event['recipient_player_shirt_number'] == recipient['number']
    # Validate each distinct event type against the public schema too.
    for kind in {e['type'] for e in events}:
        validate(next(e for e in events if e['type']==kind),schema)


@pytest.mark.parametrize('match_id', ['fixture', 'new-match-a', 'new-match-b'])
def test_manchester_simulation_uses_legal_elevens_and_retires_substituted_players(match_id):
    feed = fixture(PROFILES[0], match_id)
    clubs = {'home': ROSTER_DATA['clubs']['manchester-united'],
             'away': ROSTER_DATA['clubs']['manchester-city']}
    active = {team: {f'{team}-{slot}' for slot in club['demo_lineup']} for team, club in clubs.items()}
    bench = {team: {f'{team}-{slot}' for slot in club['demo_bench']} for team, club in clubs.items()}
    seen, substitutions = {'home': set(), 'away': set()}, {'home': 0, 'away': 0}
    for event in feed:
        team = event['team_id']
        assert event['player_id'] in active[team]
        if event['type'] == 'substitution':
            incoming = event['recipient_player_id']
            assert incoming in bench[team] and incoming not in active[team]
            active[team].remove(event['player_id'])
            active[team].add(incoming)
            bench[team].remove(incoming)
            substitutions[team] += 1
        elif event['type'] == 'pass':
            assert event['recipient_player_id'] in active[team]
            assert event['recipient_player_id'] != event['player_id']
            seen[team].add(event['player_id'])
        elif event['type'] == 'shot':
            assert event['player_position'] != 'GK'
        assert len(active[team]) == 11
    assert substitutions == {'home': 5, 'away': 5}
    assert all(len(actors) >= 14 for actors in seen.values())
    first_half = [event for event in feed if event['match_second'] < 2700]
    assert all(len({e['player_id'] for e in first_half if e['team_id'] == team and e['type'] == 'pass'}) == 11
               for team in ('home', 'away'))


def test_passing_routes_vary_by_replay_without_changing_authored_goal_timing():
    a, b = fixture(PROFILES[0], 'route-a'), fixture(PROFILES[0], 'route-b')
    route = lambda feed: [(e['player_id'], e['recipient_player_id']) for e in feed if e['type'] == 'pass']
    assert route(a) != route(b)
    assert [(e['match_second'], e['team_id']) for e in a if e['type'] == 'goal'] == [
        (e['match_second'], e['team_id']) for e in b if e['type'] == 'goal']


def test_roster_api_exposes_dated_full_manchester_reference_and_unknown_club():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as browser:
        for club_id, count in (('manchester-united', 30), ('manchester-city', 26)):
            response = browser.get(f'/api/rosters/{club_id}')
            assert response.status_code == 200
            data = response.json()
            assert len(data['club']['players']) == count
            assert data['source_published_on'] == '2026-09-22'
            assert 'not a confirmed match lineup' in data['scope']
        assert browser.get('/api/rosters/unknown').status_code == 404
