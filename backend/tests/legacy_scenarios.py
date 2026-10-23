"""Small synthetic regression fixtures. Never imported by the running application."""
import random

# second, team, action, start x, end x, outcome, possession number
# Home attacks toward x=100; Away attacks toward x=0. Gaps omit routine play.

# Legacy 30-event fixture
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

# Pressure builds: repeated Home attacking sequences, progressive passes, high recoveries, increasing shots, then goal.
PRESSURE_BUILDS_SCENARIO = [
    (0, 'home', 'kickoff', 50, None, None, 1),
    (25, 'home', 'pass', 50, 68, 'complete', 1),
    (55, 'home', 'pass', 68, 84, 'complete', 1),
    (90, 'home', 'shot', 84, 100, 'saved', 1),
    (91, 'away', 'recovery', 95, None, None, 2),
    (125, 'away', 'pass', 95, 70, 'complete', 2),
    (165, 'away', 'pass', 70, 30, 'complete', 2),
    (200, 'away', 'shot', 30, 0, 'missed', 2),
    (230, 'home', 'recovery', 10, None, None, 3),
    (265, 'home', 'pass', 10, 35, 'complete', 3),
    (290, 'home', 'pass', 35, 45, 'complete', 3),
    (315, 'home', 'pass', 45, 76, 'complete', 4),
    (330, 'home', 'shot', 76, 100, 'blocked', 4),
    (335, 'home', 'recovery', 78, None, None, 4),
    (355, 'home', 'pass', 78, 85, 'complete', 4),
    (370, 'home', 'shot', 85, 100, 'saved', 4),
    (390, 'away', 'recovery', 98, None, None, 5),
    (405, 'away', 'pass', 98, 80, 'complete', 5),
    (415, 'home', 'recovery', 80, None, None, 6),
    (435, 'home', 'pass', 80, 96, 'complete', 6),
    (450, 'home', 'shot', 96, 100, 'missed', 6),
    (475, 'away', 'recovery', 95, None, None, 7),
    (490, 'away', 'pass', 95, 75, 'complete', 7),
    (505, 'home', 'recovery', 75, None, None, 8),
    (520, 'home', 'pass', 75, 92, 'complete', 8),
    (528, 'home', 'shot', 92, 100, 'goal', 8),
    (529, 'home', 'goal', 100, None, 'goal', 8),
    (540, 'away', 'kickoff', 50, None, None, 9),
    (555, 'away', 'pass', 50, 42, 'complete', 9),
    (570, 'away', 'pass', 42, 32, 'complete', 9),
    (585, 'away', 'shot', 32, 0, 'saved', 9),
    (595, 'home', 'recovery', 5, None, None, 10),
    (600, 'home', 'pass', 5, 25, 'complete', 10),
]

# Comeback: Home scores first; Away responds with high activity and equalizes. Final 1-1.
COMEBACK_SCENARIO = [
    (0, 'home', 'kickoff', 50, None, None, 1),
    (25, 'home', 'pass', 50, 72, 'complete', 1),
    (55, 'home', 'pass', 72, 88, 'complete', 1),
    (85, 'home', 'shot', 88, 100, 'saved', 1),
    (105, 'home', 'recovery', 65, None, None, 2),
    (125, 'home', 'pass', 65, 86, 'complete', 2),
    (145, 'home', 'shot', 86, 100, 'goal', 2),
    (146, 'home', 'goal', 100, None, 'goal', 2),
    (160, 'away', 'kickoff', 50, None, None, 3),
    (185, 'away', 'pass', 50, 38, 'complete', 3),
    (215, 'away', 'pass', 38, 22, 'complete', 3),
    (240, 'away', 'shot', 22, 0, 'missed', 3),
    (270, 'home', 'recovery', 8, None, None, 4),
    (290, 'home', 'pass', 8, 30, 'complete', 4),
    (315, 'away', 'recovery', 55, None, None, 5),
    (330, 'away', 'pass', 55, 28, 'complete', 5),
    (345, 'away', 'shot', 28, 0, 'blocked', 5),
    (355, 'away', 'recovery', 28, None, None, 6),
    (375, 'away', 'pass', 28, 20, 'complete', 6),
    (390, 'away', 'shot', 20, 0, 'saved', 6),
    (415, 'home', 'recovery', 5, None, None, 7),
    (430, 'home', 'pass', 5, 40, 'complete', 7),
    (435, 'away', 'recovery', 26, None, None, 8),
    (455, 'away', 'pass', 26, 10, 'complete', 8),
    (475, 'away', 'shot', 10, 0, 'missed', 8),
    (515, 'home', 'recovery', 8, None, None, 9),
    (525, 'home', 'pass', 8, 25, 'complete', 9),
    (535, 'away', 'recovery', 24, None, None, 10),
    (550, 'away', 'pass', 24, 8, 'complete', 10),
    (558, 'away', 'shot', 8, 0, 'goal', 10),
    (559, 'away', 'goal', 0, None, 'goal', 10),
    (570, 'home', 'kickoff', 50, None, None, 11),
    (585, 'home', 'pass', 50, 60, 'complete', 11),
    (600, 'away', 'recovery', 40, None, None, 12),
]

