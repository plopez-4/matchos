# Main fan journey check — 22 October 2026

The original branded page remains the default. Its stadium banner is shorter and its main content is one column: score, playback, important moment, pitch replay, Catch Me Up, optional listening and collapsed supporting evidence. Timeline, comparisons, story list and graph moved into the development inspector. Main-page polling no longer downloads the graph.

The development link includes the current match ID and scenario. A browser check of `fan-flow-live-1022` showed that same ID, 544 recorded events, 25 deterministic stories and 584 graph nodes in the inspector. It did not need to start another three-match group to inspect the fan match.

## Behavior checked in the browser

- A full synthetic match played on the branded main page using current reference identities.
- Requesting Catch Me Up paused event delivery. The main page showed its held snapshot and a Continue match action.
- Three replay buttons appeared for the selected Fernandes–Mbeumo contribution. Selecting the second opened the recorded build-up at 16:30, ending in Mbeumo's saved shot at 16:40.
- Continue match cleared the older recap and resumed event delivery; it retained the successful viewer cursor. Playback could be paused again.
- An already-sent event advancement is allowed to settle before a recap snapshot is requested. It is not canceled halfway through a server write. Ordered retry remains idempotent.
- Older overlapping poll responses cannot supersede a newer manual refresh. A recap's replay choices are restricted to its selected story and snapshot; future and unrelated shots are excluded.

## Live Azure outcome

The private startup prompt reconnected Azure without storing the resource key in project files. Configuration status then returned true for writer v10.

The initial Casual request at 71:03 hit Azure HTTP 429 during review and correctly used factual fallback. Its unaltered response is retained in `main-fan-flow-live.json`. This was not an approved AI-written sample.

After a cooldown, a fresh Analyst request at 84:36 returned AI-written English/Spanish text and passed the existing review. The saved response is `main-fan-flow-azure-live.json`. The main page displayed the English paragraph with an AI-written label and all three contribution replay buttons. It described United's 2–1 lead, the three scorers, Fernandes' three recorded combinations in 15:00–25:00, the ten-second link rule and the absence of measured shot quality.

One successful request is an integration spot check, not a broad accuracy benchmark. Azure capacity fallback remains possible. Speech resource setup was not performed; the page retains an explicit device-voice option.

## Checks and remaining evaluation

76 frontend checks, changed-file formatting, production build and diff whitespace checks passed. The launcher passed PowerShell syntax parsing. Backend Python behavior was unchanged in this iteration; the preceding full backend run passed 303 tests.

This is an agent-operated software check, not a fan study. The five-person protocol now points to the branded main page. No participant results have been collected or filled into the results sheet.
