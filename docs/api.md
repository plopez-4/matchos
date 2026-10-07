# API v0.1

Base: `http://localhost:8000/api`. Interactive OpenAPI: `/docs`. Event schema: [match-event.schema.json](../schemas/match-event.schema.json). Pydantic model is authoritative; export script regenerates the shared contract.

| Method | Path | Behavior |
| --- | --- | --- |
| GET | /health | Process/storage status |
| POST | /events | Single event; 201 with accepted true, false for identical replay |
| GET | /matches/{id}/events | Events ordered by sequence |
| GET | /matches/{id}/analytics | Team counts and counts-v1 rule |
| GET | /matches/{id}/stories | Goal story nodes with evidence_event_ids and goal-v1 |
| POST | /matches/{id}/catch-up | Summary, evidence IDs, through_sequence, audience and rule version |

Event fields: event_id, match_id, sequence, match_second, team_id, player_id, type, x, y. Defaults: schema_version 1.0, period 1, source synthetic. Unknown fields rejected. See [example](../schemas/example-event.json).

Catch-up body: `{"since_sequence":0,"audience":"casual"}`. Audience supports casual/advanced. Window is sequence > since_sequence; client advances only after successful response. All counted events are listed as evidence. Style changes wording, not facts. UI tracks only demo-match and resets cursor on reload.

Invalid input: 422. Changed duplicate ID, reused sequence or late new event: 409. Identical duplicate returns accepted false even after newer events arrive. Unknown matches return empty data/zero counts. No updates/deletes.

Planned: pagination, stream transport, graph edges, metric windows, ingestion cursor for late arrivals and persisted viewer preferences. Agree contracts across owners before implementation.
