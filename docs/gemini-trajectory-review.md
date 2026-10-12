# Antigravity review: score trajectory milestone

Review the original MatchOS checkout at `C:\Users\lopez\.codex\.chatgpt-projects\g-p-6abc4d11ef2c819191fa6bba4f2af3de\matchos` against our engagement consensus and Codex's corrections. Do not inspect credential files, make live Azure calls, weaken security limits, publish changes, or discard unrelated work. Save findings to `docs/antigravity-trajectory-findings.md` before editing.

## Implementation

- `backend/app/intelligence.py:score_trajectory`: ordered observed goal states, all five transition types, acquisition/equalizer counts, response timing and goal evidence.
- `backend/app/fan_briefing.py`: `fan-briefing-v2` with compact score story, exact recent activity, and regular-time clock. Repeated equalizers are distinguished from genuine reversals. No generic questions remain.
- `backend/app/main.py`: matchday and catch-up use the same briefing; matchday returns every event needed for its evidence drawer. Notification wording reuses the verified story; ranking and cooldown rules remain unchanged.
- `frontend/src/components/MatchStoryBriefing.jsx`: shared Radar/Catch Me Up view with observed score path and clickable supporting events. Casual detailed analytics stay collapsed; advanced detail remains available.
- Backend trajectory/briefing tests and actual React component rendering tests in `frontend/test/match-story.test.js`.

Challenge these edge cases: same-team scoring run; a goal that reduces a deficit without leveling; repeated equalizers without reversal; actual reversal through a tie; response at 600 versus 601 seconds; adjacent same-team goals; early clipping; 75:00 versus 75:30; partial history; no new goals; no new events; halftime; added time; full time; future-event exclusion. Check that following and evidence navigation preserve cursor and ownership behavior.

At 75:30 the demo card reads:

> Newcastle United led twice. Crystal Palace have answered twice.
>
> Palace's goal came 9 minutes after Newcastle scored. Six shots total in the last five minutes, three from each side; two total in the previous five minutes. 14:30 until 90 minutes, plus added time.

The actual current window is `(70:30,75:30]`, previous `(65:30,70:30]`. Each team's count is compared as part of a total, not against the opponent's count. Timing uses match seconds, not wall-clock assumptions. A reversal changes the last leading team; a tie does not. Later taking the lead again does not turn a prior turnaround into a new reversal when the last leader stayed the same.

Check whether this gives a useful reason to follow without claiming domination, chance quality or an outcome prediction. The wording is rule-based, not free-form narration. No anchor suppression, freshness heuristic, preferences or streaming CTA was added. Source coverage is not verified solely by having an old event. Fan appeal remains an untested hypothesis.

Codex verification on 2026-10-11: 91 backend tests, 27 frontend tests and production build passed. Browser checks verified identical Radar/Catch Me Up cards and the four-goal path. Preview: [trajectory-story-preview.png](trajectory-story-preview.png). Antigravity has not yet reviewed this implementation.

## Checks

```cmd
.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run format:check
npm.cmd --prefix frontend run build
.venv\Scripts\python.exe scripts/check_secrets.py
```
