# Player contributions in Catch Me Up

Catch Me Up now prioritizes a named player's measured contribution over a generic team-shot comparison when a qualifying player story exists. This adds facts to the existing events → metrics → story graph → verified selection → recap/evidence/voice pipeline. It does not introduce player tracking or a separate dashboard.

## Rules and scope

| Story                    | Qualification                                                                                                      | What it establishes                                                               |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| `player_shot_creation`   | At least two completed passes directly followed by the recipient shooting                                          | The recorded final pass before a shot, not a goal assist or chance-quality rating |
| `player_shooting`        | At least two shots by the same player                                                                              | The player's share of the team's recorded attempts and recorded outcomes          |
| `player_forward_passing` | At least three completed passes by the same player gaining at least 15 normalized units toward the opponent's goal | Repeated forward passing, not a defensive line being bypassed                     |

A shot-creation pair must have consecutive sequences, the same match/team/period and a known shared possession, a matching recipient/shooter, matching pass endpoint and shot origin, and a nonnegative gap of at most ten seconds. Both events must be in the stated window. Intercepted passes, missing coordinates, intervening actions, different recipients and cross-possession links cannot qualify.

Current snapshots use `(max(period_start, now−600), now]`, so the latest observed shot can qualify immediately. Early windows explicitly show their shorter clock range. Historical checkpoints every five minutes preserve completed half-open ten-minute windows `[start, end)`. Snapshot and archive IDs are distinct and metric bounds explicitly identify which endpoints are inclusive. Windows never cross the halftime boundary. A recording must span the stated start; this is still recorded-event coverage, not proof of complete real-world tracking.

Snapshot story IDs can be reconstructed from their original observed snapshot. Completed checkpoint stories remain available in later history. A contribution's cursor sequence is its last contributing action, rather than the checkpoint-closing event, so merely closing another overlapping window cannot reannounce old player involvement.

Team denominators carry their own supporting event IDs. Overlapping windows are never added together. Every player story has a versioned metric-window node and `event → metric_window → story` supports edges.

## Editorial behavior

Verified shot creation takes priority over repeated shooting, then forward passing. Within a kind, the latest qualifying window takes precedence; contribution count and goal-producing shots break ties. Goals remain protected. The focused plan carries one primary contribution with its player ID, exact window, evidence and rule version.

For example, the authored featured demo at 25:00 supports:

> Bruno Fernandes repeatedly found Bryan Mbeumo: his completed passes directly preceded 3 of Manchester United's 3 shots in 15:00–25:00.

This is a **synthetic scenario using reference player names**, not a claim about a real match. The featured 15–20-minute spell explicitly authors recurring creators and finishers; other possessions retain varied roster participation and substitutions. The quiet fixture has no qualifying repeated player contribution. Headers, take-ons, possession duration and defensive-line locations are not recorded by the current schema and are not inferred.

Canonical English/Spanish contribution sentences come from the measured facts. Selected goal scorers, teams and timestamps also receive canonical sentences, so a model cannot omit a goal while merely citing its ID. Azure frames current score/elapsed-clock context, then the assembled paragraph is validated and separately reviewed. AI countdown phrases are rejected; deterministic fallback countdowns remain calculated from the snapshot. Analyst wording explains the relevant definition and limits. Known unsupported headers/dribbles/line-breaking phrases are rejected, but these targeted checks and the model review are not general proof of semantic entailment. Provider failure preserves the same player-based rule recap. The generic recent-shot paragraph is omitted when the selected player story already supplies the useful contribution.

The evidence drawer uses the selected contribution under **Who shaped the play** / **Quién influyó en el juego**. Device voice reads that displayed paragraph; cloud narration reconstructs the same snapshot and selected IDs, and requires the matching cache identity for AI prose.

## Verification

Regression coverage includes mismatched identities, time/coordinate/possession boundaries, intercepted passes, immediate snapshot availability, archived history, viewer-cursor repeats, direction-aware forward passes, evidence denominators, graph edges, bilingual fallback, exact reviewer/display text, narration reconstruction and quiet restraint. Live verification uses the bounded local runner, which spaces the two busy Azure requests by 60 seconds and separately simulates provider HTTP 503. Results are recorded in `live-azure-quality-results.json`; earlier version 5.1 results are retained separately.

The final version 6.2 run passed both busy Azure audiences in English/Spanish, both quiet cases and the simulated provider failure. Validation passed 244 backend tests, 75 frontend tests and production build. The [player-focused recap preview](player-impact-recap-preview.png) and [linked player evidence](player-impact-evidence-preview.png) show actual synthetic-demo output; no full-player tracking is implied.

Browser verification also confirmed the Enzo Fernandez → Erling Haaland pair in a 16:30–26:30 snapshot, including the two completed passes and their immediately following shots. EN/ES retained the same named contribution and goal. Catch-up now refreshes its event list and match clock after completion: a tick committed during Pause no longer leaves a referenced event absent from the browser's older feed. The final inspected evidence drawer had no missing event references. Spanish device speech remained unavailable on this machine; no Azure Speech playback claim is made.

## AI-authored commentary (v7)

The writer receives structured metrics and supporting events without prewritten player-story sentences. It writes the entire recap; accepted prose is preserved exactly for screen and voice. Local checks require selected names, counts, windows and goal coverage, followed by an independent, fallible semantic review. Rejected or unavailable AI uses the factual rule recap. Earlier screenshots and v6 live results describe the previous server-composed writing flow, not v7 validation.
