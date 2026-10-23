"""One verified editorial plan shared by recap prose, evidence and narration."""
from app.explanations import strongest_change
from app.narration_text import recap_parts
from app.player_impact import player_story_text, KINDS as PLAYER_KINDS


def change_text(story, names, audience, language):
    if story['kind'] in PLAYER_KINDS:
        return player_story_text(story, language, audience, names)
    es = language == 'es'
    metric = story['metric']
    name = names[metric['team_id']]
    kind = story['kind']
    if kind == 'shot_activity':
        current, previous = metric['current'], metric['previous']
        start, end = current['start_second']//60, current['end_second']//60
        count, baseline = current['shot_count'], previous['shot_count']
        text = (f'Entre los minutos {start} y {end}, {name} registró {count} remates, frente a {baseline} en los cinco minutos anteriores.' if es else
                f'Between minutes {start} and {end}, {name} recorded {count} shots, compared with {baseline} in the preceding five minutes.')
        if audience == 'advanced':
            text += (' El aumento cumple el umbral de al menos tres remates y dos más que antes; no mide su calidad.' if es else
                     ' The rise meets the threshold of at least three attempts and two more than before; it does not measure chance quality.')
        return text
    if kind == 'recovery_shot':
        elapsed = metric['elapsed_seconds']
        second = story['match_second']
        clock = f'{second//60}:{second%60:02d}'
        link = metric.get('goal_link')
        if link:
            effect = {'equalization':('equalizer','empate'),
                      'lead_acquisition':('go-ahead goal','gol que puso a su equipo por delante'),
                      'lead_reversal':('go-ahead goal','gol que puso a su equipo por delante'),
                      'lead_extension':('goal that extended the lead','gol que amplió la ventaja'),
                      'deficit_reduction':('goal that reduced the deficit','gol que recortó la desventaja')}[link['score_change']]
            text = (f"{link['recoverer']} recuperó el balón y, {elapsed} segundos después, {link['scorer']} remató a los {clock}: ese remate terminó en el {effect[1]} registrado a los {link['goal_clock']}." if es else
                    f"{link['recoverer']} recovered the ball and, {elapsed} seconds later, {link['scorer']} shot at {clock}: that shot produced the {effect[0]} recorded at {link['goal_clock']}.")
            if audience == 'advanced':
                text += (' La secuencia respalda este gol, no una conclusión sobre dominio o calidad del remate.' if es else
                         ' This sequence supports that goal, not a claim of dominance or shot quality.')
            return text
        text = (f'A los {clock}, {name} registró un remate {elapsed} segundos después de recuperar el balón en la misma posesión.' if es else
                f'At {clock}, {name} recorded a shot {elapsed} seconds after recovering the ball in the same possession.')
        if audience == 'advanced':
            text += (' Cumple la regla de transición de 30 segundos; la asociación no demuestra causalidad.' if es else
                     ' This meets the 30-second transition rule; the association does not establish causality.')
        return text
    start, end = metric['start_second']//60, metric['end_second']//60
    if kind == 'high_recovery':
        count = metric['recovery_count']
        text = (f'Entre los minutos {start} y {end}, {name} recuperó el balón {count} veces en el tercio rival.' if es else
                f'Between minutes {start} and {end}, {name} recovered the ball {count} times in the attacking third.')
    else:
        count = metric['pass_count']
        text = (f'Entre los minutos {start} y {end}, {name} completó {count} pases que avanzaron al menos 15 unidades del campo cada uno.' if es else
                f'Between minutes {start} and {end}, {name} completed {count} passes advancing at least 15 pitch units each.')
    if audience == 'advanced':
        if kind == 'high_recovery':
            threshold = 'x ≥ 70' if metric['team_id'] == 'home' else 'x ≤ 30'
            text += (f' Umbral: tres recuperaciones en cinco minutos en {threshold}.' if es else
                     f' Threshold: three recoveries in five minutes at {threshold}.')
        text += (' Estos registros no demuestran control ni causalidad táctica.' if es else
                 ' These records do not establish control or tactical causality.')
    return text


def bind(briefing, selected, audience):
    if not briefing:
        return None
    # The selector supplies verified objects; the writer cannot substitute its own patterns.
    change = strongest_change(selected)
    covered = [story for story in selected if story['kind'] == 'goal']
    if change:
        covered.append(change)
    plan = {'version': 'story-plan-v3-linked-goal', 'story_ids': [story['story_id'] for story in covered],
            'stories': covered, 'change_story_id': change['story_id'] if change else None,
            'status': 'change_detected' if change else 'no_qualifying_change' if briefing['comparison_available'] else 'limited_coverage',
            'snapshot': briefing['snapshot']}
    plan['player_story_id'] = change['story_id'] if change and change['kind'] in PLAYER_KINDS else None
    names = briefing['locale_facts']['names']
    linked_goal = change.get('metric', {}).get('goal_link') if change else None
    texts = {}
    for language in ('en', 'es'):
        parts = [text for text, _ in recap_parts(briefing, language)]
        goal_ids = {eid for story in covered if story['kind'] == 'goal' for eid in story['evidence_event_ids']}
        goals = [goal for goal in briefing['locale_facts'].get('goals', []) if goal['event_id'] in goal_ids]
        if goals:
            if briefing['locale_facts']['phase'] == 'playing':
                # The named goals below replace a generic latest-goal sentence.
                if not any(count >= 2 for count in briefing['trajectory']['equalizers'].values()):
                    parts = parts[1:]
            elif briefing['trajectory']['transitions']:
                parts = parts[:1] + parts[2:]
            named_goals = [
                f"{goal['player_name']} marcó para {names[goal['team_id']]} a los {goal['clock']}." if language == 'es' else
                f"{goal['player_name']} scored for {names[goal['team_id']]} at {goal['clock']}."
                for goal in goals if not linked_goal or goal['event_id'] != linked_goal['goal_event_id']]
            parts[1:1] = named_goals
        if (plan['player_story_id'] or linked_goal) and briefing['locale_facts']['phase'] == 'playing':
            # Let the player contribution carry the story instead of appending another team-shot report.
            parts = parts[:-2] + parts[-1:]
        if change:
            text = change_text(change, names, audience, language)
        else:
            text = ('La cobertura registrada es limitada; no se ha establecido un cambio que cumpla las reglas.' if language == 'es' else
                    'Recorded coverage is limited; no qualifying change has been established.') if plan['status'] == 'limited_coverage' else (
                    'No se detectó un cambio que cumpla las reglas en el tramo registrado de tu ausencia.' if language == 'es' else
                    'No qualifying change was detected in the recorded interval you missed.')
        index = max(0, len(parts)-(1 if plan['player_story_id'] or linked_goal else 2)) if briefing['locale_facts']['phase'] == 'playing' else len(parts)
        parts.insert(index, text)
        texts[language] = ' '.join(parts)
    plan['change_text'] = {language: change_text(change, names, audience, language) for language in ('en', 'es')} if change else {}
    briefing.update(story_plan=plan, audience=audience, spoken_recap=texts)
    briefing['evidence_event_ids'] = list(dict.fromkeys(briefing['evidence_event_ids'] +
        [eid for story in covered for eid in story['evidence_event_ids']]))
    return briefing
