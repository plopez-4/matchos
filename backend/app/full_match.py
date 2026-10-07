"""Seeded fictional feeds, not reconstructions of any real fixture.

Coordinates use a fixed attacking frame: Home -> 100, Away -> 0 in both halves.
The clock is cumulative playing time; halftime has zero clock duration.
"""
import random

FULL_MATCHES = {
    "united-city-90": {
        "name": "United vs City · synthetic 90-minute derby",
        "description": "Fictional players: United counter against City's longer passing sequences. 90 minutes plus 3 added minutes; not a real match replay.",
        "home": "Manchester United", "away": "Manchester City",
        "styles": {"home": "counter", "away": "possession"},
    },
    "united-hull-90": {
        "name": "United vs Hull · synthetic 90-minute match",
        "description": "Fictional players: United circulate against a deep-defending Hull side. 90 minutes plus 3 added minutes; not a real match replay.",
        "home": "Manchester United", "away": "Hull City",
        "styles": {"home": "possession", "away": "deep-block"},
    },
}

NAMES = {
    "home": ["Alex Vale", "Leo Mercer", "Noah Reed", "Eli Brooks", "Finn Cole", "Oscar Lane", "Theo Hayes", "Max Rowan", "Luca Wells", "Sam Hart", "Ben Gray", "Jamie Moss"],
    "away": ["Adam North", "Hugo Silva", "Nico Stone", "Dan Rivers", "Owen Park", "Milo Shaw", "Luis Bell", "Ryan Frost", "Kai West", "Jules Dean", "Ivan Hill", "Arlo Fox"],
}


def roster(team):
    return [{"player_id": f"{team}-{i}", "name": name,
             "position": "GK" if i == 1 else "DEF" if i <= 5 else "MID" if i <= 8 else "FWD",
             "starter": i <= 11} for i, name in enumerate(NAMES[team], 1)]


def generate_full_match(scenario_id, seed=7, match_id="full-match"):
    """Generate every modeled action with ball-holder/coordinate continuity.

    This is an event simulator, not player tracking or a physics model. Possession
    styles are author settings; they must never be presented as measured tactics.
    """
    config = FULL_MATCHES[scenario_id]
    rng = random.Random(seed)
    events = []
    active = {team: list(range(2, 12)) for team in ("home", "away")}
    possession = 0
    score = {"home": 0, "away": 0}
    subs_done = set()

    def emit(second, period, team, kind, player, x, y, **fields):
        sequence = len(events) + 1
        event = dict(schema_version="1.2", event_id=f"{scenario_id}-v1-{seed}-{sequence}",
                     match_id=match_id, sequence=sequence, period=period,
                     match_second=second, team_id=team, team_name=config[team],
                     player_id=f"{team}-{player}", player_name=NAMES[team][player-1],
                     type=kind, x=round(x, 2), y=round(y, 2), source="synthetic",
                     possession_id=f"{match_id}:p{possession}", **fields)
        events.append(event)
        return event

    for period, start, stop, kickoff_team in ((1, 0, 2700, "home"), (2, 2700, 5580, "away")):
        t, team, x, y = start, kickoff_team, 50.0, 50.0
        restart = "kickoff"
        holder = rng.choice(active[team])
        while t < stop:
            # A substitution takes place at a possession boundary. The outgoing
            # player cannot be selected again, including as a pass recipient.
            if period == 2 and t >= 3900 and team not in subs_done:
                emit(t, period, team, "substitution", 8, x, y,
                     recipient_player_id=f"{team}-12", recipient_player_name=NAMES[team][11])
                active[team].remove(8)
                active[team].append(12)
                subs_done.add(team)
                if holder == 8:
                    holder = 12
            possession += 1
            emit(t, period, team, restart, holder, x, y)
            style = config["styles"][team]
            passes = rng.randint(9, 17) if style == "possession" else rng.randint(2, 5)
            failure = False
            for _ in range(passes):
                if t + 8 >= stop:
                    break
                t += rng.randint(3, 6)
                recipient = rng.choice([p for p in active[team] if p != holder])
                forward = rng.uniform(20, 35) if style == "deep-block" else rng.uniform(15, 28) if style == "counter" else rng.uniform(4, 12)
                if style == "possession" and rng.random() < .35:
                    forward = -rng.uniform(3, 12)
                direction = 1 if team == "home" else -1
                end_x = round(max(5, min(95, x + direction * forward)), 2)
                end_y = round(max(5, min(95, y + rng.uniform(-18, 18))), 2)
                failure = rng.random() < (.055 if style == "possession" else .13)
                emit(t, period, team, "pass", holder, x, y, end_x=end_x, end_y=end_y,
                     outcome="intercepted" if failure else "complete",
                     recipient_player_id=f"{team}-{recipient}",
                     recipient_player_name=NAMES[team][recipient-1])
                x, y = end_x, end_y
                if failure:
                    break
                holder = recipient
            attacking_x = x if team == "home" else 100-x
            next_team = "away" if team == "home" else "home"
            restart = "recovery"
            next_holder = rng.choice(active[next_team])
            if not failure and attacking_x >= 76 and t + 8 < stop and rng.random() < .42:
                t += 3
                outcome = rng.choices(["saved", "blocked", "missed", "goal"], [50, 23, 24, 3])[0]
                if score[team] >= 3 and outcome == "goal":
                    outcome = "saved"
                goal_x = 100 if team == "home" else 0
                # Blocked shots stay at the block location. Saved shots finish
                # with the opposing keeper; misses restart from a goal kick.
                target_x = x if outcome == "blocked" else goal_x
                shot = emit(t, period, team, "shot", holder, x, y,
                            end_x=target_x, end_y=50, outcome=outcome)
                x, y = target_x, 50
                if outcome == "goal":
                    t += 1
                    emit(t, period, team, "goal", holder, x, y, outcome="goal",
                         related_event_id=shot["event_id"])
                    score[team] += 1
                    restart, x, y = "kickoff", 50.0, 50.0
                elif outcome in ("saved", "missed"):
                    next_holder = 1
            team, holder = next_team, next_holder
            t = min(stop, t + rng.randint(4, 8))
        emit(stop, period, team, "half_end" if period == 1 else "match_end", holder, x, y)
    return events


def full_match_catalog():
    return [dict(id=sid, name=config["name"], description=config["description"],
                 event_count=len(generate_full_match(sid)), duration_seconds=5580,
                 scenario_version="full-match-v1", data_origin="synthetic",
                 teams={team: {"name": config[team], "players": roster(team),
                               "scenario_style": config["styles"][team]}
                        for team in ("home", "away")})
            for sid, config in FULL_MATCHES.items()]
