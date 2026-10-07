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
    assert sum(t["goal"] for t in counts["teams"].values()) == 3
    stories = client.get("/api/matches/demo-match/stories").json()
    assert len(stories) == 3
    ids = {e["event_id"] for e in events}
    assert all(set(s["evidence_event_ids"]) <= ids for s in stories)
    result = client.post("/api/matches/demo-match/catch-up", json={"since_sequence": 20, "audience": "advanced"}).json()
    assert len(result["evidence_event_ids"]) == 10
    assert result["through_sequence"] == 30
    assert "Goals: 1." in result["summary"]

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
