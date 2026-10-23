# Connected scoring sequences

Updated 2026-10-23. Writer version: `fan-narrative-v12.1-ordered-scoring-actions`.

## What changed

Catch Me Up can now explain a recovery, team passing path, shot and resulting equalizer as one observed move. The same selected story powers the factual fallback, AI evidence, inspectable graph and named replay button. No new tracking feed or commentary template was added to the AI path.

A link requires a goal-producing shot and explicit related-event reference, matching scorer/team/match/period/possession, valid order and bounded timing. Intervening events must stay in the same possession. Goal arrival advances the story's availability sequence so a fan who checked at the shot can still receive the new goal context.

## Exact Palace–Newcastle example

| Time  | Recorded action                           |
| ----- | ----------------------------------------- |
| 60:00 | Takehiro Tomiyasu recovers                |
| 60:03 | Tomiyasu passes to Adam Wharton           |
| 60:06 | Wharton passes to Jean-Philippe Mateta    |
| 60:08 | Mateta passes to Ismaila Sarr             |
| 60:10 | Sarr takes the goal-producing shot        |
| 60:11 | Sarr's goal event levels the score at 1–1 |

Three completed passes is the team total, not Tomiyasu's individual count. The writer gets ordered structured actions, not a prewritten description. Replay targets the explicitly linked goal and shot; English and Spanish buttons identify the equalizer.

## Validation and limits

Local suite: 351 backend tests and 61 frontend tests passed; frontend production build passed. Tests cover unrelated/future goals, actor and possession mismatches, shot-time viewer cursors, evidence graph support, bilingual coverage, exact replay selection and preservation of accepted whole AI paragraphs. Mocked providers establish application behavior, not live writing quality.

The final two live requests are in [linked-goal-live-check.json](linked-goal-live-check.json). Both returned deterministic fallback: Casual failed `missing_recovery_goal_connection`; Analyst failed `repeated_linked_goal_explanation`. This is safe rejection, not a successful AI prose evaluation. No further cloud retries were made to manufacture an accepted sample.

Earlier v11 model-reviewed output contained incorrect attribution, clocks and tied-score language; its initial report is explicitly a failed source audit. A v12 accepted sample added unsupported praise and a generic conclusion. The current guards reject those known forms, but cannot prove general entailment. Versioned initial/rejected reports remain historical failure evidence.

The factual fallback accurately connects the move but remains mechanical. Improving reliable AI authorship is still necessary before calling the experience polished. Five real fans have not yet tested this revision. Pronunciation changes likewise still require human listening, independent of automated text/SSML checks.

A separate browser check at full time produced an AI-written player-combination recap, with named attempt/saved-shot actions. Clicking the attempt opened the recorded build-up. This is a different snapshot, not a passing result for the 62:30 linked-goal cases. [Current browser preview](current-fan-recap-preview.png).
