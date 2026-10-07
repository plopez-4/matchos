# MatchOS: complete Gemini frontend handoff

Prepared 7 October 2026. This is a practical implementation brief for the frontend teammate's work. Repository state can change: inspect the actual checkout before editing.

## Instructions to Gemini

You are helping build **MatchOS — The AI Operating System for Live Football** for a Microsoft/Premier League developer hackathon. Act as the frontend engineer. Read this entire brief, inspect the existing repository, and implement the prioritized work below using the functioning backend. Deliver working code, validation results, and a clear reviewable diff. Do not stop at design suggestions if your environment can edit files.

The owner already has a working simulator, backend, evidence-backed stories, and Azure-assisted Catch Me Up. Your responsibility is to make that working product clear, attractive, responsive, and reliable. Preserve the API contracts and existing facts. Do not replace the application with a static mockup or rebuild the backend.

If you cannot access the repository or run commands, say exactly what access is missing, then provide complete file changes or patches the owner can apply. Never claim you ran tests or connected Azure unless you actually did. Ask questions only when a missing answer prevents useful work; otherwise make reasonable frontend decisions and explain them.

## 1. Product and problem

Fans joining a match late need more than a score. They need to understand what happened, what changed, and which evidence supports that explanation. MatchOS turns synthetic football events into deterministic analytics, connected match stories, and personalized explanations.

The intended pipeline is:

```text
Synthetic simulator -> validated event ingestion -> deterministic analytics
                    -> Match Story Graph -> verified story selection
                    -> Catch Me Up -> React fan experience
```

The full vision includes live event ingestion, deterministic analytics, Match Story Graph, evidence-backed AI explanations, Catch Me Up, and personalization. The current MVP implements a narrow, functioning slice of that vision. Do not present planned capabilities as already built.

### Hackathon constraints supplied by the owner

- Use synthetic, football-realistic data. No real Premier League match data is provided or used.
- The submission needs a public GitHub repository, a short project pitch identifying Microsoft/Azure technologies, and a public demonstration video **under two minutes**.
- The video must show the working product. Avoid third-party trademarks, copyrighted music, or other materials without permission. Use original fictional team branding.
- Judging is equally weighted across technological implementation, agentic design/innovation, real-world impact, UX/presentation, and category adherence.
- Full challenge-specific technology requirements and deadlines still need confirmation; do not invent them.

## 2. Repository and current baseline

- Public repository: <https://github.com/plopez-4/matchos>
- Latest working feature branch when this brief was written: `feature/grounded-ai-explanations`.
- Reference commit: `e4873e8175d363c1ac98c89af087b5ec699bc0f9`.
- Local repository on the owner's computer:
  `C:\Users\lopez\.codex\.chatgpt-projects\g-p-6abc4d11ef2c819191fa6bba4f2af3de\matchos`
- Do not edit synced files under the parent workspace's `sources/` directory. Read applicable `AGENTS.md` instructions.
- PR 1: <https://github.com/plopez-4/matchos/pull/1>, evidence-backed stories, targets `develop`.
- PR 2: <https://github.com/plopez-4/matchos/pull/2>, Azure-backed Catch Me Up, currently stacked on PR 1's feature branch.

Those PRs were open when this brief was prepared. Verify their current state. **Do not start from an older `main`/`develop` checkout that lacks the working features.** Start from the latest working feature branch unless these changes have since been integrated into `develop`.

Create `feature/match-page-polish` for this frontend work. If working in the owner's existing checkout, inspect uncommitted changes first and preserve them. Never hard-reset, overwrite another person's work, or merge/retarget existing PRs as part of UI polishing.

### Current stack

| Area | Existing implementation |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Pydantic |
| Storage | In-memory, one backend process |
| Frontend | React 19, Vite 7, JSX, plain CSS |
| Simulator | Seeded Python synthetic scenario |
| AI | Azure-hosted `gpt-4.1-mini`, deployment `matchos-explainer` |
| Transport | HTTP APIs, frontend polling about every two seconds |

Keep this stack. A framework migration, database, authentication, hosted agents, or new deployment infrastructure is outside this assignment.

### Files to inspect first

