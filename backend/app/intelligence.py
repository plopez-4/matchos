"""Deterministic facts and evidence graph. No causal/tactical inference."""
from app.models import MatchEvent

WINDOW = 300
RULE = 'shot-frequency-v1'

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
                       'rule_version': RULE})
    return result

def match_stories(events: list[MatchEvent]):
    by_id = {e.event_id: e for e in events}
    stories = []
    for e in events:
        if e.type != 'goal':
            continue
        evidence = [e.event_id]
        shot = by_id.get(e.related_event_id)
        if shot and shot.type == 'shot' and shot.team_id == e.team_id:
            evidence.insert(0, shot.event_id)
        stories.append({'story_id': f'goal:{e.event_id}', 'kind': 'goal',
                        'text': f'{e.team_id.title()} scored at {e.match_second // 60}:{e.match_second % 60:02d}.',
                        'evidence_event_ids': evidence, 'rule_version': 'goal-v1', 'sequence': e.sequence})
    for metric in shot_windows(events):
        previous, current = metric['previous'], metric['current']
        # At least three shots and an increase of two recorded attempts.
        if current['shot_count'] < 3 or current['shot_count'] - previous['shot_count'] < 2:
            continue
        end = current['end_second']
        sequence = min(e.sequence for e in events if e.match_second >= end)
        stories.append({'story_id': f"shots:{metric['team_id']}:{end}", 'kind': 'shot_activity',
                        'text': f"{metric['team_id'].title()} recorded {current['shot_count']} shots in minutes {current['start_second'] // 60}–{end // 60}, compared with {previous['shot_count']} in the previous five minutes.",
                        'evidence_event_ids': previous['evidence_event_ids'] + current['evidence_event_ids'],
                        'metric': metric, 'rule_version': RULE, 'sequence': sequence})
    return sorted(stories, key=lambda s: s['sequence'])

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
                              'rule_version': RULE})
                for event_id in window['evidence_event_ids']:
                    edges.append({'source': event_id, 'target': metric_id, 'type': 'supports'})
                edges.append({'source': metric_id, 'target': story['story_id'], 'type': 'supports'})
        else:
            for event_id in story['evidence_event_ids']:
                edges.append({'source': event_id, 'target': story['story_id'], 'type': 'supports'})
    return {'nodes': nodes, 'edges': edges, 'rule_version': 'graph-v1'}
