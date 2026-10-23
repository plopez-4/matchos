# Antigravity review: fan-facing Catch Me Up

Review the original checkout at `C:\Users\lopez\.codex\.chatgpt-projects\g-p-6abc4d11ef2c819191fa6bba4f2af3de\matchos`. Do not overwrite unrelated local documents, inspect credentials, weaken security limits, or make live Azure calls. This is a review handoff, not a claim that Antigravity has already reviewed the changes.

## What changed

- `backend/app/fan_briefing.py`: deterministic fan-facing wording from observed events. Score-aware headlines, all newly missed goals and substitutions, recent shooting context, and a question/invitation to follow the action.
- `backend/app/main.py`: catch-up responses add `fan_briefing`; existing `match_briefing`, story selection, analytics, cursors and evidence remain available.
- `frontend/src/components/CatchUpPanel.jsx`: fan story comes first. Casual mode collapses the technical report; advanced mode opens it. Supporting events remain clickable.
- `backend/tests/test_fan_briefing.py`: equalizer, lead, extended lead, consolation goal, incomplete history, future-event exclusion, quiet/finished matches, no new events and full-game goal/evidence coverage.

## Challenge the wording

The core example at 75:30 of the synthetic Palace–Newcastle match is:

> Crystal Palace have pulled level. Crystal Palace 2–2 Newcastle United. Both sides are getting shots away, and shooting activity has picked up since the previous five minutes. Can either side find the next goal?

Check that a casual fan can understand it quickly and that every factual statement is justified. A question is an invitation, not a prediction. Goal headlines must match the actual score. An isolated shot barrage must not become a claim of domination or dangerous chances. Recent activity compares total shot counts, not each team's individual increase. Comparisons require a full ten-minute clock span and earlier observed history. Missing feed coverage is not automatically detected; never imply that absence of recorded events proves absence of play.

Challenge quiet, uneven, halftime and finished games. Would a fan find the text useful without being misled? Can every newly missed goal still be inspected? Do earlier goals remain accessible as score evidence? Are the two audience styles and no-new-events behavior clear?

Current limits: this wording layer uses rule-selected templates. It is not free-form model narration, learned tactics, player evaluation, chance-quality estimation, a stale-feed detector or a proven engagement improvement. The existing optional Azure story selection remains separate, with no new paid calls. Review the interaction of its badge with the deterministic fan narrative for possible confusion.

Return concrete findings with severity, file/function, reproduction and a minimal proposed fix before editing. For any human-approved edits, preserve evidence and run the checks below. Save findings to `docs/gemini-fan-storytelling-findings.md` so Codex can assess them.

## Checks

```cmd
.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run format:check
npm.cmd --prefix frontend run build
.venv\Scripts\python.exe scripts/check_secrets.py
```

Codex validation on 2026-10-11: 85 backend tests and 25 frontend tests passed, production build passed. Browser checks verified the equalizer briefing, supporting-event expansion and advanced detail. Preview: [fan-briefing-preview.png](fan-briefing-preview.png).
