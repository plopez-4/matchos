"""Observed chronology for the writer, without supplying commentary sentences."""


def score_chronology(trajectory, events, names):
    """Enrich observed score transitions with names and distinct action clocks."""
    by_id={event.event_id:event for event in events}
    goals={event.sequence:event for event in events if event.type=='goal'}
    rows=[]
    for transition in trajectory.get('transitions',[]):
        row=dict(transition)
        goal=goals.get(row['sequence'])
        if goal:
            row.update(goal_clock=f'{goal.match_second//60}:{goal.match_second%60:02d}',
                       scorer=goal.player_name or goal.player_id,team_name=names[goal.team_id])
            shot=by_id.get(goal.related_event_id)
            if (shot and shot.type=='shot' and shot.outcome=='goal'
                    and shot.player_id==goal.player_id and shot.team_id==goal.team_id
                    and shot.match_id==goal.match_id and shot.period==goal.period
                    and shot.sequence<goal.sequence and 0<=goal.match_second-shot.match_second<=10):
                row['shot_clock']=f'{shot.match_second//60}:{shot.match_second%60:02d}'
        rows.append(row)
    return {**trajectory,'transitions':rows}


def recovery_goal_link(chain, events, transitions):
    """Link only the actual goal-producing shot, never a nearby goal."""
    by_id = {event.event_id: event for event in events}
    recovery = by_id.get(chain['recovery_event_id'])
    shot = by_id.get(chain['shot_event_id'])
    if not recovery or not shot or shot.type != 'shot' or shot.outcome != 'goal':
        return None
    if (recovery.type != 'recovery' or not shot.possession_id
            or recovery.match_id != shot.match_id or recovery.period != shot.period
            or recovery.team_id != shot.team_id or recovery.possession_id != shot.possession_id
            or recovery.sequence >= shot.sequence
            or not 0 <= shot.match_second - recovery.match_second <= 30):
        return None
    for goal in events:
        if (goal.type != 'goal' or goal.related_event_id != shot.event_id
                or goal.match_id != shot.match_id or goal.period != shot.period
                or goal.team_id != shot.team_id or goal.player_id != shot.player_id
                or goal.possession_id != shot.possession_id or goal.sequence <= shot.sequence
                or not 0 <= goal.match_second - shot.match_second <= 10):
            continue
        path = [event for event in events if recovery.sequence <= event.sequence <= goal.sequence]
        if any(event.match_id != shot.match_id or event.period != shot.period
               or event.team_id != shot.team_id or event.possession_id != shot.possession_id for event in path):
            continue
        transition = next((row for row in transitions if row['sequence'] == goal.sequence), None)
        if transition is None:
            continue
        return {'version':'recovery-goal-v1', 'goal_event_id':goal.event_id,
                'goal_sequence':goal.sequence, 'goal_second':goal.match_second,
                'goal_clock':f'{goal.match_second//60}:{goal.match_second%60:02d}',
                'shot_clock':f'{shot.match_second//60}:{shot.match_second%60:02d}',
                'recovery_clock':f'{recovery.match_second//60}:{recovery.match_second%60:02d}',
                'recoverer':recovery.player_name or recovery.player_id,
                'scorer':goal.player_name or goal.player_id,
                'team_name':shot.team_name or shot.team_id,
                'score_change':transition['type'], 'score_before':transition['before'],
                'score_after':transition['after'],
                'completed_pass_count':sum(event.type == 'pass' and event.outcome == 'complete' for event in path),
                'completed_passes':[{'player_name':event.player_name or event.player_id,
                                    'recipient_player_name':event.recipient_player_name,
                                    'match_second':event.match_second}
                                   for event in path if event.type=='pass' and event.outcome=='complete'],
                'seconds_before_snapshot':max(event.match_second for event in events)-goal.match_second,
                'evidence_event_ids':[event.event_id for event in path]}
    return None


def creator_chronology(story, events):
    if story.get('kind') != 'player_shot_creation':
        return None
    by_id = {event.event_id: event for event in events}
    metric = story['metric']
    actions = []
    for link in metric['links']:
        before, shot = by_id.get(link['pass_event_id']), by_id.get(link['shot_event_id'])
        if before is None or shot is None:
            continue
        actions.append({
            'pass_event_id': before.event_id, 'shot_event_id': shot.event_id,
            'pass_second': before.match_second, 'shot_second': shot.match_second,
            'pass_clock': f'{before.match_second//60}:{before.match_second%60:02d}',
            'shot_clock': f'{shot.match_second//60}:{shot.match_second%60:02d}',
            'shot_sequence': shot.sequence, 'shot_outcome': shot.outcome,
            'recipient_player_name': shot.player_name or shot.player_id,
        })
    relationships = []
    for goal in events:
        if goal.type != 'goal' or goal.period != metric['period'] or goal.match_id != metric['match_id']:
            continue
        producing = by_id.get(goal.related_event_id)
        verified = (producing is not None and producing.type == 'shot' and producing.outcome == 'goal'
                    and producing.player_id == goal.player_id and producing.team_id == goal.team_id
                    and producing.period == goal.period and producing.match_id == goal.match_id
                    and producing.sequence < goal.sequence
                    and 0 <= goal.match_second-producing.match_second <= 10)
        goal_links = [action for action in actions if verified and action['shot_event_id'] == producing.event_id]
        goal_ids = {action['shot_event_id'] for action in goal_links}
        earlier = [a['shot_event_id'] for a in actions if a['shot_sequence'] < goal.sequence and a['shot_event_id'] not in goal_ids]
        later = [a['shot_event_id'] for a in actions if a['shot_sequence'] > goal.sequence]
        relationships.append({
            'goal_event_id': goal.event_id, 'goal_second': goal.match_second,
            'goal_clock': f'{goal.match_second//60}:{goal.match_second%60:02d}',
            'goal_team_id': goal.team_id, 'scorer': goal.player_name or goal.player_id,
            'goal_attempt_shot_ids': sorted(goal_ids), 'goal_attempt_count': len(goal_links),
            'other_earlier_shot_ids': earlier, 'other_earlier_count': len(earlier),
            'later_shot_ids': later, 'later_count': len(later),
            'whole_pattern_precedes_goal': len(actions) == len(metric['links']) and bool(actions) and not later,
        })
    return {'actions': actions, 'goal_relationships': relationships,
            'missing_link_count': len(metric['links'])-len(actions),
            'meaning': 'repeated_completed_pass_followed_by_shot',
            'does_not_measure': ['vision', 'finishing_quality', 'tactical_causality', 'assists']}
