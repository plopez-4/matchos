# Matchday and Match Radar: first milestone

Implemented 2026-10-08 in the original repository. This is a transparent baseline for later comparison with personalized Azure decisions, not evidence of engagement improvement.

## Try it

Start the ordinary local backend and frontend, open the **Matchday & Radar** tab and select **Start matchday**. Three authored synthetic fixtures advance on one server-owned clock:

- Manchester United–Manchester City: the prominent fixture can legitimately earn an early recommendation.
- Crystal Palace–Newcastle United: a later burst and comeback demonstrate discovering a game elsewhere.
- Brighton–Fulham: a restrained match demonstrates withholding alerts.

Each covers 93 match minutes using sparse modeled possessions, sender/recipient passes, shots, linked goals and period markers. These are not reconstructions of real matches, real player performances, complete touch-by-touch feeds, standings calculations or live video. Authored role labels are test metadata and do not affect ranking. Existing full-match scenarios remain available in the original match view.

At 1x, each playback tick advances 30 match seconds after one real second plus request time. At 4x a full run takes roughly 47 seconds plus request time. Pause stops requests; it does not leave an autonomous background simulation running. Matchday clock advancement is distinct from real-world wall time.

## Observed-event scoring

Radar reads only events already ingested up to the common clock. The matchday start response contains no future fixture feed. Windows use `(now - 300, now]` for recent shots and `(now - 600, now - 300]` for previous shots, clipped to the beginning of the feed.

| Signal                                                                 | Points |
| ---------------------------------------------------------------------- | ------ |
| Score difference at most one goal                                      | 25     |
| At least four recent shots, with at least one from each side           | 30     |
| Recent shots exceed the previous window by at least two                | 20     |
| Close score after 70 minutes                                           | 15     |
| A recorded goal in the previous three minutes while the score is close | 10     |

Qualification additionally requires a close score, recent two-sided shot activity and a total of at least 65. Finished matches are excluded. Rank by points, latest observed shot time, then match ID to resolve ties deterministically. No club popularity or authored future story gets a ranking boost.

The score is a reproducible **signal index**, not a probability, forecast, excitement ground truth or measured fan response. Shots do not measure chance quality. This baseline deliberately misses some compelling one-sided contests and scoreless tactical games; compare those limitations in future evaluation rather than hiding them.

The page displays scores, per-team recent shots, previous-window count, components and supporting event IDs/events. Score evidence includes observed goals. It does not claim that teams are fighting for European qualification or infer tactical intent from counts alone.

## Alerts and following

An in-page Heating Up notice is generated on a qualifying leader transition, with a ten-match-minute per-match cooldown. Retrying a tick returns the same notification ID; repeat reads do not generate new notices. The UI clears cooled recommendations and expires notices. There are no OS/browser push permissions, external messages or notification delivery services in this milestone.

Follow & Catch Me Up opens the selected synthetic match's briefing and observed event timeline. Briefings reuse the existing audience/evidence/fallback system. This measures neither licensed video viewing nor incremental viewing time. A simple recent-shot-count comparator is returned for later evaluation; it is not shown as an established inferior approach.

## API and security

- `POST /api/matchdays/start`: `{ "matchday_id": "fresh-id" }`, private cookie session required. Atomically reserves three match slots and ingests opening events only.
- `GET /api/matchdays/{id}`: public synthetic snapshot, ranked recommendation, comparator and latest tick notification. No mutation or future fixtures.
- `POST /api/matchdays/{id}/tick`: `{ "tick": 1 }`, owner session required. Advances exactly one canonical 30-second tick across all three matches. The current tick is idempotent; skipped or stale ticks are rejected.
- `DELETE /api/matchdays/{id}`: owner session required. Releases only that disposable replay group so New matchday can reuse capacity. No user documents or other sessions' data are affected.

Existing JSON/header/origin/host/body/request limits remain enforced. Start requests count against the session/start quota. Matchdays share the 64-match global cap, eight matches per owner, four-hour expiry and 2,500 events per match. One API worker remains required. Individual member advancement and arbitrary trusted writes cannot bypass the shared clock. No new paid ranking calls are added; Catch Me Up remains optional Azure selection under its existing budget.

## Review and evaluation

Follow-up on 2026-10-11: reviewed Antigravity's findings in `gemini-match-radar-findings.md`. Owner release now handles missing group members while preserving other sessions' matches. Window metadata uses `start_exclusive = -1` before five minutes, accurately including second zero; at five minutes the exclusive start is zero. Reset clears the local view with a warning on a transient release failure, retains the pending group, and retries cleanup before a new start; cleanup requests have a ten-second deadline. Progressive-pass windows and recovery-to-shot sequences now use compact wording with all selected story/event IDs retained. Separated ranges are listed explicitly, with no continuous-pressure claim. Goals are unchanged. The capacity-status consistency suggestion is outside this follow-up and remains open.

Local validation on 2026-10-08: 73 backend tests and 23 frontend tests passed; production build, Prettier check and Git whitespace check passed. The heuristic secret scan found no matching patterns in current files, built assets or reachable local Git history; this is not a penetration test. Browser QA confirmed complete replay, selected-fixture briefing and owner reset/restart. The existing detailed full-game "What changed" section is repetitive and remains a narrative-quality follow-up. Preview: [match-radar-preview.png](match-radar-preview.png).

Tests cover reproducible valid feeds, chronological period/pass/goal continuity, future blindness, the legitimate early prominent-fixture recommendation, the later overlooked-match recommendation, quiet/cooling/full-time suppression, evidence membership, deterministic ties, one-sided restraint, owner checks, tick retry/order, shared-clock enforcement, atomic capacity, expiry, owner release, notification deduplication and selected-match briefings. Frontend controller tests cover sequential requests, pause/abort retry and failed-tick cursor preservation.

Next: compare the baseline against human judgments, test missing/stale feeds and imperfect data, then add justified personalization and Azure recommend/wait/suppress decisions. Prototype fan tests can reveal usability and trust problems; no percentage engagement claim is justified until a suitable comparison is measured.

Gemini review handoff: [gemini-match-radar-review.md](gemini-match-radar-review.md). The initial CLI review was blocked before inference. The user subsequently supplied an Antigravity review in [gemini-match-radar-findings.md](gemini-match-radar-findings.md), which Codex assessed and used for the follow-up above. Antigravity can now review these fixes against the original repository. Do not weaken the security baseline or restore browser-submitted event facts.
