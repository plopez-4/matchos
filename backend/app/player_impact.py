"""Observed player contributions over rolling ten-minute snapshots and archived windows.

These rules do not infer possession time, defensive lines, dribbles or shot quality.
"""
from collections import defaultdict

KINDS = ('player_shot_creation', 'player_shooting', 'player_forward_passing')
VERSIONS = dict(zip(KINDS, ('player-shot-creation-v1', 'player-shooting-v1', 'player-forward-passing-v1')))
WINDOW_SECONDS = 600
SHOT_LINK_SECONDS = 10


def direct_shot_pass(previous, shot):
    if previous.type != 'pass' or shot.type != 'shot' or previous.outcome != 'complete':
        return False
    if (not previous.possession_id or not previous.recipient_player_id
            or previous.recipient_player_id != shot.player_id
            or shot.sequence != previous.sequence + 1
            or not 0 <= shot.match_second - previous.match_second <= SHOT_LINK_SECONDS):
        return False
    if any(getattr(previous, key) != getattr(shot, key)
           for key in ('match_id', 'team_id', 'period', 'possession_id')):
        return False
    return (previous.end_x is not None and previous.end_y is not None
            and abs(previous.end_x-shot.x) < 0.001 and abs(previous.end_y-shot.y) < 0.001)


def player_story_text(story, language='en', audience='casual', names=None):
    metric = story['metric']
    es = language == 'es'
    player = metric['player_name']
    team = (names or {}).get(metric['team_id'], metric['team_name'])
    start, end = metric['start_second'], metric['end_second']
    window = f'{start//60}:{start%60:02d}–{end//60}:{end%60:02d}'
    count, total = metric['count'], metric['team_total']
    if story['kind'] == 'player_shot_creation':
        text = (f'{player} dio el último pase antes de {count} de los {total} remates de {team} en {window}.' if es else
                f"{player} supplied the final pass before {count} of {team}'s {total} shots in {window}.")
        targets = {link['recipient_player_name'] for link in metric['links']}
        if len(targets) == 1:
            target = next(iter(targets))
            text = (f'{player} encontró repetidamente a {target}: sus pases completados precedieron directamente {count} de los {total} remates de {team} en {window}.' if es else
                    f"{player} repeatedly found {target}: his completed passes directly preceded {count} of {team}'s {total} shots in {window}.")
        if audience == 'advanced':
            text += (' El receptor remató en la siguiente acción registrada, en la misma posesión y en un máximo de diez segundos; no es una valoración de la ocasión.' if es else
                     ' Each recipient shot on the next recorded action, in the same possession and within ten seconds; this is not a chance-quality rating.')
    elif story['kind'] == 'player_shooting':
        text = (f'{player} concentró {count} de los {total} remates de {team} en {window}.' if es else
                f"{player} took {count} of {team}'s {total} shots in {window}.")
        if audience == 'advanced':
            saved, blocked = metric['outcomes'].get('saved', 0), metric['outcomes'].get('blocked', 0)
            text += (f' En {window}: {saved} remates parados y {blocked} bloqueados; el recuento no mide la calidad de las ocasiones.' if es else
                     f' In {window}: {saved} shots were saved and {blocked} blocked; counts do not measure chance quality.')
    else:
        text = (f'{player} hizo avanzar el balón con {count} pases completados hacia delante para {team} en {window}.' if es else
                f'{player} moved the ball upfield with {count} completed forward passes for {team} in {window}.')
        if audience == 'advanced':
            text += (f' Cada uno avanzó al menos {metric["min_gain"]} unidades normalizadas del campo; esto no demuestra que superaran una línea defensiva.' if es else
                     f' Each gained at least {metric["min_gain"]} normalized pitch units; this does not establish that a defensive line was bypassed.')
    return text


