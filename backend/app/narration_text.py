"""Short bilingual recaps from observed facts; no generated opinions or predictions."""


def spoken_clock(second, language):
    minute, remainder = divmod(second, 60)
    if language == 'es':
        return f"{minute} {'minuto' if minute == 1 else 'minutos'}" + (
            f" y {remainder} {'segundo' if remainder == 1 else 'segundos'}" if remainder else '')
    return f"{minute} {'minute' if minute == 1 else 'minutes'}" + (
        f" and {remainder} {'second' if remainder == 1 else 'seconds'}" if remainder else '')


def recap_parts(briefing, language):
    """Return (text, energized) paragraphs. Only a newly observed recent goal gets energy."""
    facts, trajectory = briefing['locale_facts'], briefing['trajectory']
    names, score = facts['names'], trajectory['score']
    now, phase = briefing['snapshot']['match_second'], facts['phase']
    latest = trajectory['transitions'][-1] if trajectory['transitions'] else None
    spanish = language == 'es'
    recent = bool(latest and facts['has_new_goals'] and phase == 'playing'
                  and 0 <= now - latest['match_second'] <= 180)
    parts = []
    if score['home'] == score['away']:
        named_score = (f"{names['home']} y {names['away']} están empatados {score['home']} a {score['away']}." if spanish else
                       f"{names['home']} and {names['away']} are level at {score['home']} all.")
    else:
        leader = 'home' if score['home'] > score['away'] else 'away'
        trailing = 'away' if leader == 'home' else 'home'
        named_score = (f"{names[leader]} va por delante de {names[trailing]}, {score[leader]} a {score[trailing]}." if spanish else
                       f"{names[leader]} lead {names[trailing]} {score[leader]} to {score[trailing]}.")
    short_score = (f"Así quedan empatados {score['home']} a {score['away']}." if spanish else
                   f"That leaves them level at {score['home']} all.")

    def turning_point():
        team = latest['team_id']
        other = 'away' if team == 'home' else 'home'
        wording = {
            'lead_acquisition': ('took the lead', 'se adelantó'),
            'equalization': ('pulled level', 'empató'),
            'lead_extension': ('extended their lead', 'amplió su ventaja'),
            'deficit_reduction': ('pulled a goal back', 'recortó la diferencia'),
            'lead_reversal': ('turned it around to lead', 'remontó para ponerse por delante'),
        }
        count = trajectory['equalizers'][team]
        if latest['type'] == 'equalization' and count >= 2:
            frequency = lambda n: ('dos veces' if n == 2 else f'{n} veces') if spanish else ('twice' if n == 2 else f'{n} times')
            leads = frequency(trajectory['lead_acquisitions'][other])
            answers = frequency(count)
            return (f"{names[other]} se adelantó {leads}, pero {names[team]} respondió {answers}." if spanish
                    else f"{names[other]} led {leads}, but {names[team]} have answered {answers}.")
        return f"{names[team]} {wording[latest['type']][int(spanish)]}."

    if phase in ('halftime', 'finished'):
        label = ('Descanso.' if phase == 'halftime' else 'Final del partido.') if spanish else (
            'Half-time.' if phase == 'halftime' else 'Full-time.')
        if phase == 'finished' and score['home'] != score['away']:
            named_score = (f"{names[leader]} ganó {score[leader]} a {score[trailing]} a {names[trailing]}." if spanish else
                           f"{names[leader]} beat {names[trailing]} {score[leader]} to {score[trailing]}.")
        elif phase == 'finished':
            named_score = (f"{names['home']} y {names['away']} terminaron empatados {score['home']} a {score['away']}." if spanish else
                           f"{names['home']} and {names['away']} finished level at {score['home']} all.")
        parts.append((f'{label} {named_score}', False))
        if latest:
            parts.append((turning_point(), False))
        else:
            parts.append(('Sin goles registrados.' if spanish else 'No goals recorded.', False))
    elif latest and facts['has_new_goals']:
        prefix = '' if recent else ('El último gol: ' if spanish else 'The last goal: ')
        repeated = latest['type'] == 'equalization' and trajectory['equalizers'][latest['team_id']] >= 2
        parts.extend([(prefix + turning_point(), recent), (short_score if repeated else named_score, False)])
    else:
        parts.append((named_score, False))
        parts.append((('No hay nuevos goles desde tu última consulta.' if spanish else
                       'No new goals since your last check.') if latest else
                      ('Sigue sin goles.' if spanish else 'Still goalless.'), False))

    # A response interval is useful context for a changed score, not a recurring alert.
    has_response = latest and latest['rapid_response'] and (facts['has_new_goals'] or phase in ('halftime', 'finished'))
    if has_response:
        delay = spoken_clock(latest['rapid_response']['elapsed_seconds'], language)
        parts.append((f'El último gol llegó {delay} después del anterior.' if spanish else
                      f'The latest goal came {delay} after the previous one.', recent))

    if phase == 'playing':
        total = facts['shots']['home'] + facts['shots']['away']
        if now < 300:
            tempo = (f'{total} remates registrados en estos primeros instantes.' if spanish else
                     f'{total} shots recorded in these opening moments.')
        elif total == 0:
            tempo = ('Sin remates registrados en los últimos cinco minutos.' if spanish else
                     'No shots recorded in the last five minutes.')
        else:
            tempo = (f"En los últimos cinco minutos se {'registró' if total == 1 else 'registraron'} {total} {'remate' if total == 1 else 'remates'}." if spanish else
                     f"Across the last five minutes, the teams have recorded {total} {'shot' if total == 1 else 'shots'}.")
            if not has_response and briefing['comparison_available'] and total > facts['previous_shots']:
                tempo = tempo[:-1] + (f", frente a {facts['previous_shots']} en los cinco anteriores." if spanish else
                                     f", up from {facts['previous_shots']} in the previous five.")
        parts.append((tempo, False))
        if now < 5400:
            remaining = spoken_clock(5400 - now, language)
            clock = (f'Faltan {remaining} para los noventa, más el añadido.' if spanish else
                     f'There are {remaining} until ninety, plus added time.')
        else:
            clock = 'Se juega el tiempo añadido.' if spanish else 'Added time is being played.'
        parts.append((clock, False))
    return parts


def recap_text(briefing, language):
    return ' '.join(text for text, _ in recap_parts(briefing, language))
