# Recap quality revision v13

Status: the frozen v13 run and focused v13.2 verification are complete. This is a developer editorial review by Codex, not an independent human or fan study.

## Problem and change

The previous prompt imposed overlapping rules: a concrete scoring sequence was also asked to carry a rolling metric window, and Spanish instructions preferred lead wording without conditioning it on the actual score. Duplicate requirements encouraged reporting a goal and then repeating its build-up separately.

The writer now receives the contract appropriate to the selected contribution: one observed scoring move, a single recovery-to-shot event, or a rolling player/team pattern. The model still authors the entire English and Spanish paragraphs; no commentary lines are inserted by the server. Linked moves can use recovery time, team-pass total and goal time without a redundant shot timestamp or invented analysis window. Rolling patterns retain their exact count/window and goal chronology requirements. Existing rejection checks remain intact.

## Frozen evaluation protocol

- Manifest: `recap-evaluation-v13-cases.json`, ten situations and two audiences, returning both languages in each request.
- Version: `fan-narrative-v13-scoped-editorial-contracts`; the report records prompt fingerprints, source hashes, actual evidence, modes, revision use and failures.
- The first fast run hit Azure 429 responses. Continuation preserves completed slots and their failures; it does not rerun rejected cases to improve the headline result. Remaining requests are spaced sixty seconds after completion.
- Intentional limited-coverage/quiet cases are counted separately from rejected AI drafts and service failures. Accepted means the application and model checks passed, not that factual quality is proven.

## Editorial criteria

Inspect accepted paragraphs against their source events for score, actors, counts, times, chronology, team versus individual pass credit, and English/Spanish equivalence. Then record duplication, grammar or filler separately. A style flaw is not automatically a factual error; a model-review pass is not automatically acceptable prose. Unsupported claims block quality acceptance regardless of the overall acceptance count.

No general accuracy percentage or improved fan engagement is established by this small deterministic scenario set. The five-person protocol remains unrun, and pronunciation listening is a separate requirement.

## Frozen v13 results

[Complete report](recap-editorial-v13-live.json): all 20 requests completed and the temporary matchday was released. Six returned AI prose, six intentionally used limited/quiet summaries, three hit provider 429 limits and five failed local content checks (two goal references, two time scopes and one individual pass attribution).

This did not pass a reliable-recap gate. The three service failures remain recorded despite later spacing. This is not a controlled comparison against earlier versions: the manifest adds the 62:30 linked-goal case and removes a different historical checkpoint.

## Captured defects and corrections

A separate two-request diagnostic captured [actual halftime drafts](recap-v13-captured-drafts.json). One simultaneously omitted the scorer/time association, credited all team passes to Rico Lewis and predicted an intense second half. Returning only the first error left other defects invisible to the one allowed revision.

Version v13.1 collects independent checks across both languages and selected facts, supplies actual scorer/time and team/individual counts in structured feedback, and asks the model to fix every listed issue. Invalid schema or fact IDs still fail immediately; there is still at most one model-authored revision. The server never patches prose.

The first v13.1 focused sample was model-reviewed but still wrong: “Lewis recovered for Manchester City and completed three passes.” The local guard mistook the nearby team name for the grammatical subject. It also called the contest balanced based on a tied score. That planned four-request run stopped after two requests and is explicitly marked as a failed source audit, not a passing evaluation.

Version v13.2 distinguishes prepositional team references from team subjects, while allowing explicit relative clauses such as “City, who completed three passes.” Captured bad prose now has regression coverage in both languages; correct collective wording remains valid. A tied score does not establish a balanced contest. These remain conservative checks for known forms, not a complete grammar or entailment proof.

## Current verification

All 368 backend tests and credential scan passed. The 61 previously passing frontend tests and build describe the unchanged frontend. The temporary local capture hook was removed; rejected prose is not exposed in fan API responses.

The [v13.2 focused report](recap-editorial-v13.2-focused-live.json) is a separate four-request check of halftime and the 62:30 equalizer. It does not replace the failed twenty-request run or establish general accuracy. Read its actual modes and failures before describing current writing as reliable. No new feature category was added.

The final four requests returned two AI paragraphs (halftime Analyst and Palace equalizer Casual), one content fallback (`missing_recovery_goal_connection`, halftime Casual) and one provider 429 (Palace Analyst). The temporary matchday was released. Source inspection of the two accepted pairs found correct score, actors, timing, chronology and collective pass credit; the Palace paragraph still ends with generic filler. This is a small developer inspection, not a general accuracy claim.

The validation bugs addressed here are fixed, but the AI writing milestone is **not complete**. Next work stays within this feature: inspect the remaining connection rejections with captured evidence, address service capacity separately from semantic rejection, then run a frozen evaluation on the final candidate before the real fan trial. Do not add tracking or another dashboard to compensate for inconsistent recaps.
