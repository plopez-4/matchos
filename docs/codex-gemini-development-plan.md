# MatchOS: Codex + Gemini development plan

Status: planning only. Implementation starts when the project owner resumes work.

## Security prerequisite

The original repository now implements the baseline in [security.md](security.md). Both assistants must preserve its ownership, quota, credential and fallback rules and run the security regressions. Browser replay advances server-owned events; do not restore browser submission of arbitrary event facts or add shared tokens to frontend code. Hosting/cloud verification remains required before public deployment.

## Product direction

MatchOS — The AI Operating System for Live Football — should help fans understand a match as it unfolds, without requiring them to know which question to ask. Its core output is an evolving, evidence-backed account of what happened, what changed, and why a fan should pay attention.

The product should earn trust through accurate, timely, understandable analysis. A polished chat box, more model calls, and more agents are not measures of progress. A good experience can include questions later, but its intelligence must already be useful without them.

Primary fan jobs:

1. I joined late: tell me what I missed and the current situation.
2. I am watching: point out an important developing change without overwhelming me.
3. I follow a team or player: show relevant involvement and opportunities.
4. I want to understand an insight: let me inspect its supporting events and limitations.

## Current foundation and honest limits

The project has event ingestion, deterministic rules, an evidence graph, selectable replays, optional Azure story selection, Casual/Advanced catch-up, and a polished match page. Two authored full-match scenarios now cover United–City and United–Hull, using fictional players, connected passes, substitutions, two halves and added time. Short fixtures remain for focused regression checks.

These feeds are synthetic scenarios, not reconstructions of real fixtures. Their tactical style settings are author assumptions. The simulator does not yet include every football action or off-ball player tracking. Two matches do not establish general tactical understanding. No model training or fine-tuning has been performed.

The latest implemented checks reported 50 backend tests and 20 frontend tests passing, plus production build and formatting checks. Each development round must rerun the appropriate checks; this historical count is not proof that subsequent changes work.

## How the two assistants work together

The owner controls priorities and passes the handoff files between assistants. We do not assume shared conversation memory, automatic messaging, or identical checkout contents.

### Codex: implement and supply evidence

- Read the latest Gemini review and inspect the actual repository state.
- Implement one bounded milestone using the agreed data/API contracts.
- Add meaningful tests for the behavior and failure cases.
- Run the relevant checks and inspect the fan-facing experience when it changes.
- Deliver a handoff with exact branch, commit, changed files, reproduction steps, actual results and unresolved limitations.
- Preserve unrelated work and keep changes reviewable.

### Gemini: independent review, then focused edits

- Verify the branch and commit before reviewing; compare actual code, not only Codex's delivery summary.
- Check football meaning, data continuity, evidence support, fan usefulness, usability and regressions.
- Try to falsify important claims with counterexamples and unseen seeds.
- Record findings with severity, file/line, reproduction and expected behavior.
- Make small, justified edits on a review branch when they fix confirmed findings.
- Do not silently rewrite shared contracts, widen scope or overwrite other work. Describe a larger proposal before implementing it.
- Run appropriate checks and provide an edit handoff.

### Codex: review Gemini's edits and close the round

- Inspect the complete diff and each finding.
- Verify that edits fix the original problem without changing the football meaning or losing evidence.
- Reproduce important failures, check regression coverage and rerun affected checks.
- Accept good changes, repair remaining problems, and explain disagreements with examples.
- Produce a final round report with what is verified and what remains uncertain.

Disagreement is useful. Agreement between two assistants is not ground truth: event evidence, documented definitions, reproducible tests and human football review decide the outcome. Neither assistant can establish branding rights or submission eligibility by agreement.

## Repository and handoff rules

- Keep `main` as the stable demo and `develop` as the integration branch, once current stacked branches have been reconciled.
- Use a feature branch for each milestone and a Gemini review branch based on its exact delivery commit.
- At the start of a round, record repository path, branch, commit and working-tree status. Locate the current full-match implementation rather than assuming an older checkout includes it.
- Never review different commits as though they are the same version. Do not copy whole directories over another checkout.
- Keep real API keys out of reports, patches, screenshots and GitHub.
- Follow repository formatting and contribution guidance.
- Once final checks pass, prepare a coherent PR and update patch notes. Publication and merging follow the owner's authorization; a delivery report alone must not claim that GitHub has been updated.

Recommended round files under `docs/reviews/<milestone>/`:

| File                        | Written by | Purpose                                                  |
| --------------------------- | ---------- | -------------------------------------------------------- |
| `implementation-handoff.md` | Codex      | Scope, exact commit, changes, checks and limitations     |
| `gemini-review.md`          | Gemini     | Findings, counterexamples and proposed fixes             |
| `gemini-edit-handoff.md`    | Gemini     | Exact edits/commits and actual verification results      |
| `codex-final-review.md`     | Codex      | Resolution of each finding and final acceptance evidence |

