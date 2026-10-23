# Current synthetic demo data

The main branded page (`/`) and development view (`/?view=development`) use three current authored fixtures:

- Manchester United vs Manchester City: `united-city-90`.
- Crystal Palace vs Newcastle United: `palace-newcastle-90`.
- Brighton vs Fulham: `brighton-fulham-90`.

`backend/app/data/demo_fixtures.json` is the shared fixture manifest. Both views use the Matchday generator and bundled reference roster identities. The dashboard uses seed 7; development matchdays use the match ID to vary participant choices. Player actions, scores and timings are fictional. Reference identities do not make these real fixtures, real lineups, licensed video or continuous tracking.

Each feed spans 93 cumulative playing minutes, with one halftime marker, normalized ball coordinates, intended pass recipients, outcomes, possessions and linked goal-producing shots. Substitutions are authored where the bundled club reference includes a demo bench. Only recorded participants are shown on the pitch; missing movement is not invented.

The older United–Hull export and independent fictional-name generator have been removed. The earlier short unnamed scenarios remain internal analytics regression inputs; they cannot be selected through the public replay routes. Existing historical evaluation reports remain records of earlier versions.

## Export and inspect

Run from the repository root:

```powershell
.venv\Scripts\python.exe scripts\export_full_matches.py
.venv\Scripts\python.exe simulator\run.py --scenario united-city-90 --match-id derby-demo --interval 0.05
```

`data/synthetic/` contains the three current JSONL feeds and their regenerated manifest. Exporting validates every event against the application model. These files support deterministic analytics and narrative evaluation; no training or fine-tuning job is performed.

Catch Me Up follows the same event-to-metric-to-story graph and grounded AI pipeline in either view. AI writing is optional and falls back to recorded-event summaries when unavailable. Player identities, rules and evidence are inspectable; counts cannot establish chance quality, tactical intent or player skill.

## Code/data cleanup — 23 October 2026

The old unnamed short scenarios are now isolated in `backend/tests/legacy_scenarios.py`. Production `backend/app/simulation.py` generates only the current named fixtures by default and rejects retired IDs. They are retained as test inputs to protect deterministic analytics; they are not loaded into the running app. Unreachable club-picker, broadcast-overlay, old recap/translation and simulator-guide modules have been removed, along with their exclusive CSS and retired-feature tests. The current roster stays on the backend; the browser no longer imports its full player database. See `docs/code-cleanup.md` for the scope and verification.
