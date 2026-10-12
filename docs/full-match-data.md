# Full-match synthetic data

Two reproducible scenario feeds are available in the website: **United vs City** and **United vs Hull**. Both simulate 90 minutes plus three added minutes with fictional players. They are not reconstructions of real fixtures, official lineups, or factual predictions. Tactical styles are author-selected settings for these scenarios, not claims about current club tactics.

## Research checked on 7 October 2026

- United vs City is listed on 13 September 2026 at Old Trafford in [United's match list](https://www.manutd.com/en/mutv/matches/mens-team). [Opta's derby report](https://theanalyst.com/articles/man-utd-vs-man-city-stats-premier-league-09-2026) reports a 0–1 result and a City red card, so that game is not a clean demonstration of 11-v-11 possession versus counterattacking throughout.
- Hull vs United is listed on 22 August 2026 at Hull in the same official match list. That is the reverse venue of the proposed synthetic United-home scenario.
- These public reports do not establish access to a complete reusable raw feed from first pass to last pass. No real event dataset was acquired or imported. Publicly visible statistics are not evidence of permission to redistribute the underlying feed.
- The [official hackathon rules, section 4.7](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) require synthetic football-realistic data. Real reports above are research references only and are not generator inputs.

## What's in the feeds

- Stable fictional player IDs, display names, positions and starting/bench status in the scenario catalog and manifest.
- Every modeled pass has a sender, intended recipient, start/end coordinates, outcome and possession ID. A completed pass transfers the ball to its recipient; an interception transfers possession to the opponent. An intended recipient is not a completed reception when outcome is `intercepted`.
- Shots, goal-producing shot references, saves represented by shot outcome plus keeper recovery, turnovers, second-half kickoff, one substitution per side, halftime and full time.
- Seeded generation, contiguous sequences, monotonic clock, changing active players, and existing evidence-backed rules. City has longer passing sequences in the derby; United have longer passing sequences against Hull.
- Schema 1.2 adds identities, recipients, intercepted passes and match lifecycle events. Existing schema 1.0/1.1 fixtures remain compatible.

The coordinate frame stays fixed for analytics: Home attacks toward 100 and Away toward 0 in both halves. These are normalized pitch units, not metres or stadium coordinates. Physical halftime direction changes are normalized away. The playing clock stops at 45:00 for halftime, resumes at the same clock value for period 2, and ends at 93:00. No real-time halftime delay is simulated.

## Run or export

In the website select a full-match scenario, choose **80× Fast preview**, and Start. This sends one event roughly every 37.5 ms plus request overhead; it is an event-delivery speed, not an exact 80× match clock. Pause, resume, reset and switching work as before. Use Catch Me Up during playback to get a paragraph about the interval since your last check.

From the repository root:

```powershell
.venv\Scripts\python.exe scripts\export_full_matches.py
.venv\Scripts\python.exe simulator\run.py --scenario united-city-90 --match-id derby-demo --interval 0.05
```

Exports live under `data/synthetic/`: two JSONL feeds and a manifest with seed, generator version, rosters and provenance. Regenerate after generator changes. These files support analytics and narrative evaluation; no training or fine-tuning job is performed. The Azure model receives verified story evidence through the existing pipeline.

## Catch Me Up

Full feeds add a readable rule-based briefing: time interval, current score, named scorers, completed/attempted passes, shots and substitutions. Advanced mode adds the most active passer by attempts for each side. All briefing claims have supporting event IDs, including earlier goals needed for the current score. Existing optional Azure story selection remains separate and accurately labeled.

## Limits

This is a connected event simulator, not a tracking system or physics model. It includes every action the generator models, not every possible football action: individual tackles, cards, fouls, carries, corners, referee decisions and player movement are not modeled yet. Deep defending is a scenario assumption; without defender positions the analytics cannot measure a defensive block. Passing volume alone must not be labeled possession percentage. Full-match realism requires further calibration and football review. Two feeds alone cannot establish general tactical understanding or train a reliable model.
