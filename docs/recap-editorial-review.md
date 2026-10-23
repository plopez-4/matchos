# Recap editorial review — 2026-10-22

## What was evaluated

The frozen baseline, `fan-narrative-v8-chronology`, completed **20 requests: ten different match snapshots, each in Casual and Analyst, with English and Spanish returned together**. It is not twenty distinct matches or twenty independent fan sessions. Every result, including failures, is retained in [the baseline report](recap-editorial-evaluation.json), alongside exact prompts and their fingerprints. Temporary demo slots were released.

## The baseline did not pass the editorial gate

- 5 requests returned model-written prose; this was an integration result, not five verified good explanations.
- 4 quiet requests deliberately used factual summaries without generating a narrative.
- 11 requests fell back: 3 missing-contribution checks, 3 unsupported-interpretation checks, 2 other shape/reference failures, 2 Azure 429 responses and 1 time-scope failure.
- Inspection of the five accepted samples identified unsupported pressure, chance quality, assist wording or related embellishment in four. Those four pairs were saved as stable regression fixtures and are now rejected by the local checks. The opening-minute analyst sample was overly detailed despite insufficient selected evidence; such empty-coverage plans now deliberately skip generation.

This inspection was performed by Codex against the supplied evidence. It was not an independent human review or a consumer study. A model-review pass alone was demonstrably insufficient.

## Corrections made from the run

1. The writer gets per-action chronology: the goal-producing link, other earlier attempts and attempts afterward. Full-window patterns cannot be framed as the build-up to an earlier goal. These are structured facts, not commentary lines.
2. The writer receives compact selected facts rather than unrelated recent raw rows. The independent review still receives the full evidence packet.
3. Single recovery-to-shot events are checked against their actual event clock and elapsed time, rather than incorrectly requiring a rolling-window range. Regression checks reject wrong times and elapsed values.
4. Positive pressure/threat, chance-quality and internal metric-name leakage are rejected. Spanish scoreboard wording such as `domina 1–0` is distinguished from a tactical dominance claim.
5. Repeated creator/shooter explanations without another observable fact are rejected. A sentence adding the goal outcome, later attempts, rule timing or a limitation can still contribute useful information.
6. Selected scorers and their goal times survive factual fallback, and limited coverage is labeled honestly.
7. One bounded AI revision is available after a focused draft fails a content check. The revised whole paragraph must pass local checks and then separate model review. Invalid shapes/unknown IDs are not repaired; failed revisions, budget exhaustion or provider errors still fall back. Successful live samples below did not require this revision; its success, failure and budget behavior are covered with mocked-provider tests.
8. Prompt fingerprints cover writer, revision and reviewer instructions, temperature and version. Cache identity includes the fingerprint. Follow-up reports also preserve source hashes. Evaluation spacing now starts after request completion, reducing overlap; this does not guarantee that Azure rate limits cannot occur.

## Follow-up evidence and its limits

The v8.1 follow-up recorded four rejected drafts. A v8.2 spot check accepted both perspectives but revealed residual repetition; v8.3 added a repetition check. These intermediate results remain separately labeled in their JSON artifacts rather than being merged into the baseline.

The final **v9 bounded-revision** [live spot check](recap-editorial-v9-live.json) reused the baseline fixture ID for an exact seeded goal-pattern comparison. Casual and Analyst both returned AI-written English/Spanish paragraphs that passed the local checks and separate review. They distinguish the goal attempt from the two later attempts; Analyst adds link-rule context. The same text is retained for display and narration. Some wording could still be tighter. Two successful requests are not a broad accuracy or acceptance-rate benchmark, and they are not a new twenty-case run on v9. The final single-event clock correction has targeted local coverage; this final live spot check exercised a rolling player-pattern case.

Final checks: **298 backend tests, 75 frontend tests, production build and changed-component formatting passed**. The existing Starlette/httpx deprecation warning remains.

## Real fan trial

The [five-fan protocol](fan-evaluation.md) and [blank results sheet](fan-evaluation-results.csv) are ready. No participant trial has been conducted. Test whether fans understand who contributed, what happened repeatedly, how the attempts relate to the goal, and what to do next. The version and displayed paragraph must be recorded for each trial. Do not claim improved engagement or comprehension before collecting those observations.
