# MatchOS — submission package

Updated 27 October 2026. The public app and repository are available. A local 1:48 demo edit exists; a public video URL and the completed hackathon portal entry remain outstanding.

## Links for the submission

- Working application: [Open MatchOS](https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io/).
- Repeatable cases: [Fixed test hub](https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io/testing.html).
- Public source: [plopez-4/matchos](https://github.com/plopez-4/matchos), default branch `main`.
- Verification: [27 October audit](release-verification-oct27.md) and [public access results](judging-access-oct27.json).
- Demo video: upload the owner-reviewed 1:48 MP4 to an accepted video host, then paste its publicly accessible URL into the project entry. The repository does not currently contain a public video link.

## Elevator pitch

MatchOS helps football fans return to the story of a match. Synthetic passes, recoveries and shots flow through deterministic analytics and a match story graph into a grounded Catch Me Up explanation. Fans can inspect the recorded evidence, replay how a goal developed, switch audience and language, and listen to the recap. Match Radar compares three simultaneous synthetic matches using activity already observed.

## Implemented technology

- Python/FastAPI validates the event stream and calculates rolling metrics, player contributions, score changes, disciplinary details and linked evidence.
- React/Vite provides the mobile-friendly fan experience, recorded-action pitch replay, fixed test hub and separate development dashboard.
- An Azure OpenAI-compatible Foundry model deployment supports verified-ID selection, complete English/Spanish narrative generation, separate model review and bounded revision. Invalid or unavailable output falls back to labeled factual text. Model review is fallible.
- Azure AI Speech provides backend-generated narration with pronunciation hints and team-name pauses. Normal and 0.75× listening speeds are available; changing an existing Azure clip's speed does not generate a new clip.
- Azure Container Apps serves the built frontend and backend at the public HTTPS address above. Judges need no account, installation or provider keys.

Orchestration runs in the application. Hosted Foundry Agent Service, Event Hubs, Cosmos DB, a real official match feed and full-player tracking are not implemented. All displayed match actions, including disciplinary incidents, are fictional. Reference player identities are dated, not a guarantee of current official squads.

## Repeatable judge walkthrough

1. Open the hosted fixed test hub. Select **Manchester United vs Manchester City → Version 1**. A fresh browser session creates its own replay; do not share another browser's `?day=...` URL.
2. Start replay and use Fast to approach **16:00**, then pause. The authored goal at **15:11** appears by the 15:30 clock step. All three fixtures advance together; selecting another fixture preserves that clock.
3. Request **Catch Me Up**. Look for the recovery at 15:00, completed passes, Bryan Mbeumo's shot at 15:10 and goal at 15:11. Inspect the actual AI-written/factual-fallback label. Capacity or validation can legitimately return fallback.
4. Expand **Inspect supporting events** to check timestamps, identities, event IDs and coordinates. Open the named goal build-up. The schematic shows involved players and recorded ball locations, with a bounded directional pulse; it is not continuous tracking or an assertion of attack quality.
5. Compare **Casual** and **Analyst**, then **English** and **Español**. Press **Listen** for the displayed snapshot. The app pauses all three matches while reviewing or listening; resume explicitly afterward. Voice options expose Automatic and Warm storyteller, plus Normal/Slower listening pace.
6. For recorded sending-off details, return to the hub and choose Version 4: Palace at 35:00, City at 55:00, Fulham at 60:00, then a losing Fulham player's post-match card at 93:00. Cards show a recorded explanation rather than a fabricated move replay. The post-match card does not change the final score or earlier playing numbers.

The public app works independently of the developer's laptop. Data and sessions are in memory: cold starts or restarts can reset a replay. Start a fresh replay if needed. Shared-session recovery creates a new owned game rather than transferring control of the original. Avoid repeated recap/audio requests solely to obtain a preferred answer; the demo uses bounded provider capacity.

## Final entry checklist

The [official Microsoft rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) and the entry portal remain authoritative.

- Include the pitch, implemented Microsoft/Azure technologies, working app link, public repository and testing instructions.
- Upload and check the demonstration video: strictly under two minutes, real working-app footage, English materials or English translations, and a public URL on an accepted host.
- Include the English translation of the Spanish narration shown in the video. The owner has a companion English transcript with the local edit.
- Preserve [asset credits](visual-assets.md). The current video framing uses the logo-free app; no licensed match footage or background music was added.
- Finish the actual project entry and verify the portal shows it as submitted. Repository publication does not submit the hackathon entry.
- Keep free judging access available through the judging window. Existing student-credit protection and application budgets do not replace an availability check.

## Evidence and limits

The 27 October audit passed 597 backend tests, 89 frontend tests, formatting, the production build, credential scanning and dependency advisory checks. Public HTTPS, cookies, two-session isolation and a bilingual Azure-authored recap passed. The demo recording also exercised supporting evidence, the goal replay, audience/language changes and Azure Spanish narration.

Ten screenshot-questionnaire submissions informed clarity changes; see [aggregated findings](fan-study-oct24/findings.md). These are not ten verified hands-on app sessions or measured engagement uplift. Historical [live recap audits](recap-v23-nine-match-review-oct24.md) retain accepted errors and rejected drafts. A fresh full twelve-version AI/listening matrix remains uncompleted; neither tests nor model review guarantee factual accuracy.
