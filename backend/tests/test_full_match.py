from app.matchday import PROFILES, fixture
from app.rosters import club_for_name
import pytest
from fastapi.testclient import TestClient
from conftest import TRUSTED_HEADERS
from pydantic import ValidationError
from app.full_match import FULL_MATCHES, generate_full_match
from app.main import app, store
from app.models import MatchEvent


@pytest.mark.parametrize("scenario", FULL_MATCHES)
@pytest.mark.parametrize("seed", [7, 42, 99])
def test_full_feed_identity_clock_and_ball_continuity(scenario, seed):
    events = generate_full_match(scenario, seed)
    assert events == generate_full_match(scenario, seed)
    assert len(events) > 500
    assert events[0]["match_second"] == 0
    assert events[-1]["match_second"] == 5580
    assert events[-1]["type"] == "match_end"
    assert [e["type"] for e in events].count("half_end") == 1
    expected_subs = sum(len(club_for_name(FULL_MATCHES[scenario][side]).get('demo_bench', [])) for side in ('home', 'away'))
    assert [e["type"] for e in events].count("substitution") == expected_subs
    active = {t: {f"{t}-{i}" for i in range(1, 12)} for t in ("home", "away")}
    previous = None
    by_id = {}
    for index, raw in enumerate(events, 1):
        e = MatchEvent(**raw)
        assert e.sequence == index and e.event_id not in by_id
        assert e.player_id in active[e.team_id]
        if previous:
            assert e.match_second >= previous.match_second
            assert e.period >= previous.period
            if previous.type == "pass" and previous.outcome == "complete" and e.type in ("pass", "shot"):
                assert e.player_id == previous.recipient_player_id
                assert (e.x, e.y) == (previous.end_x, previous.end_y)
                assert e.possession_id == previous.possession_id
        if e.type == "pass":
            assert e.recipient_player_id in active[e.team_id]
        if e.type == "substitution":
            active[e.team_id].remove(e.player_id)
            active[e.team_id].add(e.recipient_player_id)
        if e.type == "goal":
            shot = by_id[e.related_event_id]
            assert shot.type == "shot" and shot.outcome == "goal"
            assert (e.team_id, e.player_id) == (shot.team_id, shot.player_id)
        by_id[e.event_id] = e
        previous = e
    profile = next(p for p in PROFILES if p['role'] == FULL_MATCHES[scenario]['role'])
    assert events == fixture(profile, 'full-match', seed=seed)
    for raw in events:
        club = club_for_name(raw['team_name'])
        assert raw['player_name'] in {player['name'] for player in club['players']}



@pytest.mark.parametrize("scenario", FULL_MATCHES)
def test_full_match_api_and_readable_briefing(scenario, monkeypatch):
    monkeypatch.setenv("MATCHOS_AI_MODE", "off")
    store.clear()
    with TestClient(app, headers=TRUSTED_HEADERS) as client:
        response = client.get("/api/replay/scenario", params={"match_id": scenario, "scenario_id": scenario})
        assert response.status_code == 200
        assert store == {}
        events = response.json()
        for event in events:
            assert client.post("/api/events", json=event).status_code == 201
        assert client.post("/api/events", json=events[-1]).json()["accepted"] is False
        result = client.post(f"/api/matches/{scenario}/catch-up", json={"audience": "advanced"}).json()
        briefing = result["match_briefing"]
        assert FULL_MATCHES[scenario]["home"] in briefing["text"]
        assert "completed" in briefing["text"] and "93:00" in briefing["text"]
        assert "synthetic match has finished" in briefing["text"]
        ids = {e["event_id"] for e in events}
        assert set(briefing["evidence_event_ids"]) <= ids
        assert len(briefing["evidence_event_ids"]) == len(set(briefing["evidence_event_ids"]))
        assert result["through_sequence"] == len(events)
        fresh = client.post(f"/api/matches/{scenario}/catch-up", json={"since_sequence": len(events)}).json()
        assert fresh["match_briefing"] is None
    store.clear()


@pytest.mark.parametrize("bad_fields", [{"recipient_player_id": None}, {"end_y": None}, {"recipient_player_id": "away-3"}])
def test_full_feed_pass_rejects_invalid_recipient_or_coordinates(bad_fields):
    event = next(e for e in generate_full_match("united-city-90") if e["type"] == "pass")
    with pytest.raises(ValidationError):
        MatchEvent(**{**event, **bad_fields})
