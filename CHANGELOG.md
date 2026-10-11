# Patch notes

## 2026-10-11 — Fix GitHub dependency audit

- Upgrade GitHub's preinstalled setuptools to 83.0.0 and require at least that version for isolated backend builds. The failed dependency audit identified vulnerable setuptools 79.0.1 on the runner; application tests and the frontend job passed. The vulnerability audit stays enabled.

## 2026-10-11 — Matchday, Match Radar and briefing improvements

- Fixed partial matchday cleanup and aligned early-window metadata with inclusion of events at second zero.
- Reset now clears the local view after a failed release, displays a warning, and retries pending cleanup before creating another replay. Cleanup requests have a ten-second deadline.
- Compacted repeated progressive-pass windows and recovery-to-shot sequences while preserving all selected story/event IDs and every goal; separated time ranges stay explicit.
- Added three concurrent 93-minute authored synthetic highlight feeds on one server-owned clock, with prominent, overlooked and quiet test fixtures.
- Added observed-event-only Radar scoring, qualification, deterministic ranking, inspectable shot/goal evidence and a simple shots comparator for evaluation.
- Added transition-based in-page Heating Up notices with idempotent IDs/cooldowns, quiet/cooling/full-time suppression and one-click selected-match Catch Me Up.
- Added Matchday & Radar navigation, shared start/pause/resume/speed/reset controls and owner-only capacity release. Existing security limits remain enforced and individual clocks cannot bypass the matchday clock.
- Added regression tests and a Gemini/Antigravity review handoff. Antigravity's findings were reviewed against the code, with cleanup, metadata, reset recovery and briefing compaction follow-ups applied. No engagement uplift or real-video viewing claims are made.
- Validation: 78 backend tests and 25 frontend tests passed, along with the production build, Prettier check, whitespace check and heuristic secret scan.

## 2026-10-11 — Security baseline

- Replaced browser-submitted event facts with server-owned replay start/advance operations and private session cookies. Replay writes require ownership; arbitrary ingestion requires a private backend credential and is disabled by default.
- Added request/body limits, fixed session/match expiry, bounded storage, event caps, and ordered/idempotent replay advancement.
- Added bounded catch-up caching, busy-request rejection, an Azure request budget, provider payload/output limits, and deterministic fallback when limits are reached.
- Added production HTTPS/host/origin checks, secure cookies, security headers, hidden API docs, and serving of the built frontend from the API origin.
- Updated pip, pinned resolved backend dependencies, and added CI secret-pattern/dependency checks with scheduled checks. Added security regressions alongside existing replay tests.
- Public synthetic match reads remain intentional. This is a single-worker bounded demo; deployment and cloud account settings still require verification before public launch.

## Unreleased — Full-match synthetic scenarios

- Added United vs City and United vs Hull authored feeds: two halves, 90 minutes plus three added minutes, fictional rosters and over 1,200 modeled events per match.
- Added schema 1.2 with player names, intended pass recipients, intercepted passes, substitutions and halftime/full-time markers. Original fixtures remain compatible.
- Added reproducible JSONL exports and provenance manifest under `data/synthetic/`.
- Added readable, evidence-linked rule-based match briefings, including named scorers and substitutions; no model training is performed.
- Added full-match replay speeds and scenario team names/kit colors. Timeline shows sender and recipient.
- Added continuity, roster, ingestion, schema and narrative regression coverage. See [data documentation](docs/full-match-data.md) for scope and realism limits.

## Unreleased — Richer scenarios and evidence-backed stories

Implemented on `feature/richer-scenarios-and-stories`, with reviewed fixes on `fix/scenario-review`; GitHub publication has not been verified.

### Added

- Three selectable synthetic match scenarios (`pressure-builds`, `comeback`, `quiet-match`) and retained `legacy-default` fixture.
- Public scenario catalog endpoint `GET /api/replay/scenarios` returning stable ID, name, spoiler-free description, event count, duration in match seconds, and scenario version.
- Replay scenario endpoint parameter `scenario_id` on `GET /api/replay/scenario` with input validation and 404 handling.
- Three deterministic story rules backed by inspectable evidence:
  - `high-recovery-v1`: counts recoveries in completed 5-minute windows in the attacking third (Home `x >= 70`, Away `x <= 30`, threshold $\ge 3$).
  - `progressive-pass-v1`: counts completed forward passes gaining $\ge 15$ normalized pitch units in completed 5-minute windows (threshold $\ge 3$).
  - `recovery-shot-v1`: identifies same-possession recoveries leading to a shot within 30 seconds without opposing interventions.
