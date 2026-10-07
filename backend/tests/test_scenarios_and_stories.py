import json
from pathlib import Path
import pytest
from jsonschema import validate
from fastapi.testclient import TestClient

from app.main import app, store
from app.models import MatchEvent
from app.simulation import get_catalog, generate, SCENARIOS
from app.intelligence import (
    match_stories,
    high_recovery_windows,
    progressive_pass_windows,
    recovery_shot_chains,
    story_graph,
)
from app.explanations import explain, strongest_change, select_candidates, render

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/match-event.schema.json").read_text())


@pytest.fixture
def client():
    store.clear()
    with TestClient(app) as test_client:
        yield test_client


def test_scenario_catalog_metadata_and_validation(client):
    catalog = get_catalog()
    assert len(catalog) == 4
    scenario_ids = {s["id"] for s in catalog}
    assert scenario_ids == {"legacy-default", "pressure-builds", "comeback", "quiet-match"}

    res = client.get("/api/replay/scenarios")
    assert res.status_code == 200
    api_catalog = res.json()
    assert api_catalog == catalog

    for item in catalog:
        assert item["scenario_version"] == "scenario-v1"
        assert item["duration_seconds"] >= 600
        # Event count matches actual fixture length
        events = list(generate(scenario_id=item["id"]))
        assert len(events) == item["event_count"]
        # Spoiler-free: final score not disclosed in name or description
        for score_indicator in ("1-0", "0-0", "1-1", "wins", "loses", "final score"):
            assert score_indicator not in item["name"].lower()
            assert score_indicator not in item["description"].lower()

    # Reject unknown scenario
    err_res = client.get("/api/replay/scenario", params={"match_id": "test", "scenario_id": "nonexistent"})
    assert err_res.status_code == 404
    assert "Unknown scenario" in err_res.json()["detail"]

    # Reject invalid regex
    bad_param = client.get("/api/replay/scenario", params={"match_id": "test", "scenario_id": "bad/id!"})
    assert bad_param.status_code == 422


def test_all_scenarios_reproducible_and_schema_valid():
    for sc_id in ("legacy-default", "pressure-builds", "comeback", "quiet-match"):
        run1 = list(generate(seed=42, scenario_id=sc_id))
        run2 = list(generate(seed=42, scenario_id=sc_id))
        assert run1 == run2

        # Check unique event IDs and prefix
        event_ids = [e["event_id"] for e in run1]
        assert len(event_ids) == len(set(event_ids))
        if sc_id == "legacy-default":
            assert all(eid.startswith("scenario-v1-42-") for eid in event_ids)
        else:
            assert all(eid.startswith(f"{sc_id}-v1-42-") for eid in event_ids)

        # Validate each event against schema
        for ev in run1:
            validate(ev, SCHEMA)


def test_pressure_builds_scenario_ingestion_and_stories(client):
    events = list(generate(seed=7, match_id="pb-match", scenario_id="pressure-builds"))
    for ev in events:
        res = client.post("/api/events", json=ev)
        assert res.status_code == 201

    analytics = client.get("/api/matches/pb-match/analytics").json()
    assert analytics["teams"]["home"]["goal"] == 1
    assert analytics["teams"]["away"]["goal"] == 0
    assert analytics["teams"]["home"]["shot"] == 5

    stories = client.get("/api/matches/pb-match/stories").json()
    story_kinds = {s["kind"] for s in stories}
    assert "goal" in story_kinds
    assert "shot_activity" in story_kinds
    assert "high_recovery" in story_kinds
    assert "progressive_pass" in story_kinds
    assert "recovery_shot" in story_kinds

    # High recovery story verifies attacking third recoveries
    rec_story = next(s for s in stories if s["kind"] == "high_recovery")
    assert rec_story["metric"]["team_id"] == "home"
    assert rec_story["metric"]["recovery_count"] >= 3
    assert rec_story["metric"]["qualifying_x_threshold"] == 70.0
    assert rec_story["sequence"] >= 30  # Verified at or after window end

    # Recovery-to-shot story
    trans_story = next(s for s in stories if s["kind"] == "recovery_shot")
    assert trans_story["metric"]["elapsed_seconds"] <= 30
    assert trans_story["metric"]["team_id"] == "home"

    # Catch Me Up contains both What happened and What changed
    catchup = client.post(
        "/api/matches/pb-match/catch-up",
        json={"since_sequence": 0, "audience": "advanced"},
    ).json()
    sections = catchup["explanation"]["sections"]
    section_titles = [s["title"] for s in sections]
    assert "What happened" in section_titles
    assert "What changed" in section_titles