```text
README.md                         Product overview and startup instructions
CONTRIBUTING.md                   Collaboration workflow
frontend/src/main.jsx            Current app, API calls, polling and Catch Me Up
frontend/src/styles.css           Current dark interface
frontend/package.json             Scripts and dependencies
frontend/vite.config.js           Development /api proxy
backend/app/main.py              Endpoint implementations
backend/app/models.py            Authoritative validation contract
backend/app/intelligence.py      Counts, stories, graph, catch-up facts
backend/app/explanations.py      Azure selection and verified rendering
backend/tests/                   Existing regression tests
simulator/run.py                 Known synthetic replay
schemas/match-event.schema.json  Exported event schema
docs/api.md                      API notes
docs/architecture.md             Architecture and planned work
docs/product.md                  Product scope
docs/azure-ai.md                 Existing Azure integration
docs/hackathon-submission.md     Submission checklist
```

At the last validation, all 18 backend tests passed, the frontend production build passed, and live Azure Catch Me Up worked for both casual and advanced audiences. This is historical evidence, not permission to claim your own changes are tested without checking them.

## 3. What actually works today

1. The simulator posts 30 fictional events spanning ten minutes of match time.
2. The backend validates event IDs, sequence order, match clock and goal-to-shot references.
3. Deterministic rules count recorded passes, shots, goals and recoveries.
4. Goal stories link a goal to its supporting events.
5. A shot-activity rule compares two completed five-minute windows and creates an evidence-backed story when recorded attempts rise sufficiently.
6. The derived Match Story Graph connects events, metric windows and stories with `supports` edges.
7. Catch Me Up uses a sequence cursor to summarize events the viewer has not checked yet.
8. Azure can select verified candidate story IDs through tool calls. The server validates the selection and renders trusted factual text.
9. Casual and advanced audiences receive different wording while retaining the same supporting evidence.
10. If Azure is disabled, misconfigured or fails validation, deterministic summaries still work.

**AI honesty:** this is Azure-assisted selection of verified stories, not unrestricted generated commentary. The current runtime is not a hosted Foundry agent or a multi-agent system. Those are future possibilities, not claims to put in the interface.

### Known replay, seed 7

| Fact | Expected result after all 30 events |
| --- | --- |
| Match ID | `demo-match` |
| Latest recorded clock | `10:00`, period 1 |
| Score | Home 1–0 Away |
| Recorded shots, whole replay | Home 5, Away 2 |
| Goal | Home at `9:31`, sequence 22 |
| Supporting shot | Home at `9:30`, sequence 21 |
| Home shots in minutes 0–5 | 1 |
| Home shots in minutes 5–10 | 4 |
| Stories | Goal and increased home shot activity |

Seed changes fictional player identities, not this storyline. This is a sparse highlights feed: counts refer to **recorded events**, not exhaustive real-match statistics. Increased shots do not prove possession, pressure, dominance, or causation. Do not add fake possession percentages, win probabilities, xG, heatmaps or momentum meters.

## 4. Run the existing app

Use three terminals, all starting in the repository root. On Windows use PowerShell. Do not run setup from `C:\Windows\system32`.

### Obtain an independent checkout, if needed

```powershell
git clone --branch feature/grounded-ai-explanations https://github.com/plopez-4/matchos.git
cd matchos
git switch -c feature/match-page-polish
```

If those features have been merged, use the current integrated branch instead. If already in the owner's checkout, inspect `git status` and branch history before switching.

### Terminal 1: backend

Fresh machines need Git, Python 3.11+ and Node.js compatible with Vite 7 (Node 22.12+ is a suitable baseline). If `py` is unavailable, use the installed Python executable; do not assume the command `python` exists.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e "./backend[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

On an existing setup, reuse `.venv` and skip creating it. Calling its Python executable avoids requiring PowerShell activation.

Backend: <http://127.0.0.1:8000/docs>. Health: <http://127.0.0.1:8000/api/health>.

### Terminal 2: frontend

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open the URL Vite prints, normally <http://127.0.0.1:5173>. Requests to `/api` are proxied to the backend. Keep the existing `--configLoader native` script option; it supports the current Windows setup.

### Terminal 3: simulator, from the repository root

```powershell
.\.venv\Scripts\python.exe simulator/run.py --seed 7 --count 30 --interval 0.5 --api http://127.0.0.1:8000
```

The replay ends after 30 events; it is not an endless live match. Replaying identical events is idempotent and will not create a fresh feed. To replay from an empty state, restart the backend, then run the simulator again. Restarting clears all events because storage is in memory. Do not change seed on an already populated match: its sequence numbers would conflict.