# Quiet match: midfield circulation, few shots, no goals. Restraint demonstrated. Final 0-0.
QUIET_MATCH_SCENARIO = [
    (0, 'home', 'kickoff', 50, None, None, 1),
    (20, 'home', 'pass', 50, 58, 'complete', 1),
    (45, 'home', 'pass', 58, 64, 'complete', 1),
    (75, 'away', 'recovery', 38, None, None, 2),
    (100, 'away', 'pass', 38, 45, 'complete', 2),
    (125, 'away', 'pass', 45, 39, 'complete', 2),
    (150, 'home', 'recovery', 58, None, None, 3),
    (175, 'home', 'pass', 58, 52, 'complete', 3),
    (200, 'home', 'pass', 52, 60, 'complete', 3),
    (225, 'home', 'pass', 60, 68, 'complete', 3),
    (250, 'home', 'shot', 68, 100, 'missed', 3),
    (270, 'away', 'recovery', 35, None, None, 4),
    (290, 'away', 'pass', 35, 42, 'complete', 4),
    (310, 'home', 'recovery', 55, None, None, 5),
    (330, 'home', 'pass', 55, 62, 'complete', 5),
    (355, 'home', 'pass', 62, 56, 'complete', 5),
    (380, 'away', 'recovery', 46, None, None, 6),
    (405, 'away', 'pass', 46, 40, 'complete', 6),
    (430, 'away', 'pass', 40, 34, 'complete', 6),
    (455, 'home', 'recovery', 62, None, None, 7),
    (475, 'home', 'pass', 62, 54, 'complete', 7),
    (500, 'away', 'recovery', 44, None, None, 8),
    (520, 'away', 'pass', 44, 38, 'complete', 8),
    (540, 'away', 'shot', 38, 0, 'saved', 8),
    (555, 'home', 'recovery', 52, None, None, 9),
    (570, 'home', 'pass', 52, 58, 'complete', 9),
    (585, 'away', 'recovery', 40, None, None, 10),
    (595, 'away', 'pass', 40, 46, 'complete', 10),
    (600, 'home', 'recovery', 50, None, None, 11),
    (600, 'home', 'pass', 50, 56, 'complete', 11),
]

SCENARIOS = {
    'legacy-default': SCENARIO,
    'pressure-builds': PRESSURE_BUILDS_SCENARIO,
    'comeback': COMEBACK_SCENARIO,
    'quiet-match': QUIET_MATCH_SCENARIO,
}


def generate(seed=7, count=None, match_id="demo-match", scenario_id="legacy-default"):
    scenario_id = scenario_id or "legacy-default"
    if scenario_id not in SCENARIOS:
        valid_ids = list(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario '{scenario_id}'. Available scenarios: {valid_ids}")
    fixture = SCENARIOS[scenario_id]
    if count is None:
        count = len(fixture)
    if not 1 <= count <= len(fixture):
        raise ValueError(f"Scenario '{scenario_id}' supports 1..{len(fixture)} events, requested {count}")
    rng = random.Random(seed)
    # Seed varies fictional player identities, not the known storyline/metrics.
    players = {team: rng.sample(range(2, 12), 10) for team in ('home', 'away')}
    for sequence, row in enumerate(fixture[:count], start=1):
        second, team, kind, x, end_x, outcome, possession = row
        if scenario_id == 'legacy-default':
            event_id = f"scenario-v1-{seed}-{sequence}"
        else:
            event_id = f"{scenario_id}-v1-{seed}-{sequence}"
        event = dict(schema_version="1.1", event_id=event_id,
                     match_id=match_id, sequence=sequence, period=1, match_second=second,
                     team_id=team, player_id=f"{team}-{players[team][sequence % 10]}",
                     type=kind, x=x, y=50, source="synthetic",
                     possession_id=f"{match_id}:p{possession}")
        if end_x is not None:
            event.update(end_x=end_x, end_y=50)
        if outcome is not None:
            event['outcome'] = outcome
        if kind == 'goal':
            if scenario_id == 'legacy-default':
                event['related_event_id'] = f"scenario-v1-{seed}-{sequence - 1}"
            else:
                event['related_event_id'] = f"{scenario_id}-v1-{seed}-{sequence - 1}"
            event['player_id'] = f"{team}-{players[team][(sequence - 1) % 10]}"
        yield event