Use the milestone names below. Do not manufacture terminal transcripts or label illustrative examples as test results.

## Milestone 1: reproducible match variations and data quality

Goal: prove the app responds to evidence across different outcomes instead of following a fixed storyline.

Codex implements:

- A bounded `seed` parameter carried through generation, API, replay URL and metadata.
- A clearly named repeatable demo option and a New match variation action.
- Fresh match IDs for new variations; resetting a variation retains its seed.
- Event counts calculated for the selected seed, rather than copied from the default fixture.
- Provenance identifying generator version, seed, synthetic origin and coordinate/clock conventions.
- Validation of player availability, pass recipient continuity, possession changes, shot/goal references, halftime and final whistle.

Gemini challenges:

- Same seed reproduces identical events and IDs; different seeds may still produce the same score.
- Seeds beyond the demo seed generate schema-valid, logically connected matches.
- A failed or paused replay resumes safely without duplicate goals or skipped events.
- Switching scenario/seed clears old score, summaries and evidence and ignores stale requests.
- Neither description nor summary leaks events that have not arrived yet.

Acceptance: replay any saved variation; validate a declared set of unseen seeds; demonstrate different generated event sequences; do not guarantee unique scores or claim empirical realism without calibration evidence.

## Milestone 2: possession sequences and player involvement

Goal: make the match understandable through connected actions.

Codex implements:

- Possession summaries: start/end, duration, completed/attempted passes, start/end locations, players involved and outcome.
- Pass networks using completed sender-to-recipient links.
- Player involvement: completed/attempted passes, receptions, shots and recoveries, with time windows and evidence IDs.
- Observed sequence descriptions, such as a recovery followed by forward passes and a shot.
- A clear separation between measured facts, explicitly defined indicators and unverified hypotheses.

Gemini challenges:

- A long passing sequence does not automatically mean dominance or an effective attack.
- A player making many passes is not automatically the most influential player.
- Intercepted passes do not count as completed receptions.
- Goal events do not double-count goal-producing shots.
- Normalized attack coordinates remain consistent across halves and teams.
- Sparse fixtures are not treated as complete feeds for possession-time calculations.

Acceptance: manually inspect representative possessions; reconcile player/team totals; ensure every displayed measure has a documented definition and supporting events. Describe quick attacks and long buildups from observed sequences; do not infer tactics solely from team names or simulator style settings.

## Milestone 3: changes over time and an evolving Story Graph

Goal: detect meaningful developments that a fan might otherwise miss.

Codex implements:

- Comparisons of completed 5/10/15-minute windows, with explicit baseline and minimum evidence requirements.
- Changes in shot activity, progressive passing, recovery locations and player involvement.
- Sequence-to-story graph connections and traceable revisions as evidence arrives.
- Story importance based on match context, strength of evidence, recency and novelty.
- Duplicate suppression and a restrained insight feed rather than a card for every possible metric.

Gemini challenges:

- Window boundaries, empty baselines, small samples and interrupted possessions.
- One unusual event creating an exaggerated trend.
- Repeated stories crowding out goals or other important moments.
- Substitutions being described as causes without sufficient evidence.
- Old stories being presented as current, or contradictory stories surviving later updates.

Acceptance: controlled fixtures must trigger the intended rules and reject near-miss cases. Each insight states what was observed and the interval. Qualifiers reflect evidence coverage and sample size; do not invent confidence percentages.

## Milestone 4: a readable, grounded Catch Me Up

Goal: answer the fan's real need in a short briefing rather than reciting metrics.

Target structure:

1. Current score and match phase, with what happened since the fan's last check.
2. One or two meaningful changes, explained in plain language.
3. Relevant player involvement and a fact-supported reason to pay attention next.

Codex implements:

- Named teams and players throughout the briefing and story cards.
- A compact context packet containing score, time, interval, selected facts, source IDs and known limitations.
- Clear separation of previous context from newly missed events.
- Casual wording and Advanced wording that differ in explanation depth, not accuracy.
- Optional Azure narrative generation through a constrained output contract. Claims must cite supplied fact IDs; quantities and identities are checked before display.
- A dependable deterministic fallback when Azure is unavailable, output is invalid or a claim cannot be verified.
- A readable brief with expandable supporting detail; do not put hundreds of raw IDs in the main reading flow.

Gemini challenges:

- Unsupported causal language: 'because', 'dominating', 'exhausted', 'changed formation'.
- Fabricated names, numbers, timestamps, injuries, standings or future events.
- The model treating seeded scenario descriptions as observed match facts.
- A new summary omitting a goal or losing the cursor after a failure.
- Casual simplification changing the factual meaning.
- AI output containing a fact ID but making a stronger claim than that fact supports. Citation alone is not verification.

