# API v0.1

The public replay catalog now contains only `united-city-90`, `palace-newcastle-90`, and `brighton-fulham-90`. The default is `united-city-90`. Both website views use `backend/app/data/demo_fixtures.json` and the current Matchday generator with reference roster identities. Retired Hull/placeholder scenarios return 404 from replay routes. Short legacy fixtures remain internal regression inputs only.

The `fan_briefing` field now uses `fan-briefing-v2`: three sections (score story, recent action, clock), exact current/previous shot-window boundaries, comparison availability, and an observed-goal `trajectory`. Its ordered transitions distinguish `lead_acquisition`, `equalization`, `lead_extension`, `deficit_reduction` and `lead_reversal`; acquisitions count a reversal as taking the lead as well. `rapid_response` is present only when the preceding goal is by the opponent and the interval is at most 600 match seconds. Matchday entries return the same `briefing` and `briefing_events` for the shared Radar card. Catch-up returns `null` for no new events, retaining the existing cursor contract. Early shot windows include second zero using an exclusive start of -1; no previous-window metadata is returned before 300 seconds. A comparison's clock-span requirement does not establish that a real source has complete coverage.

Catch-up responses add `fan_briefing` (or `null` when no new events): a headline, scoreline, match clock, three fan-facing sections and supporting event IDs. Existing `match_briefing`, `explanation`, stories and evidence fields remain available for the analytical view. This additive field uses deterministic wording from observed facts and adds no provider calls.

Matchday routes: `POST /matchdays/start`, `GET /matchdays/{id}`, `POST /matchdays/{id}/tick`, and owner-only `DELETE /matchdays/{id}`. They advance three server-owned synthetic feeds on one shared clock and return an observed-event Radar snapshot. See [Match Radar API, rules and limits](match-radar.md).

`POST /matchdays/start` accepts optional `resume_on_capacity` (default false). When true and a new three-match group cannot fit, it returns the most recently created complete group owned by the requesting session, with `resumed_due_to_capacity: true` and its actual `matchday_id`. The focused UI uses this to recover after reopening the home page repeatedly; it updates the URL and explains how to start fresh. No groups are evicted and ownership/capacity limits remain enforced. If no complete owned group exists, the capacity error remains. **New demo** releases the current group before starting another.

Player stories add `player_shot_creation`, `player_shooting` and `player_forward_passing` to the existing story endpoint and graph. Their metrics include player identity, exact window bounds, snapshot/archive mode, count, team denominator, coverage, rule version and source IDs. Shot-creation metrics include explicit pass/shot/recipient links and elapsed time. The focused `story_plan.player_story_id` identifies the player contribution selected for prose, evidence and narration. See [player-impact definitions](player-impact.md).

## Security contract

All writes require JSON and `X-MatchOS-Client: replay` (or a trusted ingestion credential). The marker is CSRF protection, not a password. Origin/Host checks and request limits apply. Public reads expose only synthetic match data.

- `POST /api/session` with `{}` establishes a private HttpOnly cookie; browsers use same-origin credentials.
- `POST /api/replay/start` with `{ "match_id": "fresh-id", "scenario_id": "palace-newcastle-90" }` reserves a replay for that session and returns its canonical fixture. The same owner/scenario can retry; another owner receives 403.
- `POST /api/matches/{id}/advance` with `{ "sequence": 1 }` appends only the corresponding server-owned event. Other fields are rejected. Ordered retries are idempotent.
- `POST /api/events` requires `X-MatchOS-Ingest-Token` matching a private server token of at least 32 characters. Disabled by default. Trusted ingestion cannot overwrite browser-owned replays.
- Catch Me Up rejects a cursor ahead of the match, caches identical revision/cursor/audience/mode requests, and rejects busy/excess requests with 429. Provider limits produce a deterministic explanation instead of unlimited Azure work.

Expired sessions require reloading and starting a fresh replay. Capacity failures use 429/503; oversized bodies use 413. See [security setup](security.md) for exact quotas and production configuration.

The three current full-match scenarios listed above use schema 1.2. Catalog entries include dated reference roster identities, authored demo roles and synthetic-data/version metadata. Events add `team_name`, `player_name`, `recipient_player_id` and `recipient_player_name`. Full-feed passes require both destination coordinates, a different same-team intended recipient, and `complete`/`intercepted` outcome. New types are `substitution`, `half_end`, `match_end`; existing 1.0/1.1 fixtures remain supported. Catch-up adds optional `match_briefing` with readable rule-based text, evidence IDs and `full-feed-briefing-v1` rule version. Clock and coordinate conventions are documented in [full-match data](full-match-data.md).

Hosted base: `https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io/api`. Local base: `http://localhost:8000/api`. Interactive OpenAPI `/docs` is available locally and intentionally disabled in production. Event schema: [match-event.schema.json](../schemas/match-event.schema.json). Pydantic model is authoritative; export script regenerates the shared contract.

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

