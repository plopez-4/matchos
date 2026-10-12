# Initial GitHub issue drafts

Create milestone **M1: End-to-end evidence-backed demo**. Labels: backend, frontend, intelligence, docs, integration, priority:p0. Owners below are role placeholders; assign real handles after inviting teammates. Numbers here are draft task IDs, not live GitHub issues.

## 1. Publish repository and establish workflow
Owner: Lead. Labels: docs, priority:p0. Depends: none.
- Create empty matchos remote; push main/develop; invite both teammates.
- Set protections/required review and CI; create milestone and these issues.
Acceptance: team can clone/run scaffold; both branches protected.

## 2. Harden replay and repository boundary
Owner: Lead. Labels: backend, priority:p0. Depends: 1.
- Extract repository interface; decide PostgreSQL scope for M1.
- Document ordered replay/cursor policy and recovery from simulator failure.
- Verify duplicates, sequence conflicts, malformed events and restart behavior.
Acceptance: identical replay preserves counts; no silently missed late events; deployment storage limits documented.

## 3. Match page and evidence drilldown
Owner: Teammate 2. Labels: frontend, priority:p0. Depends: contract agreement with 2.
- Add metric cards, story cards, readable event evidence and timeline.
- Loading/error/empty states; responsive keyboard-accessible layout.
Acceptance: all story IDs resolve to readable evidence; outage visible; replay renders correctly.

## 4. Deterministic window analytics
Owner: Teammate 3. Labels: intelligence, priority:p0. Depends: contract agreement with 2.
- Define windows, units, minimum samples and versioned rules.
- Start shot/recovery frequency; extend schema only with available data.
- Test fixed fixtures and insufficient evidence.
Acceptance: expected fixture results; no pressure/possession claims inferred from unsupported counts.

## 5. Match Story Graph
Owner: Teammate 3; reviewer Lead. Labels: intelligence, backend, priority:p0. Depends: 4.
- Typed event/metric/story nodes; supports and preceded-by edges.
- Stable IDs, evidence links and rule versions; agree graph API.
Acceptance: one evolving pattern traces to original events; orphan evidence rejected; no causal claim from time ordering alone.

## 6. Catch Me Up and personalization
Owner: Lead + Teammate 2. Labels: integration, priority:p0. Depends: 2, 3, 5.
- Summarize what happened/changed/matters using agreed window.
- Scope or persist viewer cursor; reset per match.
- Casual/advanced wording from identical facts/evidence.
Acceptance: repeat summary contains only new events; empty/error/loading states; every factual change cites evidence.

## 7. Evidence-verified AI adapter
Owner: Teammate 3; reviewer Lead. Labels: intelligence. Depends: 5, 6.
- Provider-independent interface, structured output, fact/ID verification.
- Server-side keys, prompt/model versions and latency; deterministic fallback.
Acceptance: fabricated evidence/unsupported claims rejected; timeout yields useful fallback. Required for the AI-powered submission; deterministic text remains a fallback.

## 8. Rehearse and release v0.1.0
Owner: All; coordinator Lead. Labels: integration, priority:p0. Depends: 2–6.
- Clean setup, CI, repeated replay, evidence inspection and responsive UI.
- Capture a functioning demo under two minutes; reviewed develop → main PR and release tag.
Acceptance: milestone gate satisfied and all owners sign off.
