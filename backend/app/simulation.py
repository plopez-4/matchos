"""Shared deterministic synthetic scenario for browser and CLI replays."""
import random

# second, team, action, start x, end x, outcome, possession number
# Home attacks toward x=100; Away attacks toward x=0. Gaps omit routine play.
SCENARIO = [
    (0, 'home', 'kickoff', 50, None, None, 1),
    (20, 'home', 'pass', 50, 65, 'complete', 1),
    (60, 'home', 'pass', 65, 82, 'complete', 1),
    (100, 'home', 'shot', 82, 100, 'saved', 1),
    (101, 'away', 'recovery', 100, None, None, 2),
    (130, 'away', 'pass', 100, 65, 'complete', 2),
    (180, 'away', 'pass', 65, 20, 'complete', 2),
    (210, 'away', 'shot', 20, 0, 'missed', 2),
    (240, 'home', 'recovery', 8, None, None, 3),
    (300, 'home', 'pass', 8, 32, 'complete', 3),
    (310, 'home', 'pass', 32, 80, 'complete', 3),
    (330, 'home', 'shot', 80, 82, 'blocked', 3),
    (331, 'home', 'recovery', 82, None, None, 3),
    (380, 'home', 'pass', 82, 88, 'complete', 3),
    (410, 'home', 'shot', 88, 100, 'saved', 3),
    (430, 'home', 'recovery', 80, None, None, 4),
    (470, 'home', 'pass', 80, 90, 'complete', 4),
    (490, 'home', 'shot', 90, 100, 'missed', 4),
    (540, 'home', 'recovery', 45, None, None, 5),
    (560, 'home', 'pass', 45, 88, 'complete', 5),
    (570, 'home', 'shot', 88, 100, 'goal', 5),
    (571, 'home', 'goal', 100, None, 'goal', 5),
    (580, 'away', 'kickoff', 50, None, None, 6),
    (582, 'away', 'pass', 50, 45, 'complete', 6),
    (585, 'away', 'pass', 45, 35, 'complete', 6),
    (589, 'away', 'pass', 35, 24, 'complete', 6),
    (594, 'away', 'pass', 24, 16, 'complete', 6),
    (599, 'away', 'shot', 16, 0, 'saved', 6),
    (600, 'home', 'recovery', 0, None, None, 7),
    (600, 'home', 'pass', 0, 12, 'complete', 7),
]

def generate(seed=7, count=30, match_id="demo-match"):
    if not 1 <= count <= len(SCENARIO):
        raise ValueError('This scenario supports 1..30 events')
    rng = random.Random(seed)
    # Seed varies fictional player identities, not the known storyline/metrics.
    players = {team: rng.sample(range(2, 12), 10) for team in ('home', 'away')}
    for sequence, row in enumerate(SCENARIO[:count], start=1):
        second, team, kind, x, end_x, outcome, possession = row
        event = dict(schema_version="1.1", event_id=f"scenario-v1-{seed}-{sequence}",
                     match_id=match_id, sequence=sequence, period=1, match_second=second,
                     team_id=team, player_id=f"{team}-{players[team][sequence % 10]}",
                     type=kind, x=x, y=50, source="synthetic",
                     possession_id=f"{match_id}:p{possession}")
        if end_x is not None:
            event.update(end_x=end_x, end_y=50)
        if outcome is not None:
            event['outcome'] = outcome
        if kind == 'goal':
            event['related_event_id'] = f"scenario-v1-{seed}-{sequence - 1}"
            event['player_id'] = f"{team}-{players[team][(sequence - 1) % 10]}"
        yield event
