"""Deterministic facts and evidence graph. No causal/tactical inference."""
from app.models import MatchEvent

WINDOW = 300
RULE_SHOT = 'shot-frequency-v1'
RULE_GOAL = 'goal-v1'
RULE_RECOVERY = 'high-recovery-v1'
RULE_PROGRESSIVE = 'progressive-pass-v1'
RULE_TRANSITION = 'recovery-shot-v1'
RULE_GRAPH = 'graph-v1'

RECOVERY_THRESHOLD_COUNT = 3
RECOVERY_HOME_X = 70.0
RECOVERY_AWAY_X = 30.0
PROGRESSIVE_PASS_MIN_GAIN = 15.0
PROGRESSIVE_PASS_THRESHOLD_COUNT = 3
TRANSITION_MAX_SECONDS = 30


def shot_windows(events: list[MatchEvent]):
    if not events:
        return []
    end = max(e.match_second for e in events) // WINDOW * WINDOW
    # Both five-minute intervals must have elapsed and the feed must cover the baseline.
    if end < WINDOW * 2 or min(e.match_second for e in events) > end - WINDOW * 2:
        return []
    result = []
    for team in ('home', 'away'):
        windows = []
        for start, stop in ((end - 2 * WINDOW, end - WINDOW), (end - WINDOW, end)):
            shots = [e for e in events if e.team_id == team and e.type == 'shot'
                     and start <= e.match_second < stop]
            windows.append({'start_second': start, 'end_second': stop,
                            'shot_count': len(shots), 'evidence_event_ids': [e.event_id for e in shots]})
        result.append({'team_id': team, 'previous': windows[0], 'current': windows[1],
                       'rule_version': RULE_SHOT})
    return result


def high_recovery_windows(events: list[MatchEvent]):
    if not events:
        return []
    min_sec = min(e.match_second for e in events)
    max_sec = max(e.match_second for e in events)
    windows = []
    k = 0
    while (k + 1) * WINDOW <= max_sec:
        start, end = k * WINDOW, (k + 1) * WINDOW
        if min_sec <= start:
            for team in ('home', 'away'):
                x_thresh = RECOVERY_HOME_X if team == 'home' else RECOVERY_AWAY_X
                qualifying = [
                    e for e in events
                    if e.team_id == team and e.type == 'recovery'
                    and start <= e.match_second < end
                    and (e.x >= RECOVERY_HOME_X if team == 'home' else e.x <= RECOVERY_AWAY_X)
                ]
                windows.append({
                    'team_id': team,
                    'start_second': start,
                    'end_second': end,
                    'recovery_count': len(qualifying),
                    'threshold': RECOVERY_THRESHOLD_COUNT,
                    'qualifying_x_threshold': x_thresh,
                    'evidence_event_ids': [e.event_id for e in qualifying],
                    'rule_version': RULE_RECOVERY,
                })
        k += 1
    return windows


def progressive_pass_windows(events: list[MatchEvent]):
    if not events:
        return []
    min_sec = min(e.match_second for e in events)
    max_sec = max(e.match_second for e in events)
    windows = []
    k = 0
    while (k + 1) * WINDOW <= max_sec:
        start, end = k * WINDOW, (k + 1) * WINDOW
        if min_sec <= start:
            for team in ('home', 'away'):
                qualifying = [
                    e for e in events
                    if e.team_id == team and e.type == 'pass'
                    and e.outcome == 'complete'
                    and e.end_x is not None and e.x is not None
                    and start <= e.match_second < end
                    and ((e.end_x - e.x >= PROGRESSIVE_PASS_MIN_GAIN)
                         if team == 'home' else (e.x - e.end_x >= PROGRESSIVE_PASS_MIN_GAIN))
                ]
                windows.append({
                    'team_id': team,
                    'start_second': start,
                    'end_second': end,
                    'pass_count': len(qualifying),
                    'threshold': PROGRESSIVE_PASS_THRESHOLD_COUNT,
                    'min_gain': PROGRESSIVE_PASS_MIN_GAIN,
                    'evidence_event_ids': [e.event_id for e in qualifying],
                    'rule_version': RULE_PROGRESSIVE,
                })
        k += 1
    return windows


def recovery_shot_chains(events: list[MatchEvent]):
    chains = []
    for i, e in enumerate(events):
        if e.type != 'shot' or not e.possession_id:
            continue
        chain = [e]
        rec = None
        for prev in reversed(events[:i]):
            if (prev.period != e.period or
                    prev.possession_id != e.possession_id or
                    prev.team_id != e.team_id):
                break
            chain.insert(0, prev)
            if prev.type == 'recovery':
                rec = prev
                break
        if rec and 0 <= e.match_second - rec.match_second <= TRANSITION_MAX_SECONDS:
            chains.append({
                'team_id': e.team_id,
                'recovery_event_id': rec.event_id,
                'shot_event_id': e.event_id,
                'shot_sequence': e.sequence,
                'elapsed_seconds': e.match_second - rec.match_second,
                'possession_id': e.possession_id,
                'threshold_seconds': TRANSITION_MAX_SECONDS,
                'evidence_event_ids': [ev.event_id for ev in chain],
                'rule_version': RULE_TRANSITION,
            })
    return chains


