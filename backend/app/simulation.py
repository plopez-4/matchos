"""Public replay adapter for the current reference-identity demo fixtures."""
from app.full_match import FULL_MATCHES, generate_full_match, full_match_catalog


def get_catalog():
    return full_match_catalog()


def generate(seed=7, count=None, match_id="demo-match", scenario_id="united-city-90"):
    scenario_id = scenario_id or "united-city-90"
    if scenario_id not in FULL_MATCHES:
        raise ValueError(f"Unknown scenario '{scenario_id}'. Available scenarios: {list(FULL_MATCHES)}")
    events = generate_full_match(scenario_id, seed, match_id)
    if count is not None and not 1 <= count <= len(events):
        raise ValueError(f"Scenario supports 1..{len(events)} events")
    yield from events if count is None else events[:count]