def test_comeback_scenario_two_goals_and_kickoffs(client):
    events = list(generate(seed=7, match_id="cb-match", scenario_id="comeback"))
    for ev in events:
        res = client.post("/api/events", json=ev)
        assert res.status_code == 201

    analytics = client.get("/api/matches/cb-match/analytics").json()
    assert analytics["teams"]["home"]["goal"] == 1
    assert analytics["teams"]["away"]["goal"] == 1

    goals = [e for e in events if e["type"] == "goal"]
    assert len(goals) == 2
    assert goals[0]["team_id"] == "home"
    assert goals[1]["team_id"] == "away"
    # Ensure substantial playback separation
    assert goals[1]["match_second"] - goals[0]["match_second"] >= 300
    assert goals[1]["sequence"] - goals[0]["sequence"] >= 15

    # Check kickoffs following each goal
    g1_idx = [i for i, e in enumerate(events) if e["type"] == "goal"][0]
    g2_idx = [i for i, e in enumerate(events) if e["type"] == "goal"][1]
    assert events[g1_idx + 1]["type"] == "kickoff" and events[g1_idx + 1]["team_id"] == "away"
    assert events[g2_idx + 1]["type"] == "kickoff" and events[g2_idx + 1]["team_id"] == "home"

    stories = client.get("/api/matches/cb-match/stories").json()
    goal_stories = [s for s in stories if s["kind"] == "goal"]
    assert len(goal_stories) == 2


def test_quiet_match_restraint_and_no_drama(client):
    events = list(generate(seed=7, match_id="qm-match", scenario_id="quiet-match"))
    for ev in events:
        res = client.post("/api/events", json=ev)
        assert res.status_code == 201

    analytics = client.get("/api/matches/qm-match/analytics").json()
    assert analytics["teams"]["home"]["goal"] == 0
    assert analytics["teams"]["away"]["goal"] == 0
    assert analytics["teams"]["home"]["shot"] <= 1
    assert analytics["teams"]["away"]["shot"] <= 1

    stories = client.get("/api/matches/qm-match/stories").json()
    assert stories == []

    # Graph has events but 0 story nodes and 0 edges
    g = client.get("/api/matches/qm-match/graph").json()
    assert len(g["nodes"]) == len(events)
    assert g["edges"] == []

    # Catch up indicates no qualifying drama
    catchup = client.post(
        "/api/matches/qm-match/catch-up",
        json={"since_sequence": 0, "audience": "casual"},
    ).json()
    assert "No qualifying activity patterns or goals recorded" in catchup["summary"]
    assert catchup["explanation"]["sections"] == []


def test_rule_boundaries_high_recovery():
    # Home: >= 70 qualifies; < 70 does not
    # Away: <= 30 qualifies; > 30 does not
    base = [
        MatchEvent(schema_version="1.1", event_id="e0", match_id="m", sequence=1, match_second=0,
                   team_id="home", player_id="home-1", type="kickoff", x=50, y=50),
        # Home recovery at 69.9 (fails)
        MatchEvent(schema_version="1.1", event_id="e1", match_id="m", sequence=2, match_second=100,
                   team_id="home", player_id="home-2", type="recovery", x=69.9, y=50),
        # Home recovery at 70.0 (qualifies)
        MatchEvent(schema_version="1.1", event_id="e2", match_id="m", sequence=3, match_second=150,
                   team_id="home", player_id="home-3", type="recovery", x=70.0, y=50),
        # Home recovery at 80.0 (qualifies)
        MatchEvent(schema_version="1.1", event_id="e3", match_id="m", sequence=4, match_second=200,
                   team_id="home", player_id="home-4", type="recovery", x=80.0, y=50),
        # Away recovery at 30.1 (fails)
        MatchEvent(schema_version="1.1", event_id="e4", match_id="m", sequence=5, match_second=220,
                   team_id="away", player_id="away-1", type="recovery", x=30.1, y=50),
        # Away recovery at 30.0 (qualifies)
        MatchEvent(schema_version="1.1", event_id="e5", match_id="m", sequence=6, match_second=250,
                   team_id="away", player_id="away-2", type="recovery", x=30.0, y=50),
        # Boundary event at 300 to close window [0, 300)
        MatchEvent(schema_version="1.1", event_id="e6", match_id="m", sequence=7, match_second=300,
                   team_id="home", player_id="home-1", type="pass", x=50, y=50, end_x=55, end_y=50, outcome="complete"),
    ]
    w = high_recovery_windows(base)
    home_w = next(item for item in w if item["team_id"] == "home")
    away_w = next(item for item in w if item["team_id"] == "away")
    assert home_w["recovery_count"] == 2  # e2, e3 (e1 excluded)
    assert away_w["recovery_count"] == 1  # e5 (e4 excluded)
    # Neither met threshold 3 -> no stories
    assert all(s["kind"] != "high_recovery" for s in match_stories(base))