Acceptance: each factual sentence has adequate evidence; all missed goals are covered; no future events appear; a quiet interval remains quiet. Compare the AI briefing with the deterministic fallback on the same evidence. Record failures and fix causes, not merely prompt around examples.

## Milestone 5: useful personalization and proactive insights

Goal: help different fans without changing the facts.

Codex implements:

- Favorite team and optional favorite player.
- Relevant selection/ranking and explanation depth.
- A calm 'What changed?' feed that surfaces significant new evidence automatically.
- 'Why am I seeing this?' and evidence inspection.
- Short summaries when the fan returns after missing play.

Gemini challenges:

- A favorite-team preference hiding an opposing goal or decisive event.
- Excessive alerts, repetitive phrasing and metrics that do not answer a fan need.
- Preferences changing factual results rather than presentation.
- Misleading predictions in 'what to watch next'. Phrase this as attention guidance, with supporting observations.

Acceptance: the same match produces meaningfully different relevant briefings for different preferences, while retaining shared critical facts. A fan can get value without typing a question.

## Milestone 6: evaluation, deployment and submission

Goal: demonstrate useful analysis, not just an attractive example.

- Keep small controlled fixtures for rule accuracy and unseen full-match seeds for generalization checks.
- Include edge cases: goalless periods, incomplete passes, disrupted possessions, score changes, substitutions, recovery after provider failure and scenario switches.
- Prepare an evaluation table: expected fact/insight, observed output, evidence validity, unsupported claims, goal coverage, latency and fan feedback.
- Evaluate story importance and readability with a few human football viewers. Record disagreements rather than declaring the assistants' preferences objective.
- Verify live Azure integration, then deploy a public working demo and complete submission materials.
- Resolve asset permissions and accurately describe implemented Microsoft technologies.

Acceptance: judges can open the app, run a variation, understand a change, inspect evidence and use Catch Me Up. Documentation clearly separates implemented behavior, tested behavior and future plans.

## Quality gates for every round

| Gate             | Required evidence                                                                 |
| ---------------- | --------------------------------------------------------------------------------- |
| Football meaning | Defined metrics; valid counterexamples; no unsupported tactical or causal claims  |
| Data             | Valid schema, coherent identities/possessions, correct clocks and reproducibility |
| Evidence         | Claims trace to sufficient events; no invented IDs or look-ahead                  |
| Product          | A concrete fan need improved; usable without asking the model a question          |
| Reliability      | Appropriate regression checks, API contracts and failure behavior                 |
| Presentation     | Names/colors correct; readable summaries; relevant browser checks                 |
| Delivery         | Exact commits, actual check results, patch notes and disclosed limitations        |

Block completion on incorrect scores, missing goals, future leakage, invented facts, broken evidence or lost replay/catch-up state. Treat wording and layout suggestions in proportion to their impact. Do not repeatedly rerun unrelated tests after checks have passed unless further changes or unresolved concerns justify it.

## Practical next session

Start with **Milestone 1 only**: seed-based variations and reproducibility. Codex implements and produces the handoff. The owner gives it to Gemini. Gemini independently reviews and makes focused edits. The owner returns Gemini's report and exact branch/commit to Codex for final verification. Move to possession analysis only after that round is closed.

## Copyable prompt for Gemini

Read `docs/codex-gemini-development-plan.md` and the current milestone's `implementation-handoff.md`. First verify the checkout, branch, base commit and uncommitted changes. Review the actual implementation independently for football meaning, evidence correctness, fan usefulness, reliability and scope. Try controlled counterexamples and unseen seeds where relevant. Write actionable findings to `gemini-review.md`. Make focused fixes on a review branch based on the supplied commit, preserve unrelated work, and do not silently widen the milestone or alter shared contracts. Run appropriate checks and write `gemini-edit-handoff.md` with exact commits, changed files, actual results, unresolved issues and reproduction steps. Do not claim that the model has been trained, the project is published, or the analytics prove tactical causation unless the supplied evidence establishes that. The owner will return your edits to Codex for final review.

## Long-term contribution to football AI

The valuable foundation is an auditable pipeline: versioned event contracts, explicit analytical definitions, connected story evidence, constrained language generation and reproducible evaluation. That makes improvements measurable and lets future integrations replace the synthetic source with an appropriately licensed feed.

Potential later users include fans returning to a game, commentators preparing a recap and analysts investigating a sequence. These are future applications to validate, not current production claims. Training custom models is a separate future decision requiring a defined task, appropriate data rights, diverse data and held-out evaluation. It is not a prerequisite for the next milestones.
