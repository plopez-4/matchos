from fastapi import FastAPI, HTTPException
from app.models import MatchEvent, CatchUpRequest

app = FastAPI(title="MatchOS", version="0.1.0")
# Single-process demo store. Replace before using multiple workers.
store: dict[str, dict[str, MatchEvent]] = {}

@app.get("/api/health")
def health():
    return {"status": "ok", "storage": "in-memory"}

def events_for(match_id):
    return sorted(store.get(match_id, {}).values(), key=lambda e: e.sequence)

@app.post("/api/events", status_code=201)
def ingest(event: MatchEvent):
    match = store.setdefault(event.match_id, {})
    if event.event_id in match:
        if match[event.event_id] != event:
            raise HTTPException(409, "Event ID reused with different content")
        return {"accepted": False, "event_id": event.event_id}
    if any(e.sequence == event.sequence for e in match.values()):
        raise HTTPException(409, "Sequence already exists")
    # Ordered append ensures sequence cursors never miss late arrivals.
    if match and event.sequence <= max(e.sequence for e in match.values()):
        raise HTTPException(409, "Out-of-order event; replay in sequence order")
    match[event.event_id] = event
    return {"accepted": True, "event_id": event.event_id}

@app.get("/api/matches/{match_id}/events")
def events(match_id: str):
    return events_for(match_id)

@app.get("/api/matches/{match_id}/analytics")
def analytics(match_id: str):
    items = events_for(match_id)
    return {"match_id": match_id, "event_count": len(items), "teams": {
        team: {kind: sum(e.team_id == team and e.type == kind for e in items)
               for kind in ("pass", "shot", "goal", "recovery")}
        for team in ("home", "away")}, "rule_version": "counts-v1"}

@app.get("/api/matches/{match_id}/stories")
def stories(match_id: str):
    return [{"story_id": f"goal:{e.event_id}", "text": f"{e.team_id.title()} scored at {e.match_second // 60}:{e.match_second % 60:02d}.",
             "evidence_event_ids": [e.event_id], "rule_version": "goal-v1", "sequence": e.sequence}
            for e in events_for(match_id) if e.type == "goal"]

@app.post("/api/matches/{match_id}/catch-up")
def catch_up(match_id: str, request: CatchUpRequest):
    items = [e for e in events_for(match_id) if e.sequence > request.since_sequence]
    goals = sum(e.type == "goal" for e in items)
    text = f"Recorded events since your last check: {len(items)}. Goals: {goals}."
    if request.audience == "advanced":
        text += f" Shots: {sum(e.type == 'shot' for e in items)}; recoveries: {sum(e.type == 'recovery' for e in items)}."
    return {"summary": text, "evidence_event_ids": [e.event_id for e in items],
            "through_sequence": max([request.since_sequence] + [e.sequence for e in items]),
            "audience": request.audience, "rule_version": "catch-up-v1"}
