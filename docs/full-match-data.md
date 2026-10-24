# Current synthetic demo data

The main branded page (`/`) and development view (`/?view=development`) use three current authored fixtures:

- Manchester United vs Manchester City: `united-city-90`.
- Crystal Palace vs Newcastle United: `palace-newcastle-90`.
- Brighton vs Fulham: `brighton-fulham-90`.

`backend/app/data/demo_fixtures.json` is the shared fixture manifest. `backend/app/data/match_variants.json` contains three authored versions per pairing, nine matches total. New matchday independently chooses one of the three for each fixture, giving 27 possible combinations with only three concurrent matches. Selection is derived from the new random matchday ID and saved with each session; the version's seed fixes its passing routes. A random selection can repeat a previous combination. Switching, reopening, requesting a recap or opening an alert never rerolls a fixture.

Both views use this library and bundled reference identities. Player actions, scores and timings are fictional. Reference identities do not make these real fixtures, confirmed lineups, licensed video or continuous tracking. Narrative version names and future event schedules are not exposed in the matchday response; Radar receives only ingested events.

The main page runs all three fixtures on one clock. Switching the selected match preserves everyone's progress. Catch Me Up, Listen and opening a hot-match alert pause the shared clock so the evidence stays stable during review. Resume continues all three. Hot-match notifications appear at the top of the viewport for another fixture only while its recorded evidence supports the reason; quiet matches and expired reasons do not qualify. Opening an alert selects that fixture and a recorded action without automatically requesting an AI recap.

## Nine prepared matches

The following outcomes document the library for development; they are not presented as advance predictions to fans:

| Fixture          | Version                      | Events | Shots | Final score |
| ---------------- | ---------------------------- | -----: | ----: | ----------- |
| United–City      | 1: early pressure            |    782 |    10 | 2–1         |
| United–City      | 2: patient derby             |    759 |     2 | 0–0         |
| United–City      | 3: late comeback             |    779 |    12 | 2–2         |
| Palace–Newcastle | 1: repeated replies          |    787 |    15 | 2–2         |
| Palace–Newcastle | 2: first-half exchange       |    752 |    10 | 1–1         |
| Palace–Newcastle | 3: one-sided score           |    775 |     4 | 2–0         |
| Brighton–Fulham  | 1: patient contest           |    754 |     2 | 0–0         |
| Brighton–Fulham  | 2: open first half           |    774 |    10 | 1–1         |
| Brighton–Fulham  | 3: late turnaround and reply |    766 |    12 | 2–2         |

All six clubs have eleven distinct starters, including one goalkeeper. Every starter participates in first-half passing actions in each prepared version. Possessions use two to four linked circulation passes, sometimes followed by a final pass and shot. Direction, recipients, outcomes and coordinates remain connected; circulation may go backwards. Manchester retains five substitutions per side, replacing outgoing players while keeping eleven active. The other four clubs now have starting elevens but no authored bench substitutions; their broader reference squads remain smaller.

The new identities and shirt numbers were checked against the [dated Premier League squad-number reference](https://www.premierleague.com/en/news/4725682/all-20-premier-league-clubs-squad-numbers-for-202627-season). Roles and starting lineups are authored demo choices. New names have not received a separate human pronunciation audition.

Radar remains a versioned deterministic comparison, not a trained preference model or a prediction of future entertainment. It uses close scores, recent equalizers/lead reversals and observed shot activity. Tests cover every combination, prove all three fixtures can lead, and retain a combination that produces no hot recommendation throughout the matchday. A current recommendation is allowed to change as evidence arrives.

Verification on 24 October: with Brighton selected, Palace advanced in the background and produced a fixed-position hot-match notification. Opening it selected Palace at the same 82:00 shared clock, paused all fixtures, and exposed a recorded action. Catch Me Up used that paused snapshot; Resume cleared review and continued the shared clock. This verification used AI and Azure Speech off.

Each feed spans 93 cumulative playing minutes, with one halftime marker, normalized ball coordinates, intended pass recipients, outcomes, possessions and linked goal-producing shots. Substitutions are authored where the bundled club reference includes a demo bench. Only recorded participants are shown on the pitch; missing movement is not invented.

The older United–Hull export and independent fictional-name generator have been removed. The earlier short unnamed scenarios remain internal analytics regression inputs; they cannot be selected through the public replay routes. Existing historical evaluation reports remain records of earlier versions.

## Export and inspect

Run from the repository root:

```powershell
.venv\Scripts\python.exe scripts\export_full_matches.py
.venv\Scripts\python.exe simulator\run.py --scenario united-city-90 --match-id derby-demo --interval 0.05
```

`data/synthetic/` contains nine JSONL feeds and their regenerated manifest. The original fixture filenames identify version 1; `-v2` and `-v3` identify the alternatives. Exporting validates every event against the application model. `library_fixture(profile, match_id, variant)` is the seeded library entry point (zero-based variant). The older single-fixture diagnostic adapter retains its deterministic regression profile; it does not choose the shared matchday versions. These files support analytics and narrative evaluation; no training or fine-tuning job is performed.

`backend/tests/test_match_library.py` verifies legal active players, all starters' participation, linked passes/goals, reproducibility, all 27 combinations, stable reopening, observed-only ranking and bounded source-linked recap packets for every version. A thirteen-row historical scoring example is retained only under `backend/tests/fixtures/` to keep bilingual prose-contract tests independent of future generator changes.

Catch Me Up follows the same event-to-metric-to-story graph and grounded AI pipeline in either view. AI writing is optional and falls back to recorded-event summaries when unavailable. Player identities, rules and evidence are inspectable; counts cannot establish chance quality, tactical intent or player skill.

## Code/data cleanup — 23 October 2026

The old unnamed short scenarios are now isolated in `backend/tests/legacy_scenarios.py`. Production `backend/app/simulation.py` generates only the current named fixtures by default and rejects retired IDs. They are retained as test inputs to protect deterministic analytics; they are not loaded into the running app. Unreachable club-picker, broadcast-overlay, old recap/translation and simulator-guide modules have been removed, along with their exclusive CSS and retired-feature tests. The current roster stays on the backend; the browser no longer imports its full player database. See `docs/code-cleanup.md` for the scope and verification.
