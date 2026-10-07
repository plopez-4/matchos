# M1 — End-to-end evidence-backed demo

Suggested timebox: three working days, adjusted to the hackathon deadline. Integrate on develop daily.

| Stage | Lead: backend/integration                               | Teammate 2: frontend                         | Teammate 3: analytics/AI                    |
| ----- | ------------------------------------------------------- | -------------------------------------------- | ------------------------------------------- |
| Day 1 | Publish repo, invite team, agree contract, replay tests | Run scaffold, match page/response contracts  | Metric definitions and evidence model       |
| Day 2 | Repository boundary, ordered replay/cursor              | Timeline, evidence drilldown, summary states | Window analytics and graph nodes/edges      |
| Day 3 | Integration checks, release PR                          | Responsive/accessibility pass and demo       | Verified explanations and audience phrasing |

## First actions

Lead runs demo and publishes repo/issues. Frontend owner claims task 3. Intelligence owner claims task 4 and writes metric definitions before code.

## Release gate

- Clean setup works and CI passes on develop/release PR.
- Two identical replays preserve counts and score.
- One documented window pattern becomes a graph story with resolvable evidence and versioned rule.
- Catch Me Up covers the agreed cursor window with empty/error/loading states.
- Casual and advanced views share underlying facts; unsupported tactical claims suppressed.
- Demo under two minutes rehearsed; limitations documented; all three owners sign off.

## Demo timing

Target 1:45 total: 0:00 problem; 0:12 replay; 0:37 story/evidence and agent tools; 1:02 Catch Me Up; 1:27 Microsoft integration and impact.

The working slice now includes window patterns, an event/metric/story support graph, verified Azure story selection and a polished broadcast dashboard. Remaining gates include integrating stacked PRs, clean-clone verification and demo/deployment readiness. For submission, implement an AI-powered explanation path; deterministic explanations remain the fallback. Verify required Microsoft hero technologies against the full challenge brief.