### Azure and secrets

Frontend development does not require an Azure account or a key. A fresh clone can use deterministic mode. The owner has already configured a working Azure deployment in their backend environment.

- Actual deployment name: **`matchos-explainer`**, with the hyphen.
- AI credentials belong only in the backend environment. Never put them in React, `VITE_*` variables, screenshots, logs, commits or this document.
- Do not request that the owner paste keys into Gemini. Do not inspect secret files or print environment variables to diagnose UI issues.
- Follow `docs/azure-ai.md` if integration details are relevant. A Foundry project URL ending `/api/projects/matchos` is not the OpenAI inference base URL.
- A working backend can be left running while you change frontend files. Avoid unnecessary backend restarts during a demo.
- Only show an Azure-selected label when the response explicitly says `explanation.mode === "azure"`.

## 5. API contract for the frontend

All routes below start with `/api`. Use the existing development proxy and relative URLs. Backend source and `/docs` are authoritative if this brief and code differ. Inspect successful responses before introducing assumptions.

| Method | Route | Use |
| --- | --- | --- |
| GET | `/health` | Process status; reports in-memory storage |
| GET | `/matches/demo-match/events` | Ordered event array |
| GET | `/matches/demo-match/analytics` | Recorded team counts and shot windows |
| GET | `/matches/demo-match/stories` | Evidence-backed story array |
| GET | `/matches/demo-match/graph` | Derived graph, optional UI enhancement |
| POST | `/matches/demo-match/catch-up` | Viewer summary since a sequence cursor |
| POST | `/events` | Simulator ingestion; frontend does not need to create events |

### Event

Required fields include `event_id`, `match_id`, `sequence`, `match_second`, `team_id`, `player_id`, `type`, `x`, `y`. Defaults include `schema_version: "1.1"`, `period: 1`, `source: "synthetic"`. Version 1.0 remains accepted.

- `team_id`: `home` or `away`.
- `type`: `kickoff`, `pass`, `shot`, `goal`, `recovery`.
- Optional: `possession_id`, `end_x`, `end_y`, `outcome`, `related_event_id`.
- `outcome`, when present: `complete`, `saved`, `blocked`, `missed`, `goal`.
- `match_second` is recorded match time, not wall-clock time. Format 571 as `9:31`.
- Sort by `sequence`. Multiple events can have the same match second.
- Resolve evidence by `event_id`, not array position or a numeric suffix.

### Analytics

```json
{
  "match_id": "demo-match",
  "event_count": 30,
  "teams": {
    "home": {"pass": 8, "shot": 5, "goal": 1, "recovery": 5},
    "away": {"pass": 6, "shot": 2, "goal": 0, "recovery": 1}
  },
  "rule_version": "counts-v1",
  "shot_windows": []
}
```

The JSON above shows the seed-7 replay counts and illustrates the response shape; the actual completed replay also has populated shot windows. Inspect the real response and do not hardcode these values. Kickoffs contribute to event count but are not one of the four displayed team count keys.

Each populated `shot_windows` entry contains `team_id`, `previous`, `current`, and `rule_version`. Each window contains `start_second`, `end_second`, `shot_count`, and `evidence_event_ids`. Intervals are `[start,end)`: an event at exactly 10:00 is outside the 5–10 shot window.

Windows remain empty until the backend has sufficient ten-minute coverage. Display an honest waiting state. The rule compares the latest completed five-minute window with its predecessor, not a continuously moving real-time pressure estimate.

### Stories

A story contains `story_id`, `kind`, `text`, `evidence_event_ids`, `rule_version`, and `sequence`. Shot activity also includes `metric` with the window comparison.

- Goal example ID: `goal:scenario-v1-7-22`, kind `goal`, text `Home scored at 9:31.`
- Activity example ID: `shots:home:600`, kind `shot_activity`, text `Home recorded 4 shots in minutes 5–10, compared with 1 in the previous five minutes.`
- Rule versions currently include `goal-v1` and `shot-frequency-v1`. Keep these in optional technical details rather than prominent fan-facing text.

### Catch Me Up

Request:

```json
{"since_sequence": 0, "audience": "casual"}
```

Audience is `casual` or `advanced`. The request includes events whose sequence is greater than `since_sequence`.

Response fields:

