# MatchOS architecture

Current application path, checked against the source on 27 October 2026.

## End-to-end flow

Synthetic events → FastAPI validation and owned replay storage → deterministic analytics → Match Story Graph → verified story selection and audience plan → bilingual narrative generation and review → fan recap, evidence, schematic replay and optional speech.

The backend calculates facts before AI writes prose. Each story retains source event IDs and rule versions. Model review is fallible; failed validation/review or unavailable capacity returns labeled deterministic wording. The pitch is a visual explanation of recorded actions, not an independent source of tracking data.

## Events and concurrent replay

The shared [fixture manifest](../backend/app/data/demo_fixtures.json) defines `united-city-90`, `palace-newcastle-90`, and `brighton-fulham-90`. [Authored versions](../backend/app/data/match_variants.json) supply four alternatives per fixture, twelve total. New matchday independently selects one per fixture, giving 64 combinations. The `/testing.html` hub fixes a version for repeatable testing. Retired placeholder/short feeds are not public selectable scenarios.

`backend/app/matchday.py` generates all three streams and ranks observed activity. `full_match.py` adapts the same fixtures for single-match/CLI use; `simulation.py` exposes the current public catalog. Names are dated reference identities with authored demo roles; actions and performances are fictional. Active teams begin with eleven players. Substitutions and in-match dismissals affect subsequent actions; a post-match card does not retrospectively change the score or playing numbers.

The main and development matchday views use one shared clock advancing in 30-second ticks through a 93-minute authored timeline. Playback is driven by the open browser, with sequential acknowledged requests and safe retries. Normal/Fast are accelerated demo pacing, not real-time feed claims. Catch Me Up and narration pause the three matches for a snapshot.

## Deterministic analytics and graph

- Team counts cover recorded passes, recoveries, shots and goals. Goals are separate events with explicit shot references.
- Shot-frequency stories compare completed five-minute windows: at least three shots in the current window and an increase of at least two over the previous window, with the required baseline coverage.
- High-recovery stories require at least three recoveries in the opponent's defensive third in a completed window: home `x >= 70`, away `x <= 30`.
- Progressive-pass stories require at least three completed passes gaining at least 15 normalized units toward the opponent's goal in a completed window.
- Recovery-to-shot sequences require the same team, non-null possession and period, within 30 recorded seconds, without opposition interruption.
- Ten-minute player contribution windows add shot creation, shooting and forward-passing stories; see [player impact](player-impact.md) for thresholds and explicit pass-to-shot links.
- The graph contains `event`, `metric_window` and `story` nodes, joined by typed `supports` edges. Mathematical support and temporal sequence do not establish tactical causation.

Coordinates are normalized 0–100 stadium coordinates, not measured metres. This authored feed keeps home attacking toward `x=100` and away toward `x=0` in both halves. A real provider adapter would need explicit direction/coverage normalization. Event `sequence` is match ordering, not an arrival timestamp. Late-arriving provider data would need an ingestion-cursor design before acceptance.

## Grounded AI and presentation

The optional Azure selector can select only supplied verified candidate IDs. A shared story plan binds selected goals and qualifying changes to their original evidence. The writer receives structured observed facts, chronology and that plan, rather than prewritten commentary lines. A separate model review and local checks can trigger a bounded revision or a complete deterministic fallback. Rejected prose is replaced as a whole.

Casual/Analyst and English/Spanish share the observed snapshot and evidence while adapting presentation. Viewer cursors advance only after a successful catch-up response and remain browser-memory state. The evidence drawer and narration refer to the displayed recap; `narrative_id` lets the backend resolve cached AI text without accepting arbitrary browser speech text. See [fan narrative](fan-narrative.md) and [API contract](api.md).

`PitchReplay.jsx` follows a selected recorded move, preserving possession/team/period boundaries and validated shot-to-goal links. It shows involved players, recorded locations, a ball trail and action captions. Completed pass destinations or action origins drive field-area/direction labels. Brief directional pulses pause with replay and respect reduced-motion settings. Intercepted passes do not infer the next possessing team or a destination highlight. Sending-off details replace an invented pitch sequence.

Match Radar ranks the three already observed streams using deterministic activity/context rules. It is not a learning algorithm, outcome prediction or measured entertainment score. An observed post-match card is informational and does not revive a live hot-match recommendation.

## Hosting and trust boundary

The public deployment serves the Vite build and FastAPI API from the same HTTPS origin on Azure Container Apps. One worker and at most one replica preserve process-local storage, quotas and caches. Private runtime secrets configure Azure OpenAI and Speech; neither keys nor an ingestion credential belong in the browser, image or repository.

Reads expose synthetic match data. Replay advancement, catch-up and narration retain owner-session checks. The browser renews an expired anonymous session once; a specifically identified foreign-matchday link starts a new owned group rather than transferring ownership. A fresh root or test-hub link is the appropriate shareable entry point.

Cold starts/restarts clear in-memory replay state and counters. The prototype has no durable shared storage, real official feed, account system or full-player tracking. See [security](security.md), [hosted deployment](judging-deployment.md) and the [dated publication audit](release-verification-oct27.md).
