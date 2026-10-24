# Full nine-match review and corrections — 24 October 2026

## Frozen v23 result

The [live report](recap-v23-nine-version-live-oct24.json) completed eighteen requests: every one of the nine prepared match versions in Casual and Analyst, with English and Spanish in each response. Thirteen returned Azure prose; five returned the factual fallback. Reasons were two missing scoring connections, two ambiguous statistic windows and one unsupported interpretation. No provider-capacity, app-budget or HTTP failure occurred. All three temporary replay groups were released. Failed slots were preserved rather than retried into successes.

This is the nine-version, nine-situation protocol. It excludes the additional halftime and Palace 62:30 situations in the earlier eleven-situation reports. Source hashes and actual writer version identify the frozen candidate. These counts are writer modes, not a factual acceptance rate or a controlled comparison with earlier runs.

The [72-pair deterministic baseline](recap-v23-deterministic-oct24.json) covers four snapshots in both audiences for all nine versions. The [separate source recount](recap-v23-source-audit-oct24.json) found no structured source mismatch in its 72 pairs plus the eighteen live pairs. It checks observed evidence, scores, scorer/shot/goal clocks and selected metrics; it does not certify the model's prose.

## Source review of displayed text

The [case-by-case editorial record](recap-v23-editorial-review-oct24.json) reviews all eighteen displayed English/Spanish pairs. No incorrect displayed score, scorer/time pair or measured total was found. Seventeen displayed pairs had no source error found in this developer review; the remaining pair has material pass-owner ambiguity and is not approved as factually clear. This is not a real fan study, pronunciation audition or proof of general factual accuracy.

The problem appears in Palace/Newcastle's no-new-goal Casual recap. It reads as if Wissa is “passing to Joe Willock, then Tino Livramento, Anthony Elanga, and finally Harvey Barnes.” The Spanish has the same direct-recipient list. The source route is Wissa → Willock → Livramento → Elanga → Barnes. Wissa makes only the first pass. Naming every player on the route does not establish who made each pass. The separate model review passed this output, demonstrating why a review pass alone cannot close the gate.

The other twelve displayed AI pairs have their scorer order, current scores and selected action counts consistent with the feed. Some repeat the score in a generic closing sentence. Casual and Analyst are very similar in the open Brighton case. The derby Casual phrase “Mount completed a sequence of three passes involving…” names the correct collective sequence but would be clearer with United as the subject. These are editorial findings, distinct from wrong numeric facts.

All five displayed factual fallbacks match their source facts. Four fallback requests nevertheless contain a source-correct draft rejected by wording checks:

| Situation                       | Valid wording rejected                                               | Cause                                                                                                                                                              |
| ------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Repeated Palace replies, Casual | Kamada made one completed pass; Lerma and Wharton completed two more | The verified 1+2 partition parser missed “made one completed pass” and Spanish subjunctive “completara un pase.”                                                   |
| Quiet derby, Casual             | “as the match passes 62 minutes”                                     | The football-pass check treated the clock verb “passes” as a quantified passing claim. The original Spanish also used the valid relative form “tras” the recovery. |
| Quiet derby, Analyst            | Ten-second recovery-to-shot sequence, within the thirty-second rule  | The valid duration plus rule definition was mistaken for an unscoped shot statistic; the timed-route coverage also disallowed the extra valid duration.            |
| No-new-goal Palace, Analyst     | Ten-second recovery-to-shot event, within the thirty-second rule     | The same scope issue rejected the correct original; its revision then introduced Spanish “asistio,” which the assist guard rejected.                               |

The remaining first-half Palace Casual revision omits the required team-pass total or shot-duration detail and ambiguously credits Wissa with multiple passes. It is not treated as a clean false-rejection example.

## Corrections after the freeze

The v24 candidate changes validation only; the match data, analytic rules, writer prose generation and feature set remain unchanged. The server still accepts or rejects whole paragraphs and returns the factual fallback. It never repairs the AI's sentences.

