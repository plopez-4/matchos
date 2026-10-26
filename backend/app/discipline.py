"""Recorded synthetic disciplinary facts; never infer a reason from coordinates."""
import json
from importlib.resources import files

REASONS = json.loads(files('app').joinpath('data/sending_off_reasons.json').read_text(encoding='utf-8'))


def card_facts(event, events):
    post = event.card_phase == 'post_match'
    count = sum(e.type == 'red_card' and e.card_phase != 'post_match'
                and e.team_id == event.team_id and e.sequence <= event.sequence for e in events)
    return {'event_id': event.event_id, 'player_name': event.player_name or event.player_id,
            'team_id': event.team_id, 'clock': f'{event.match_second//60}:{event.match_second%60:02d}',
            'match_second': event.match_second, 'card_phase': event.card_phase or 'during_match',
            'card_reason': event.card_reason, 'reason_text': REASONS.get(event.card_reason),
            'players_remaining': None if post else 11-count}


def card_text(card, names, language='en', finished=False):
    es = language == 'es'
    player, team, clock = card['player_name'], names[card['team_id']], card['clock']
    if card.get('card_phase') == 'post_match':
        text = (f'{player}, de {team}, fue expulsado con tarjeta roja después del pitido final ({clock}).' if es else
                f'{player} of {team} was sent off with a red card after the final whistle ({clock}).')
    else:
        remaining = card.get('players_remaining', 10)
        text = (f"{team} {'jugó' if finished else 'juega'} con {remaining} hombres tras la expulsión con tarjeta roja de {player} a los {clock}." if es else
                f"{team} {'played with' if finished else 'are down to'} {remaining} men after {player} was sent off with a red card at {clock}.")
    reason = card.get('reason_text')
    return text + ' ' + (reason[language] if reason else (
        'El motivo de la expulsión no consta en los datos.' if es else 'The reason for the dismissal is not recorded.'))
