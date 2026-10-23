# Follow a recorded build-up

The pitch remains an event-based explanation of a synthetic match, not a continuous player-tracking system. This revision addresses fans mistaking old action locations and changes in recorded time for players teleporting.

- The current action shows only its observed participants, with shirt numbers (initials when absent), roles and names. A completed pass can show its receiver at the recorded endpoint. An intercepted pass does not claim the intended receiver was there or received the ball.
- Historical ball locations use small, faded trail dots rather than player-sized circles. Only the currently connected portion of the move retains its trail.
- Animation connects recorded endpoints schematically. Playback duration is compressed and bounded; it is not a measurement of ball speed or flight time. Pausing retains the ball animation's position instead of recreating it at an endpoint. Reduced-motion settings show endpoints without animation.
- Continuity requires consecutive sequences in the same known possession, match, team and period; matching endpoints; and matching recipient/next-actor identity after a completed pass. Recovery/kickoff-to-action continuity requires the same actor. A shot-to-goal link requires its recorded related-event ID and matching scorer.
- More than ten seconds between observations is conservatively treated as a recording gap, even if endpoints coincide. This is a presentation rule, not an analytics threshold or a claim that movement occurred in the interval.
- Missing movement, sequence gaps, intercepted passes and possession/period changes use a short faded cut with the next event's timestamp and elapsed time. No guessed carry is drawn across the gap. Latest mode can still skip older possessions to remain responsive, but it displays the elapsed gap.
- Selecting a goal holds its recorded possession through the shot and goal, then stops. Returning to latest is explicit. A goal marker does not place the shooter on the goal line: a linked shot supplies the shooter's action location; the ball supplies the goal location.

The analytics, story plan, graph, selected evidence and narrated recap are unchanged. No off-ball positions are generated or sent to AI.

Validation: 74 frontend tests and production build passed. Regression coverage includes identity/coordinate/time gaps, both pass outcomes, pass-to-shot-to-goal continuity, trail resets, recorded participant positions and safe empty rendering. Browser checks verified a selected Manchester City goal finishing at 40:11 and staying paused, plus pausing its 40:03 pass. The [build-up preview](coherent-build-up-preview.png) shows the involved-player markers and trail; the [transition preview](recorded-gap-preview.png) shows a cut to a newer recorded move. These screenshots show synthetic event replay, not full-player tracking.
