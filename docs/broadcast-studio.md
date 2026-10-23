# Broadcast preview, event vectors and Listen

> Historical design record: this experimental frontend feature was removed from the active code on 23 October 2026. It is not available in the current main or development view.

## Broadcast Mode

Every shared Match Story card has a **Broadcast Mode** button. The bottom overlay shows club codes, observed score/clock, the grounded headline and a compact score-story/shot/clock ticker. It is a preview over the application, not a live television feed. **EN/ES** uses the same deterministic language rendering as the card. **Close** or **Escape** dismisses it and returns focus to the triggering button. Opening another card's overlay closes the first; updated card facts update the active cue.

The overlay is mounted outside the card through a React portal, so card clipping does not hide it. It wraps on phones, caps its height and keeps its controls within a scrollable lower third. It is nonmodal; it does not trap keyboard focus or lock the underlying page. Its visible label always identifies a broadcast preview and synthetic replay.

`broadcastCue()` in `frontend/src/utils/broadcast.js` produces a serializable cue with version, locale, score bug, match clock/seconds, headline, ticker and supporting event IDs. The rendered overlay also exposes its timestamp and IDs as data attributes. This is a local cue producer, not an implemented production overlay API, delivery bus, video timestamp synchronizer or rendering-partner integration. No real match-video rights are provided.

## Pitch inspection

Expand the story evidence drawer, then **View recorded vector** on a supported event. The SVG is 120 × 80 pixels and renders only when inspected, avoiding hundreds of hidden pitch tiles in a full-match recap. Coordinates map directly from the source's normalized 0–100 axes to the drawing; the direction is not flipped based on team name.

- Passes use a cyan arrow. Recorded goal shots use green; other recorded shots use red. Arrows show the actual stored destination, even for off-target action, rather than redirecting all shots to goal.
- Missing, nonfinite or out-of-range coordinates produce no vector. A zero-length vector produces only its recorded point.
- A goal without destination coordinates can use its explicitly linked, earlier goal shot only when that shot is loaded and agrees on match, team and actor. The caption says **Recorded shot linked to goal**. Missing linked shots do not produce inferred arrows.
- Names come from the recorded event. Synthetic-action/reference-identity labels and supporting IDs remain visible. The pitch tile does not establish real tracking, formations, tactical intent or movement speed.

The moving dashed line respects reduced-motion preferences. SVG titles describe the player and exact endpoints; IDs are unique across multiple cards.

## Listen

The current Voice selector adds optional **Matchday narrator** and **Warm storyteller** cloud profiles, plus explicit **Device voice (basic)**. See [Azure narration setup](azure-narration.md). The local-only behavior below describes the device option; cloud narration is an opt-in configured backend service, not offline synthesis. Missing Speech configuration is shown clearly and cloud auditions remain disabled.

**Listen** reads a snapshot of the displayed headline, scoreline, clock and three grounded sections. It does not generate narration or read the optional historical benchmark as a prediction. **Stop** cancels it. Starting another card cancels the previous managed recap; language/fixture changes and unmounting stop that card's audio. Clock updates do not restart speech automatically; the status identifies the snapshot being read.

Only a matching EN/ES voice with `localService === true` is accepted. There is no remote/default-voice fallback, no microphone request, no external credential and no application speech API call. Native voices depend on browser/OS configuration: unsupported browsers or missing local voices show a disabled button and explanatory label. See [voice locality](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService) and [voice loading](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/voiceschanged_event). Offline availability is conditional on an installed local voice; zero latency or universal support is not promised.

## Validation

104 backend tests and 45 frontend tests passed. Tests exercise EN/ES cue facts, phase handling, escaped text, SVG endpoints/IDs, absent and mismatched shot evidence, local-only voice selection, cancellation ownership and error recovery. Production build passed without size warnings or new packages: JavaScript 309.20 kB (94.39 kB gzip), CSS 42.70 kB (8.96 kB gzip). These sizes are not measured sub-second load performance.

Browser checks confirmed EN/ES overlays, exclusive ownership, Escape dismissal, an inspected Mateta shot from `(82, 50)` to `(100, 50)`, and a 390px layout without horizontal overflow. Local English speech entered the reading state and stopped on command. This browser had no local Spanish voice, so Spanish Listen correctly remained disabled; Spanish audio was not claimed as tested playback.

Previews: [broadcast](broadcast-studio-preview.png), [recorded vector](pitch-vector-preview.png).
