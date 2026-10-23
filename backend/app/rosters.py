"""Bundled reference identities; synthetic actor slots are not shirt numbers."""
import json
from importlib.resources import files
from functools import lru_cache

ROSTER_DATA = json.loads(files('app').joinpath('data/players_2026.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=64)
def club_for_name(team_name):
    return next((club for club in ROSTER_DATA['clubs'].values()
                 if team_name in [club['name'], *club.get('aliases', [])]), None)


@lru_cache(maxsize=512)
def player_for_slot(team_name, slot):
    club = club_for_name(team_name)
    if not club:
        return None
    identity = club.get('demo_slots', {}).get(str(slot))
    return next((player for player in club['players'] if player['id'] == identity), None)


def player_fields(team_name, slot, prefix='player'):
    player = player_for_slot(team_name, slot)
    if not player:
        return {f'{prefix}_name':f'{team_name} Player {slot}'}
    return {f'{prefix}_name':player['name'], f'{prefix}_shirt_number':player['number'],
            f'{prefix}_position':player['position']}


def player_name_for(team_name, slot):
    return player_fields(team_name, slot)['player_name']