- Additive analytics structure in `GET /api/matches/{match_id}/analytics` exposing `high_recoveries`, `progressive_passes`, and `recovery_shots`.
- Accessible browser scenario selector beside replay controls with live URL state persistence (`?scenario=<id>`) and clean reset lifecycle.
- Visual story badges, borders, and icons for all story kinds: `badge-recovery`, `badge-pass`, `badge-transition`.
- Evidence graph nodes for metric windows and support edges for all new story kinds with unique IDs and verified edge endpoints.
- Expanded Casual and Advanced Catch Me Up deterministic rendering and candidate-bounded Azure story selection.
- Simulator CLI `--scenario` flag supporting all catalog fixtures with automatic count defaults.

### Improved

- Restraint in quiet matches: displays clear explanation when no qualifying patterns or goals occur, without inventing drama.
- Candidate selection bounding: protects goal stories and strongest verified activity changes up to an 8-story candidate window.
- Test coverage expanded to 30 backend tests and 19 frontend tests covering boundary conditions, directions, and edge cases.

- Website replay controls: start, pause/resume, 0.5ז4� speed, progress and fresh-session reset. Browser and CLI share the same scenario; normal event validation remains in force.

- Pinned Prettier formatter, shared repository style configuration, formatting commands and an automated CI formatting check.

- Modular responsive match dashboard, recorded-stat strip, timeline filters and evidence inspection.
- Premier League-inspired purple/white theme, league artwork, credited Goodison Park photo and Microsoft Azure technology attribution.
- Optimized the stadium photograph to a 960px WebP (about 172 KB) for faster delivery.
- Locally bundled Manrope and Bebas Neue fonts with their license files.
- Shared fictional white/red kit colors for scores, statistics, shot bars and timeline labels.
- Six-second scorer-colored GOAL scoreboard takeover, polite goal announcement and reduced-motion behavior.
- Fresh replay sessions using `?match=<id>` and simulator `--match-id`, preserving the running Azure backend.
- Graph/pipeline inspection, actual response-audience labels and readable Azure selection/verification trace.
- Desktop/mobile screenshots, frontend handoff, delivery/recheck report and visual asset credits.

### Improved

- Catch Me Up displays What happened and What changed with evidence instead of repeating the joined summary.
- Shot comparison bars use recorded counts and labeled completed five-minute windows.
- Frontend tests exercise production catch-up state, scorer detection and timeline-selection functions.
- CI runs frontend tests and covers stacked feature-branch pull requests.
- README, API, architecture, product, contribution, milestone and submission docs describe the working implementation.

### Fixed

- Restored exact legacy replay evidence/IDs, required both pass destination coordinates, enabled scenario switching during playback, and preserved all goals through deterministic fallback when Azure candidate limits overflow. Added review regressions and corrected delivery claims.

- Catch Me Up stuck loading after a detected backend reset; aborts and generation checks isolate stale requests.
- Valid summaries disappearing when newer than the latest polling snapshot.
- Catch-up failures losing the prior cursor/result or being erased by successful polling.
- Evidence navigation to events hidden by filters or the initial 12-event limit.
- Repeated scrolling on each poll; reduced-motion navigation uses immediate scrolling.
- In-flight polling updating state after cleanup.
- Mobile grid overflow and squeezed card headings.
- Demo sequence trying to inspect an Azure trace after an empty check replaced it; removed the absolute hallucination-elimination claim.

### Validation and known limits

18 backend tests, 12 frontend tests and the production build passed locally. Browser checks verified live Azure Casual/Advanced results, an empty check, hidden evidence navigation, asset loading, team colors, mobile layout and a red-team takeover in an isolated synthetic test. White-team detection and reset/queue behavior are regression-tested.

The main replay remains 30 fictional events and Home 1–0 Away. No real Premier League match data or AI credentials were added. Single-process memory storage, sparse highlights, derived graph snapshots and unverified public deployment remain limitations. Sequence-only reset detection can miss a restart/full replay if no lower sequence is observed. Counts cannot reconstruct exact cross-team goal order within one polling interval. Full browser fault injection and screen-reader audits remain future checks. Asset terms are separate from MIT application code.

## Earlier foundation

FastAPI ingestion, Pydantic/JSON Schema contract, seeded replay, deterministic counts/windows, evidence-backed goal/activity stories, support graph, and optional Azure tool-based story selection with deterministic fallback were established in PRs #1 and #2.
