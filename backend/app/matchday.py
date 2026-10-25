"""Authored synthetic matchday and an observed-events-only Radar baseline.

No real fixtures, standings, video, learned probability, or future-event inputs.
"""
from app.models import MatchEvent
from app.rosters import ROSTER_DATA, player_fields, player_name_for, club_for_name, player_for_slot
import random
import json
from importlib.resources import files
from hashlib import sha256

VERSION = "match-radar-v4-nine-matches"
DURATION = 5580
TICK_SECONDS = 30
PROFILES = [
    {"role": "featured", "home": "Manchester United", "away": "Manchester City",
     "activity_windows": [(900, 1200)],
     "creative_spells": {"home": 7, "away": 7},
     "finishing_spells": {"home": 9, "away": 10},
     "description": "A prominent fixture with an early busy spell.",
     "shots": {300:"home", 600:"away", 900:"home", 930:"away", 990:"home", 1050:"away", 1110:"home", 1170:"away", 2400:"away", 4800:"home"},
     "goals": {900, 2400, 4800}},
    {"role": "comeback", "home": "Crystal Palace", "away": "Newcastle United",
     "activity_windows": [(4200, 4800)],
     "description": "An overlooked fixture; discover its story as events arrive.",
     "shots": {900:"away", 3600:"home", 3960:"away", 4200:"home", 4230:"away", 4290:"home", 4350:"away", 4410:"home", 4470:"away", 4500:"home", 4560:"away", 4620:"home", 4680:"away", 4740:"home", 4770:"away"},
     "goals": {900, 3600, 3960, 4500}},
    {"role": "quiet", "home": "Brighton", "away": "Fulham",
     "description": "A restrained fixture that tests when Radar should stay quiet.",
     "shots": {1200:"home", 3300:"away"}, "goals": set()},
]


DEMO_FIXTURES = json.loads(files('app').joinpath('data/demo_fixtures.json').read_text(encoding='utf-8'))
for profile in PROFILES:
    metadata = next(item for item in DEMO_FIXTURES if item['role'] == profile['role'])
    profile.update({key: metadata[key] for key in ('home', 'away', 'description')})

VARIANTS = json.loads(files('app').joinpath('data/match_variants.json').read_text(encoding='utf-8'))


def selected_variant(match_id):
    """Independent uniform-style selection from a random matchday UUID; stable on reopen."""
    if 'red-card' in match_id or 'red_card' in match_id:
        return 3
    return int.from_bytes(sha256(match_id.encode()).digest()[:8], 'big') % len(VARIANTS['featured'])


def versioned_profile(profile, variant):
    if variant not in range(len(VARIANTS[profile['role']])):
        raise ValueError('Unknown match version')
    config = VARIANTS[profile['role']][variant]
    return {**profile, **config, 'shots': {int(t):side for t,side in config['shots'].items()},
            'goals': set(config['goals']), 'varied_routes': True,
            'red_card': config.get('red_card')}


def library_fixture(profile, match_id, variant):
    config = versioned_profile(profile, variant)
    return fixture(config, match_id, seed=config['seed'])


