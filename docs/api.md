# API v0.1

Full-match scenarios `united-city-90` and `united-hull-90` use schema 1.2. Catalog entries include fictional rosters and scenario style settings. Events add `team_name`, `player_name`, `recipient_player_id` and `recipient_player_name`. Full-feed passes require both destination coordinates, a different same-team intended recipient, and `complete`/`intercepted` outcome. New types are `substitution`, `half_end`, `match_end`; existing 1.0/1.1 fixtures remain supported. Catch-up adds optional `match_briefing` with readable rule-based text, evidence IDs and `full-feed-briefing-v1` rule version. Clock and coordinate conventions are documented in [full-match data](full-match-data.md).

Base: `http://localhost:8000/api`. Interactive OpenAPI: `/docs`. Event schema: [match-event.schema.json](../schemas/match-event.schema.json). Pydantic model is authoritative; export script regenerates the shared contract.

| Method | Path                    | Behavior                                                                       |
| ------ | ----------------------- | ------------------------------------------------------------------------------ |
| GET    | /health                 | Process/storage status                                                         |
| GET    | /replay/scenarios       | Catalog of selectable synthetic scenarios with spoiler-free metadata           |
| GET    | /replay/scenario        | Read-only event list for a scenario (`match_id` and optional `scenario_id`)    |
| POST   | /events                 | Single event; 201 with accepted true, false for identical replay               |
| GET    | /matches/{id}/events    | Events ordered by sequence                                                     |
| GET    | /matches/{id}/analytics | Team counts, shot windows, high recoveries, progressive passes, recovery shots |
| GET    | /matches/{id}/stories   | Verified narrative stories with evidence_event_ids and rule versions           |
| GET    | /matches/{id}/graph     | Derived event, metric_window, and story nodes with supports edges              |
| POST   | /matches/{id}/catch-up  | Summary, evidence IDs, through_sequence, audience and rule version             |

Event fields: event_id, match_id, sequence, match_second, team_id, player_id, type, x, y. Defaults: schema_version 1.1, period 1, source synthetic; explicit version 1.0 remains accepted. Version 1.1 adds kickoff events and optional possession_id, end_x/end_y, outcome and related_event_id. Goals with a related_event_id must resolve to the same scorer/team's stored goal-producing shot; references cannot be reused. Unknown fields rejected. See [legacy-compatible example](../schemas/example-event.json).

## Analytics and deterministic story rules

All analytics and narrative stories are strictly derived from synthetic match events using deterministic rules:

1. **Team Counts (`counts-v1`)**: Pass, shot, goal, and recovery tallies per team (`home`, `away`).
2. **Shot Frequency Comparison (`shot-frequency-v1`)**: Evaluates completed five-minute windows $[start, end)$ where $end = 300, 600, \dots$. Requires feed coverage of the baseline ($min(match\_second) \le end - 2 \times 300$). Emits a story when a team records $\ge 3$ shots in the current window and an increase of $\ge 2$ over the prior window.
3. **High Recovery Activity (`high-recovery-v1`)**: Counts recoveries in completed five-minute windows in the opponent's defensive third (Home qualifies at $x \ge 70$; Away qualifies at $x \le 30$). Emits a story when a team reaches $\ge 3$ qualifying recoveries in a completed window. Trigger sequence is the first observed event at or after the window boundary.
4. **Progressive Passing (`progressive-pass-v1`)**: Evaluates completed passes ($type = pass$, $outcome = complete$, non-null endpoints). Measures forward gain ($end\_x - x$ for Home; $x - end\_x$ for Away). Qualifies when forward gain $\ge 15.0$ normalized pitch units. Emits a story when a team reaches $\ge 3$ progressive passes in a completed five-minute window.
5. **Recovery-to-Shot Sequences (`recovery-shot-v1`)**: Identifies a recovery followed by a shot by the same team, within the same non-null possession and period, within $\le 30$ recorded match seconds. All intermediate events must belong to the same team and possession. Uses the nearest valid preceding recovery. Trigger sequence is the shot's sequence.
6. **Goal Stories (`goal-v1`)**: Emitted for each goal event, citing its verified goal-producing shot.
7. **Support Graph (`graph-v1`)**: Nodes represent events, metric windows, and stories. Edges denote mathematical evidentiary support (`type: "supports"`), not causal or tactical assertions.

## Catch Me Up fan briefings

Catch-up body: `{"since_sequence":0,"audience":"casual"}`. Audience supports `casual` and `advanced`. Window evaluates events where $sequence > since\_sequence$; client advances cursor only after successful response.

- **What happened**: Synthesizes verified score changes and goal events.
- **What changed**: Plainly explains observed shifts in shooting volume, high recoveries, progressive passes, and rapid transitions.
- **Casual vs. Advanced**: Casual provides plain English narrative overviews; Advanced includes exact threshold rules, window boundaries, pitch coordinates, and event IDs. Both share the exact same supporting event IDs.
- **Restraint**: If events arrive but no patterns qualify (e.g. in a quiet match), Catch Me Up explicitly reports that no qualifying patterns were observed, without hallucinating momentum or tactics.
- **Candidate Bounding**: Up to 8 candidates are presented to Azure OpenAI or deterministic fallback. Goals and the strongest eligible activity change are preserved.

## Replay and scenario catalog

- `GET /api/replay/scenarios`: Returns an array of scenario metadata:
  - `id`: Stable identifier (`pressure-builds`, `comeback`, `quiet-match`, `legacy-default`).
  - `name`: Human-readable title.
  - `description`: Spoiler-free preview (final scores are never revealed).
  - `event_count`: Total events in the fixture.
  - `duration_seconds`: Match duration (typically 600 seconds / 10 minutes).
  - `scenario_version`: `scenario-v1`.
- `GET /api/replay/scenario?match_id=<id>&scenario_id=<scenario_id>`: Returns the read-only event array without writing to storage. Omitted `scenario_id` defaults to `legacy-default` for backward compatibility. Events pass through normal `POST /events` validation during browser or CLI playback.
- Playback is browser-driven and sequential. Cancellation and speed changes are safe and idempotent. Reset creates a fresh match ID and URL while preserving the chosen scenario.

## Review compatibility corrections

Legacy event content and IDs are unchanged from the original fixture. New rules can add supported stories (four for the full legacy fixture); consumers must not assume exactly two. Progressive passes require both destination coordinates. If goals plus the strongest activity change exceed the eight-candidate Azure budget, the full deterministic briefing is returned with `candidate_budget_or_identity_failure`, with no provider call.
