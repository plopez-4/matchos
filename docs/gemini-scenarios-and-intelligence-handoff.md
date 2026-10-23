# Gemini handoff: richer MatchOS scenarios and evidence-backed stories

## Your assignment

Implement three selectable synthetic match scenarios and three new deterministic story rules. Integrate them into the existing browser replay controls, Match Story Graph, evidence inspection, and Casual/Advanced Catch Me Up. Deliver working code, meaningful tests, updated documentation, and a delivery report. Do not stop at a design proposal.

Read the actual repository before editing. This document describes the starting point; if files have changed, preserve newer work and explain any necessary adjustments.

## Project and workspace

- Product: **MatchOS — The AI Operating System for Live Football**.
- Goal: turn synthetic live football events into understandable, personalized match intelligence backed by inspectable evidence.
- Local repository: `C:\Users\lopez\.codex\.chatgpt-projects\g-p-6abc4d11ef2c819191fa6bba4f2af3de\matchos`.
- Public repository: <https://github.com/plopez-4/matchos>.
- Starting implementation branch: `feature/match-page-polish`, currently reviewed in PR #3. It stacks on `feature/grounded-ai-explanations` (PR #2), which stacks on PR #1.
- Workflow: `main` releases, `develop` integration, feature branches for changes. Follow `CONTRIBUTING.md` and applicable `AGENTS.md`.
- The parent directory is a ChatGPT project mirror. Files under its `sources/` directory are read-only reference material.
- There may be unrelated untracked files and user edits. Preserve them; do not stage everything blindly.

This is a Microsoft/Premier League hackathon entry. **All match events must be synthetic and football-realistic.** Do not fetch real match data. Sponsor participation does not establish permission to reuse their logos. The current UI contains sponsor/league marks whose permission has not been confirmed; do not add more official marks, claim endorsement, or describe permission as granted. Keep this assignment focused on simulation and intelligence.

## Current working system

Backend: Python 3.11+, FastAPI, Pydantic, single-process in-memory event storage.

Frontend: React 19, Vite 7, JSX/CSS, no TypeScript or state-library migration needed.

The app already has:

- Ordered, idempotent event ingestion with event/sequence conflict validation.
- Recorded pass, recovery, shot, and goal counts.
- Goal stories and comparison of recorded shots in completed five-minute windows.
- A derived graph of events, metric windows, stories, and `supports` edges.
- Catch Me Up with Casual/Advanced selection, sequence cursors, evidence links, and optional Azure story selection.
- Timeline filtering, navigation to otherwise-hidden evidence, scorer-colored GOAL animations, and responsive layout.
- Website replay controls: Start, Pause/Resume, 0.5×–4× speed, progress, Reset into a fresh match URL.
- A single shared 30-event fictional ten-minute fixture. Home wins 1–0; Home has five shots and Away two. The seed changes fictional player identities, not the storyline.
- Prettier configuration, formatting commands, and a CI formatting check.

Baseline validation before this assignment: **20 backend tests, 16 frontend tests, successful production build and formatting check**. Increase coverage for new behavior; do not replace existing tests to hide regressions.

### Important files

| File                                         | Responsibility                                                              |
| -------------------------------------------- | --------------------------------------------------------------------------- |
| `backend/app/models.py`                      | Authoritative event and Catch Me Up contracts                               |
| `backend/app/simulation.py`                  | Shared scenario and `generate(seed=7, count=30, match_id="demo-match")`     |
| `simulator/run.py`                           | CLI adapter importing the shared generator                                  |
| `backend/app/main.py`                        | API endpoints, store, ingestion, analytics, Catch Me Up                     |
| `backend/app/intelligence.py`                | Shot windows, match stories, support graph                                  |
| `backend/app/explanations.py`                | Azure selection/verification, deterministic fallback and audience rendering |
| `frontend/src/App.jsx`                       | Match URL, keyed dashboard remount/reset, Catch Me Up lifecycle             |
| `frontend/src/components/ReplayControls.jsx` | Playback controls and progress                                              |
| `frontend/src/utils/replay.js`               | Sequential cancellable playback loop                                        |
| `frontend/src/api.js`                        | Browser API calls                                                           |
| `frontend/src/hooks/useMatchData.js`         | Polling and rollback detection                                              |
| `frontend/src/components/StoryCard.jsx`      | Stories and evidence inspection                                             |
| `frontend/src/components/EvidenceGraph.jsx`  | Graph/pipeline view                                                         |
| `frontend/src/components/CatchUpPanel.jsx`   | Briefing sections and evidence                                              |
| `frontend/src/components/EventTimeline.jsx`  | Event filtering and selection                                               |
| `frontend/src/utils/catchUpState.js`         | Stale-response-safe Catch Me Up reducer                                     |
| `frontend/src/utils/teams.js`                | Team colors and scorer detection                                            |
| `backend/tests/`, `frontend/test/`           | Existing regression tests                                                   |
| `schemas/`                                   | Exported event schema and example                                           |

