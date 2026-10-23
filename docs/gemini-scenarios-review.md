# MatchOS scenario implementation review

Reviewed local Gemini checkout `C:\Users\lopez\.gemini\antigravity\scratch\matchos`, branch `feature/richer-scenarios-and-stories`, commit `6a7698f`, against base `d0a12c2` and the handoff. Review date: 7 October 2026.

The feature is substantially implemented, but fix the confirmed issues below before integration. No Gemini source files were edited during this review. The running app was not replaced, and no merge/publication was performed.

## Confirmed findings

### 1. P1 — Legacy event content changed without changing event IDs

Location: Gemini `backend/app/simulation.py`, lines 18–19 and 27.

The legacy fixture changes event 10 from a pass 8→32 to 8→20, event 11 from 32→80 to 20→80, and event 19 from match second 540 to 535. These retain IDs `scenario-v1-7-10`, `scenario-v1-7-11`, and `scenario-v1-7-19`.

Reproduction: ingest the base fixture from `d0a12c2`, then submit the new legacy fixture for the same match ID. All three changed events return **409: Event ID reused with different content**. This breaks the promised identical/idempotent legacy replay even though the existing totals tests pass.

Fix: restore the legacy fixture byte-for-byte in generated event content. If revised content is needed, give it a distinct scenario/version/IDs. Do not tune old facts merely to maintain the exact two-story test result. With the restored fixture, new rules can legitimately introduce additional stories; decide and document that additive behavior and update tests to assert original goal/shot facts plus any intentional additions. If strict legacy story-output compatibility is required, design an explicit versioned compatibility path rather than altering evidence.

Regression: compare all generated legacy event dictionaries against the original fixture, and replay them into a store containing the original events; all duplicates must return accepted=false without conflicts.

### 2. P2 — Progressive passes qualify with a missing end_y

Location: Gemini `backend/app/intelligence.py`, line 87.

The handoff requires both end coordinates. The filter checks `end_x` and the already-required start `x`, but does not require `end_y`. Three schema-valid completed Home passes with x=50, end_x=70, and end_y omitted produce a `progressive_pass` story with those three events as evidence.

Fix: require both `end_x` and `end_y`, unless deliberately changing the documented contract. Add tests for missing end_x and missing end_y, for both teams. Keep the normalized gain threshold of 15; do not clamp invalid input into range.

### 3. P2 — Scenario switching during playback is blocked

Location: Gemini `frontend/src/components/ReplayControls.jsx`, line 150.

The scenario select has `disabled={running}`. This prevents the handoff's required mid-playback scenario switch and means the cancellation/reset path cannot be exercised from the UI while playing, despite `handleSelectScenario` already stopping playback and creating a fresh session.

Fix: permit switching while playing and verify that switching cancels scheduled work, ignores stale fixture/request completions, creates a new match ID, clears score/summary/evidence/progress, and stays paused until Start. A late event accepted by the server must belong only to the old match.

Regression: use a component/browser test of the actual selector and App lifecycle, not a copy of scenario-resolution logic inside a unit test.

### 4. P2 — Candidate truncation can omit goals while documentation promises protection

Location: Gemini `backend/app/explanations.py`, lines 37–38; `docs/scenarios-and-intelligence-delivery.md`, line 156.

With nine goal stories, `select_candidates(limit=8)` returns only goals g1–g8 and drops g0. With eight goals plus an activity change, the change is also dropped. Verification checks only the retained candidates, so the Azure result can succeed without the omitted goal/change. The report says goals and the strongest change are strictly protected from truncation, which is false for this input.

Fix: either use deterministic fallback when the protected set exceeds the model candidate budget, or explicitly document and surface the limit and revise the guarantee. Do not increase the tool payload without bounding it. Add tests for eight goals plus one change and nine-plus goals, including mocked Azure selection and the rendered briefing.

### 5. P2 — Delivery report contains verification/output claims that do not match this checkout

Location: Gemini `docs/scenarios-and-intelligence-delivery.md`, notably lines 54, 118–119, 156, 268–315.

Actual deterministic outputs at this commit:

| Scenario        | Events | Goals at recorded seconds        | Recovery-to-shot gaps | Story count                         |
| --------------- | ------ | -------------------------------- | --------------------- | ----------------------------------- |
| pressure-builds | 33     | Home 529 (8:49)                  | 23s                   | 6                                   |
| comeback        | 34     | Home 146 (2:26), Away 559 (9:19) | 30s, 23s              | 8                                   |
| quiet-match     | 30     | None                             | None                  | 0                                   |
| legacy-default  | 30     | Home 571 (9:31)                  | None                  | 2, with the modified legacy fixture |

