import json
import sys
from pathlib import Path
import pytest
from jsonschema import validate
from fastapi.testclient import TestClient
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "backend"))
from simulator.run import generate
from app.main import app, store
from app.models import MatchEvent

@pytest.fixture
def client():
    store.clear()
    with TestClient(app) as client:
        yield client

def test_replay_and_evidence(client):
    events = list(generate(7, 30))
    schema = json.loads((root / "schemas/match-event.schema.json").read_text())
    assert events == list(generate(7, 30))
    for event in events:
        validate(event, schema)
        assert client.post("/api/events", json=event).json()["accepted"]
    for event in events:
        assert not client.post("/api/events", json=event).json()["accepted"]
    counts = client.get("/api/matches/demo-match/analytics").json()
    assert counts["event_count"] == 30
    assert sum(t["goal"] for t in counts["teams"].values()) == 1
    assert counts['teams']['home']['shot'] == 5
    assert counts['teams']['away']['shot'] == 2
    stories = client.get("/api/matches/demo-match/stories").json()
    assert len(stories) == 2
    activity = next(s for s in stories if s['kind'] == 'shot_activity')
    assert activity['metric']['previous']['shot_count'] == 1
    assert activity['metric']['current']['shot_count'] == 4
    ids = {e["event_id"] for e in events}
    assert all(set(s["evidence_event_ids"]) <= ids for s in stories)
    result = client.post("/api/matches/demo-match/catch-up", json={"since_sequence": 20, "audience": "advanced"}).json()
    assert len(result["evidence_event_ids"]) == 10
    assert result["through_sequence"] == 30
    assert "Goals: 1." in result["summary"]
    assert 'recorded 4 shots' in result['summary']
    graph = client.get('/api/matches/demo-match/graph').json()
    node_ids = {n['id'] for n in graph['nodes']}
    assert len(node_ids) == len(graph['nodes'])
    assert all(e['source'] in node_ids and e['target'] in node_ids for e in graph['edges'])
    assert len([n for n in graph['nodes'] if n['type'] == 'metric_window']) == 2
    assert client.post('/api/matches/demo-match/catch-up', json={'since_sequence': 30}).json()['stories'] == []

def test_validation_conflicts_and_order(client):
    events = list(generate(7, 3))
    assert client.post("/api/events", json={**events[0], "x": 101}).status_code == 422
    client.post("/api/events", json=events[0])
    assert client.post("/api/events", json={**events[0], "type": "goal"}).status_code == 409
    assert client.post("/api/events", json={**events[0], "event_id": "other"}).status_code == 409
    client.post("/api/events", json=events[2])
    assert client.post("/api/events", json=events[1]).status_code == 409

def test_empty(client):
    assert client.get("/api/matches/missing/events").json() == []
    assert client.post("/api/matches/missing/catch-up", json={}).json()["through_sequence"] == 0

def test_schema_matches_model():
    schema = json.loads((root / "schemas/match-event.schema.json").read_text())
    schema.pop("$schema")
    assert schema == MatchEvent.model_json_schema()

def test_scenario_goal_and_continuity():
    events = list(generate())
    goals = [e for e in events if e['type'] == 'goal']
    assert len(goals) == 1
    by_id = {e['event_id']: e for e in events}
    for goal in goals:
        shot = by_id[goal['related_event_id']]
        assert shot['type'] == 'shot' and shot['outcome'] == 'goal'
        assert shot['player_id'] == goal['player_id']
        assert shot['team_id'] == goal['team_id']
        assert shot['match_second'] < goal['match_second']
    for before, after in zip(events, events[1:]):
        assert before['match_second'] <= after['match_second']
        if before['type'] == 'pass' and before['possession_id'] == after['possession_id']:
            assert before['end_x'] == after['x']
    assert all(e['player_id'].startswith(e['team_id'] + '-') for e in events)

def test_insufficient_window_and_boundary(client):
    from app.intelligence import shot_windows, match_stories
    events = [MatchEvent(**e) for e in generate(count=28)]
    assert shot_windows(events) == []  # 599 seconds: second window not complete.
    assert all(s['kind'] != 'shot_activity' for s in match_stories(events))
    events = [MatchEvent(**e) for e in generate()]
    # Windows are [start,end); a shot at 300 belongs only to current.
    events[9] = events[9].model_copy(update={'type': 'shot'})
    windows = shot_windows(events)
    home = next(w for w in windows if w['team_id'] == 'home')
    assert home['previous']['shot_count'] == 1
    assert home['current']['shot_count'] == 5
    reduced = [e for e in events if e.type != 'shot' or e.match_second < 300 or e.match_second == 570]
    assert all(s['kind'] != 'shot_activity' for s in match_stories(reduced))

def test_orphan_goal_and_backwards_clock(client):
    events = list(generate())
    assert client.post('/api/events', json=events[21]).status_code == 422
    client.post('/api/events', json=events[1])
    assert client.post('/api/events', json={**events[2], 'match_second': 1}).status_code == 409
