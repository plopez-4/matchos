# Expressive match narration

The optional Azure Speech integration is implemented and tested with mocked provider audio. The project owner configured a Speech resource and confirmed live playback on 12 October 2026. Automated checks still use mocked audio; the revised wording below needs a fresh listening comparison. Foundry chat-model deployment settings are not used as Speech credentials. The basic device reader remains an explicit fallback option; cloud narration never silently substitutes it after a failure.

## Voice audition

The main fan page defaults to **Automatic (Azure when connected)**. Once the server reports Speech availability, Listen uses the Matchday Azure profile in the selected recap language, including Spanish on computers with only English voices installed. Without Speech configuration, Automatic uses an installed matching device voice; it remains disabled when neither provider can serve that language. Explicit voice choices are preserved, and a failed Azure request never silently switches providers. After connecting Speech, reload the page or use **Voice options → Check voice connection**.

Each Match Story card offers **Matchday narrator**, **Warm storyteller** and **Device voice (basic)**. **Listen** reads the selected match snapshot. **Preview voice** compares profiles on the same verified, synthetic Palace–Newcastle 2–2 recap at 75:30. Preview is separate from the selected fixture's recap.

| Profile           | English               | Spanish                | Measured / recent-goal styles                    |
| ----------------- | --------------------- | ---------------------- | ------------------------------------------------ |
| Warm storyteller  | Ryan, British English | Dalia, Mexican Spanish | Ryan: chat / cheerful; Dalia: default / cheerful |
| Matchday narrator | Davis, US English     | Jorge, Mexican Spanish | Davis: friendly / excited; Jorge: chat / excited |

