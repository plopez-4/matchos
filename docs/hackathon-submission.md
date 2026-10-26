# MatchOS — current submission package

Updated 25 October 2026. This repository package is not a completed hackathon portal entry.

## Project description

MatchOS helps returning football fans understand what they missed and decide what to follow next. Synthetic passes, recoveries and shots feed deterministic analytics and an event-to-metric-to-story evidence graph. Optional Azure AI selects verified stories and writes a bilingual Catch Me Up paragraph from structured observations. Fans can follow recorded scoring moves, listen in English or Spanish, and inspect the supporting events. Match Radar compares three simultaneous streams using observed activity. Red cards open concise recorded explanations, including a dismissal after full time that leaves the result and playing numbers unchanged.

## Implemented technology

- Python/FastAPI: validated synthetic replay, rolling analytics, player contributions, score trajectory, disciplinary metadata and linked evidence.
- React/Vite: mobile fan page, schematic build-up replay, fixed-case test hub and separate development inspector.
- Azure OpenAI-compatible Foundry deployment: verified-ID selection, whole-paragraph EN/ES writing, model review, bounded revision and factual fallback.
- Azure AI Speech: optional server-generated narration, pronunciation hints and club-name pauses. Automatic and Warm storyteller are the visible voice choices.

Orchestration runs in the application. Hosted Foundry Agent Service, Event Hubs, Cosmos DB and full player tracking are not implemented. A Container Apps deployment package exists; no public hosting deployment is claimed. The current source and CI image must be verified before any deployment.

## Submission checklist

The [official Microsoft rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) remain the authority; the earlier requirements review was recorded on 23 October. Check them and the entry portal before final submission.

- Public source: [plopez-4/matchos](https://github.com/plopez-4/matchos), canonical branch `main` after release integration.
- Project description: provided above; refine only for the portal's actual fields.
- Demo video: final public link still needed. Use the [1:45 storyboard](demo-storyboard.md), showing the actual app and its synthetic-data disclosure.
- Judging access: public website or accepted runnable build/access instructions still need confirmation. Localhost links are not external access.
- English materials: root README and this description; the app also supports Spanish.
- Assets: confirm [asset permissions and attribution](visual-assets.md) in recorded footage. Unlicensed Premier League/Microsoft logos have been removed.

Publishing code alone does not submit the entry. Deployment remains separate from this GitHub update and requires an agreed cost/access setup.

## Repeatable judge walkthrough

1. Clone `main` and follow the root README. Open `/testing.html` and select a fixed version; do not rely on random matchday selection.
2. Use Normal/Fast demo pace, pause after a listed goal, and request Catch Me Up. All three match streams pause for the snapshot.
3. Check the current score, actual named participants, separate shot/goal clocks and source evidence. Open the explicitly linked goal build-up.
4. Switch English/Spanish and Casual/Analyst. Identify whether the paragraph is AI-written or factual fallback; Azure configuration alone does not establish authorship.
5. In version 4, inspect Palace's 35:00 card, City's 55:00 card, Fulham's 60:00 card, then the losing Fulham player's post-match dismissal at 93:00. Card reasons are fictional authored data, not claims about actual incidents.
6. Optionally demonstrate Listen with private Azure Speech configuration. Never show keys in footage or provide them in public instructions.

## Evidence and remaining quality work

- Current local checks: **597 backend tests, 72 frontend tests and production build passed** on 25 October. CI adds formatting, credential/dependency scans and container build/startup checks. Automated providers are mocked.
- Ten screenshot-questionnaire submissions were reviewed; see [aggregated findings](fan-study-oct24/findings.md). This is comprehension feedback, not ten hands-on sessions or proof of engagement uplift. The owner confirmed the current phone and computer presentation.
- The [v23 live audit](recap-v23-nine-match-review-oct24.md) preserves eighteen live requests, accepted errors, rejected drafts and later focused confirmations. Those historical results do not certify writer v27 or all twelve current match versions.
- Remaining delivery: confirm hosted judging access, record/upload the final video, check final portal requirements and submit. A fresh live AI matrix and broader hands-on/listening checks remain separate quality evidence.

Do not claim guaranteed factual accuracy, real-time production feeds, continuous tracking, trained recommendations or measured engagement improvements.
