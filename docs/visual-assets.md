# Broadcast theme and visual assets

MatchOS uses a purple and white broadcast theme, a locally bundled photograph and fonts, and fictional white/red kit colors. The fixture palette is configured in `frontend/src/utils/teams.js`; no real club or real match data was added.

## Asset credits

- `premier-league.svg`: unchanged white lion/wordmark artwork from https://logo.premierleague.com/img/lion-light.svg. © Copyright The Football Association Premier League Limited, 2016. The mark is not covered by this repository's MIT license. Brand guidance and use terms: https://logo.premierleague.com/. Hackathon participation does not establish sponsorship or endorsement; confirm the event's authorization for the mark before including it in the public submission video.
- `goodison-park.webp`: Goodison Park, Liverpool, photographed by **Arne Müseler / arne-mueseler.com**, 31 July 2023. Source: https://commons.wikimedia.org/wiki/File:Liverpool_fc_everton_stadium.jpg. License: https://creativecommons.org/licenses/by-sa/3.0/de/deed.en. Downloaded the 1280px thumbnail and optimized it to a 960px WebP for delivery; CSS displays a crop with a purple overlay. The photograph and its visual adaptation remain CC BY-SA 3.0 DE, separately from application code. Visible attribution and license links appear beneath the photograph.
- `BebasNeue-Regular.ttf` and `Manrope.ttf`: Google Fonts source repository, https://github.com/google/fonts/tree/main/ofl/bebasneue and https://github.com/google/fonts/tree/main/ofl/manrope. SIL Open Font License 1.1; accompanying license files are bundled with the fonts. Fonts load locally without contacting Google.
- Four-square Microsoft identifier: code-native representation accompanying the factual label “Powered by Microsoft Azure.” Microsoft marks remain their owners' property; no official project endorsement is claimed.

## Goal celebration

The scoreboard compares successful analytics snapshots. A score rise queues a 6-second GOAL takeover in the scorer's configured kit color, then returns to the score. First load sets a baseline without replaying old goals. Repeated identical polling snapshots do not repeat a celebration; score rollback clears pending celebrations. If multiple goals arrive within one polling interval, each is queued; their exact cross-team order is unavailable from the counts alone.

Reduced-motion mode displays the same announcement without the wipe/zoom movement. Goal text is announced through a polite status region. Polling and Catch Me Up continue while the noninteractive overlay is displayed.

## Validation

- 12 frontend tests pass, including scorer detection, first-load suppression, repeated polls, reset/correction behavior and multiple-goal queues. Production build passes.
- Browser loaded the league mark, stadium photograph and local fonts. Home statistics computed as white and away statistics as red.
- A separate backend on port 8001 and a temporary frontend on 5175 were used to ingest synthetic goal checks. The Away FC GOAL overlay was observed after a real analytics increase to 1–1, and the scoreboard returned afterward. The owner's port-8000 replay stayed at its original 1–0 score. White-team behavior is covered by the shared scorer/configuration tests; the brief live white overlay was not captured reliably.
- At 375px, both images loaded and document width was 360px (viewport 375px including scrollbar), without horizontal page overflow.
- A previously scored fixture opened without a goal takeover. The live theme screenshot is [premier-theme-preview.png](premier-theme-preview.png).