Style mappings follow [Microsoft's supported voice styles](https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/ai-services/speech-service/includes/language-support/voice-styles-and-roles.md), checked 11 October 2026. Region/resource availability still needs a live audition. These are named Azure voices, not clones of football commentators.

For rule-based text, only a newly observed goal within the last 180 match seconds, during play, enables energized delivery. The headline and response get that style; score, shot counts and clock stay measured. A goal already seen by the catch-up cursor stays measured even if it was recent. Halftime, full time and older moments use measured delivery. This is an editorial delivery rule, not a learned excitement probability. Optional [model-written prose](fan-narrative.md) is read as one measured paragraph, exactly as displayed; its model review is fallible. SSML paragraphs provide pauses. Emotional quality is subjective and should be assessed by listening before selecting a default.

## Story-first spoken recaps

Both Azure profiles and the basic device voice use the same server-built English/Spanish text (`spoken_recap`). The displayed card and its complete goal path, per-team counts and supporting event IDs remain available. Older backend responses without that field retain the previous device-reader fallback.

Spanish Azure narration adds SSML pronunciation aliases for Manchester United, Manchester City and the shortened Manchester/United/City forms. The original spelling, facts and Spanish conjunction remain in the paragraph; only spoken pronunciation receives a hint. English and device narration are unchanged. Azure accepted a fresh Spanish match recap with these hints on 23 October 2026; listening remains the check for subjective pronunciation quality.

The [complete player-name audit](spanish-player-name-audit/README.md) covers all 133 bundled players in both Spanish profiles. Seventeen targeted hints are maintained separately in `backend/app/data/spanish_pronunciations.json`, with written sources. Names without hints retain default provider pronunciation and remain pending listening approval. The audit's HTML playlist and JSON inventory distinguish successful audio generation from actual listening approval.

- After a changed score: lead with the observed turning point, give the score, then one response interval when supported. Close with recent shots and regular time remaining. A shot comparison is used when available and not competing with a response interval.
- With no new goal: state the score and that no new goals have been recorded, then summarize recent shots and time remaining. Do not replay the old scoring headline as a fresh alert.
- At halftime/full-time: identify the phase, give the score and summarize the last score transition; omit the live countdown and recent-shot window.
- Before five minutes: say “opening moments.” Without sufficient history: omit the comparison. No shots means no shots **recorded**, not a claim about possession, quality or pressure. Added time never produces a negative countdown.

The 75:30 English audition now says:

> Newcastle United led twice, but Crystal Palace have answered twice. That leaves them level at 2 all. The latest goal came 9 minutes after the previous one. Across the last five minutes, the teams have recorded 6 shots. There are 14 minutes and 30 seconds until ninety, plus added time.

The editorial target is roughly 15–25 seconds for a live rule recap. This sample is 50 written words in English and 48 in Spanish; spoken numbers, voice and pauses affect actual duration. Optional model prose targets 45–75 words per locale. No duration guarantee or measured engagement improvement is claimed. All goals stay in the evidence drawer even when the audio summarizes their trajectory.

## Student setup

1. In [Azure Portal](https://portal.azure.com/), search for **Speech** and create a Speech resource under your student subscription. Choose **Canada Central** if the subscription permits it; it supports neural speech according to [regional availability](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions). Use the **Free F0** tier if offered. Microsoft currently lists 0.5 million neural TTS characters monthly for the free tier; check the creation screen and [current pricing](https://azure.microsoft.com/en-us/pricing/details/speech/) before accepting a paid tier. Availability is not guaranteed by this app.
2. Wait for deployment, then open **Keys and Endpoint**. Keep the key private; do not paste it in chat, GitHub, frontend settings or screenshots.
3. Stop the existing backend with Ctrl+C in its terminal. From the project root in PowerShell, run:

   ```powershell
   .\scripts\start_backend.ps1 -Speech -SpeechRegion canadacentral
   ```

   The launcher prompts for the key using hidden input. It passes the key only through the backend process environment, saves no credential file and restores the parent terminal's previous settings on exit. Use the actual resource's region if different. The `.env.example` values are documentation; this repository does not automatically load `.env`.

4. Keep the frontend running, refresh the page and choose **New matchday**. Backend restarts clear this in-memory demo and session ownership. Create a fresh replay before using cloud **Listen**. Profile availability refreshes on page reload.
5. At the same paused snapshot, compare **Preview voice** for Warm and Matchday. Check English/Spanish, clear pronunciations, pauses and appropriate energy. Decide by listening; the mocked tests do not prove voice quality or live service availability.

## Data and credentials

The browser sends a validated match ID, sequence cursor, clock, language and allowlisted profile—not free-form text, SSML, provider URL or credentials. For a displayed model paragraph it also sends an opaque `narrative_id`; the backend resolves that exact cached text or returns 409, never substituting another paragraph. The backend requires the replay's owning session, rebuilds the story from stored events, and rejects a snapshot that omits recorded events at its stated clock. SSML escapes text and uses only allowlisted voices/styles. The audition endpoint also requires a session and generates its fixed sample from the deterministic fixture.

Only the selected recap is sent to Azure Speech. Historical benchmarks and evidence IDs are not sent as narration; there is no microphone request, real video stream or player training dataset. Model-written text can be read only after the writer/reviewer path has accepted and cached it; it is not a mathematical guarantee of factual correctness. Audio is returned as MP3 through the backend. Speech credentials are distinct from the optional Azure OpenAI model configuration. The integration uses existing `httpx`, with no new SDK dependency. See the [official REST API](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech).

## Bounded operation

- Off by default. Missing key or invalid region disables cloud controls and causes no provider request.
- One in-flight provider call; six narration/audition requests per minute per session; 50 provider calls and 50,000 SSML characters reserved per backend process. Failures consume the reserved budget and are not automatically retried.
- At most 3,200 spoken-text characters, 512 KiB returned audio and eight cached clips (at most 4 MiB). HTTP timeouts and a streaming deadline check limit slow responses; redirects are disabled and the endpoint is constrained to the regional Azure Speech hostname.
- Provider error bodies and credentials are never returned to the browser. The UI offers retry or explicit device fallback rather than concealing failures.
- Stop, fixture/language/profile changes and unmounting abort pending client requests and release audio URLs. All cards and native speech share one playback owner. A backend synthesis may finish after client cancellation and still count toward Azure usage.

These limits are per process and reset on restart/reload. They are not a distributed quota or Azure billing cap. Use F0/provider quotas and account cost controls where applicable; keep the demo on one backend worker.

## Validation

164 backend tests and 51 frontend tests passed; production build passed. Tests use mocked Azure responses, covering snapshot ownership, future/omitted events, unsupported inputs, XML escaping, style selection, off/missing configuration, cache/budget limits, oversized/error responses, playback races and shared cancellation. New coverage checks both languages across all five score transitions, quiet/no-new-goal updates, halftime/full-time, added time, comparison coverage, future exclusion and shared device/cloud wording. The launcher previously passed a PowerShell syntax check.

Earlier browser checks verified the voice selector, clear setup-needed state, disabled cloud auditions and explicit device playback/Stop. The owner subsequently confirmed live cloud playback; automated verification of the new wording does not constitute a fresh live listening test. See the earlier [setup preview](narrator-setup-preview.png).
