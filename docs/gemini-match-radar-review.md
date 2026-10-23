# Gemini review: Matchday and Match Radar baseline

Work in the original repository:

`C:\Users\lopez\.codex\.chatgpt-projects\g-p-6abc4d11ef2c819191fa6bba4f2af3de\matchos`

This milestone implements a bounded three-match synthetic simulation and a deterministic recommendation baseline. It is not an AI ranking implementation, notification delivery service, empirical engagement study, or licensed video player. The existing optional Azure story selection remains available through Catch Me Up.

## Review scope

- `backend/app/matchday.py`: sparse 93-minute authored feeds, observed-event windows, scoring, qualification and ranking.
- `backend/app/main.py`: shared matchday start/read/tick/release routes, canonical ingestion, owner checks, cooldown notifications and simple shots comparator.
- `backend/app/security.py`: preserve the bounded security baseline. Matchdays consume three ordinary match slots; new starts count against existing request quotas.
- `frontend/src/components/Matchday.jsx`: start/pause/resume/reset, one shared clock, recommendation evidence, transient in-page alerts and selected-match Catch Me Up.
- `frontend/src/utils/matchday.js`, `frontend/src/api.js`, `frontend/src/App.jsx`: sequential tick replay, abort/retry behavior, protected requests and view navigation.
- New backend/frontend tests and `docs/match-radar.md`.

The repository contains pre-existing uncommitted security changes and untracked user documents. Do not discard, overwrite, stage or publish unrelated work. Do not read local environment/credential files, inspect process environment, request live Azure calls, weaken quotas, put credentials in browser code, or change branding during this review.

## Challenge the implementation

1. Does each decision use only events observed up to the shared clock? Generated future events and authored role/profile metadata must not determine the ranking.
2. Are window boundaries and goal/shot counts correct? Is the displayed signal clearly a rule score, not a probability?
3. Can a quiet draw or a one-sided shot barrage generate an inappropriate recommendation? Can the prominent fixture legitimately rank first?
4. Are notifications transition-based, deduplicated on retries, suppressed on cooling/finish and constrained by the ten-match-minute per-match cooldown?
5. Can anyone bypass ownership, advance just one member, jump ticks, mutate fixture facts, exceed capacity, or release another session's matchday?
6. Can pause/reset/navigation or an aborted request cause stale clock, alert, event list or Catch Me Up data to overwrite a newer view?
7. Does resetting release owned capacity safely? Are partial failures understandable without changing user trust boundaries?
8. Is there unnecessary architecture or overclaiming? No current claim of improved engagement, real match reconstruction, table stakes or video viewing is justified.

Known quality limitation from browser QA: the concise match briefing works, but the existing full-game "What changed" section repeats many five-minute progressive-pass stories. Propose an evidence-preserving selection/grouping approach before editing it; do not discard goals, invent tactical causality, or equate shot volume with chance quality.

For the automated first review, provide findings only, with severity, file/function, concrete reproduction and minimal suggested fix. Do not edit files or run tools when the code bundle is supplied directly. Codex will assess and apply supported fixes, then rerun tests. Human-directed Gemini edits can follow separately against this original checkout.

## Checks

```powershell
.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run format:check
npm.cmd --prefix frontend run build
.venv\Scripts\python.exe -B scripts/check_secrets.py
```

Try the **Matchday & Radar** tab and start the matchday. At 1x, one second advances 30 match seconds; 4x finishes a 93-minute authored feed in roughly 47 seconds plus request time. Inspect the early prominent-fixture signal, the later overlooked-match signal, the quiet periods, and selected-match Catch Me Up. Test on a narrow screen and with keyboard controls.
