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

Checks at that stage: 438 backend tests, shared formatting and credential scan. The structured source recount covers 72 deterministic pairs, 22 v14 pairs, 22 v15 pairs and six v16 pairs; a passing recount is distinct from acceptance of their prose. Those two full runs and focused follow-up contain 50 Catch Me Up requests in total; internal selector/writer/reviewer calls can be more numerous. The later investigations below are separate reports and do not replace those results.

**Release gate remains open:** the new checks cover observed defects, not complete natural-language entailment. Repetition, language quality, possible false rejections and remaining relationship/clock phrasing need source review before presenting AI writing as consistently reliable. The raw capture files retain their initial pending-editorial metadata; this document records the subsequent developer review. The five-person comprehension test and actual bilingual listening check are still separate, uncompleted gates.

## Rejected-draft investigation and v17 matrix

The [six-request v16 capture](recap-v16-rejection-capture-oct24.json) preserves original drafts, the one permitted AI revision and internal rejection reasons. This is an opt-in development endpoint restricted to loopback clients and replays owned by their session; it returns 404 in production. Normal fan responses do not contain rejected drafts. Capture is request-local, bounded and not retained by the server. It uses the ordinary inference budget, rate limits, cache and selected evidence. An empty trace can mean a cached or unattempted writer.

This capture separated actual errors from false rejections:

- Bruno's draft assigned 15:10 to a pass actually recorded at 15:09. That remains an error.
- The quiet Spanish revision used “realizara un remate” rather than the few verbs recognized by the old duration check. The action was correct.
- Explaining the documented 30-second rule after a verified transition is a rule definition, not a new rolling statistic.
- “Three completed team passes” was incorrectly parsed as an individual completing a numeric count named “team.”

The resulting [v17 all-nine matrix](recap-v17-nine-version-live-oct24.json) completed 18 requests: nine versions × two audiences, both languages in each request. Twelve returned Azure prose; six used deterministic fallback: one model-review rejection, three missing scoring connections, one ambiguous window and one missing contribution. No provider-capacity or app-budget fallback occurred. All temporary replay groups were released. This smaller matrix covers every version but excludes the extra halftime and 62:30 Palace cases in the original eleven-situation protocol.

Actual accepted defects remained: the derby Analyst Spanish paragraph called 15:10 the goal time instead of 15:11; Fulham's Casual recap assigned the equalizer and later go-ahead goal to 70:11, although the equalizer was at 60:11; quiet derby Casual called a completed pass “precise,” which the feed does not measure. Model review passed those outputs. Correct rejections also remained: one Palace draft attached a future recovery to an earlier goal, and several original drafts attributed every team pass to one player.

The rejected revisions exposed further false rejections. Wissa's one completed pass followed by two more team passes is a valid three-pass decomposition. “Ugarte and Fernandes completed two more” is an explicit joint subject, not Fernandes alone. A recovery-to-shot explanation can refer back across a scoreboard sentence when its exact linked clocks, duration and pass partition are all established. A fully timestamped quiet route can span several short sentences. Those captured correct forms now have positive regression checks; wrong remainders, individual attribution, action clocks and duration retain negative checks.

The v18 candidate adds these bounded scope/count checks and rejects the captured explicit goal-clock, equalizer-clock and unsupported pass-quality claims. It still accepts or rejects the model's entire paragraph; it does not insert commentary or repair sentences. These EN/ES pattern checks are not a general language parser or a proof of factual entailment. The [independent source recount](recap-rejection-source-audit-oct24.json) checks the saved structured facts separately from prose.

## v18 all-nine verification and named v19 evidence

The [v18 all-nine matrix](recap-v18-nine-version-live-oct24.json) also completed all 18 requests: twelve Azure recaps and six deterministic fallbacks. The fallback reasons were two model-review rejections and one each for a missing scoring connection, ambiguous statistic window, unsupported interpretation and wrong recovery clock. No application-budget or provider-capacity fallback occurred; all replay groups were released. These are writer modes, not factual acceptance rates or a controlled comparison with v17.

The pass-quality rejection caught the captured “precise pass” claim. The late Fulham Analyst paragraph used the correct goal order, and the late derby Casual paragraph correctly credited the final three passes collectively. However, the latter assigned the historical 10:11 City goal to Haaland; Doku actually scored it. Both early derby audiences still assigned 15:11 to the goal attempt rather than its 15:10 shot, and Palace Analyst combined a shot and goal under 75:11. The no-new-goal Palace translation also leaves the intermediate passer ambiguous. The matrix therefore fails factual/editorial acceptance despite twelve successful model reviews.