def match_stories(events: list[MatchEvent]):
    by_id = {e.event_id: e for e in events}
    stories = []

    # 1. Goal stories
    for e in events:
        if e.type != 'goal':
            continue
        evidence = [e.event_id]
        shot = by_id.get(e.related_event_id)
        if shot and shot.type == 'shot' and shot.team_id == e.team_id:
            evidence.insert(0, shot.event_id)
        stories.append({
            'story_id': f'goal:{e.event_id}',
            'kind': 'goal',
            'text': f'{e.team_id.title()} scored at {e.match_second // 60}:{e.match_second % 60:02d}.',
            'evidence_event_ids': evidence,
            'rule_version': RULE_GOAL,
            'sequence': e.sequence,
        })

    # 2. Shot frequency stories
    for metric in shot_windows(events):
        previous, current = metric['previous'], metric['current']
        # At least three shots and an increase of two recorded attempts.
        if current['shot_count'] < 3 or current['shot_count'] - previous['shot_count'] < 2:
            continue
        end = current['end_second']
        sequence = min(e.sequence for e in events if e.match_second >= end)
        stories.append({
            'story_id': f"shots:{metric['team_id']}:{end}",
            'kind': 'shot_activity',
            'text': f"{metric['team_id'].title()} recorded {current['shot_count']} shots in minutes {current['start_second'] // 60}–{end // 60}, compared with {previous['shot_count']} in the previous five minutes.",
            'evidence_event_ids': previous['evidence_event_ids'] + current['evidence_event_ids'],
            'metric': metric,
            'rule_version': RULE_SHOT,
            'sequence': sequence,
        })

    # 3. High recovery stories
    for w in high_recovery_windows(events):
        if w['recovery_count'] >= RECOVERY_THRESHOLD_COUNT:
            end = w['end_second']
            sequence = min(e.sequence for e in events if e.match_second >= end)
            stories.append({
                'story_id': f"recovery:{w['team_id']}:{end}",
                'kind': 'high_recovery',
                'text': f"{w['team_id'].title()} recovered the ball {w['recovery_count']} times in the attacking third in minutes {w['start_second'] // 60}–{end // 60}.",
                'evidence_event_ids': w['evidence_event_ids'],
                'metric': w,
                'rule_version': RULE_RECOVERY,
                'sequence': sequence,
            })

    # 4. Progressive pass stories
    for w in progressive_pass_windows(events):
        if w['pass_count'] >= PROGRESSIVE_PASS_THRESHOLD_COUNT:
            end = w['end_second']
            sequence = min(e.sequence for e in events if e.match_second >= end)
            stories.append({
                'story_id': f"prog-pass:{w['team_id']}:{end}",
                'kind': 'progressive_pass',
                'text': f"{w['team_id'].title()} completed {w['pass_count']} forward passes gaining at least 15 pitch units each in minutes {w['start_second'] // 60}–{end // 60}.",
                'evidence_event_ids': w['evidence_event_ids'],
                'metric': w,
                'rule_version': RULE_PROGRESSIVE,
                'sequence': sequence,
            })

    # 5. Recovery to shot transition stories
    for c in recovery_shot_chains(events):
        stories.append({
            'story_id': f"recovery-shot:{c['shot_event_id']}",
            'kind': 'recovery_shot',
            'text': f"{c['team_id'].title()} recorded a shot {c['elapsed_seconds']} seconds after recovering the ball in the same possession.",
            'evidence_event_ids': c['evidence_event_ids'],
            'metric': c,
            'rule_version': RULE_TRANSITION,
            'sequence': c['shot_sequence'],
        })

    return sorted(stories, key=lambda s: (s['sequence'], s['story_id']))


def story_graph(events: list[MatchEvent]):
    nodes = [{'id': e.event_id, 'type': 'event', 'event': e.model_dump()} for e in events]
    edges = []
    for story in match_stories(events):
        nodes.append({'id': story['story_id'], 'type': 'story', 'story': story})
        if story['kind'] == 'shot_activity':
            for label in ('previous', 'current'):
                window = story['metric'][label]
                metric_id = f"metric:{story['story_id']}:{label}"
                nodes.append({'id': metric_id, 'type': 'metric_window', **window,
                              'rule_version': RULE_SHOT})
                for event_id in window['evidence_event_ids']:
                    edges.append({'source': event_id, 'target': metric_id, 'type': 'supports'})
                edges.append({'source': metric_id, 'target': story['story_id'], 'type': 'supports'})
        elif story['kind'] in ('high_recovery', 'progressive_pass'):
            metric_id = f"metric:{story['story_id']}"
            nodes.append({'id': metric_id, 'type': 'metric_window', **story['metric']})
            for event_id in story['evidence_event_ids']:
                edges.append({'source': event_id, 'target': metric_id, 'type': 'supports'})
            edges.append({'source': metric_id, 'target': story['story_id'], 'type': 'supports'})
        else:
            for event_id in story['evidence_event_ids']:
                edges.append({'source': event_id, 'target': story['story_id'], 'type': 'supports'})
    return {'nodes': nodes, 'edges': edges, 'rule_version': RULE_GRAPH}