def player_impact_stories(events, min_gain=15):
    stories = []
    matches = defaultdict(list)
    for event in events:
        matches[event.match_id].append(event)
    for match_id, match_events in matches.items():
        ordered = sorted(match_events, key=lambda event: event.sequence)
        sequence_by_id = {event.event_id: event.sequence for event in ordered}
        previous_by_shot = {shot.event_id: before for before, shot in zip(ordered, ordered[1:])
                            if direct_shot_pass(before, shot)}
        for period in (1, 2):
            observed = [event for event in ordered if event.period == period]
            if not observed:
                continue
            phase_start = 0 if period == 1 else 2700
            now = max(event.match_second for event in observed)
            first = min(event.match_second for event in observed)
            windows = [(end-WINDOW_SECONDS, end, False)
                       for end in range(phase_start+WINDOW_SECONDS, now//300*300+1, 300)]
            # The live snapshot includes the latest observed action; fans need not wait for a checkpoint.
            # Fixed half-open windows archive the spell independently of later quiet activity.
            windows.append((max(phase_start, now-WINDOW_SECONDS), now, True))
            for start, end, snapshot in windows:
                if first > start:
                    continue
                window = [event for event in observed if
                          (start < event.match_second <= end if snapshot else start <= event.match_second < end)]
                for team in ('home', 'away'):
                    team_events = [event for event in window if event.team_id == team]
                    shots = [event for event in team_events if event.type == 'shot']
                    progressive = [event for event in team_events if event.type == 'pass' and event.outcome == 'complete'
                                   and event.end_x is not None and event.end_y is not None
                                   and (event.end_x-event.x if team == 'home' else event.x-event.end_x) >= min_gain]
                    groups = {kind: defaultdict(list) for kind in KINDS}
                    for shot in shots:
                        groups['player_shooting'][shot.player_id].append(shot)
                        before = previous_by_shot.get(shot.event_id)
                        # Both actions must fall inside the stated window.
                        if before and (before.match_second > start if snapshot else before.match_second >= start):
                            groups['player_shot_creation'][before.player_id].append((before, shot))
                    for event in progressive:
                        groups['player_forward_passing'][event.player_id].append(event)
                    for kind, players in groups.items():
                        for player_id, contributions in players.items():
                            if len(contributions) < (3 if kind == 'player_forward_passing' else 2):
                                continue
                            source = [event for pair in contributions for event in pair] if kind == 'player_shot_creation' else contributions
                            actor = contributions[-1][0] if kind == 'player_shot_creation' else contributions[-1]
                            # Denominators are evidence-backed too, rather than unreferenced context.
                            context = progressive if kind == 'player_forward_passing' else shots
                            evidence = sorted({event.event_id for event in source+context}, key=sequence_by_id.get)
                            metric = {'match_id': match_id, 'team_id': team, 'team_name': actor.team_name or team.title(),
                                      'period': period, 'player_id': player_id, 'player_name': actor.player_name or player_id,
                                      'start_second': start, 'end_second': end, 'count': len(contributions),
                                      'team_total': len(context), 'min_gain': min_gain, 'max_link_seconds': SHOT_LINK_SECONDS,
                                      'evidence_event_ids': evidence, 'rule_version': VERSIONS[kind],
                                      'coverage': 'recorded_events_only', 'window_mode': 'snapshot' if snapshot else 'archive',
                                      'start_inclusive': not snapshot, 'end_inclusive': snapshot}
                            if kind == 'player_shot_creation':
                                metric['links'] = [{'pass_event_id': before.event_id, 'shot_event_id': shot.event_id,
                                                    'recipient_player_id': shot.player_id,
                                                    'recipient_player_name': shot.player_name or shot.player_id,
                                                    'elapsed_seconds': shot.match_second-before.match_second}
                                                   for before, shot in contributions]
                                metric['goal_shot_count'] = sum(shot.outcome == 'goal' for _, shot in contributions)
                            if kind == 'player_shooting':
                                metric['outcomes'] = {outcome: sum(event.outcome == outcome for event in contributions)
                                                      for outcome in ('saved', 'blocked', 'missed', 'goal')}
                            suffix = ':snapshot' if snapshot else ''
                            story = {'story_id': f'player:{kind}:{match_id}:{player_id}:{end}{suffix}', 'kind': kind,
                                     'metric': metric, 'evidence_event_ids': evidence,
                                     # A closing window alone must not reannounce old involvement after a viewer cursor.
                                     'sequence': max(event.sequence for event in source),
                                     'available_second': end, 'rule_version': VERSIONS[kind]}
                            story['text'] = player_story_text(story)
                            stories.append(story)
    return stories
