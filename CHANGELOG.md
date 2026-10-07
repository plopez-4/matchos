# Patch notes

## Unreleased — 7 October 2026

Published for review on `feature/match-page-polish`; not a tagged release on `main`.

### Added

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
