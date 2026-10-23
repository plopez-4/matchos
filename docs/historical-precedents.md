# Historical precedents

Open-domain historical aggregates calibrated for synthetic match context.

This means a historical benchmark is selected for a matching synthetic state. It does **not** mean a calibrated predictive model, all-time Premier League coverage, model training, or modified historical results. All replay events and match analytics remain synthetic. The benchmark sits outside their event-ID evidence chain, with its own visible citation, season, sample size and EN/ES disclaimer.

## One curated benchmark

Source: [OpenFootball England, Premier League 2016–17, pinned revision 4dffd3b](https://raw.githubusercontent.com/openfootball/england/4dffd3b1ad3b04ba6f885eb7fca3b1c2318a6c7d/2016-17/1-premierleague.txt). The [source repository declares its data public domain](https://github.com/openfootball/england#license). Verified 11 October 2026.

Across 380 fixtures, 156 had a one-goal halftime margin. For the leading team, the full-time outcomes were 113 wins, 32 draws and 11 losses. The displayed percentage is `round(100 × 113 / 156, 1) = 72.4%`. Home and away leaders are pooled; each qualifying match is counted once. This is one season, not Premier League history, a team-specific streak, or a win probability for this replay.

The source omits halftime scores for 27 matches, all 0–0 final results. These cannot have had a halftime lead and are excluded from the qualifying sample. A missing halftime score for any other result causes the offline verifier to fail rather than silently bias the denominator.

The single packaged table is `backend/app/data/historical_precedents.json`, bundled with the Python application so installed builds use the same data as local development. No ten-year database, raw historical rows, commercial API client or runtime network call is introduced. To reproduce, save the pinned source locally and run `python scripts/calibrate_historical_precedents.py path/to/1-premierleague.txt`. This checks the counts against the table and prints a source checksum; it does not rewrite the table or download anything.

## Trigger and limitations

Show one optional Historical Precedent field only when the latest observed event is `half_end` and the observed score margin is exactly one goal. No field for tied/multi-goal halftime scores, live play, second-half kickoff or full time; no appropriate full-time benchmark has been curated. Future events cannot trigger context. With no new events, existing Catch Me Up behavior still returns no briefing. The field uses no AI call, ranking influence or synthetic event IDs.

In Match Radar, pause at 45:00 to see the Palace–Newcastle halftime precedent; advancing resumes the second half and clears it. The authored second-half kickoff is at 45:01, rather than sharing 45:00 with `half_end`, so the shared clock can observe the boundary. All fixture event IDs, goal times and final scores are preserved.

The organizer's synthetic-data requirement does not, by itself, authorize real historical reference material in a submission. Confirm inclusion with the organizers before using this optional context in the submission/demo. Public-domain data status is separate from trademark permissions.
