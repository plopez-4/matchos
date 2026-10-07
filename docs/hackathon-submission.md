# Inside the Game — submission plan

Source: user-provided hackathon brief. Full category requirements at https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/home/executive_challenges were not accessible during review. Required hero technologies, category-specific conditions and key dates remain unconfirmed. Do not infer a deadline.

## Submission requirements from supplied brief

- Newly built AI-powered project using synthetic, football-realistic events only.
- Short pitch explaining problem, behavior and Microsoft/Azure technologies actually used.
- Functioning product footage in a video strictly shorter than two minutes; aim for 1:45.
- Public video URL on a supported platform and public GitHub repository.
- No third-party trademarks, music or other copyrighted material without permission. Use fictional teams, original UI and original narration.

Repository: https://github.com/plopez-4/matchos (public).

## First implementation step

Replace independent random events with a seeded, coherent scenario: calm opening, a sustained attacking spell, a plausible shot/goal sequence, and a response from the other side. Track possession, player/team membership, clock progression and spatial continuity. Goals follow goal-producing shots; distinguish recorded shot attempts from goal events to prevent double counting. Provide a fixture with known expected counts and evidence IDs.

Then implement one five-minute shot-frequency comparison, connect its metric/story nodes to evidence, and display a fan explanation. Call this increased recorded shooting activity; do not equate it to tactical pressure without supporting data.

## AI and Azure plan

An AI-powered path is needed for the submitted product. Deterministic text remains the failure fallback, not the final AI implementation.

Proposed Microsoft integration: Microsoft Foundry for a tool-using explanation agent. Tools retrieve trusted metric windows and graph evidence; the agent selects a supported storyline and adapts phrasing to the viewer. Validate facts and cited IDs before display. Include an orchestration trace showing tool calls, evidence checks and fallback behavior. These are implementation recommendations, not verified mandatory hero technologies.

Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview

Deployment service and model choice follow category verification and available Azure access. Azure OpenAI-compatible tool-based selection is implemented and live Casual/Advanced calls have been verified. Hosted Foundry Agent Service deployment remains future work; describe only the actual implementation.

## Rubric mapping (20% each)

| Criterion                     | Demonstrable proof                                                                                  |
| ----------------------------- | --------------------------------------------------------------------------------------------------- |
| Technological implementation  | Passing CI, shared contracts, real Microsoft integration, documented architecture                   |
| Agentic design and innovation | Tool-using story selection, graph retrieval, evidence validation and execution trace                |
| Real-world impact             | Returning fan understands missed action; hosted demo, recovery/error behavior and deployment limits |
| UX and presentation           | Readable match view, evidence drilldown, useful Catch Me Up, concise functioning demo               |
| Category adherence            | Verify full challenge brief, synthetic realism, public repo/video, required technologies            |

## 1:45 video outline

- 0:00–0:12: Returning fan's problem and MatchOS promise.
- 0:12–0:37: Live fictional match and evolving activity.
- 0:37–1:02: One story, graph evidence and visible agent tool trace.
- 1:02–1:27: Catch Me Up with casual/advanced phrasing from the same facts.
- 1:27–1:45: Microsoft technology actually used, working deployment and impact.

## Outstanding inputs

Full challenge/category text, required hero technologies, submission deadline, artwork authorization for the demo video and public deployment details. Azure account/model access is available. Team participation is pending; build the vertical slice solo while ownership roles remain available.

## Current demo and assets

Run the latest dashboard branch, open a fresh replay URL at 0–0 and start its simulator match ID. Show the goal takeover, recorded shot comparison and both Catch Me Up sections. Inspect the Azure trace before an empty check replaces it. Reload for a fresh viewer cursor before demonstrating the other audience over the same events. Keep the video under two minutes. Credit the stadium photo and confirm league/Microsoft artwork authorization against event guidance before video submission; sources/terms are in visual-assets.md. No public video or hosted deployment is claimed by these code changes.
