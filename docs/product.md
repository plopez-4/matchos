# Product focus

## Current page assignment — 22 October 2026

The owner selected the original page with the stadium hero and Premier League/Microsoft branding as the main user screen at `/`. The focused Matchday page is now the development view at `/?view=development`, for testing replay, missed intervals, narrative and evidence. Both use the same current three-fixture catalog and reference rosters. This overrides the earlier default-page assignment in the design notes below. See [the migration record](shared-demo-migration.md).

## Main fan journey implementation

The branded main page now keeps one column: compact stadium branding, score/clock, match playback, important moment, recorded pitch replay, and the shared concise Catch Me Up with optional listening. Technical event counts, the permanent event timeline, shot-comparison panel, story list, graph and model diagnostics are absent from this view. Supporting recap evidence stays available on demand.

The Development dashboard link carries the current match ID and scenario into `/?view=development&match=…&scenario=…`. Its inspector shows the exact same recorded match's timeline, deterministic stories, comparisons and graph. Without a match ID, the development Matchday simulator still provides its three-match test environment.

Catch-up pauses match delivery and waits for the one already-sent advancement to complete before requesting its snapshot. Replaying an earlier moment or listening holds playback. Continue match clears stale recap text, retains the last successful missed-event cursor, and resumes delivery. A quiet repeated catch-up retains its previous paragraph with the original timestamp. Changing perspective rewrites the same captured interval rather than consuming it again.

Selected player contributions now expose replay links derived from the selected story's source actions, bounded by the recap snapshot. Creator links require the referenced completed pass and recipient shot; unrelated team attempts are not turned into contribution replays. These links reuse the existing pitch replay rather than adding another analysis panel.

## The promise

**Missed the action? See how it happened and understand what changed.**

MatchOS helps a fan rejoin a football match after missing important action. A goal alert opens the goal's recorded build-up; a concise recap connects the moment to the score story. Replay and context are one experience.

## The main experience

One selected match: **score and clock → important moment → pitch replay → short Catch Me Up → return to latest**.

- The default app is the focused match experience. There are no competing dashboard tabs or promotional stadium header.
- Other fixtures live in a compact **Other matches** control. Radar is an occasional entry point, not another permanent dashboard section.
- A goal recommendation opens the cited observed goal, not a later generic pass. Selecting an important moment pauses match advancement so its context stays stable while the build-up plays.
- One primary replay action sits beside the moment title. Playback can be paused; earlier moments are collapsed. **Return to latest** resumes the synthetic matchday.
- Catch Me Up preserves the complete concise paragraph: score story, meaningful changes, supporting activity and current situation. Do not truncate the writer's paragraph by sentence count just to make the screen smaller. **Catch me up** holds the match and summarizes events since the last successful catch-up; opening a different match starts with its full context. Source mode and snapshot clock stay visible. The existing “What changed” analysis and supporting events are available on demand.
- Starting/resuming ordinary playback uses the current recorded-event summary. Resuming clears the older requested recap so it does not continue to describe a superseded score.
- Resuming preserves the last successful catch-up cursor, so the next request still covers the absence. Failed/aborted requests never advance it. An empty repeat check reports that there is no new action and retains the previous explanation with its original timestamp.

Changing perspective rewrites the displayed catch-up window without discarding missed actions. Language changes use the bilingual version of the same recap. The caption identifies the perspective actually shown, including after a failed request.

## The build behind it

The original four capabilities remain: validated event ingestion, deterministic analytics, the Match Story Graph, and evidence-backed Catch Me Up. The pitch makes recorded sequences visible; it does not replace match intelligence. The optional Azure writer remains available through the existing recap request and must be configured and demonstrated honestly before any AI-powered submission claim.

## What leaves the fan screen

The oversized hero, club onboarding, squad explorer, permanent Radar panel, three-fixture card grid, duplicate summaries, audience configuration, narration setup, broadcast controls, historical comparisons, graph presentation and raw event-log wall are not part of this milestone's fan journey.

Existing experimental code and the explicit development dashboard (`?view=single`) remain available through **Demo controls**, rather than being primary navigation. This is not authorization to expand those experiments. Catch Me Up includes compact Casual / Analyst and English / Spanish controls. Analyst adds measured event-window context and limitations; Casual prioritizes the score story. A compact Listen to recap button reads the displayed language using an installed local device voice. Starting speech pauses match advancement. Stop cancels playback; changing the recap or language cancels stale audio. Azure narrator choices remain under Voice options and require a configured Speech resource. Additional presentation work remains deferred.

## Scope freeze

The next iteration is correction and fan evaluation, not additional feature categories. An addition must be necessary to help the fan identify the missed moment, understand it, or rejoin the match. Otherwise defer it.

## Evaluation

Ask a new fan to open a goal alert without coaching. Can they identify the match and score, explain what changed after one replay, and find the next action? Compare the focused screen with the former dashboard. Record confusion, unnecessary clicks and whether the recap/replay combination helps. Animation appeal alone is not proof of utility or engagement uplift.

## Demo boundaries

The working feed is authored synthetic football action, with recorded ball-event coordinates and reference player identities. It is not real match footage, full player tracking or a licensed stream. Radar eligibility is deterministic. AI wording can fall back to recorded-event summaries; neither mode proves causal tactical claims or predicts what happens next. No real-feed deployment or measured engagement improvement is claimed.

## Code/data cleanup — 23 October 2026

The old unnamed short scenarios are now isolated in `backend/tests/legacy_scenarios.py`. Production `backend/app/simulation.py` generates only the current named fixtures by default and rejects retired IDs. They are retained as test inputs to protect deterministic analytics; they are not loaded into the running app. Unreachable club-picker, broadcast-overlay, old recap/translation and simulator-guide modules have been removed, along with their exclusive CSS and retired-feature tests. The current roster stays on the backend; the browser no longer imports its full player database. See `docs/code-cleanup.md` for the scope and verification.