The v19 candidate enriches **every observed score transition** with the actual scorer, team and separate shot/goal clocks; those fields come from recorded events, not prose generation. The writer also receives individual pass totals counted directly from the verified scoring path. The active writer and reviewer instructions distinguish historical scorers, shot/goal clocks and exact pass recipients. New conservative checks reject the captured explicit shot-clock and historical-scorer constructions. They do not establish accuracy for every possible phrasing.

The [v19 deterministic report](recap-v19-deterministic-oct24.json) rebuilds all nine versions at four snapshots in both audiences: 72 EN/ES pairs. Evidence packets remain within 32 KiB. This checks the enriched source context, not live prose quality. The [v19 live follow-up](recap-v19-focused-live-oct24.json) is deliberately focused on three situations: early derby, repeated Palace replies and late derby equalizer, in both audiences. It cannot replace a final all-nine run on this candidate.

All six focused requests completed: two returned Azure prose and four returned deterministic fallback. Reasons: two ambiguous statistic windows, one missing scoring connection and one explicit wrong shot clock. Both temporary groups were released; no provider-capacity or application-budget fallback occurred. Source review of the two displayed AI pairs found the selected scorers, clocks, pass totals and equalizers consistent with the recorded events. Historical context now names Wissa's 15:11 goal correctly in Palace Analyst, and Doku's 10:11 goal and Diallo's 50:11 equalizer correctly in derby Analyst. Generic closing language and repetition remain editorial issues; this is not a human acceptance study or proof of general correctness.

The four fallbacks are not interchangeable failures. The early derby revisions correctly distinguish pass 15:09, shot 15:10 and goal 15:11, but the scope validator rejects the separately enumerated two saved shots at 16:40 and 18:40 because their sentence lacks a repeated rolling window. This is a remaining false-rejection case. The Palace Casual revision omits the required team-pass total/duration and implies Kamada passed to both intermediate players; the source credits one pass to him. The late derby Casual revision gets the historical scorers right but still says “shot and goal at 75:11”; the explicit shot-clock guard rejects it because the shot is at 75:10. Failures were preserved and not retried within the report.

The updated [independent recount](recap-rejection-source-audit-oct24.json) covers all five new reports: 120 saved EN/ES pairs, with no structured source mismatch. It checks enriched scorer/team/shot/goal fields against the original feed as well as the selected metrics. This investigation made 48 Catch Me Up requests across four live reports; internal model calls are more numerous. App limits and Azure allocation were unchanged. Development reloads reset process counters as documented; these tests do not demonstrate a durable multi-visitor spending cap.

**Current verdict: reliability gate remains open.** The captured defects and false rejections have substantially more regression coverage, but the final candidate has only a focused live check. Two of six focused requests returned AI prose, and correct enumerated-shot descriptions are still being rejected. Resolve that scope case with source-backed positive and negative tests before spending more calls on another complete frozen matrix. Then repeat the independent source review, real five-person comprehension check and bilingual listening/browser walkthrough. No deployment was performed.

Final local verification: 474 backend tests passed, shared formatting passed, and the credential scan found no matching patterns in current files, built assets or reachable local Git history. The heuristic scan is not a guarantee that every possible secret format is absent. CI also runs frontend tests/build, dependency audits and a production container check.

## Reproduce

```powershell
.venv\Scripts\python.exe scripts\evaluate_match_library.py --output docs\recap-library-deterministic-new.json
.venv\Scripts\python.exe scripts\evaluate_match_library.py --live --output docs\recap-library-live-new.json
.venv\Scripts\python.exe scripts\audit_recap_sources.py docs\recap-library-deterministic-new.json docs\recap-library-live-new.json --output docs\recap-library-source-audit-new.json
```

Live mode uses the existing locally configured backend and its normal application/provider budgets. A new report makes paid provider calls when AI is configured; do not repeatedly rerun failing samples to manufacture an acceptance rate. Preserve the frozen source, outputs, service failures and independent editorial conclusions.

Use `--capture-rejections` only for the local development investigation. The ordinary live evaluation route records displayed prose and modes without exposing drafts. Use repeated `--case NAME` flags for a declared subset; the report records selected situations, planned requests and actual version coverage. Do not present a focused subset as a complete all-nine acceptance run.
