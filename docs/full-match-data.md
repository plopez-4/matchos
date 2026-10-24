# Current synthetic demo data

The main branded page (`/`) and development view (`/?view=development`) use three current authored fixtures:

- Manchester United vs Manchester City: `united-city-90`.
- Crystal Palace vs Newcastle United: `palace-newcastle-90`.
- Brighton vs Fulham: `brighton-fulham-90`.

`backend/app/data/demo_fixtures.json` is the shared fixture manifest. Both views use the Matchday generator and bundled reference roster identities. Shared matchdays use the match ID to vary participant choices; the exported comparison below uses seed 7. Player actions, scores and timings are fictional. Reference identities do not make these real fixtures, real lineups, licensed video or continuous tracking.

The main page runs all three fixtures on one clock. Switching the selected match preserves everyone's progress. Catch Me Up, Listen and opening a hot-match alert pause the shared clock so the evidence stays stable during review. Resume continues all three. Hot-match notifications appear at the top of the viewport for another fixture only while its recorded evidence supports the reason; quiet matches and expired reasons do not qualify. Opening an alert selects that fixture and a recorded action without automatically requesting an AI recap.

## Fixture depth and limitations

These fixtures are not equally rich. A generator comparison at seed 7 gives:

| Fixture                           | Events | Passes | Shots | Goals | Distinct players per team, including pass recipients |
| --------------------------------- | -----: | -----: | ----: | ----: | ---------------------------------------------------- |
| Manchester United–Manchester City |    593 |    382 |    10 |     3 | 16 / 16                                              |
| Crystal Palace–Newcastle United   |    594 |    387 |    15 |     4 | 4 / 4                                                |
| Brighton–Fulham                   |    564 |    374 |     2 |     0 | 4 / 4                                                |

Manchester has fuller demo lineups, bench substitutions and authored creator/finisher spells. Palace–Newcastle offers more scoring action and comeback evidence, but its participant pool is narrower. Brighton–Fulham is intentionally uneventful, providing a negative control for momentum and hot-match claims. Similar event totals do not imply equal roster or narrative quality. The other four clubs still need broader verified reference rosters and stronger authored player sequences before claiming parity with the Manchester fixture. This UI repair does not change those feeds.

Verification on 24 October: with Brighton selected, Palace advanced in the background and produced a fixed-position hot-match notification. Opening it selected Palace at the same 82:00 shared clock, paused all fixtures, and exposed a recorded action. Catch Me Up used that paused snapshot; Resume cleared review and continued the shared clock. This verification used AI and Azure Speech off.

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