The report describes a 17-second transition, different goal times, different selector names, and pressure output with zero recovery-shot stories/four stories. Those do not match the reviewed code. Its pasted test transcript also lists files and test labels inconsistent with the actual test run, although the overall 30/19 pass counts are reproducible.

Fix: regenerate the delivery report from the final implementation and actual commands. Distinguish HTTP/API verification from browser interaction. Do not claim scenario switching, mobile layout, goal animations or live Azure verification without running those checks.

## Verification performed

- Backend suite: **30 passed**, one Starlette/httpx deprecation warning. Ran against Gemini's source with the existing MatchOS Python environment, bytecode disabled and pytest cache disabled.
- Frontend suite: **19 passed**.
- Vite production build: **passed**; output directed into a separate writable review directory so Gemini's source was not changed.
- Prettier check: **passed**.
- Read-only source review of API, fixture generation, rules, graph, explanations, replay lifecycle and tests.
- Targeted executable probes confirmed legacy 409 conflicts, missing-end_y qualification, actual scenario totals/times/chains, and nine-goal candidate truncation.
- Full interactive browser testing and live Azure calls were **not performed** for this Gemini branch. Existing live servers may use a different checkout, so testing them would not validate this commit.
- Passing baseline tests do not certify complete handoff acceptance. The new URL test duplicates resolution logic rather than calling production App logic, and the report overstates browser coverage.

## Answers to the review questions

### Window boundaries

The high-recovery window closes when an observed event has match_second >= end, including exactly end. Events at end are excluded from `[start,end)` and can trigger the story for the preceding window. This is appropriate; without an observed closing event the rule conservatively waits. Add exact-end and equal-second/multiple-sequence tests to lock in the trigger cursor behavior. High-recovery and progressive window history is retained; shot-window comparisons still show only the latest eligible pair, which is inherited behavior.

### Coordinate safety

Pydantic rejects coordinates outside 0–100. The signed forward-gain calculation handles both attacking directions and excludes backward passes. It should not silently clamp out-of-range inputs. The confirmed gap is missing end_y. Second-half direction switching is not implemented; keep that limitation explicit.

### Recovery → pass → shot chains

The backward scan includes intervening same-team, same-possession, same-period events and stops at the nearest recovery. An opposing event, different/null possession, or different period breaks the chain. A shot with null possession is skipped. Negative time gaps and gaps above 30 are rejected. The current code relies on the API's ordered input; add tests for nearest recovery, null possession, wrong period, equal timestamps, and multiple shots. Avoid the Casual wording “turned a recovery directly into a shot” if there are intervening passes; use the measured sequence wording instead.

### Legacy compatibility

Original totals and existing tests pass, but event-content compatibility fails as finding 1 demonstrates. API response additions are otherwise additive. Preserve original evidence and version any intentional changes.

### Graph integrity

The new metric-window node is added before its edges, so the claimed missing-window-edge issue was not reproduced. All three new fixtures pass the graph endpoint/unique-node tests. Add tests at intermediate replay prefixes and for multiple completed windows, ensuring every supporting event and edge endpoint exists and repeated reads produce stable IDs.

### Candidate IDs and quiet-match behavior

Normal generated story IDs are unique. Candidate selection does not itself deduplicate IDs; dictionary-equality comparisons are not an ID uniqueness check. The Azure result validation rejects unknown and duplicate selected IDs, but a malformed duplicate candidate set deserves an explicit invariant/test if the selector will accept external story objects. The verified truncation issue is finding 4.

Quiet match generates no stories; `explain([])` returns before calling Azure. Its summary is rendered from deterministic counts and the explicit no-pattern message, and the frontend has a fallback that displays that summary when there are no sections. This protects that path from model-invented narration, but “zero hallucinations” is too broad a system-wide guarantee. Add a mocked-client test proving the provider is not called for quiet-match/empty candidates.

### Reset/polling races

The dashboard is keyed by match ID and scenario ID. Changing scenario creates a new match, unmounts old polling/playback, and resets the Catch Me Up generation. Abort checks guard late results, so no new cross-session polling race was established in source review. Browser/component verification is still needed; the disabled selector currently prevents the requested mid-playback interaction.

## Recommended fix order

1. Restore/version the legacy fixture and add the old-event replay regression.
2. Fix end_y qualification and add boundary/missing-field tests.
3. Enable scenario switching during playback and browser-test stale responses/reset.
4. Resolve goal/change candidate overflow and test mocked Azure behavior.
5. Correct the report, run the full checks, and record honest browser/demo results.

Return the corrected branch and an updated delivery report for re-review. Keep unrelated files untouched and do not merge the feature before these issues are resolved.