def fixture(profile, match_id, seed=None):
    """Sparse 93-minute authored possessions; not a complete tracking feed."""
    result = []
    rng = random.Random(seed if seed is not None else int.from_bytes(sha256(match_id.encode()).digest()[:8], 'big'))
    clubs = {team: club_for_name(profile[team]) for team in ('home', 'away')}
    active = {team: list(clubs[team]['demo_lineup']) for team in clubs}
    if any(len(set(lineup)) != 11 for lineup in active.values()):
        raise ValueError('Synthetic fixtures require eleven distinct starting players per side')
    benches = {team: list(clubs[team].get('demo_bench', [])) for team in clubs}
    replacements = {team: 0 for team in clubs}

    def choose(team, excluded, roles=()):
        pool = [actor for actor in active[team] if actor not in excluded]
        preferred = [actor for actor in pool if player_for_slot(profile[team], actor)['position'] in roles]
        return rng.choice(preferred or pool)
    x, y, previous_goal, kickoff_team = 50, 50, True, "home"
    for slot in range(0, DURATION, TICK_SECONDS):
        period = 1 if slot < 2700 else 2
        team = profile["shots"].get(slot, "home" if slot//30 % 2 == 0 else "away")
        if previous_goal:
            team = kickoff_team
        else:
            busy_spell = any(start <= slot < stop for start, stop in profile.get('activity_windows', []))
            # A sparse authored feed starts each new possession at its recorded
            # recovery location, rather than recycling the previous shot's goal line.
            x = (72 if team == 'home' else 28) if busy_spell else (
                35 + slot//30 % 3 * 4 if team == 'home' else 65 - slot//30 % 3 * 4)
            y = 25 + slot//30 % 5 * 12
        direction = 1 if team == "home" else -1
        possession = f"{match_id}:p{slot//30+1}"

        def emit(second, kind, player, event_team=None, **fields):
            t = event_team or team
            sequence = len(result)+1
            raw = dict(schema_version="1.2", event_id=f"{match_id}-e{sequence}",
                       match_id=match_id, sequence=sequence, period=period,
                       match_second=second, team_id=t, team_name=profile[t],
                       player_id=f"{t}-{player}", **player_fields(profile[t], player),
                       roster_version=ROSTER_DATA["version"],
                       type=kind, x=x, y=y, possession_id=possession, source="synthetic", **fields)
            result.append(MatchEvent(**raw).model_dump())
            return raw["event_id"]

        red_card_cfg = profile.get("red_card")
        if red_card_cfg and slot == red_card_cfg.get("second"):
            card_team = red_card_cfg["team"]
            card_player = red_card_cfg.get("player") or red_card_cfg.get("player_slot")
            if card_player in active[card_team]:
                emit(slot, "red_card", card_player, event_team=card_team)
                active[card_team].remove(card_player)

        if slot == 2700:
            period = 1
            emit(slot, "half_end", 2)
            period, team = 2, "away"
            direction = -1
            x, y, previous_goal = 50, 50, True
        # Bench actors have their own stable identities. Outgoing players never
        # reappear as senders or recipients after their authored substitution.
        used = replacements[team]
        if used < len(benches[team]) and slot >= 3600 + used * 300 and not previous_goal:
            candidate_outgoing = [11, 8, 2, 6, 9][used]
            if candidate_outgoing in active[team]:
                outgoing = candidate_outgoing
            else:
                candidates = [p for p in active[team] if player_for_slot(profile[team], p)['position'] != 'GK']
                outgoing = candidates[0] if candidates else None
            if outgoing:
                incoming = benches[team][used]
                emit(slot, 'substitution', outgoing, recipient_player_id=f'{team}-{incoming}',
                     **player_fields(profile[team], incoming, 'recipient_player'))
                active[team][active[team].index(outgoing)] = incoming
                replacements[team] += 1
        outfield = [actor for actor in active[team] if player_for_slot(profile[team], actor)['position'] != 'GK']
        holder = outfield[(slot//60 + (3 if team == 'away' else 0)) % len(outfield)]
        keepers = [actor for actor in active[team] if player_for_slot(profile[team], actor)['position'] == 'GK']
        if keepers and slot//30 % 13 == 0 and not previous_goal:
            holder = keepers[0]
        middle = choose(team, {holder}, ('MID',))
        final = choose(team, {holder, middle}, ('MID', 'FWD'))
        # Explicit synthetic creator/finisher spells make repeated contributions testable.
        # All other possessions keep varied roster participation; these are not real player claims.
        busy_spell = any(start <= slot < stop for start, stop in profile.get('activity_windows', []))
        creator = profile.get('creative_spells', {}).get(team) if busy_spell else None
        finisher = profile.get('finishing_spells', {}).get(team) if busy_spell else None
        if creator in active[team]:
            if holder == creator:
                holder = choose(team, {creator}, ('MID', 'DEF'))
            middle = choose(team, {holder, creator}, ('MID',))
            final = creator
        # Keep the halftime boundary observable before the second-half kickoff.
        emit(slot+1 if slot == 2700 or replacements[team] > used else slot, "kickoff" if previous_goal else "recovery", holder)
        previous_goal = False
        # Two to four linked passes per possession, including safe circulation.
        route = [holder, middle]
        for _ in range(rng.randrange(3) if profile.get('varied_routes') else 0):
            route.append(choose(team, {route[-1], final}, ('DEF', 'MID')))
        route.append(final)
        for pass_index, (sender, recipient) in enumerate(zip(route, route[1:])):
            # Routine circulation is not automatically progressive. Authored busy
            # spells have longer forward passes; quiet fixtures retain shorter moves.
            busy_spell = any(start <= slot < stop for start, stop in profile.get('activity_windows', []))
            gain = ((rng.choice((15, 18)) if busy_spell else rng.choice((-5, 3, 6, 8)))
                    if profile.get('varied_routes') else
                    ((15 + slot//30 % 2 * 3) if busy_spell else (6 + slot//30 % 3)))
            end_x = max(5, min(95, x+direction*gain))
            end_y = max(10, min(90, y + (rng.choice((-12, -8, 5, 10)) if profile.get('varied_routes')
                                       else (8 if slot//30 % 2 else -8))))
            intercepted = pass_index == len(route)-2 and slot//30 % 7 == 3 and slot not in profile['shots']
            emit(slot+(2+pass_index*2 if profile.get('varied_routes') else 3+pass_index*3), "pass", sender,
                 end_x=end_x, end_y=end_y, outcome="intercepted" if intercepted else "complete",
                 recipient_player_id=f"{team}-{recipient}",
                 **player_fields(profile[team], recipient, "recipient_player"))
            x, y = end_x, end_y
        if slot in profile["shots"]:
            # An authored attacking sequence brings the same holder forward.
            attack_x = 82 if team == "home" else 18
            shooter = finisher if finisher in active[team] and finisher != final else choose(team, {final}, ('FWD',))
            emit(slot+(9 if profile.get('varied_routes') else 8), "pass", final, end_x=attack_x, end_y=y, outcome="complete",
                 recipient_player_id=f"{team}-{shooter}", **player_fields(profile[team], shooter, "recipient_player"))
            x = attack_x
            goal = slot in profile["goals"]
            goal_x = 100 if team == "home" else 0
            shot_id = emit(slot+10, "shot", shooter, end_x=goal_x, end_y=50,
                           outcome="goal" if goal else "saved")
            x, y = goal_x, 50
            if goal:
                emit(slot+11, "goal", shooter, outcome="goal", related_event_id=shot_id)
                x, y, previous_goal = 50, 50, True
                kickoff_team = "away" if team == "home" else "home"
    # A marker advances the observed clock even when no shot is recorded.
    emit(DURATION, "match_end", active[team][0])
    return result


def pulse(events, now):
    """Windows are (start, end]; all input must already have been ingested."""
    events = sorted((e for e in events if e.match_second <= now), key=lambda e:e.sequence)
    current = [e for e in events if max(-1, now-300) < e.match_second <= now and e.type == "shot"]
    previous = [e for e in events if max(-1, now-600) < e.match_second <= now-300 and e.type == "shot"]
    goals = [e for e in events if e.type == "goal" and e.match_second <= now]
    red_cards = [e for e in events if e.type == "red_card" and e.match_second <= now]
    recent_red_cards = [e for e in red_cards if now-180 < e.match_second <= now]
    score = {team: sum(e.team_id == team for e in goals) for team in ("home", "away")}
    shots = {team: sum(e.team_id == team for e in current) for team in ("home", "away")}
    card_counts = {team: sum(e.team_id == team for e in red_cards) for team in ("home", "away")}
    close = abs(score["home"]-score["away"]) <= 1
    two_way = min(shots.values()) >= 1 and len(current) >= 4
    increasing = len(current) >= len(previous)+2
    late = now >= 4200
    recent_goals = [e for e in goals if now-180 < e.match_second]
    components = {"close_score":25 if close else 0,
                  "two_way_shots":30 if two_way else 0,
                  "rising_shot_activity":20 if increasing else 0,
                  "late_close_match":15 if close and late else 0,
                  "recent_goal":10 if close and recent_goals else 0,
                  "recent_red_card":35 if recent_red_cards else 0}
    rating = sum(components.values())
    why_now = watch_reason(events, now, score, current, previous, close and two_way and rating >= 65, recent_red_cards=recent_red_cards)
    eligible = why_now is not None
    evidence = {e.event_id:e for e in current+previous+goals+red_cards}
    return {"score":score, "shots_last_five":shots, "shots_previous_five":len(previous),
            "red_cards":card_counts,
            "rating":rating, "components":components, "eligible":eligible, "why_now":why_now,
            "reason": f'{shots["home"]} home and {shots["away"]} away shots in the last five minutes; {len(previous)} total in the previous five.',
            "evidence_event_ids":list(evidence),
            "evidence_events":[e.model_dump() for e in evidence.values()],
            "last_shot_second":max((e.match_second for e in current),default=-1),
            "window": {"start_exclusive":max(-1,now-300),"end_inclusive":now},
            "suppression_reason": None if eligible else "finished" if now >= DURATION else "not_enough_recent_two_way_activity" if not two_way else "not_a_close_contest" if not close else "below_threshold"}


def watch_reason(events, now, score, current, previous, activity_eligible, recent_red_cards=None):
    """A short discovery reason; eligibility and wording use observed facts only."""
    if now >= DURATION or (events and events[-1].type in ("half_end", "match_end")):
        return None
    names = {team:next((e.team_name for e in events if e.team_id == team and e.team_name),
                       "Home" if team == "home" else "Away") for team in ("home", "away")}
    goals = [e for e in events if e.type == "goal"]
    running = {"home":0, "away":0}
    leaders = set()
    trigger = None
    for goal in goals:
        running[goal.team_id] += 1
        other = "away" if goal.team_id == "home" else "home"
        kind = "equalizer" if running["home"] == running["away"] else (
            "lead_reversal" if running[goal.team_id] == running[other]+1 and other in leaders else None)
        if running["home"] != running["away"]:
            leaders.add("home" if running["home"] > running["away"] else "away")
        # Only the latest goal can describe the current score change.
        trigger = (kind, goal) if kind and now-180 < goal.match_second <= now else None
    scoreline = f'{names["home"]} {score["home"]}–{score["away"]} {names["away"]}'
    card_event = recent_red_cards[-1] if recent_red_cards else None
    card_is_newer = (card_event is not None and (trigger is None or card_event.match_second >= trigger[1].match_second))

    if trigger and not card_is_newer:
        kind, goal = trigger
        headline = (f'{names[goal.team_id]} have just drawn level.' if kind == "equalizer"
                    else f'{names[goal.team_id]} have turned the lead around.')
        reason = f'{scoreline}. '
        if len(goals) >= 2 and kind == "equalizer":
            gap = goal.match_second-goals[-2].match_second
            minutes, seconds = divmod(gap, 60)
            reason += f'The equalizer came {minutes}:{seconds:02d} after the previous goal. '
        expires = goal.match_second+180
        ids = [e.event_id for e in goals]
    elif card_event:
        kind = "red_card"
        player_name = card_event.player_name or f"Player {card_event.player_id}"
        team_name = names[card_event.team_id]
        headline = f'{team_name} down to 10 men after {player_name} was sent off.'
        c_min, c_sec = divmod(card_event.match_second, 60)
        reason = f'{scoreline}. {player_name} was shown a red card at {c_min}:{c_sec:02d}. '
        expires = card_event.match_second+180
        ids = [e.event_id for e in goals] + [card_event.event_id]
    elif activity_eligible:
        kind = "shot_activity"
        headline = 'Both sides are recording shots in a close match.'
        reason = f'{scoreline}. '
        expires = min(e.match_second+300 for e in current)
        ids = [e.event_id for e in goals+current+previous]
    else:
        return None
    if current:
        reason += f'{len(current)} shots in the last five minutes'
        if kind == "shot_activity":
            reason += f', compared with {len(previous)} in the five before that'
        reason += '. '
    if now < 5400:
        minutes, seconds = divmod(5400-now, 60)
        reason += f'{minutes}:{seconds:02d} until ninety, plus added time.'
    else:
        reason += 'The match is in added time.'
    result_dict = {"trigger":kind, "headline":headline, "text":reason,
                   "observed_second":now, "expires_at_second":min(expires, DURATION),
                   "evidence_event_ids":list(dict.fromkeys(ids))}
    if card_event and kind == "red_card":
        result_dict["card_event_id"] = card_event.event_id
    return result_dict


def rank(entries):
    eligible = [item for item in entries if item["pulse"]["eligible"]]
    return sorted(eligible, key=lambda item:(-item["pulse"]["rating"], -item["pulse"]["last_shot_second"], item["match_id"]))