```text
summary                       Full legacy-compatible summary string
intro                         Short introductory counts
evidence_event_ids            IDs of newly counted events
through_sequence              Cursor to use after this successful check
audience                      Actual response audience
rule_version                  Currently catch-up-v3
stories                       Candidate stories in this catch-up window
context_evidence_event_ids    Evidence for selected stories, possibly earlier events
explanation:
  mode                        azure or deterministic
  selected_story_ids          Verified selection
  text                        Joined rendered sections
  sections[]:
    title                     What happened / What changed
    text                      Trusted rendered explanation
    story_ids                 Stories used in this section
    evidence_event_ids        Supporting events for this section
  prompt_version              Currently story-selector-v2
  trace[]                     Selection/validation/fallback steps
  fallback_reason             null or a machine-readable reason
  latency_ms                  Optional execution timing
  model                       Deployment name when applicable
```

Render `intro` plus `explanation.sections`; do not also repeat the entire `summary` beneath them. Use `summary` as a compatibility fallback if sections/intro are unavailable. `stories` can include candidates beyond the selected stories; use section evidence for the displayed explanation.

Trace steps can include `get_match_evidence`, `verify_selection`, `complete_coverage`, and `fallback`. Translate these into readable wording in a secondary details panel. Do not expose raw status codes as the main explanation.

**Cursor rules:**

- Start at 0 for a fresh viewing session.
- Advance to the returned `through_sequence` only after a successful request.
- On failure, retain the prior successful cursor and explanation so retrying does not skip events.
- Disable duplicate requests while a Catch Me Up call is pending.
- An empty window returns “You're up to date. No new recorded events.” and no story sections; it does not require an Azure call.
- The existing UI resets its summary when the observed latest sequence moves backwards after a backend restart. Preserve or improve this behavior.
- There is no backend session/generation token. A restart followed by a full replay can escape this heuristic if polling never sees the lower sequence. Do not claim perfect reset detection or persist the cursor across sessions without addressing this limitation.
- Changing the selected audience applies to the next request. Show the audience of an already displayed response accurately. Do not automatically advance the cursor on style change or silently claim old text has been regenerated.

### Match Story Graph

`nodes` include `event`, `metric_window` and `story` types. `edges` use `source`, `target` and `type: "supports"`. Rule version is `graph-v1`.

An optional compact evidence diagram can show events -> recorded shot count -> story. Label edges as support/evidence, never causation. The graph is derived on reads; historical shot-pattern snapshots are not permanently stored.

### Error and empty behavior

- HTTP 422: invalid input. HTTP 409: conflicting ingestion IDs/sequences/references or ordering.
- Unknown matches return empty arrays/zero counts, not necessarily a 404.
- Empty data is distinct from an unreachable backend.
- Retain the last successful snapshot during a polling failure, but mark it as stale/reconnecting.
- Do not label deterministic mode as a broken application. It is a valid fallback.

## 6. Work to implement, in order

### P0: preserve the functioning product

Before styling, run the current replay and inspect the live responses. Confirm the score, shot comparison, stories and Catch Me Up work. Keep the polling, proxy, API payloads and cursor semantics working throughout your edits.

### P1: match dashboard and visual hierarchy

- Build a polished responsive dashboard with a clear MatchOS identity and concise product description.
- Put a compact scoreboard, latest recorded match time, fictional team names, and a **Synthetic replay** label near the top.
- Use consistent fictional names such as Home FC and Away FC; map backend home/away IDs for display without modifying factual story text incorrectly.
- Distinguish first loading, connected polling, reconnecting/stale data, empty replay, and request errors.
- Derive time from the latest recorded event. Do not tick a pretend match clock while the simulator is stopped.
- Place Catch Me Up prominently, with match stories and recent events easy to scan.
- Prefer a balanced two-column desktop layout and a single-column mobile layout. Avoid horizontal scrolling at 375px.
- Keep the existing dark direction if useful; improve spacing, type sizes, contrast and restrained accent colors. No giant decorative elements that bury the functioning demo.

### P1: Catch Me Up experience