Read the explanation adapter carefully: `render`, `strongest_change`, candidate selection, required-story checks, and prompts currently make assumptions about `goal` and `shot_activity`. Adding new story kinds only in `intelligence.py` will leave them missing from some briefings.

## Milestone 1: scenario catalog and selector

Add these scenarios, plus retain the existing legacy fixture for compatibility:

1. **Pressure builds** (`pressure-builds`): repeated Home attacking sequences, progressive passes and high recoveries, increasing recorded shot activity, then a Home goal. Explain measurable activity; do not infer actual pressing effectiveness or possession dominance.
2. **Comeback** (`comeback`): Home scores first; Away later records stronger attacking activity and equalizes. Final score 1–1. Include valid goal-producing shot references and kickoffs after each goal. Keep the two goals separated enough in playback for both animations to be understandable.
3. **Quiet match** (`quiet-match`): mostly midfield circulation and recoveries, few shots, no goals. Final score 0–0. Keep qualifying high-recovery bursts and recovery-to-shot patterns below the story thresholds so the app demonstrates restraint rather than inventing drama.

Each fixture should cover at least 10:00 of recorded match time, start at kickoff, include a baseline event at 0:00 and an event at/after the last analysis-window boundary, and use sensible positional/possession continuity. Include routine events as well as highlights, but label the fixture honestly as a synthetic replay rather than a complete professional tracking feed.

Target roughly 30–50 events per new scenario so a fast-speed demonstration remains practical. Seeded generation must be reproducible. Player identities should remain stable within possessions; each goal must identify the same scorer as its linked shot. Possession changes and recovery locations must be plausible. Match clocks must never move backward, including when multiple events share a second.

### API and generator compatibility

- Keep the current `GET /api/replay/scenario?match_id=<id>` array response and default legacy behavior compatible.
- Add an optional `scenario_id` parameter to that endpoint; validate it against the catalog, with a useful error for unknown scenarios.
- Add `GET /api/replay/scenarios` returning public metadata: stable ID, name, spoiler-free description, event count, duration in match seconds, and scenario version. Do not reveal the final score in the selector.
- Extend the shared generator and CLI with scenario selection. Preserve legacy positional calls and the default 30-event fixture relied on by existing tests.
- New scenarios may have different lengths. Avoid assuming every fixture contains 30 events or rejecting counts above 30 when a chosen fixture supports them. Document count defaults/limits explicitly.
- Include scenario/version/seed in new fixture event IDs so replaying a different fixture cannot silently reuse IDs for different content. Preserve legacy IDs for the legacy default.
- Selecting/downloading a fixture must be read-only. Events must still enter through existing `/api/events` validation; do not bypass it or write a complete match on selection.

### Frontend behavior

- Put an accessible **Scenario** selector beside the existing replay controls with a short description and actual event count.
- Selecting another scenario must stop the old playback and open a fresh match ID; it must not append a different scenario to an existing match.
- Preserve the selected scenario through Reset and Start new replay. Persist the scenario in the URL so reload/share retains the selection; validate URL input and use a documented fallback for invalid values.
- Keep Start, Pause/Resume, speed, and progress functional. Progress maximum must come from the selected fixture, with a loading state while metadata/events load.
- Reset remounts match-specific state: score baseline/goal animation queue, Catch Me Up cursor and pending requests, evidence selection, event list, and replay progress.
- Changing speed or resuming must continue from the last acknowledged event. Cancellation may leave one already-received event on the server; rely on existing idempotent retry and never silently skip it.
- A failed request must show a useful error and allow retry without losing progress. Rapid scenario changes must ignore stale downloads and playback completions.
- Do not require a simulator terminal for ordinary website use. Preserve CLI replay for developers.
- Match polling can briefly lag playback progress. Do not fabricate events or statistics to conceal that delay.

