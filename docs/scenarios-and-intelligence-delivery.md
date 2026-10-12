# Scenarios and intelligence delivery � corrected after review

Date: 7 October 2026. Working branch: `fix/scenario-review`, based on Gemini implementation `6a7698f`.

This report replaces the earlier delivery narrative and example transcripts. It describes the corrected code and verification actually performed. It is not a tagged release or a production deployment.

## Implemented behavior

The website offers Pressure Builds, The Comeback, Quiet Match, and Legacy Fixture. The catalog is read-only; selecting a fixture does not ingest it. Browser playback submits ordered events through the existing validated ingestion API. The CLI uses the same shared generator. All events and player IDs are fictional; Home attacks toward x=100 and Away toward x=0 on a normalized 0�100 pitch.

The scenario selector now works during playback. Switching stops playback, aborts old requests, opens a fresh match URL, and clears match-specific score, summary, evidence and progress state. The new scenario stays ready until Start is clicked. Reset retains the chosen scenario and opens another fresh match. A previously sent request may still be accepted into the old match; idempotent ingestion handles retries. Playback requires the page to stay open.

## Reproducible scenario output

Seed 7, full fixtures, derived directly from the shared generator and production rules:

| Scenario          | Events | Final score | Goal times           | Recovery-to-shot gaps | Stories | Graph nodes / edges |
| ----------------- | ------ | ----------- | -------------------- | --------------------- | ------- | ------------------- |
| `pressure-builds` | 33     | 1�0         | Home 8:49            | 23s                   | 6       | 44 / 24             |
| `comeback`        | 34     | 1�1         | Home 2:26, Away 9:19 | 30s, 23s              | 8       | 47 / 30             |
| `quiet-match`     | 30     | 0�0         | None                 | None                  | 0       | 30 / 0              |
| `legacy-default`  | 30     | 1�0         | Home 9:31            | 30s                   | 4       | 37 / 16             |

All fixtures cover 10:00 of recorded match time. Descriptions avoid revealing the final score or equalizer. Pressure Builds has six verified stories; The Comeback has eight. Quiet Match has no qualifying stories and shows the deterministic no-pattern summary. The original Legacy Fixture is restored exactly and now has four stories because new rules legitimately recognize additional patterns in unchanged evidence.

## Deterministic definitions

- `goal-v1`: a stored goal, with its validated goal-producing shot reference when supplied.
- `shot-frequency-v1`: recorded shots in the latest two completed five-minute windows; at least three current shots and an increase of at least two. Existing semantics are retained.
- `high-recovery-v1`: at least three recoveries in a completed five-minute window, Home x>=70 or Away x<=30. This measures recorded recoveries, not pressing effectiveness or possession dominance.
- `progressive-pass-v1`: at least three completed passes in a completed window, both destination coordinates required, forward gain >=15 normalized pitch units. Home gain=end_x-x; Away gain=x-end_x. These are not metres or an official provider definition.
- `recovery-shot-v1`: the nearest preceding recovery followed by a same-team shot in a contiguous non-null possession and the same period, with elapsed recorded time from 0 to 30 seconds inclusive. Evidence includes intervening same-possession passes. Opposing events or possession/period breaks invalidate the chain.

Completed windows use [start,end); an event exactly at end can trigger the preceding window's story but is not counted inside it. Window stories trigger at the first observed event at/after the closing boundary. New recovery/pass window stories remain available across later windows. Graph edges are `supports`, not claims of tactical causation.

## Review fixes

1. Restored the original legacy event content and retained original event IDs. A frozen seed-7 JSON fixture checks full dictionary equality and replaying into an existing store without 409 conflicts. Tests preserve original goal/shot facts and explicitly recognize the additive progressive-pass/recovery-shot stories and metric node.
2. Added missing-end_y validation to progressive passing, with both-team tests for each missing destination coordinate.
3. Enabled mid-playback scenario changes. Scenario URL validation now uses an exported production helper, which the frontend unit test imports instead of copying App logic.
4. Candidate selection rejects duplicate IDs and protected-set overflow. Azure input stays bounded to eight candidates. If goals plus the strongest activity change cannot fit, the app skips the provider and renders the full deterministic briefing. No goal or protected change is silently removed. Overflow tests cover nine goals and eight goals plus a change; mocked transports confirm no provider request occurs.
5. Removed causal/direct-transition language from Casual output and corrected scenario descriptions, goal times, chain gaps and verification claims.
6. Pytest explicitly imports the backend in the current checkout, preventing a reused editable-install environment from silently testing a different checkout.

## API and compatibility

- `GET /api/replay/scenarios`: catalog ID, name, description, count, duration and version.
- `GET /api/replay/scenario?match_id=<id>&scenario_id=<id>`: complete event array; scenario defaults to `legacy-default`. Match/scenario parameter syntax is validated and unknown scenario IDs return 404.
- `POST /api/events`: existing append validation and idempotency remain unchanged.
- Analytics adds high-recovery windows, progressive-pass windows and recovery-shot chains; existing counts and shot windows remain.
- Catch Me Up retains its response structure, cursors, Casual/Advanced audiences and optional Azure selection. New story kinds are additive.
- CLI adds `--scenario`, with full-fixture count by default and counts validated against the chosen fixture's length. Original positional generator calls and legacy event content remain compatible.
- The event schema remains 1.1; no schema-field migration is needed.

## Validation

- Backend: **39 tests passed**, including nine new parameterized review regression cases. One Starlette/httpx deprecation warning remains.
- Frontend: **19 tests passed**.
- Production Vite build: passed.
- Shared Prettier check: passed.
- Backend tests use local deterministic logic and mocked Azure requests; no live Azure call or paid resource provisioning is needed.
- Browser checks use isolated backend port 8001 and frontend port 5175, leaving the owner's servers untouched. Verified Start at 4�, selecting The Comeback while Pressure Builds was playing, new match URL, zero progress/score reset, and starting the new selected fixture.

Additional browser verification: The Comeback completed at 34 events, 1�1, with both goals and the new patterns in Casual Catch Me Up. Switching to Quiet Match cleared the prior summary/cursor; it completed at 30 events, 0�0, with zero stories and the explicit no-pattern summary. The stopped Pressure Builds session remained at 11 events. The duplicate intro in quiet-match output was removed. No copied or illustrative test transcript is presented as an actual run.

## Review/demo steps

Start the normal backend on port 8000 and frontend with the repository's standard commands. Open the printed frontend URL with `?match=<fresh-id>&scenario=pressure-builds`. Pick 4� for a short demo. Start, switch to The Comeback during play, check that a fresh ready match appears, then Start again. At completion Home and Away each have one goal. Inspect a new story's event IDs in the timeline and use Catch Me Up. Reset and run Quiet Match to confirm 0�0 and the no-pattern summary. Legacy Fixture must preserve its original 30 events, 9:31 Home goal, and five/two recorded shot counts.

## Limits

Storage remains single-process and in memory. The graph is derived on reads. Browser playback ends when its tab closes or reloads. Second-half attack-direction changes, public deployment, authentication, full accessibility auditing and complete network-fault injection are outside this fix. A sparse synthetic feed describes recorded events only. Logo permission remains unconfirmed; this change grants no branding rights. Live Azure behavior is covered by mocks here and is not claimed as newly verified.
