# M1 — End-to-end evidence-backed demo

Suggested timebox: three working days, adjusted to the hackathon deadline. Integrate on develop daily.

| Stage | Lead: backend/integration | Teammate 2: frontend | Teammate 3: analytics/AI |
| --- | --- | --- | --- |
| Day 1 | Publish repo, invite team, agree contract, replay tests | Run scaffold, match page/response contracts | Metric definitions and evidence model |
| Day 2 | Repository boundary, ordered replay/cursor | Timeline, evidence drilldown, summary states | Window analytics and graph nodes/edges |
| Day 3 | Integration checks, release PR | Responsive/accessibility pass and demo | Verified explanations and audience phrasing |

## First actions
Lead runs demo and publishes repo/issues. Frontend owner claims task 3. Intelligence owner claims task 4 and writes metric definitions before code.

## Release gate
- Clean setup works and CI passes on develop/release PR.
- Two identical replays preserve counts and score.
- One documented window pattern becomes a graph story with resolvable evidence and versioned rule.
- Catch Me Up covers the agreed cursor window with empty/error/loading states.
- Casual and advanced views share underlying facts; unsupported tactical claims suppressed.
- Three-minute demo rehearsed; limitations documented; all three owners sign off.

## Demo timing
0:00 problem; 0:30 replay; 1:00 timeline/stats; 1:30 story/evidence; 2:00 Catch Me Up in both styles; 2:30 graph and next steps.

This scaffold starts M1. Window patterns, full graph and evidence-verified LLM integration are not implemented yet. LLM adapter is optional if deadline is short; deterministic explanations remain usable.
