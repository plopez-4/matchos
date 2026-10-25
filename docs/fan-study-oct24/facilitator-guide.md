# MatchOS: five-person fan test

> Superseded for the current Google Form: the user requested a remote screenshot-only questionnaire. See `screenshot-test-guide.md` for the active questions and scoring. The Google Form at the link below now uses that format. The hands-on script retained below is a separate future test; it does not describe the current form.

Prepared October 24, 2026. No participant results have been collected.

Google Form editor: https://docs.google.com/forms/d/1kqvrzFZ8ceJWrQTkcjnMBZ_-PK87wb_b1pZgcmAu7U0/edit

Participant form (published): https://docs.google.com/forms/d/e/1FAIpQLSdJ-X0yaVZEejlRVxnbdgNtkuM0AtJ0lgL-joOXMswmqDDCCw/viewform

The form contains 16 questions and three screenshot prompts. Only the participant code is required. Email collection and the sign-in-required one-response limit are off. Do not send the editor URL to participants.

For remote screenshot-only respondents, tell them to write “screenshots only” for questions requiring app interaction and leave untried tasks unanswered. Collect their comprehension feedback, but do not count it as hands-on usability evidence. Let them zoom the images. First-impression and free-text understanding answers should be given before looking at multiple-choice alternatives.

## Saved screenshot conditions

Screenshots were taken from the running main fan page using `red-card-fan-study-oct24` on October 24. `01-main-screen.png` is the initial screen. `02-catch-me-up.png` is the full screen at 45:30, Casual / English, labeled AI-written; `02-recap-detail.png` is its unaltered recap crop used in the form. The displayed paragraph describes Rico Lewis's recovery at 40:00, a five-pass team sequence, Jeremy Doku's shot at 40:10 and goal at 40:11, with City leading 1–0 at 45:30. These are the displayed claims, not an independent factual acceptance audit.

`03-red-card-alert.png` shows the United–City screen paused at 61:00 while the alert refers to Fulham's Joachim Andersen being sent off at 60:00 in Brighton–Fulham (0–0). `03-red-card-detail.png` is a crop of that actual alert used in the form. Do not confuse City's earlier Elliot Anderson card with Fulham's Joachim Andersen card in the toast. Full screenshots preserve the surrounding UI and stadium-photo attribution.

## Before the session

Recruit five real people with a mix of regular and occasional football viewing. Assign P01–P05; collect no names or emails. Allow 10–15 minutes each. Participation is voluntary. Ask separately before recording audio/video; notes alone are sufficient.

Use the main fan screen, not development. Since MatchOS is local, participants must use your computer or watch your screen share and direct your clicks. A localhost link will not work on someone else's computer or phone. For a real mobile test, arrange a reachable approved test host first; do not describe a desktop screenshot viewed on a phone as mobile app testing.

Freeze the app version and scenario before recruiting. Do not change wording halfway through the five sessions. Save the actual recap, language, perspective, match version and AI/fallback label used. Screen captures test comprehension only; hands-on task results must be recorded separately.

For repeatable red-card demonstrations, a fresh matchday ID containing `red-card` selects the fourth variant of all three fixtures. Use a different suffix for each participant, such as `red-card-study-p01`. Open `http://127.0.0.1:5173/?day=red-card-study-p01`. Confirm the actual fixture/version before starting. Do not reuse a progressed day or click New matchday and assume the same scenario. Keep the user on United–City while the Palace sending-off occurs at 35:00, so the other-match alert is relevant. Prepare just before the event, then lower replay speed so they can read the notification. The 180-second window is match-clock time and passes quickly at 80×.

Read the source evidence for the actual recap to make your answer key. Never score from remembered player names. The current fourth Palace variant records a Palace red card at 35:00; verify the actual displayed name and time before the trial. Red cards are currently an alert/replay feature; do not assume Catch Me Up already narrates them.

## Opening script

“We are testing MatchOS, not you or your football knowledge. This is fictional match action, not a live broadcast. Please say what you are thinking. You may stop or skip any question. I will watch first without explaining where to click.”

## Tasks, in order

1. Show the initial screen and first-impression image. Ask: “What do you think this helps you do?” Record the unaided answer before explaining anything.
2. At the prepared replay checkpoint, say: “You have been away from this match. Find out what you missed, then tell me what happened and what changed.” Do not name Catch Me Up or point to its button. Give up to 90 seconds. Record first action, time, success and help. Ask them to describe one player contribution and the order of the events in their own words.
3. Say: “How would you check whether that explanation is supported?” Allow 60 seconds. Observe whether they can open supporting events/replay and relate it to one actual claim. Finding a button alone is not proof of understanding.
4. Resume toward the prepared sending-off while they are viewing the other fixture. Say: “Continue as you normally would. Tell me if anything catches your attention.” Record whether they notice the alert before prompting. Afterward ask: “What happened there? What would you expect if you opened it?” Let them follow it. Note whether they reach the correct match and recorded event. If they never notice it, record that, then show the screenshot for a separate comprehension question; do not count that as unaided discovery.
5. Ask them to finish the form. First ask open-ended questions, then multiple-choice questions so options do not teach the answer. Do not correct answers until the session ends. Listen is optional; log voice/language if used. Do not require repeated paid AI requests merely to make the study look successful.

## Facilitator answer key (do not send to participants)

- MatchOS helps a returning fan understand recorded action, what changed, and decide what to follow. Accept equivalent wording.
- Pitch markers represent recorded action locations connected in a schematic replay, not continuous tracking or prediction.
- A red-card alert points to a recorded sending-off. It does not predict the winner or supply broadcast video.
- Recap factual answers must match the saved paragraph AND actual source events. Distinguish what the fan misunderstood from an incorrect/ambiguous paragraph.
- A “No” to tuning in is valid; the reasoning matters. Self-reported intent is not observed viewing.

## Recording and decision

Use `observer-notes.csv`. For each task record `unaided`, `helped`, `not_completed`, or `not_attempted`; leave unknown values blank. Record approximate seconds and a short paraphrase, or an exact quote only with permission. Treat screenshot-only completion separately from hands-on completion. Do not enter invented answers or AI-personality reviews as participant data.

Proposed formative target: at least four of five can independently catch up, describe the main change and contribution correctly, and follow an alert to its event. Report each task count separately as well as the combined result. Two people making the same serious misconception is a reason to revise the relevant wording even if other tasks pass. Five people are an early usability signal, not evidence of engagement uplift or population-wide accuracy.

After five sessions, summarize: participants and conditions; task counts; actual AI/fallback exposure; top repeated confusions; exact proposed corrections; remaining uncertainties. Avoid averaging unanswered ratings as zero. Keep response data private; do not commit real participant responses to the public repository.
