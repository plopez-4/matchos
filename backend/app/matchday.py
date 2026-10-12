"""Authored synthetic matchday and an observed-events-only Radar baseline.

No real fixtures, standings, video, learned probability, or future-event inputs.
"""
from app.models import MatchEvent

VERSION = "match-radar-v1"
DURATION = 5580
TICK_SECONDS = 30
PROFILES = [
    {"role": "featured", "home": "Manchester United", "away": "Manchester City",
     "description": "A prominent fixture with an early busy spell.",
     "shots": {300:"home", 600:"away", 900:"home", 930:"away", 990:"home", 1050:"away", 1110:"home", 1170:"away", 2400:"away", 4800:"home"},
     "goals": {900, 2400, 4800}},
    {"role": "comeback", "home": "Crystal Palace", "away": "Newcastle United",
     "description": "An overlooked fixture; discover its story as events arrive.",
     "shots": {900:"away", 3600:"home", 3960:"away", 4200:"home", 4230:"away", 4290:"home", 4350:"away", 4410:"home", 4470:"away", 4500:"home", 4560:"away", 4620:"home", 4680:"away", 4740:"home", 4770:"away"},
     "goals": {900, 3600, 3960, 4500}},
    {"role": "quiet", "home": "Brighton", "away": "Fulham",
     "description": "A restrained fixture that tests when Radar should stay quiet.",
     "shots": {1200:"home", 3300:"away"}, "goals": set()},
]


def fixture(profile, match_id):
    """Sparse 93-minute authored possessions; not a complete tracking feed."""
    result = []
    x, y, previous_goal, kickoff_team = 50, 50, True, "home"
    for slot in range(0, DURATION, TICK_SECONDS):
        period = 1 if slot < 2700 else 2
        team = profile["shots"].get(slot, "home" if slot//30 % 2 == 0 else "away")
        if previous_goal:
            team = kickoff_team
        direction = 1 if team == "home" else -1
        possession = f"{match_id}:p{slot//30+1}"

        def emit(second, kind, player, **fields):
            sequence = len(result)+1
            raw = dict(schema_version="1.2", event_id=f"{match_id}-e{sequence}",
                       match_id=match_id, sequence=sequence, period=period,
                       match_second=second, team_id=team, team_name=profile[team],
                       player_id=f"{team}-{player}", player_name=f"{profile[team]} Player {player}",
                       type=kind, x=x, y=y, possession_id=possession, source="synthetic", **fields)
            result.append(MatchEvent(**raw).model_dump())
            return raw["event_id"]

        if slot == 2700:
            period = 1
            emit(slot, "half_end", 2)
            period, team = 2, "away"
            direction = -1
            x, y, previous_goal = 50, 50, True
        emit(slot, "kickoff" if previous_goal else "recovery", 2)
        previous_goal = False
        for sender, recipient in ((2, 7), (7, 9)):
            end_x = max(5, min(95, x+direction*15))
            emit(slot+3 if sender == 2 else slot+6, "pass", sender,
                 end_x=end_x, end_y=y, outcome="complete",
                 recipient_player_id=f"{team}-{recipient}",
                 recipient_player_name=f"{profile[team]} Player {recipient}")
            x = end_x
        if slot in profile["shots"]:
            # An authored attacking sequence brings the same holder forward.
            attack_x = 82 if team == "home" else 18
            emit(slot+8, "pass", 9, end_x=attack_x, end_y=y, outcome="complete",
                 recipient_player_id=f"{team}-10", recipient_player_name=f"{profile[team]} Player 10")
            x = attack_x
            goal = slot in profile["goals"]
            goal_x = 100 if team == "home" else 0
            shot_id = emit(slot+10, "shot", 10, end_x=goal_x, end_y=50,
                           outcome="goal" if goal else "saved")
            x, y = goal_x, 50
            if goal:
                emit(slot+11, "goal", 10, outcome="goal", related_event_id=shot_id)
                x, y, previous_goal = 50, 50, True
                kickoff_team = "away" if team == "home" else "home"
    # A marker advances the observed clock even when no shot is recorded.
    emit(DURATION, "match_end", 2)
    return result


def pulse(events, now):
    """Windows are (start, end]; all input must already have been ingested."""
    current = [e for e in events if max(-1, now-300) < e.match_second <= now and e.type == "shot"]
    previous = [e for e in events if max(-1, now-600) < e.match_second <= now-300 and e.type == "shot"]
    goals = [e for e in events if e.type == "goal" and e.match_second <= now]
    score = {team: sum(e.team_id == team for e in goals) for team in ("home", "away")}
    shots = {team: sum(e.team_id == team for e in current) for team in ("home", "away")}
    close = abs(score["home"]-score["away"]) <= 1
    two_way = min(shots.values()) >= 1 and len(current) >= 4
    increasing = len(current) >= len(previous)+2
    late = now >= 4200
    recent_goals = [e for e in goals if now-180 < e.match_second]
    components = {"close_score":25 if close else 0,
                  "two_way_shots":30 if two_way else 0,
                  "rising_shot_activity":20 if increasing else 0,
                  "late_close_match":15 if close and late else 0,
                  "recent_goal":10 if close and recent_goals else 0}
    rating = sum(components.values())
    eligible = now < DURATION and close and two_way and rating >= 65
    evidence = {e.event_id:e for e in current+previous+goals}
    return {"score":score, "shots_last_five":shots, "shots_previous_five":len(previous),
            "rating":rating, "components":components, "eligible":eligible,
            "reason": f'{shots["home"]} home and {shots["away"]} away shots in the last five minutes; {len(previous)} total in the previous five.',
            "evidence_event_ids":list(evidence),
            "evidence_events":[e.model_dump() for e in evidence.values()],
            "last_shot_second":max((e.match_second for e in current),default=-1),
            "window": {"start_exclusive":max(-1,now-300),"end_inclusive":now},
            "suppression_reason": None if eligible else "finished" if now >= DURATION else "not_enough_recent_two_way_activity" if not two_way else "not_a_close_contest" if not close else "below_threshold"}


def rank(entries):
    eligible = [item for item in entries if item["pulse"]["eligible"]]
    return sorted(eligible, key=lambda item:(-item["pulse"]["rating"], -item["pulse"]["last_shot_second"], item["match_id"]))