- Use clearly labeled Casual / Advanced controls with keyboard support and visible focus.
- Explain the choice briefly: simple explanation versus more detail about recorded metrics.
- Provide idle, loading, success, up-to-date and retry states.
- Display “What happened” and “What changed” as distinct readable sections when returned.
- Keep counts and important facts prominent; avoid overwhelming the fan with event IDs.
- Give each section an expandable **View supporting events** control. Show readable clock, team, event type and outcome where available.
- Keep raw event IDs and rule/trace information available in secondary details for transparency.
- If an evidence event is absent from the loaded snapshot, show that it is unavailable; do not fabricate its contents. A later poll may resolve it.
- Use honest mode labels, e.g. “Selected with Azure AI · checked against match evidence” or “Evidence-backed rule summary”.
- Treat `ai_disabled` as normal configuration. An actual provider failure can have unobtrusive fallback detail; do not interrupt the usable deterministic result with a dramatic error banner.
- Preserve the prior response while a new check is pending. Show which audience produced that response.

### P1: story cards, shot comparison and timeline

- Give story cards clear human labels such as Goal and Shot activity, readable text, and evidence counts.
- Replace prominent rule-version strings with optional technical details.
- Visualize previous/current recorded shot counts with simple labeled bars or another honest comparison. Always include interval labels and numerical counts; do not rely only on color.
- Before the comparison is available, explain that it needs two completed five-minute windows.
- Make a readable recent-event timeline, newest first, preserving sequence order for equal timestamps.
- Visually emphasize goals and shots without making passes/recoveries unreadable.
- Keep supporting goal-producing shot and goal events distinct; do not count the goal as another shot.
- Optionally let an evidence selection highlight or scroll to matching timeline events. Provide a clear way to remove the selection.

### P1: reliability and accessibility

- Separate polling errors from Catch Me Up errors. A successful poll must not erase a failed catch-up request before the user can read/retry it.
- Avoid overlapping polling requests. Preserve the current recursive timeout behavior or an equally sound approach.
- Clean up timers and pending requests on unmount; avoid stale state updates.
- Handle a backend reset during an in-flight Catch Me Up request so an old response does not restore an obsolete cursor after the UI has detected the reset.
- Handle missing optional fields, empty arrays and delayed evidence gracefully.
- Provide semantic headings, labels, actual buttons, visible focus, sufficient contrast and useful screen-reader announcements.
- Avoid re-announcing the entire dashboard every two seconds. Reserve polite live announcements for meaningful status/result changes.
- Respect reduced-motion preferences; keep animations modest.
- Do not store credentials or secretly enable browser calls directly to Azure.

### P2: only after P1 is complete

- A compact evidence flow using the existing graph endpoint.
- A useful match-story filter or audience preference that does not break cursor behavior.
- A clearer secondary “How this was explained” panel for the hackathon demo.
- Small transition polish and an empty-state walkthrough explaining how to start the simulator.

Defer multi-match navigation, login, notifications, multilingual support, real football feeds, free-form chatbot features, new analytics and a full node-graph editor. Do not expand scope until the core demo is polished and verified.

## 7. Suggested implementation structure

The existing app is mostly in one `main.jsx`. You may split it into components and hooks as needed. One reasonable structure is:

```text
frontend/src/
  main.jsx                       React bootstrap
  App.jsx                        Dashboard composition
  api.js                         Shared request/error handling
  hooks/useMatchData.js           Polling and status lifecycle
  components/
    MatchHeader.jsx
    Scoreboard.jsx
    CatchUpPanel.jsx
    StoryCard.jsx
    EvidenceList.jsx
    ShotComparison.jsx
    EventTimeline.jsx
  styles.css                     Shared tokens and responsive styling
```

This structure is a suggestion, not a requirement. Keep changes understandable. Reuse simple CSS and code-native icons/SVG where suitable. Add dependencies only when they solve a clear need; do not introduce a UI framework solely to restyle this small application.

The development proxy is not a finished production hosting configuration. Do not claim the app is publicly deployed merely because the production build succeeds.

## 8. Acceptance checklist and validation

### Functional checks

