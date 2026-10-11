import os
import re
import threading
from pathlib import Path
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from fastapi.staticfiles import StaticFiles
from app import security
from app import matchday
from app.simulation import generate, get_catalog
from app.models import MatchEvent, CatchUpRequest
from app.intelligence import (
    match_stories,
    shot_windows,
    story_graph,
    high_recovery_windows,
    progressive_pass_windows,
    recovery_shot_chains,
)
from app.explanations import explain
from app.briefing import full_feed_briefing

app = FastAPI(title="MatchOS", version="0.1.0",
              docs_url=None if security.production() else "/docs",
              redoc_url=None if security.production() else "/redoc",
              openapi_url=None if security.production() else "/openapi.json")
app.add_middleware(security.SecurityMiddleware)
# Single-process demo store. Replace before using multiple workers.
store: dict[str, dict[str, MatchEvent]] = {}
CATCH_LOCK = threading.Lock()


class ReplayStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    match_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    scenario_id: str = Field(default="legacy-default", pattern=r"^[a-zA-Z0-9_-]{1,80}$")


class ReplayAdvance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: int = Field(ge=1, le=security.MAX_EVENTS)


class MatchdayStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    matchday_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,60}$")


class MatchdayTick(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tick: int = Field(ge=1, le=matchday.DURATION//matchday.TICK_SECONDS)


def day_members(day_id):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", day_id):
        raise HTTPException(422, "Invalid matchday ID")
    security.expire(store)
    members = [f'{day_id}-{p["role"]}' for p in matchday.PROFILES]
    if any(mid not in security.matches or security.matches[mid].get("matchday_id") != day_id for mid in members):
        raise HTTPException(404, "Matchday expired or does not exist")
    return members


def matchday_view(day_id, members):
    state = security.matches[members[0]]
    now = state["clock"]
    entries = []
    for mid, profile in zip(members, matchday.PROFILES):
        events = events_for(mid)
        entries.append({"match_id":mid, "role":profile["role"], "home":profile["home"],
                        "away":profile["away"], "event_count":len(events),
                        "pulse":matchday.pulse(events, now)})
    ranked = matchday.rank(entries)
    # Evaluation comparator: activity count alone, with no personalization/AI.
    baseline = sorted(entries, key=lambda e:(-sum(e["pulse"]["shots_last_five"].values()), e["match_id"]))
    return {"matchday_id":day_id, "clock_second":now, "tick":state["tick"],
            "duration_seconds":matchday.DURATION, "finished":now >= matchday.DURATION,
            "rule_version":matchday.VERSION, "data_origin":"synthetic",
            "matches":entries, "recommendation":ranked[0] if ranked else None,
            "notification":state.get("notification"),
            "simple_shot_baseline":baseline[0]["match_id"] if sum(baseline[0]["pulse"]["shots_last_five"].values()) else None}


@app.post("/api/matchdays/start")
def start_matchday(payload: MatchdayStart, request: Request):
    with security.LOCK:
        owner = security.session(request)
        security.expire(store)
        members = [f'{payload.matchday_id}-{p["role"]}' for p in matchday.PROFILES]
        if any(mid in security.matches for mid in members):
            day_members(payload.matchday_id)
            if any(security.matches[mid]["owner"] != owner for mid in members):
                raise HTTPException(403, "This matchday belongs to another session")
            return matchday_view(payload.matchday_id, members)
        if len(security.matches)+3 > security.MAX_MATCHES or sum(m["owner"] == owner for m in security.matches.values())+3 > 8:
            raise HTTPException(429, "Not enough demo capacity for three matches")
        fixtures = [matchday.fixture(profile, mid) for profile, mid in zip(matchday.PROFILES, members)]
        if any(len(feed) > security.MAX_EVENTS for feed in fixtures):
            raise HTTPException(503, "Matchday exceeds event capacity")
        for mid, profile, feed in zip(members, matchday.PROFILES, fixtures):
            security.claim_match(mid, owner, store, feed, f'matchday-{profile["role"]}')
            security.matches[mid].update(matchday_id=payload.matchday_id)
            for raw in feed:
                if raw["match_second"] > 0:
                    break
                append_event(MatchEvent(**raw))
        expiry = security.matches[members[0]]["expires"]
        for mid in members:
            security.matches[mid]["expires"] = expiry
        security.matches[members[0]].update(clock=0, tick=0, previous_leader=None,
                                          last_notified={}, notification=None)
        return matchday_view(payload.matchday_id, members)


@app.get("/api/matchdays/{day_id}")
def get_matchday(day_id: str):
    with security.LOCK:
        return matchday_view(day_id, day_members(day_id))


@app.delete("/api/matchdays/{day_id}")
def release_matchday(day_id: str, request: Request):
    with security.LOCK:
        owner = security.session(request)
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", day_id):
            raise HTTPException(422, "Invalid matchday ID")
        security.expire(store)
        members = [mid for mid, meta in security.matches.items()
                   if meta.get("matchday_id") == day_id]
        if not members:
            raise HTTPException(404, "Matchday expired or does not exist")
        if any(security.matches[mid]["owner"] != owner for mid in members):
            raise HTTPException(403, "This matchday belongs to another session")
        for mid in members:
            store.pop(mid, None)
        security.expire(store)
        return {"released":True}


@app.post("/api/matchdays/{day_id}/tick")
def tick_matchday(day_id: str, payload: MatchdayTick, request: Request):
    with security.LOCK:
        members = day_members(day_id)
        state = security.matches[members[0]]
        if any(security.matches[mid]["owner"] != security.session(request) for mid in members):
            raise HTTPException(403, "This matchday belongs to another session")
        if payload.tick == state["tick"]:
            return matchday_view(day_id, members)
        if payload.tick != state["tick"]+1 or state["clock"] >= matchday.DURATION:
            raise HTTPException(409, "Advance one matchday tick at a time")
        now = min(matchday.DURATION, state["clock"]+matchday.TICK_SECONDS)
        for mid in members:
            feed = security.matches[mid]["fixture"]
            cursor = len(store[mid])
            for raw in feed[cursor:]:
                if raw["match_second"] > now:
                    break
                append_event(MatchEvent(**raw))
        state.update(clock=now, tick=payload.tick, notification=None)
        view = matchday_view(day_id, members)
        leader = view["recommendation"]
        leader_id = leader["match_id"] if leader else None
        if leader_id and leader_id != state["previous_leader"] and now-state["last_notified"].get(leader_id, -600) >= 600:
            state["last_notified"][leader_id] = now
            state["notification"] = {"id":f'{state["generation"]}:{payload.tick}:{leader_id}',
                                     "match_id":leader_id, "clock_second":now,
                                     "title":f'Heating up: {leader["home"]} vs {leader["away"]}',
                                     "reason":leader["pulse"]["reason"]}
        state["previous_leader"] = leader_id
        view["notification"] = state["notification"]
        return view


@app.post("/api/session")
def create_session(request: Request, response: Response):
    return security.new_session(request, response, store)


@lru_cache(maxsize=1)
def catalog():
    return get_catalog()


@app.post("/api/replay/start", response_model=list[MatchEvent])
def start_replay(payload: ReplayStart, request: Request):
    if payload.scenario_id not in {s["id"] for s in catalog()}:
        raise HTTPException(404, "Unknown scenario")
    with security.LOCK:
        owner = security.session(request)
        security.expire(store)
        meta = security.matches.get(payload.match_id)
        if meta:
            security.claim_match(payload.match_id, owner, store, scenario=payload.scenario_id)
            return meta["fixture"]
        fixture = list(generate(seed=7, match_id=payload.match_id, scenario_id=payload.scenario_id))
        if len(fixture) > security.MAX_EVENTS:
            raise HTTPException(503, "Scenario exceeds demo capacity")
        security.claim_match(payload.match_id, owner, store, fixture, payload.scenario_id)
        return fixture


@app.post("/api/matches/{match_id}/advance", status_code=201)
def advance_replay(match_id: str, payload: ReplayAdvance, request: Request):
    with security.LOCK:
        security.expire(store)
        meta = security.matches.get(match_id)
        if not meta:
            raise HTTPException(404, "Replay expired or does not exist")
        if meta["owner"] != security.session(request):
            raise HTTPException(403, "This replay belongs to another session")
        if meta.get("matchday_id"):
            raise HTTPException(409, "Use the shared matchday clock to advance this replay")
        fixture = meta["fixture"]
        if not fixture or payload.sequence > len(fixture):
            raise HTTPException(422, "Invalid replay sequence")
        if payload.sequence > len(store[match_id]) + 1:
            raise HTTPException(409, "Replay must advance in sequence order")
        return append_event(MatchEvent(**fixture[payload.sequence - 1]))


@app.get("/api/health")
def health():
    return {"status": "ok", "storage": "in-memory"}


@app.get("/api/replay/scenarios")
def replay_scenarios():
    return catalog()


@app.get("/api/replay/scenario", response_model=list[MatchEvent])
def replay_scenario(
    match_id: str = Query(pattern=r"^[a-zA-Z0-9_-]{1,80}$"),
    scenario_id: str = Query(default="legacy-default", pattern=r"^[a-zA-Z0-9_-]{1,80}$"),
):
    catalog_ids = {s["id"] for s in catalog()}
    if scenario_id not in catalog_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario '{scenario_id}'. Available: {sorted(catalog_ids)}",
        )
    # Read-only fixture: events still pass through the normal ingestion validator.
    return list(generate(seed=7, match_id=match_id, scenario_id=scenario_id))


def events_for(match_id):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", match_id):
        raise HTTPException(422, "Invalid match ID")
    with security.LOCK:
        security.expire(store)
        return sorted(store.get(match_id, {}).values(), key=lambda e: e.sequence)


@app.post("/api/events", status_code=201)
def ingest(event: MatchEvent, request: Request):
    security.trusted_ingestion(request)
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", event.match_id):
        raise HTTPException(422, "Invalid match ID")
    with security.LOCK:
        security.claim_match(event.match_id, "trusted-ingestion", store)
        return append_event(event)


def append_event(event: MatchEvent):
    match = store.setdefault(event.match_id, {})
    if event.event_id in match:
        if match[event.event_id] != event:
            raise HTTPException(409, "Event ID reused with different content")
        return {"accepted": False, "event_id": event.event_id}
    if len(match) >= security.MAX_EVENTS:
        raise HTTPException(429, "Match event limit reached")
    if any(e.sequence == event.sequence for e in match.values()):
        raise HTTPException(409, "Sequence already exists")
    # Ordered append ensures sequence cursors never miss late arrivals.
    if match and event.sequence <= max(e.sequence for e in match.values()):
        raise HTTPException(409, "Out-of-order event; replay in sequence order")
    if match and event.match_second < max(e.match_second for e in match.values()):
        raise HTTPException(409, "Match clock moved backwards")
    if event.related_event_id:
        shot = match.get(event.related_event_id)
        if (
            event.type != "goal"
            or not shot
            or shot.type != "shot"
            or shot.team_id != event.team_id
            or shot.outcome != "goal"
            or shot.player_id != event.player_id
        ):
            raise HTTPException(
                422, "Goal reference must resolve to its scorer's goal-producing shot"
            )
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
    return {
        "match_id": match_id,
        "event_count": len(items),
        "teams": {
            team: {
                kind: sum(e.team_id == team and e.type == kind for e in items)
                for kind in ("pass", "shot", "goal", "recovery")
            }
            for team in ("home", "away")
        },
        "rule_version": "counts-v1",
        "shot_windows": shot_windows(items),
        "high_recoveries": high_recovery_windows(items),
        "progressive_passes": progressive_pass_windows(items),
        "recovery_shots": recovery_shot_chains(items),
    }


@app.get("/api/matches/{match_id}/stories")
def stories(match_id: str):
    return match_stories(events_for(match_id))


@app.get("/api/matches/{match_id}/graph")
def graph(match_id: str):
    return story_graph(events_for(match_id))


@app.post("/api/matches/{match_id}/catch-up")
def catch_up(match_id: str, request: CatchUpRequest):
    with security.LOCK:
        all_items = events_for(match_id)
        generation = security.matches.get(match_id, {}).get("generation")
    revision = all_items[-1].sequence if all_items else 0
    if request.since_sequence > revision:
        raise HTTPException(422, "Cursor is ahead of the current match")
    # Fail fast instead of letting slow provider requests occupy every worker.
    if not CATCH_LOCK.acquire(blocking=False):
        raise HTTPException(429, "Catch Me Up is busy; try again shortly", headers={"Retry-After": "2"})
    try:
        cache_key = (match_id, generation, revision, request.since_sequence, request.audience,
                     os.getenv("MATCHOS_AI_MODE", "off"))
        with security.LOCK:
            if cache_key in security.catch_cache:
                security.catch_cache.move_to_end(cache_key)
                return security.catch_cache[cache_key]
        result = build_catch_up(all_items, request)
        with security.LOCK:
            security.catch_cache[cache_key] = result
            while len(security.catch_cache) > 32:
                security.catch_cache.popitem(last=False)
        return result
    finally:
        CATCH_LOCK.release()


def build_catch_up(all_items, request):
    items = [e for e in all_items if e.sequence > request.since_sequence]
    goals = sum(e.type == "goal" for e in items)
    intro = (
        f"{len(items)} new recorded events. {goals} {'goal' if goals == 1 else 'goals'}."
        if items
        else "You’re up to date. No new recorded events."
    )
    if request.audience == "advanced":
        intro += (
            f" Shots: {sum(e.type == 'shot' for e in items)}; "
            f"recoveries: {sum(e.type == 'recovery' for e in items)}."
        )
    new_stories = [
        s for s in match_stories(all_items) if s["sequence"] > request.since_sequence
    ]
    explanation = explain(new_stories, request.audience)
    if items and not new_stories:
        text = intro + " No qualifying activity patterns or goals recorded in this period."
    else:
        text = intro + (" " + explanation["text"] if explanation["text"] else "")
    selected = [s for s in new_stories if s["story_id"] in explanation["selected_story_ids"]]
    briefing = full_feed_briefing(all_items, items, request.audience)
    return {
        "match_briefing": briefing,
        "summary": text,
        "intro": intro,
        "evidence_event_ids": [e.event_id for e in items],
        "through_sequence": max([request.since_sequence] + [e.sequence for e in items]),
        "audience": request.audience,
        "rule_version": "catch-up-v3",
        "stories": new_stories,
        "context_evidence_event_ids": sorted(
            {eid for s in selected for eid in s["evidence_event_ids"]}
        ),
        "explanation": explanation,
    }


# Production serves the built app and API from one origin. HTTPS terminates at a
# trusted reverse proxy; configure Uvicorn's forwarded-allow-ips explicitly.
if security.production():
    app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend" / "dist", html=True), name="frontend")