Explicit Catch Me Up requests can also attach `narrative` with `mode`, localized `text`, evidence IDs, version and fallback reason. A reviewed model result adds `id`, `model`, `fact_ids` and `review: model_review_passed`. This is model-written prose with a fallible model review, not deterministic claim verification. Its text also becomes `spoken_recap`. Live matchday ticks retain the deterministic paragraph without provider requests. See [writer behavior and limits](fan-narrative.md).

To read a displayed AI paragraph, `/api/narration` additionally accepts its opaque `narrative_id`. The server resolves it for the owned snapshot; missing/expired/mismatched cached text returns 409 and never falls back silently to another paragraph. Omitting this ID reads the rule recap. The browser cannot submit narration text.

Briefings also include `spoken_recap: {en, es}`: concise, deterministic narration from the same observed score trajectory, shot windows and phase. Device speech and Azure speech use this shared wording. It summarizes rather than reading every evidence row; the full sections, goal transitions and evidence IDs remain available. No new provider call is needed to create this text.

Catch-up body: `{"since_sequence":0,"audience":"casual"}`. Audience supports `casual` and `advanced`. Window evaluates events where $sequence > since\_sequence$; client advances cursor only after successful response.

- **What happened**: Synthesizes verified score changes and goal events.
- **What changed**: Plainly explains observed shifts in shooting volume, high recoveries, progressive passes, and rapid transitions.
- **Casual vs. Advanced**: Casual provides plain English narrative overviews; Advanced includes exact threshold rules, window boundaries, pitch coordinates, and event IDs. Both share the exact same supporting event IDs.
- **Restraint**: If events arrive but no patterns qualify (e.g. in a quiet match), Catch Me Up explicitly reports that no qualifying patterns were observed, without hallucinating momentum or tactics.
- **Candidate Bounding**: Up to 8 candidates are presented to Azure OpenAI or deterministic fallback. Goals and the strongest eligible activity change are preserved.

## Replay and scenario catalog

- `GET /api/replay/scenarios` returns the current three fixtures: `united-city-90`, `palace-newcastle-90`, and `brighton-fulham-90`. Each entry includes `id`, `name`, spoiler-free `description`, `event_count`, `duration_seconds`, `scenario_version`, `data_origin: synthetic`, `version_count: 4`, and reference team/player metadata.
- `GET /api/replay/scenario?match_id=<id>&scenario_id=<scenario_id>` returns a read-only event array without writing to storage. The default is `united-city-90`. Retired placeholder/short scenarios are not selectable public replays.
- The main fan and development matchday experiences use the shared `/api/matchdays` routes. All three fixture streams advance together in 30-second clock steps, through a 93-minute authored timeline. New matchday selects one of four versions independently per fixture; the fixed test hub preserves the chosen version.
- The owner-only single-replay `/api/replay/start` and `/api/matches/{id}/advance` routes remain available for CLI/integration use. Browser matchday cancellation and retries retain the last acknowledged tick; they do not authorize another session to advance an existing group.

## Review compatibility corrections

Fan briefings now include a `snapshot` (`match_id`, `through_sequence`, `since_sequence`, `match_second`) for optional narration. `GET /api/narration/status` returns configuration availability and allowed profiles without keys. `POST /api/narration` accepts the snapshot plus `language` (`en`/`es`) and `voice_profile` (`warm`/`matchday`), requires the owning replay session and returns bounded `audio/mpeg`. It rejects free-form text/SSML/URLs and snapshots omitting recorded events at their clock. `POST /api/narration/audition` accepts only language/profile and requires a session; it uses the fixed canonical synthetic 75:30 recap. Both cloud paths are disabled without backend Speech configuration. See [setup and limits](azure-narration.md).

Match Radar events can include optional `player_shirt_number`, `recipient_player_shirt_number`, `player_position`, `recipient_player_position` and `roster_version`. Shirt numbers come from the dated reference subset; positions are authored demo roles. Actor IDs such as `home-7` remain synthetic identifiers and must not be displayed as jersey numbers. `source` remains `synthetic`; these are not real player performances. The published JSON schema includes these additive fields; older events omit them or use null defaults.

The shared `fan_briefing` payload optionally includes `historical_precedent` (otherwise `null`). This is external, curated historical context with localized `text`/`caveat`, `source`, source revision/checksum, season and aggregate counts. It is not a synthetic match event, a story candidate, a prediction or part of `evidence_event_ids`. It appears only at an observed one-goal halftime lead. See [benchmark derivation](historical-precedents.md). Existing consumers may ignore this additive field.

Legacy event content and IDs are unchanged from the original fixture. New rules can add supported stories (four for the full legacy fixture); consumers must not assume exactly two. Progressive passes require both destination coordinates. If goals plus the strongest activity change exceed the eight-candidate Azure budget, the full deterministic briefing is returned with `candidate_budget_or_identity_failure`, with no provider call.
