# Live Azure verification — 22 October 2026

## Connection gate

Verified against the user-started local backend after private key entry. No keys were read by the agent or saved in this report. The user terminal must remain open; this process configuration is not persisted.

One fresh authored featured match was advanced to 25:00 through the matchday API. A Casual Catch Me Up request returned:

- Selector mode: azure; no fallback. Evidence retrieval and selection validation succeeded. The backend added the protected `shots:home:1200` change to complete coverage.
- Writer mode: azure; no fallback. English and Spanish paragraphs were returned.
- Review: model_review_passed.
- End-to-end catch-up latency: 6.28 seconds for this single sample; this is not a performance benchmark.
- Covered plan: the authored goal at 15:11 and the retained Home shot increase in minutes 15–20.
- The temporary verification matchday was released successfully.

This proves real selector/writer/reviewer integration for one sample. It does not establish reliability, universal factual grounding, audience quality or live Azure Speech. Speech status was unavailable; device voice remains a separate option.

## Quality finding

The accepted English paragraph included “increased their threat” after citing a three-versus-zero shot increase. That interpretation is stronger than the directly measured count. The passing phrase “in this period” also needs a more explicit window, because the historical shooting comparison and recent passing aggregate cover different intervals. The Spanish wording “ninguna intención” for no attempts is awkward. Automatic model review passed despite these concerns; do not market it as proof of semantic correctness.

This finding led to the revisions and acceptance gate below. The user restarted the same private terminal with auto reload; credentials remained in that terminal's process environment.

## Grounding revision and failed attempts

Versions 4–4.3 added conservative interpretation/window checks. Fresh busy recaps repeatedly fell back because the model omitted the baseline window or used ambiguous measurement language. One passing sample did not establish reliability. Requiring verbatim copying of server sentences was insufficient, so version 5 moved measurement rendering into actual server composition.

Version 5 initially accepted Analyst text but rejected Casual text; subsequent checks accepted Casual but Azure returned HTTP 429 during Analyst review. These runs were not counted as full acceptance. The final runner spaces the two busy requests by 60 seconds and does not automatically retry failed model calls. Explicit negative limitations such as “these counts do not prove dominance” are distinguished from positive dominance claims.

Version `fan-narrative-v5.1` validates incoming references and prose bounds, discards model statistical sentences, inserts canonical bilingual measurements, removes unrendered optional aggregate references, then validates and separately reviews the assembled paragraph. Known unsupported interpretation checks run before composition as well, so discarded sentences cannot hide those violations. Analyst shooting text adds the limitation that counts do not establish possession, control or chance quality. The focused label says **AI-assisted recap · server-calculated metrics**. This division of work preserves the deterministic analytics core; the context model and reviewer remain fallible.

## Final bounded acceptance result

The live acceptance runner `scripts/verify_live_ai.py` confirmed the loaded writer version, then checked the following cases. Every recap includes English and Spanish. Full outputs for this earlier version are saved in [the version 5.1 results](live-azure-quality-results-v5.1.json).

| Case                        | Result                                                                      |
| --------------------------- | --------------------------------------------------------------------------- |
| Busy, Casual                | Azure selector, assembled writer and separate reviewer passed; 7.20 seconds |
| Busy, Analyst               | Azure selector, assembled writer and separate reviewer passed; 5.97 seconds |
| Quiet, Casual               | No qualifying change; intentionally rule-based, no writer call              |
| Quiet, Analyst              | No qualifying change; intentionally rule-based, no writer call              |
| Simulated provider HTTP 503 | Both rule-based paragraphs preserved exactly                                |

The busy plans retained the goal at 15:11 and `shots:home:1200`: Manchester United recorded three shots in 15:00–20:00 versus zero in 10:00–15:00. Neither language presented that spell as current activity at 25:00. Temporary verification matches were released. These are authored synthetic fixtures and one final bounded run, not a reliability or latency benchmark. Earlier rate limiting remains relevant to demo pacing.

Validation: **212 backend tests**, **72 frontend tests**, production build and diff whitespace check passed. A backend dependency deprecation warning remains. Regression coverage includes wrong model counts being replaced by server measurements, invalid references/markup rejected before composition, exact reviewer/display/audio text identity, unsupported claims, bilingual scope checks and quiet/provider-failure behavior.

No keys were read or persisted by the verification runner. Keep the user-owned backend terminal open. This gate does not verify Azure Speech, all match phases, every pattern type, or general semantic correctness. The browser preview [shows the unchanged compact page with its rule-based full-time recap](grounded-recap-page-preview.png), not the accepted Azure sample.

## Player-impact revision

Version 6 adds named player contributions and creator/recipient links. Its first bounded run passed the automated checks, but manual review found an incorrect Spanish phrase: “a falta de 25 minutos” at 25:00 elapsed. The model reviewer incorrectly accepted it. The Casual draft also cited a selected goal without describing it explicitly. The [initial version 6 results](live-azure-quality-results-v6-initial.json) are retained as evidence of those limitations; they are not a full quality approval.

Version 6.1 inserts canonical selected-goal sentences alongside canonical player measurements. Model context is restricted to current score and elapsed clock, with explicit rejection of AI countdown phrases. This revision's bounded results are in [the latest verification report](live-azure-quality-results.json). See [player rule definitions and tests](player-impact.md).

Version 6.2 removes model context sentences that redundantly retell a selected canonical goal. If no independent context remains, the server supplies the observed current score/phase/clock. The live counterexample is covered by a regression in both languages. Final bounded checks passed: busy Casual and Analyst both used Azure selection/writing/review; quiet Casual and Analyst intentionally used no-selected-story rule recaps; simulated HTTP 503 preserved the player-based fallback. English and Spanish retained the goal at 15:11 and Bruno Fernandes's three direct pass-to-shot links to Bryan Mbeumo in 15:00–25:00. No countdown mistranslation was present in the final sampled paragraphs. These results remain a small authored-data sample, not proof of general semantic correctness.

Final regression validation: **244 backend tests**, **75 frontend tests**, production build and diff whitespace check passed. The existing backend dependency deprecation warning remains. Azure Speech configuration/playback was not part of this gate; narration reconstruction and exact display/audio text are covered by tests.

## AI authorship revision — v7.2 (2026-10-22)

The focused recap now sends structured selected facts and event rows without prewritten player commentary or canonical sentences. Azure writes the whole bilingual paragraph. Accepted prose reaches the reviewer, display and narration unchanged; rejected prose falls back as a whole.

Live iterations exposed both legitimate rejections (invented assist counts and wrong analysis-window bounds) and parser limitations (Spanish `hasta el` clock connectors and an explanatory sentence referring back to a measured passage). The original v7 failed run is retained in `live-azure-quality-results-v7-initial.json`. The most recent full multi-case report in `live-azure-quality-results.json` is mixed: its casual draft was rejected by semantic review, its analyst draft passed, quiet selections skipped generation as intended, and simulated provider failure retained the factual fallback. It is not an all-pass claim.

After final prompt and validation refinements, a separate live casual request passed both local coverage checks and independent semantic review; its actual bilingual output and selected evidence are saved in `live-ai-authorship-casual.json`. No commentary sentences were inserted or repaired. The final focused regression run passed 91 tests. The complete backend run before the final two assist-rejection cases passed 253 tests. Review is fallible, and descriptive language in accepted samples is not a mathematical factual guarantee or a broad quality benchmark.