- A bounded EN/ES direct-recipient check compares known named passers with their actual recorded recipients. It rejects the captured Wissa list, allows explicit subject changes and collective route wording, and allows a player such as Bassey to have multiple direct recipients when the source records them.
- The same source-count proof accepts the new one-pass-plus-two-more wordings. Wrong individual counts and wrong remainders remain rejected.
- A match clock “passes 62 minutes” does not provide a football passing statistic. Adding an actual three-pass claim still needs its proper scope.
- A bounded recovery-to-shot continuation may state its actual duration and the actual rule limit after the corresponding source clocks. Duration, threshold, seconds units and within/outside relation are checked separately. Wrong values or units remain rejected.
- Spanish “tras” and shot noun forms retain the distinction between the actual recovery and shot clocks. Attaching the shot time to the recovery remains rejected.

All five captured source-correct drafts/revisions above now pass local validation; these represent four requests, with both original and revision covered for quiet derby Analyst. The unclear Wissa ownership output is rejected in both languages. The other twelve reviewed AI pairs retain acceptance. A new full bilingual example with each actual passer named passes too. The accepted ambiguity and failed drafts are preserved in `backend/tests/fixtures/v23-nine-match-review.json`.

The full-suite check also caught an older positive example that assigned Wharton the pass actually made by Mateta. Its text now names the recorded Mateta → Sarr pass explicitly; the former ambiguous version is retained as a negative test. The underlying event fixture was not changed.

## Current release decision

The frozen v23 candidate did not meet a clean reliability sign-off: one accepted pair was materially ambiguous and four requests contained false rejections. The new v24 checks address those captured findings. Local revalidation of recorded drafts is not a new model-review pass or a live all-nine acceptance result. The separate [v24 focused confirmation](recap-v24-focused-live-oct24.json) covers the three affected situations in both audiences and preserves its own actual modes and failures.

The focused run completed six requests: four Azure recaps and two factual fallbacks, with no capacity, budget or HTTP failures; all temporary groups were released. The [focused editorial record](recap-v24-editorial-review-oct24.json) reviews each pair. Source review found the four displayed AI pairs consistent with the recorded scores, goal chronology and selected actions. Both rule explanations now returned AI prose with the actual ten-second duration and thirty-second limit. The no-new-goal Casual route explicitly distinguishes Wissa's pass from Willock's next pass, although later hops remain compressed.

The Palace Analyst original incorrectly gave Kamada both Lerma and Wharton as direct recipients, and the new guard rejected it. The revision retained the Spanish ownership error and omitted required scoring-sequence detail. Its English also exposed a false diagnostic: the following goal scorer was mistaken for an extra recipient. Quiet derby Casual had unsupported precise-pass praise in its original; its source-correct revision used the ordinal clock form “match passes the 62nd minute,” which still triggered the statistic check.

The final v25 validation correction recognizes ordinal clock forms and separates a following named scoring action from a recipient list. Tests preserve rejection of an actual wrong recipient even when that player is followed by a scoring verb. The captured quiet Casual revision passes, as do all four displayed AI pairs from the focused run. Those final changes were verified on the actual saved outputs and negative cases; no further paid inference was run afterward. The final candidate therefore has a focused predecessor check plus static regression evidence, not a complete live acceptance run of v25.

The independent recount now covers all 96 saved pairs: 72 deterministic, eighteen frozen live and six focused. The source checks pass; that does not certify natural-language attribution. This review made 24 Catch Me Up requests across the two live reports; internal model calls are more numerous. Earlier results remain unchanged and are not replaced by later successes.

Final local verification: 557 backend tests passed. Shared formatting and credential checks accompany the GitHub update; CI also runs frontend tests/build, dependency audits and the production container check.

The AI reliability gate remains open. Verify the final candidate across the frozen matrix before calling it consistently reliable, and complete the real five-person comprehension test and English/Spanish listening/browser walkthrough. The shared deterministic analytics and evidence graph passed the source recount. No app budget, Azure allocation or hosting setting was increased, and deployment remains on hold. Development reloads reset process counters as already documented.