def test_rule_boundaries_progressive_pass():
    # Threshold: gain >= 15.0. Incomplete passes and missing end_x excluded.
    base = [
        MatchEvent(schema_version="1.1", event_id="e0", match_id="m", sequence=1, match_second=0,
                   team_id="home", player_id="home-1", type="kickoff", x=50, y=50),
        # Home gain 14.9 (fails)
        MatchEvent(schema_version="1.1", event_id="e1", match_id="m", sequence=2, match_second=50,
                   team_id="home", player_id="home-2", type="pass", x=50.0, y=50, end_x=64.9, end_y=50, outcome="complete"),
        # Home gain 15.0 (qualifies)
        MatchEvent(schema_version="1.1", event_id="e2", match_id="m", sequence=3, match_second=100,
                   team_id="home", player_id="home-2", type="pass", x=50.0, y=50, end_x=65.0, end_y=50, outcome="complete"),
        # Incomplete pass with gain 20 (fails due to outcome)
        MatchEvent(schema_version="1.1", event_id="e3", match_id="m", sequence=4, match_second=150,
                   team_id="home", player_id="home-3", type="pass", x=50.0, y=50, end_x=70.0, end_y=50, outcome="blocked"),
        # Away gain 15.0: x=60 -> 45 (qualifies)
        MatchEvent(schema_version="1.1", event_id="e4", match_id="m", sequence=5, match_second=200,
                   team_id="away", player_id="away-1", type="pass", x=60.0, y=50, end_x=45.0, end_y=50, outcome="complete"),
        # Away backward pass: x=45 -> 50 (fails)
        MatchEvent(schema_version="1.1", event_id="e5", match_id="m", sequence=6, match_second=250,
                   team_id="away", player_id="away-1", type="pass", x=45.0, y=50, end_x=50.0, end_y=50, outcome="complete"),
        MatchEvent(schema_version="1.1", event_id="e6", match_id="m", sequence=7, match_second=300,
                   team_id="home", player_id="home-1", type="pass", x=50, y=50, end_x=52, end_y=50, outcome="complete"),
    ]
    w = progressive_pass_windows(base)
    home_w = next(item for item in w if item["team_id"] == "home")
    away_w = next(item for item in w if item["team_id"] == "away")
    assert home_w["pass_count"] == 1  # e2
    assert away_w["pass_count"] == 1  # e4


def test_rule_boundaries_recovery_to_shot():
    # Gap <= 30s qualifies; 31s does not. Broken possession does not.
    # Case 1: valid 30s gap
    valid_events = [
        MatchEvent(schema_version="1.1", event_id="e1", match_id="m", sequence=1, match_second=100,
                   team_id="home", player_id="h1", type="recovery", x=60, y=50, possession_id="m:p1"),
        MatchEvent(schema_version="1.1", event_id="e2", match_id="m", sequence=2, match_second=115,
                   team_id="home", player_id="h2", type="pass", x=60, y=50, end_x=80, end_y=50, outcome="complete", possession_id="m:p1"),
        MatchEvent(schema_version="1.1", event_id="e3", match_id="m", sequence=3, match_second=130,
                   team_id="home", player_id="h2", type="shot", x=80, y=50, outcome="missed", possession_id="m:p1"),
    ]
    c1 = recovery_shot_chains(valid_events)
    assert len(c1) == 1
    assert c1[0]["elapsed_seconds"] == 30
    assert c1[0]["evidence_event_ids"] == ["e1", "e2", "e3"]

    # Case 2: 31s gap (fails)
    too_long = [
        valid_events[0],
        valid_events[1],
        valid_events[2].model_copy(update={"match_second": 131}),
    ]
    assert recovery_shot_chains(too_long) == []

    # Case 3: Intervening opposition event breaks the chain
    broken = [
        valid_events[0],
        MatchEvent(schema_version="1.1", event_id="e_away", match_id="m", sequence=2, match_second=110,
                   team_id="away", player_id="a1", type="recovery", x=40, y=50, possession_id="m:p2"),
        valid_events[2].model_copy(update={"sequence": 3}),
    ]
    assert recovery_shot_chains(broken) == []


def test_graph_integrity_and_unique_nodes(client):
    for sc_id in ("pressure-builds", "comeback", "quiet-match"):
        events = [MatchEvent(**e) for e in generate(scenario_id=sc_id)]
        g = story_graph(events)
        node_ids = {n["id"] for n in g["nodes"]}
        assert len(node_ids) == len(g["nodes"])
        for edge in g["edges"]:
            assert edge["source"] in node_ids
            assert edge["target"] in node_ids
            assert edge["type"] == "supports"


def test_candidate_selection_bounding_and_priorities():
    # 10 stories: 2 goals, 8 non-goals
    stories = [
        {"story_id": f"s{i}", "kind": "progressive_pass", "sequence": i,
         "text": f"Pass story {i}", "evidence_event_ids": [f"e{i}"], "rule_version": "progressive-pass-v1"}
        for i in range(1, 9)
    ]
    stories.insert(0, {"story_id": "g1", "kind": "goal", "sequence": 1,
                       "text": "Goal 1", "evidence_event_ids": ["eg1"], "rule_version": "goal-v1"})
    stories.append({"story_id": "g2", "kind": "goal", "sequence": 20,
                    "text": "Goal 2", "evidence_event_ids": ["eg2"], "rule_version": "goal-v1"})

    candidates = select_candidates(stories, limit=8)
    assert len(candidates) == 8
    # Both goals must be preserved even though g1 was early
    cand_ids = {c["story_id"] for c in candidates}
    assert "g1" in cand_ids
    assert "g2" in cand_ids
    # Chronological ordering preserved
    assert [c["sequence"] for c in candidates] == sorted(c["sequence"] for c in candidates)