## Milestone 2: three deterministic analytics and story rules

Use the existing schema 1.1 fields. Pitch positions are normalized 0–100: Home attacks toward x=100; Away toward x=0. These fixtures use period 1. Do not claim second-half direction support without defining and testing it.

Rules should use named constants, stable rule versions, stable story IDs, structured metrics, and ordered supporting event IDs. Every displayed factual statement must be derivable from those metrics and events. Prefer explicit measured language.

### A. High recovery activity — `high-recovery-v1`

- Home qualifies at `x >= 70`; Away qualifies at `x <= 30`.
- Count recovery events in completed five-minute windows `[start, end)`.
- Emit a story when at least **3 qualifying recoveries** occur for one team in a completed window.
- Use the first observed event at/after the window end as the story's trigger sequence so Catch Me Up can announce it when verified, not retrospectively pretend it was known sooner.
- Example: “Home recovered the ball 3 times in the attacking third in minutes 5–10.”
- Evidence: exactly the qualifying recovery event IDs; metric: team, bounds, count, qualifying location definition.
- Do not call this measured possession, pressure intensity, successful pressing, or proof that a goal was caused by pressing.

### B. Progressive passing — `progressive-pass-v1`

- Require `type == pass`, `outcome == complete`, and both end coordinates.
- Home forward gain is `end_x - x`; Away gain is `x - end_x`.
- A pass qualifies at **at least 15 normalized pitch-length units of forward gain**. This is a documented MatchOS proxy, not metres or an official provider definition.
- Count in completed five-minute windows; emit a story at **3 or more qualifying passes** for a team.
- Example: “Away completed 4 forward passes gaining at least 15 pitch units each in minutes 5–10.”
- Evidence: exactly qualifying passes. Exclude incomplete outcomes, backward passes, and missing destinations. Include threshold boundary tests for both teams.

### C. Recovery-to-shot sequences — `recovery-shot-v1`

- Identify a recovery followed by a shot by the same team, in the same non-null possession and period, within **30 recorded match seconds**.
- Require the recovery and shot to be in correct sequence order, with no intervening opposing-team event or possession change that breaks the chain.
- Use the nearest valid preceding recovery so one shot produces at most one such story. Do not reuse a superseded recovery to inflate counts.
- Example: “Home recorded a shot 18 seconds after recovering the ball in the same possession.”
- Evidence: the ordered chain from the recovery through the shot, including intervening same-possession passes. Trigger sequence: the shot's sequence.
- A goal may link to this chain through its existing shot reference, but do not count the goal as a second shot or state that the recovery caused the goal.
- Missing possession, broken chains, negative time gaps, wrong team, and gaps above 30 seconds must not qualify.

### Window/history requirements

Preserve existing `shot-frequency-v1` semantics. Decide and document whether new window stories retain all completed-window results; prefer retaining them so earlier verified stories do not disappear when a later window closes. Never duplicate an identical story on polling. Analyze only observed completed windows, with feed coverage of their baseline; a sparse feed cannot prove the absence of unrecorded actions.

## Milestone 3: integrate the new facts everywhere

- Expose the new analytics in a clearly documented additive API structure without breaking current team counts or shot-window consumers.
- Render readable names, badges, metric explanations, and evidence drawers for each new kind. Do not fall back to labels implying every non-goal story is a shot comparison.
- Generalize graph building to connect event evidence to new stories and metric windows. IDs must be unique; all edge endpoints must exist; edges remain `supports`, not causal claims.
- Update Casual/Advanced deterministic rendering and Azure story-selection/verification so the new story kinds appear when warranted.
- Preserve all relevant score-change stories within documented candidate limits. Define selection priorities explicitly so the new rules do not displace goals or flood the briefing with near-duplicate statements.
- Candidate bounding is currently the last eight stories. Handle goals outside that slice deliberately; do not claim all match goals are guaranteed if selection truncation can remove them.
- Casual explains the observed change plainly. Advanced includes the threshold, window/elapsed time, count, and evidence. Both audiences must use the same verified facts.
- Quiet-match output should say there are no qualifying new patterns when appropriate. Never manufacture momentum, possession percentages, xG, tactics, or players from missing data.
- “Who to watch” is optional after the core milestone: if implemented, rank real synthetic player IDs from observed qualifying contributions, cite supporting events, and say this reflects recorded activity. Do not predict who will score or invent real player names.
- Keep Azure optional. Tests and the full demo must work without credentials using deterministic fallback. Do not read, print, commit, or share secrets.

