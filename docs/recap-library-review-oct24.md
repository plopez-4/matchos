# Nine-match recap audit — 24 October 2026

This is a developer source review by Codex, not a human fan study, a pronunciation audition or proof of general factual accuracy. No website was deployed and no Azure resource/quota was changed.

## Frozen protocol

The deterministic report covers all nine versions at 20:00, halftime, 75:30 and full-time, in Casual and Analyst: 72 English/Spanish pairs. A separate recount rebuilds the seeded feeds and checks current scores, observed evidence IDs, goal chronology, linked recoveries/shots/goals, team passing totals and selected player contributions. These checks verify the structured facts; they do not establish that AI prose expresses those facts correctly.

The live matrix covers eleven situations in both audiences, 22 requests returning 44 language paragraphs. It includes every version plus halftime and the 62:30 Palace equalizer. Each selected version is verified against the running backend before inference. Requests are paced thirty seconds after completion. Every response, rejection, app-budget fallback and latency is preserved; failed slots are never rerun within the same report. Temporary matchday groups are released. No provider key is read by the evaluator.

Source fingerprints, actual writer modes, evidence packets, selected stories and observed goals are saved alongside the text. The writer/model reviewer remain fallible. A model-review pass is not editorial acceptance.

## Original v14 findings

[Full live report](recap-library-v14-live-oct24.json): all 22 slots completed; 14 returned Azure prose and eight returned deterministic fallbacks. The fallbacks were two ambiguous-window rejections, two missing scoring connections, one model-review rejection and three application AI-budget/concurrency limits. Those limits are not Azure 429s. All temporary groups were released.

The [72-pair deterministic baseline](recap-library-deterministic-oct24.json) and 22 live packets passed the [structured source recount](recap-library-source-audit-oct24.json). That did **not** make the live wording reliable:

- Both Brighton quiet-match audiences attached 55:10 to Muniz's recovery and placed the shot ten seconds later. Recorded recovery: 55:00; recorded shot: 55:10.
- Both no-new-goal Palace audiences made the same recovery/shot-clock error for Wissa and Barnes.
- The quiet Brighton Analyst paragraph inferred a tightly contested encounter from the goalless state. The quiet derby Casual paragraph invented high tension.
- The first-half Palace Casual wording attributed completing three “team passes” to Wissa; the recorded sequence credits him one pass. The collective modifier did not clearly identify the team as the subject.
- Several accepted paragraphs repeated the score or ended in generic conclusions. Spanish examples included time-of-day phrasing and “intentos salvados.” These are language/editorial issues, distinct from score/count failures.

Four actual accepted pairs are preserved in `backend/tests/fixtures/library-v14-accepted-errors.json`. Their eight language outputs now have rejection coverage. The full failed report remains unchanged as evidence rather than being replaced by later successes.

## v15 correction and follow-up

The writer now receives explicit recovery and shot clocks and ordered recorded actions for non-scoring transitions. Conservative checks reject attaching a shot's clock to the recovery, expand individual-versus-team pass attribution checks to the observed gerund/infinitive forms, and reject the captured unsupported tension/contested descriptions. Correct explicit and relative EN/ES timing forms retain regression coverage. The model still authors the entire paragraph; no commentary sentences are inserted or repaired by the server. Spanish prompting clarifies elapsed-minute clocks and saved-shot wording.

429 backend tests passed after these changes. The [v15 live report](recap-library-v15-live-oct24.json) is a distinct frozen follow-up over the same situations, not a replacement for v14 or a controlled statistical comparison. All 22 slots completed: five returned Azure prose and seventeen returned deterministic fallbacks (three ambiguous windows, three missing scoring connections, four missing contributions, two model-review rejections and five application-budget/concurrency limits). All temporary groups were released. The last cases therefore do not establish live AI quality for those versions.

An early v15 sample confirms a remaining relationship-checking gap: the Palace Casual paragraph describes Tomiyasu's second pass as going back to Tomiyasu himself. The actual recipients of his two passes were Lerma and Wharton. Another accepted halftime paragraph calls the first half balanced from the tied score. Rico Lewis's two recipients in that halftime paragraph were correct; an initial commentary observation to the contrary was corrected after inspecting the exact event list.

The Palace Analyst sample also repeats 15:11 and describes a combined “shot and goal at 60:11,” obscuring the separate 60:10 shot and 60:11 goal. The Wissa Casual sample correctly distinguishes his one completed pass from the team's three. Overall, v15 did not pass either the consistent-writing or factual acceptance gate. More fallbacks are not an accuracy improvement statistic.

## v16 targeted relationship correction

Source-backed checks now reject explicitly named recipients that do not belong to the claimed passer's recorded passes within the checked individual completed-pass-count constructions. The actual Tomiyasu self-recipient output has EN/ES regression coverage, alongside a positive test for Lewis's correct recipients. “Balanced first half” is covered as an unsupported inference. For a non-scoring transition, both exact action clocks can express the measured duration without a redundant numeric sentence. Correct timing and attribution forms remain accepted.

The [six-request focused follow-up](recap-library-v16-focused-oct24.json) covers the Palace equalizer, quiet Brighton transition and first-half Palace exchange in both audiences. It is deliberately separate from the two full matrices and cannot replace a final all-nine-version acceptance run. Production budget settings and Azure allocation were not raised; development code reloads reset the process counters as documented. The application's conservative reservation budget can be reached before actual provider-call count or subscription credit.

All six slots completed and both temporary groups were released. Two Palace equalizer requests returned Azure prose; developer EN/ES review found correct scorer, recoverer, goal/recovery clocks and five team passes, with no captured self-recipient error. They still repeat the score and include generic closing language. The other four returned content fallbacks: one missing selected contribution, one ambiguous statistic window, and two missing scoring connections. There were no provider 429s or application-budget fallbacks in this focused run. Its main demonstrations did not work in both audiences across all selected situations, so the release gate remains open.

Final checks: 438 backend tests, shared formatting and credential scan. The structured source recount covers 72 deterministic pairs, 22 v14 pairs, 22 v15 pairs and six v16 pairs; a passing recount is distinct from acceptance of their prose. The two full runs and focused follow-up contain 50 Catch Me Up requests in total; internal selector/writer/reviewer calls can be more numerous. No further live requests were made to improve the acceptance counts.

**Release gate remains open:** the new checks cover observed defects, not complete natural-language entailment. Repetition, language quality, possible false rejections and remaining relationship/clock phrasing need source review before presenting AI writing as consistently reliable. The raw capture files retain their initial pending-editorial metadata; this document records the subsequent developer review. The five-person comprehension test and actual bilingual listening check are still separate, uncompleted gates.

## Reproduce

```powershell
.venv\Scripts\python.exe scripts\evaluate_match_library.py --output docs\recap-library-deterministic-new.json
.venv\Scripts\python.exe scripts\evaluate_match_library.py --live --output docs\recap-library-live-new.json
.venv\Scripts\python.exe scripts\audit_recap_sources.py docs\recap-library-deterministic-new.json docs\recap-library-live-new.json --output docs\recap-library-source-audit-new.json
```

Live mode uses the existing locally configured backend and its normal application/provider budgets. A new report makes paid provider calls when AI is configured; do not repeatedly rerun failing samples to manufacture an acceptance rate. Preserve the frozen source, outputs, service failures and independent editorial conclusions.