- [ ] Empty backend: useful waiting state, no invented score/history or misleading Azure label.
- [ ] Replay running: real recorded events update without refreshing the browser.
- [ ] Full seed-7 replay: 30 events, Home 1–0 Away, time 10:00, shots Home 5 / Away 2.
- [ ] Goal story: Home scored 9:31; supporting shot is 9:30.
- [ ] Shot change: Home 4 recorded attempts in minutes 5–10 versus 1 in minutes 0–5.
- [ ] First Catch Me Up: readable introduction and both available story sections.
- [ ] Second check with no new events: up-to-date state without losing cursor correctness.
- [ ] Casual and Advanced choices: correct response audience displayed; no duplicate fact rendering.
- [ ] Azure disabled: fully usable deterministic summary, accurately labeled.
- [ ] Azure enabled, if the owner provides an already configured running backend: actual returned mode displayed and evidence remains inspectable.
- [ ] Catch-up failure: prior response/cursor retained, useful retry; successful polling does not erase the error.
- [ ] Backend offline: clear connection/stale-data state; reconnecting restores updates.
- [ ] Backend restart: detected sequence rollback resets the viewing cursor; no stale in-flight response undoes that reset.
- [ ] Evidence controls show real linked events; absent events are labeled unavailable.

### Visual/accessibility checks

- [ ] Check approximately 375px, 768px and 1440px widths.
- [ ] No horizontal overflow, clipped controls, tiny evidence text, or overlapping panels.
- [ ] Complete the main flow using the keyboard.
- [ ] Controls have visible focus and understandable names.
- [ ] Comparison labels and states are understandable without color.
- [ ] Reduced motion works; polling does not spam announcements.
- [ ] No console errors or uncontrolled repeated network requests during ordinary use.

### Commands

From `frontend`:

```powershell
npm.cmd run build
```

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
```

Use the existing tests to detect regressions. If you introduce substantial cursor/concurrency behavior, add a small number of meaningful tests for that behavior with an appropriate frontend test setup. Do not add tests that merely repeat static markup or manufacture a large test suite for cosmetic changes.

Record what you actually ran and observed. If live Azure, mobile browser access or another check was unavailable, mark it unverified rather than claiming success.

## 9. Review, workflow and deliverables

The intended long-term workflow is feature branches -> reviewed PR into `develop` -> stable release into `main`. Currently the backend features are in stacked PRs. Verify the base before opening your PR:

- If backend work remains unmerged, target the current working backend branch `feature/grounded-ai-explanations` so reviewers see only your frontend changes.
- If it has been integrated into `develop`, branch from and target `develop`.
- Do not merge PRs, force-push shared branches, or publish infrastructure changes without the owner's direction.
- Run local checks even if GitHub CI does not trigger for a stacked feature-branch target.

Deliver:

1. Working frontend changes on `feature/match-page-polish`, with readable components and styling.
2. A short summary of the improved user experience and files changed.
3. Screenshots of desktop and mobile layouts if your tools support real browser captures.
4. Validation results, manual reproduction steps, and remaining limitations.
5. Updated frontend usage documentation only where behavior changed.
6. A reviewable PR or patch, depending on your available access. Keep backend changes out unless a necessary bug fix is clearly explained and agreed.

Suggested PR title: **Polish the MatchOS dashboard and evidence-backed Catch Me Up experience**.

Suggested task order for one frontend contributor:

1. Run and understand the existing replay and contracts.
2. Refactor only enough to make the UI maintainable.
3. Implement dashboard hierarchy and responsive styles.
4. Improve Catch Me Up sections, evidence and audience controls.
5. Improve story cards, shot comparison and timeline.
6. Fix request/state/error behavior and accessibility.
7. Verify the checklist, capture results, and prepare the review.

## 10. How this fits the rest of the team

| Owner | Responsibility |
| --- | --- |
| Project owner / backend lead | Event ingestion, schema, deterministic rules, graph contracts, integration and Azure configuration |
| Gemini acting as frontend teammate | The complete frontend assignment in this document |
| Future AI contributor | Improving grounded selection, orchestration and evaluation with agreed backend contracts |

The owner has already built the backend/AI slice. Do not redo it simply because the original plan expected three people. Frontend work should expose that functioning slice clearly.

## 11. Demo goal

Build an interface that can tell this truthful story in roughly 1 minute 45 seconds:

1. Introduce MatchOS and the synthetic match scoreboard.
2. Show the replay feeding actual events into the dashboard.
3. Show the goal and increase in recorded shot activity.
4. Click Catch Me Up and explain What happened / What changed.
5. Expand supporting events to prove the explanation is grounded.
6. Show audience personalization and the actual Azure selection/verification details if Azure is active.

The viewer should immediately understand: **MatchOS helps a fan catch up on a match with explanations they can check against the events.**

End your implementation report with: what works, what was tested, any remaining issue, and how the owner can run the result. Do not substitute a new roadmap for the requested working frontend.