## Acceptance criteria and tests

Write tests for meaningful outcomes and failure cases, using the production rules/playback logic.

1. Each scenario is reproducible for a fixed seed, conforms to `MatchEvent` and exported JSON Schema, and ingests in order without validation errors.
2. Pressure builds ends Home 1–0 and produces intended activity stories. Comeback ends 1–1 with two valid goal references and Away activity. Quiet match ends 0–0 and does not emit high-recovery or recovery-shot drama stories.
3. Legacy generator calls, CLI behavior, original fixture totals, existing APIs and existing tests still pass.
4. Scenario catalog is consistent with generated counts/durations. Invalid IDs and counts are rejected clearly.
5. Rules cover both attacking directions, exact location/gain/time thresholds, five-minute boundaries, missing fields, broken possession chains, and duplicate prevention.
6. Every story's evidence exists in that match; graph IDs are unique and all edges resolve. Trigger sequences allow a correct incremental Catch Me Up cursor.
7. Casual/Advanced render new story kinds correctly. Azure mocked tests reject fabricated IDs/invalid selections and retain deterministic fallback on failure.
8. Browser-test all three scenarios: select, start, pause, resume, speed change, finish, reset and select another scenario mid-playback. Old requests must not update the new match.
9. Confirm existing timeline evidence navigation, Catch Me Up reset/error handling, and both goal takeover colors still work.
10. Verify desktop and 375px mobile controls: labels, keyboard interaction, readable wrapping, no horizontal overflow, reduced-motion behavior.
11. Run the existing Prettier check, frontend tests, production build and backend suite. Report real results and limitations; do not claim hosted CI or browser checks you did not perform.

## Running and checking on Windows

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Run the frontend in a second terminal:

```powershell
npm.cmd --prefix frontend run dev -- --port 5174
```

Open the frontend's printed Local URL. If a server is already running, reuse it. Do not kill unrelated processes or start duplicate listeners. The default proxy expects backend port 8000.

Checks from repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
npm.cmd --prefix frontend run format
npm.cmd --prefix frontend run format:check
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
```

If event fields change, run `scripts/export_schema.py` and inspect the generated schema; prefer avoiding a schema change for this milestone. Do not assume a new schema version is needed for additive analytics/story output.

## Scope and delivery

Preserve the current design, fonts, kit colors, replay lifecycle and evidence-first architecture. Do not replace frameworks, redesign the whole page, add a database/authentication system, deploy resources, incur Azure charges for testing, or add model-generated factual narration as part of this task.

Update `README.md`, `CHANGELOG.md`, `docs/api.md`, `docs/architecture.md`, and relevant product/demo instructions. Include exact metric definitions, scenario selection/CLI usage, browser-owned playback limitations, and the unchanged synthetic-data requirement.

Create `docs/scenarios-and-intelligence-delivery.md` containing:

- Implemented scenarios and expected final scores/event counts.
- Rule definitions, versions, thresholds, trigger sequences, and sample evidence-backed output.
- Files changed, API additions, backward-compatibility choices.
- Actual test/build/format results and browser checks, with screenshots where useful.
- Any limitations, incomplete requirements, and exact review/demo steps.

Keep the changes isolated and reviewable. Inspect Git status before editing/staging and preserve other work. If the human authorizes publication, use a feature branch/PR based on the current prerequisite branch and report its link; do not merge into `main` or `develop`, force-push, or imply the work is published when it exists only locally. Do not email organizers or teammates as part of this assignment.

Recommended implementation order: inspect current code → shared scenario catalog/fixtures → API and CLI compatibility → selector and reset lifecycle → deterministic rules → graph/briefing integration → tests and browser checks → docs and delivery report.
