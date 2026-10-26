# Recorded sending-off explanations

All MatchOS incidents are authored **fictional synthetic action** using reference player identities. These dismissals are not claims about actual player conduct or real fixtures. A losing result is a scenario choice, never a reason for a card.

## Rules checked

The player sending-off categories in [IFAB Law 12, 2026/27](https://theifab.com/laws/latest/fouls-and-misconduct/) include:

- Denying a goal or obvious goal-scoring opportunity through deliberate handball, excluding a goalkeeper inside their own penalty area.
- Non-deliberate handball offences denying such an opportunity outside the player's own penalty area.
- Fouls denying an obvious goal-scoring opportunity; penalty-area attempts to play or challenge for the ball have a yellow-card exception. Holding, pulling or pushing without that attempt does not receive that exception.
- Serious foul play: a ball challenge endangering safety or using excessive force.
- Violent conduct, including attempted violence without contact, outside a ball challenge.
- Biting or spitting.
- Offensive, insulting or abusive language/actions.
- A second caution, which requires an earlier caution.
- Entering the video operation room.
- Unauthorised field entry and interference denying a goal or obvious opportunity.
- Competition options: provocative communication while covering the mouth; leaving in protest; encouraging others to leave in protest. These are documented but not enabled in the demo fixtures.

A slide or push is not automatically red. Ordinary dissent is normally yellow. [IFAB Law 5](https://theifab.com/laws/latest/the-referee/) allows disciplinary action until the referee leaves the field after the match. Post-match abuse may therefore warrant red; respectful disagreement does not.

## Implemented fictional incidents

All are in fixed **version 4**; the other eleven-versus-eleven starts and version selection stay the same.

| Fixture          | Incident                              | Recorded reason                                                 |
| ---------------- | ------------------------------------- | --------------------------------------------------------------- |
| United–City      | Elliot Anderson, City, 55:00          | Serious foul play: dangerous sliding challenge                  |
| Palace–Newcastle | Tyrick Mitchell, Palace, 35:00        | Violent conduct: off-ball punch                                 |
| Brighton–Fulham  | Joachim Andersen, Fulham, 60:00       | Violent conduct: excessively forceful off-ball push             |
| Brighton–Fulham  | Sander Berge, Fulham, after full time | Abusive language towards the referee while disputing a decision |

The final incident follows the 93:00 match-end marker. Fulham lose 1–0; generation rejects a tied/winning-team configuration. It does not remove an additional player from the match or imply Fulham played with nine. No invented speech, foul video, coordinate animation, suspension or appeal outcome is supplied.

## Data and presentation

- `backend/app/data/sending_off_reasons.json`: shared English/Spanish catalogue, including researched categories that are not instantiated in the four incidents above.
- `backend/app/data/match_variants.json`: authored incident reason and post-match scenario configuration.
- `MatchEvent.card_reason` and `card_phase`: validated recorded metadata. Legacy missing reasons remain explicitly unknown.
- Recaps, AI evidence packets and the sending-off details panel use these recorded facts. AI writer/reviewer instructions distinguish post-match timing; local checks reject omitted timing and claims that the post-match card reduced playing numbers.
- **View sending-off details** opens a short factual explanation and inspectable event ID in the existing match view. Goals/chances retain pitch replays.
- Post-match notices remain accessible at full time, but never become a recommendation to tune into a finished match.

Use the fixed test hub at `/testing.html`: version 4 of each fixture, with Brighton–Fulham at full time for the final incident. Existing replay sessions retain their original generated data; restart the backend and create a fresh test matchday to see updated incidents. This change does not require an Azure call or a larger quota.
