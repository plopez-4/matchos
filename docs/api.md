# API v0.1

Base: `http://localhost:8000/api`. Interactive OpenAPI: `/docs`. Event schema: [match-event.schema.json](../schemas/match-event.schema.json). Pydantic model is authoritative; export script regenerates the shared contract.

| Method | Path                    | Behavior                                                           |
| ------ | ----------------------- | ------------------------------------------------------------------ |
| GET    | /health                 | Process/storage status                                             |
| POST   | /events                 | Single event; 201 with accepted true, false for identical replay   |
| GET    | /matches/{id}/events    | Events ordered by sequence                                         |
| GET    | /matches/{id}/analytics | Team counts and counts-v1 rule                                     |
| GET    | /matches/{id}/stories   | Goal story nodes with evidence_event_ids and goal-v1               |
| GET    | /matches/{id}/graph     | Derived event/metric/story nodes and supports edges                |
| POST   | /matches/{id}/catch-up  | Summary, evidence IDs, through_sequence, audience and rule version |

Event fields: event_id, match_id, sequence, match_second, team_id, player_id, type, x, y. Defaults: schema_version 1.1, period 1, source synthetic; explicit version 1.0 remains accepted. Version 1.1 adds kickoff events and optional possession_id, end_x/end_y, outcome and related_event_id. Goals with a related_event_id must resolve to the same scorer/team's stored goal-producing shot; references cannot be reused. Unknown fields rejected. See [legacy-compatible example](../schemas/example-event.json).

Analytics includes shot_windows for the most recent completed five-minute interval and its predecessor. Windows use [start,end), require ten elapsed minutes and an event covering the baseline start. An activity story needs at least three current-window shots and an increase of at least two. Counts describe recorded attempts, including goal-producing shots; goal events are not counted as extra attempts. In a sparse feed these are recorded counts, not exhaustive match statistics.

Catch-up body: `{"since_sequence":0,"audience":"casual"}`. Audience supports casual/advanced. Window is sequence > since_sequence; client advances only after successful response. All counted new events are listed in evidence_event_ids. New stories are included with context_evidence_event_ids, which can refer to earlier events needed for comparisons. Style changes wording, not facts. UI defaults to demo-match and supports a validated ?match=<id> query for separate replay sessions. Cursors reset on page reload or detected sequence rollback; newer responses ahead of polling remain valid. Failed requests retain the prior successful cursor.

Invalid input: 422. Changed duplicate ID, reused sequence or late new event: 409. Identical duplicate returns accepted false even after newer events arrive. Unknown matches return empty data/zero counts. No updates/deletes.

Graph is computed from current events on reads, with no durable history or causal edges. The current shot pattern compares only the latest completed intervals; previous pattern snapshots are not persisted. Planned: pagination, stream transport, durable graph history, ingestion cursor for late arrivals and persisted viewer preferences. Agree contracts across owners before implementation.

Catch-up responses also include explanation: mode (azure/deterministic), selected_story_ids, text, prompt_version, latency_ms, trace and fallback_reason. Azure mode selects valid candidate IDs through two tool calls, then renders trusted story text. It does not generate free-form factual prose. Candidate context evidence may be a superset of selected evidence. See azure-ai.md for setup and live verification details.

Catch-up v3 adds intro and explanation.sections. Each section has title, text, story_ids and evidence_event_ids. What happened covers goals; What changed covers recorded shot activity. Casual wording is simpler; advanced summaries include window-event counts. Both audiences retain the same evidence. The strongest eligible change is added if the model omits it, with a complete_coverage trace entry. Context evidence now corresponds to the selected stories. Empty windows contain no story sections and report that the viewer is up to date. Live Azure calls have been verified for both audiences.

## Browser replay

`GET /replay/scenario?match_id=<id>` returns the shared 30-event seed-7 synthetic fixture without writing it to storage. The match ID must contain 1�80 letters, digits, underscores or hyphens; invalid IDs return 422. Each returned event includes schema defaults and is submitted individually through `POST /events` during browser playback.

Playback is browser-owned, not a backend job. Pause cancels the scheduled next event and aborts pending requests; a request already received by the server can still be accepted. Duplicate retry is idempotent. Speed changes reschedule from the last acknowledged event. Reset creates a new match URL, remounts the dashboard and cancels old requests; it does not delete existing match data. Closing/reloading stops playback; an existing match can be viewed or replaced by a new replay. Do not run a terminal simulator concurrently against the same match ID. No public production replay service or authentication is provided.
