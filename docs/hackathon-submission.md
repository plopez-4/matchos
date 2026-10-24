# MatchOS — current submission package

Updated 2026-10-24. This repository package is not a completed hackathon portal entry. See the [publication readiness review](publish-readiness.md) for current release gates.

## Pitch

MatchOS helps football fans return to a match and understand what they missed. Synthetic passes, recoveries and shots feed deterministic analytics and an evidence graph. An optional Azure-hosted model selects verified stories and writes a bilingual recap from structured observations. A fan can watch how a scoring move unfolded, listen in English or Spanish, and inspect the recorded events behind the explanation. Rejected prose produces a labeled factual fallback.

## Implemented technology

- Python/FastAPI: validated replay, rolling analytics, player contributions, score trajectory and event-to-story evidence.
- React/Vite: focused fan page, schematic pitch replay, named replay actions and separate development inspector.
- Azure OpenAI-compatible Foundry deployment: tool-based selection, whole-paragraph EN/ES writing, model review and bounded revision.
- Azure AI Speech: optional server-generated narration, pronunciation hints and club-name pauses.

These are application-orchestrated calls. Hosted Foundry Agent Service, a distributed multi-agent deployment, Event Hubs and Cosmos DB are not implemented. A verified image and Azure Container Apps template are prepared; no public hosting deployment is claimed.

## Official requirements

Source: [Microsoft official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md), re-read 2026-10-23, sections 4.1–4.9 and 6.

The rules require synthetic football-realistic data, a project description, functioning demo footage under two minutes, a public supported video URL, public GitHub code, judging access, and English submission materials or translations. Third-party assets need permission. Judging weighs implementation, agentic innovation, impact, experience and category fit equally. Publishing GitHub alone does not complete the entry.

## Judge testing path

1. Clone canonical `main` and follow the root README. Open `/`, select Palace–Newcastle and start a fresh replay.
2. Use Demo settings to advance; pause just after Sarr's 60:11 equalizer and before the next goal at 66:11.
3. Request Catch Me Up. Inspect the connection from Tomiyasu's recovery to Sarr's equalizer, then open its named replay and supporting events.
4. Switch EN/ES and Casual/Analyst. State whether each paragraph is AI-written or factual fallback; configured Azure alone does not prove authorship.
5. Optionally demonstrate Listen with private Azure Speech configuration. Never disclose resource keys in public testing instructions.

## Evidence and remaining work

- Latest validated checks: 391 backend tests, 62 frontend tests, frontend build, formatting, credential scan, dependency audit and container startup passed.
- [Linked sequence report](linked-scoring-sequence.md): exact chronology, strict linking, live failures and fallback behavior.
- [Five-fan evaluation](fan-evaluation.md): prepared; real sessions remain unrun.
- Latest v14 live check: one source-correct bilingual halftime recap after revision, with repeated equalizer wording still present. The [24 October evidence](recap-capacity-oct24.md) and [earlier editorial review](recap-quality-v13-review.md) preserve the limited success and failures separately. Consistent accurate, engaging AI prose remains unresolved.
- Public code: https://github.com/plopez-4/matchos. Canonical release branch: `main` after integration.
- Public demo video: not provided. Hosted judging access/test build: not confirmed. Complete these before portal submission.
- Confirm [asset permissions](visual-assets.md) for footage. No permission is inferred from hackathon branding.

Use the [1:45 storyboard](demo-storyboard.md). Demonstrate the actual app and name only services implemented. Do not claim guaranteed accuracy, continuous tracking or measured engagement improvements.
