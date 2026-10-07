# API v0.1

Base: `http://localhost:8000/api`. Interactive OpenAPI: `/docs`. Event schema: [match-event.schema.json](../schemas/match-event.schema.json). Pydantic model is authoritative; export script regenerates the shared contract.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | /health | Process/storage status |
| POST | /events | Single event; 201 with accepted true, false for identical replay |
| GET | /matches/{id}/events | Events ordered by sequence |
| GET | /matches/{id}/analytics | Team counts and counts-v1 rule |
| GET | /matches/{id}/stories | Goal story nodes with evidence_event_ids and goal-v1 |
| GET | /matches/{id}/graph | Derived event/metric/story nodes and supports edges |
| POST | /matches/{id}/catch-up | Summary, evidence IDs, through_sequence, audience and rule version |

Event fields: event_id, match_id, sequence, match_second, team_id, player_id, type, x, y. Defaults: schema_version 1.1, period 1, source synthetic; explicit version 1.0 remains accepted. Version 1.1 adds kickoff events and optional possession_id, end_x/end_y, outcome and related_event_id. Goals with a related_event_id must resolve to the same scorer/team's stored goal-producing shot; references cannot be reused. Unknown fields rejected. See [legacy-compatible example](../schemas/example-event.json).

Analytics includes shot_windows for the most recent completed five-minute interval and its predecessor. Windows use [start,end), require ten elapsed minutes and an event covering the baseline start. An activity story needs at least three current-window shots and an increase of at least two. Counts describe recorded attempts, including goal-producing shots; goal events are not counted as extra attempts. In a sparse feed these are recorded counts, not exhaustive match statistics.

Catch-up body: `{"since_sequence":0,"audience":"casual"}`. Audience supports casual/advanced. Window is sequence > since_sequence; client advances only after successful response. All counted new events are listed in evidence_event_ids. New stories are included with context_evidence_event_ids, which can refer to earlier events needed for comparisons. Style changes wording, not facts. UI tracks only demo-match and resets cursor on reload or when the observed match sequence moves backwards.

Invalid input: 422. Changed duplicate ID, reused sequence or late new event: 409. Identical duplicate returns accepted false even after newer events arrive. Unknown matches return empty data/zero counts. No updates/deletes.

Graph is computed from current events on reads, with no durable history or causal edges. The current shot pattern compares only the latest completed intervals; previous pattern snapshots are not persisted. Planned: pagination, stream transport, durable graph history, ingestion cursor for late arrivals and persisted viewer preferences. Agree contracts across owners before implementation.
