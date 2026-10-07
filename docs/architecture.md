# Architecture

## Flow

Synthetic simulator → FastAPI validation → event repository → deterministic analytics → story graph → evidence verifier/explanation service → React.

Today: in-memory repository, count and completed-window shot analytics, goal/activity stories, derived support graph, deterministic Catch Me Up and two-second frontend polling. These are replaceable foundations, not a complete tactical engine.

## Target responsibilities

- Ingestion: version/source validation, event ID deduplication and sequence conflicts. Ordered append is currently required; reject new events below the match cursor.
- Repository: PostgreSQL with unique (match_id,event_id) and (match_id,sequence), migrations and durable graph storage. Add a repository interface before persistence.
- Analytics: pure functions over ordered events, explicit windows/units/sample thresholds and versioned rules. Possession requires control/time data; progressive passes require end coordinates and attack direction. Current schema cannot support those metrics.
- Match Story Graph: typed event, metric-window and story nodes; supports and preceded-by edges. Store evidence IDs and rule versions. Temporal association is not causation.
- AI: supplied facts → evidence verification → audience-aware phrasing → structured output validation. Reject unknown IDs/unsupported claims and fall back to deterministic text on failure. Store model/prompt version and latency.
- Viewer: per-match cursor and preferences; starter cursor lives only in React memory and resets on reload.

## Event semantics

sequence is unique ordering within a match, not an arrival timestamp. match_second is elapsed match clock including stoppage; period distinguishes halves. New arrivals cannot move the clock backwards. x/y and optional end_x/end_y are 0..100 stadium coordinates; the scripted scenario assumes Home attacks x=100 and Away x=0. This assumption is not generalized into provider analytics. Goals are separate events linked to goal-producing shots; shot counts count only shot events. If future provider feeds allow late arrivals, replace sequence catch-up with an ingestion cursor before accepting them.

The simulator is a sparse, plausible highlights fixture rather than a full touch-by-touch match model. The seed varies fictional team-specific players; timing/action structure stays fixed for reproducible expected metrics. Graphs are derived snapshots: historical pattern persistence, fuller spatial/possession simulation and provider normalization remain upcoming work.

## Deployment limits

Data resets on restart. Use one process/worker; no shared storage, auth, pagination, rate limits or public deployment hardening yet. Keep provider/AI credentials on the server. Production adds durable storage, authenticated ingestion and bounded queries before exposure.

## Implemented frontend and AI path

The Azure model retrieves trusted story candidates, selects IDs, and the backend validates the selection before rendering factual audience wording. This is not free-form narration or hosted Agent Service orchestration. The UI separates story sections, evidence, actual audience/mode and trace. A generation-aware catch-up reducer and abortable requests preserve failure/reset behavior.

All reads and Catch Me Up use demo-match or a validated ?match=<id> query. Fresh simulator IDs allow replay without restarting the Azure-enabled process. Viewer cursors remain in React memory. Goal takeovers compare analytics snapshots and use shared kit colors; first-load baselines, unchanged polls and rollback do not create new goals. Current graph edges are supports only; preceded-by remains a future idea. Coordinates are normalized 0..100, not measured metres.

## Browser-controlled replay

The shared fixture lives in `backend/app/simulation.py`; `simulator/run.py` reuses it for CLI compatibility. A read-only FastAPI scenario endpoint supplies events to the browser. A cancellable sequential playback loop submits each event to the existing ingestion endpoint, retaining the last acknowledged cursor for retries. React remounts match-specific state on a fresh-session reset, clearing summaries, timeline highlights and score celebrations. Playback requires an open page and stores no background job.
