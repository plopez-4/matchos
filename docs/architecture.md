# Architecture

## Flow

Synthetic simulator → FastAPI validation → event repository → deterministic analytics → story graph → evidence verifier/explanation service → React.

Today: in-memory repository, count and completed-window shot analytics, high recovery analytics, progressive pass analytics, recovery-to-shot sequences, derived support graph with metric-window nodes, deterministic Catch Me Up (casual and advanced audiences), optional Azure OpenAI story selection, and two-second frontend polling. These are reproducible foundations, not a full commercial tactical engine.

## Target responsibilities

- Ingestion: version/source validation, event ID deduplication and sequence conflicts. Schema v1.1 supports optional possession_id, end coordinates (end_x, end_y), outcome, and related_event_id. Ordered append is currently required; reject new events below the match cursor.
- Repository: PostgreSQL with unique (match_id,event_id) and (match_id,sequence), migrations and durable graph storage. Add a repository interface before persistence.
- Analytics: pure functions over ordered events, explicit windows/units/sample thresholds and versioned rules.
  - `shot-frequency-v1`: completed five-minute windows $[start, end)$, threshold $\ge 3$ shots, shift $\ge 2$ shots vs. prior window.
  - `high-recovery-v1`: completed five-minute windows $[start, end)$, recoveries in opponent's defensive third (Home $x \ge 70$, Away $x \le 30$), threshold $\ge 3$ recoveries.
  - `progressive-pass-v1`: completed five-minute windows $[start, end)$, forward gain $\ge 15.0$ normalized units towards opponent's goal line ($end\_x - x \ge 15$ for Home, $x - end\_x \ge 15$ for Away), threshold $\ge 3$ passes.
  - `recovery-shot-v1`: recovery followed by shot by same team in same non-null possession and period within $\le 30$ recorded match seconds without opposition interruption.
- Match Story Graph: typed `event`, `metric_window`, and `story` nodes; `supports` edges connecting events to metric windows and metric windows/events to stories. Store evidence IDs and rule versions. Temporal association is evidentiary support, not tactical causation.
- AI: supplied facts → evidence verification → audience-aware phrasing → structured output validation. Reject unknown IDs/unsupported claims and fall back to deterministic text on failure. Store model/prompt version and latency.
- Viewer: per-match cursor and preferences; starter cursor lives only in React memory and resets on reload.

## Event semantics

sequence is unique ordering within a match, not an arrival timestamp. match_second is elapsed match clock including stoppage; period distinguishes halves. New arrivals cannot move the clock backwards. x/y and optional end_x/end_y are 0..100 stadium coordinates; the scripted scenarios assume Home attacks x=100 and Away x=0. Goals are separate events linked to goal-producing shots; shot counts count only shot events. If future provider feeds allow late arrivals, replace sequence catch-up with an ingestion cursor before accepting them.

The simulator provides sparse, plausible highlights fixtures across multiple selectable scenarios rather than a full touch-by-touch match model. The seed varies fictional team-specific players; timing/action structure stays fixed for reproducible expected metrics. Graphs are derived snapshots: historical pattern persistence, fuller spatial/possession simulation and provider normalization remain upcoming work.

## Deployment limits

Data resets on restart. Use one process/worker. Replay writes have session ownership, arbitrary ingestion requires a backend token, and requests/storage/provider use are bounded. Production mode requires HTTPS, serves the built frontend and sets security headers. There is no shared durable storage or account system. See [security setup](security.md) for limits and deployment verification.

## Implemented frontend and AI path

The Azure model retrieves trusted story candidates, selects IDs, and the backend validates the selection before rendering factual audience wording. This is not free-form narration or hosted Agent Service orchestration. The UI separates story sections, evidence, actual audience/mode and trace. A generation-aware catch-up reducer and abortable requests preserve failure/reset behavior.

All reads and Catch Me Up use demo-match or a validated ?match=<id> query. Fresh simulator IDs allow replay without restarting the Azure-enabled process. Viewer cursors remain in React memory. Goal takeovers compare analytics snapshots and use shared kit colors; first-load baselines, unchanged polls and rollback do not create new goals. Current graph edges are supports only; preceded-by remains a future idea. Coordinates are normalized 0..100, not measured metres.

## Browser-controlled replay and scenario catalog

The scenario catalog lives in `backend/app/simulation.py`; `simulator/run.py` reuses it via `--scenario` CLI parameter. Available scenarios:

- `pressure-builds`: Home attacking momentum with high recoveries and progressive passes culminating in a late 1–0 goal (33 events).
- `comeback`: Early Home goal followed by Away defensive recoveries, rapid counter-attack transition shot, and equalizer (34 events, 1–1).
- `quiet-match`: Midfield restraint demonstrating that Catch Me Up reports no false momentum when thresholds are unmet (30 events, 0–0).
- `legacy-default`: Preserved baseline 10-minute fixture for backward compatibility (30 events, 1–0).

The read-only catalog/fixture endpoints remain available. Browser playback establishes an HttpOnly cookie session and uses `POST /api/replay/start` to allocate a bounded replay. The cancellable playback loop sends only a sequence to `POST /api/matches/{id}/advance`; the backend ingests its own canonical event after verifying ownership and order. The client retains the last acknowledged cursor for retries. React remounts match-specific state on reset, clearing summaries, timeline highlights and score celebrations while preserving the chosen scenario. Playback requires an open page and stores no background job. Read access to synthetic matches remains public by design.
