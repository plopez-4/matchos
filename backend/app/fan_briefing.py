"""A compact score story, recent action and clock, rendered from observed facts."""
from collections import Counter
from app.intelligence import score_trajectory
from app.historical_context import historical_precedent
from app.narration_text import recap_text


def fan_briefing(events, new_events, *, now=None):
    if not new_events:
        return None
    now = new_events[-1].match_second if now is None else now
    observed = sorted((e for e in events if e.match_second <= now), key=lambda e: e.sequence)
    if not observed:
        return None
    names = {e.team_id: e.team_name for e in observed if e.team_name}
    name = lambda team: names.get(team, team.title())
    clock = lambda second: f'{second//60}:{second%60:02d}'
    trajectory = score_trajectory(observed)
    score = trajectory['score']
    score_ids = trajectory['evidence_event_ids']
    transitions = trajectory['transitions']
    scoreline = f"{name('home')} {score['home']}–{score['away']} {name('away')}"
    finished = observed[-1].type == 'match_end'
    halftime = observed[-1].type == 'half_end'
    headline = 'The story so far'
    swing = 'No goals have been recorded.'
    if transitions:
        latest = transitions[-1]
        team = latest['team_id']
        other = 'away' if team == 'home' else 'home'
        wording = {'lead_acquisition':'have taken the lead', 'equalization':'have pulled level',
                   'lead_extension':'have extended their lead', 'deficit_reduction':'have pulled a goal back',
                   'lead_reversal':'have turned it around to lead'}
        headline = f'{name(team)} {wording[latest["type"]]}'
        count = trajectory['equalizers'][team]
        frequency = lambda n: 'twice' if n == 2 else f'{n} times'
        if latest['type'] == 'equalization' and count >= 2:
            headline = f'{name(other)} led {frequency(trajectory["lead_acquisitions"][other])}. {name(team)} have answered {frequency(count)}.'
        swing = f'{name(team)} {wording[latest["type"]]} at {clock(latest["match_second"])}.'
        response = latest['rapid_response']
        if response:
            elapsed = response['elapsed_seconds']
            unit = 'minute' if elapsed == 60 else 'minutes'
            delay = f'{elapsed//60} {unit}' if elapsed % 60 == 0 else f'{clock(elapsed)} of match time'
            swing += f' Their goal came {delay} after {name(other)} scored.'
        if not any(e.type == 'goal' and e.match_second <= now for e in new_events):
            swing = 'No new goals since your last check. ' + swing
    current_start, previous_start = max(-1, now-300), max(-1, now-600)
    current = [e for e in observed if current_start < e.match_second <= now and e.type == 'shot']
    previous = [e for e in observed if previous_start < e.match_second <= now-300 and e.type == 'shot']
    counts = Counter(e.team_id for e in current)
    period = 'last five minutes' if now >= 300 else 'opening moments'
    tempo = (f'{len(current)} shots total in the {period}: {counts["home"]} for '
             f'{name("home")}, {counts["away"]} for {name("away")}.') if current else 'No shots recorded in the recent window.'
    comparison_ready = now >= 600 and observed[0].match_second <= now-600
    if comparison_ready:
        tempo += f' Compared with {len(previous)} total in the previous five minutes.'
    else:
        tempo += ' A full two-window comparison is unavailable.'
    timing = f'{clock(5400-now)} until 90 minutes, plus added time.' if now < 5400 else '90 minutes played; added time is being played.'
    if halftime:
        headline, timing = 'Half-time: the story so far', 'The first half has finished.'
    if finished:
        headline, timing = 'The final whistle: here is how it ended', 'The synthetic match has finished.'
    sections = [
        {'title':'The score story', 'text':swing, 'evidence_event_ids':score_ids},
        {'title':'Recent action', 'text':tempo, 'evidence_event_ids':[e.event_id for e in current+previous]},
        {'title':'The clock', 'text':timing, 'evidence_event_ids':[observed[-1].event_id]},
    ]
    briefing = {'headline':headline, 'scoreline':scoreline, 'clock':clock(now), 'sections':sections,
            'snapshot':{'match_id':observed[-1].match_id, 'through_sequence':observed[-1].sequence,
                        'since_sequence':min((e.sequence for e in new_events if e.match_second<=now), default=observed[-1].sequence+1)-1,
                        'match_second':now},
            'historical_precedent':historical_precedent('finished' if finished else 'halftime' if halftime else 'playing', score),
            'locale_facts':{'names':{'home':name('home'),'away':name('away')},
                            'goals':[{'event_id':event.event_id, 'player_name':event.player_name or event.player_id,
                                      'team_id':event.team_id, 'clock':clock(event.match_second)}
                                     for event in observed if event.type == 'goal'],
                            'phase':'finished' if finished else 'halftime' if halftime else 'playing',
                            'shots':{'home':counts['home'],'away':counts['away']},
                            'previous_shots':len(previous), 'has_new_goals':any(e.type == 'goal' and e.match_second <= now for e in new_events)},
            'trajectory':trajectory, 'late_parity':now >= 4200 and not finished and score['home'] == score['away'],
            'window':{'start_exclusive':current_start,'end_inclusive':now},
            'previous_window':{'start_exclusive':previous_start,'end_inclusive':now-300} if now >= 300 else None,
            'comparison_available':comparison_ready, 'rule_version':'fan-briefing-v2',
            'evidence_event_ids':list(dict.fromkeys(eid for section in sections for eid in section['evidence_event_ids']))}

    briefing['spoken_recap'] = {language: recap_text(briefing, language) for language in ('en', 'es')}
    return briefing
