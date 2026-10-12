from fastapi import FastAPI, HTTPException
from app.models import MatchEvent, CatchUpRequest
from app.intelligence import match_stories, shot_windows, story_graph
from app.explanations import explain

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
    if match and event.match_second < max(e.match_second for e in match.values()):
        raise HTTPException(409, "Match clock moved backwards")
    if event.related_event_id:
        shot = match.get(event.related_event_id)
        if event.type != 'goal' or not shot or shot.type != 'shot' or shot.team_id != event.team_id or shot.outcome != 'goal' or shot.player_id != event.player_id:
            raise HTTPException(422, "Goal reference must resolve to its scorer's goal-producing shot")
        if any(e.related_event_id == event.related_event_id for e in match.values()):
            raise HTTPException(409, "Goal-producing shot already has a goal event")
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
        for team in ("home", "away")}, "rule_version": "counts-v1",
        "shot_windows": shot_windows(items)}

@app.get("/api/matches/{match_id}/stories")
def stories(match_id: str):
    return match_stories(events_for(match_id))

@app.get("/api/matches/{match_id}/graph")
def graph(match_id: str):
    return story_graph(events_for(match_id))

@app.post("/api/matches/{match_id}/catch-up")
def catch_up(match_id: str, request: CatchUpRequest):
    items = [e for e in events_for(match_id) if e.sequence > request.since_sequence]
    goals = sum(e.type == "goal" for e in items)
    intro = f"{len(items)} new recorded events. {goals} {'goal' if goals == 1 else 'goals'}." if items else 'You’re up to date. No new recorded events.'
    if request.audience == "advanced":
        intro += f" Shots: {sum(e.type == 'shot' for e in items)}; recoveries: {sum(e.type == 'recovery' for e in items)}."
    new_stories = [s for s in match_stories(events_for(match_id)) if s['sequence'] > request.since_sequence]
    explanation = explain(new_stories, request.audience)
    text = intro + (' ' + explanation['text'] if explanation['text'] else '')
    selected = [s for s in new_stories if s['story_id'] in explanation['selected_story_ids']]
    return {"summary": text, "intro": intro, "evidence_event_ids": [e.event_id for e in items],
            "through_sequence": max([request.since_sequence] + [e.sequence for e in items]),
            "audience": request.audience, "rule_version": "catch-up-v3", "stories": new_stories,
            "context_evidence_event_ids": sorted({eid for s in selected for eid in s['evidence_event_ids']}),
            "explanation": explanation}
