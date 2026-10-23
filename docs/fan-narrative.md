# One story, with the evidence underneath

Latest quality revision: [v13–v13.2 editorial review](recap-quality-v13-review.md) separates scoring moves from rolling metrics, gives the one AI revision all detected errors and fixes a team-versus-player subject bug. The twenty-request run failed its quality gate; focused follow-ups are labeled separately. Model review remains fallible.

Current update: [connected scoring sequences](linked-scoring-sequence.md) documents the v12.1 evidence format, strict recovery-to-goal link and final live failures. Older version sections below are development history, not current acceptance results.

Player-impact revision: the primary plan now prefers a verified named player contribution—direct pass-to-shot links, repeated shooting, or repeated forward passing—over a generic team-shot comparison. Repeated creator/recipient combinations can be named together. Snapshot windows include the latest observed action; checkpoint windows retain missed history. See [definitions and limits](player-impact.md). The selected contribution replaces the generic recent-shot sentence in fallback prose; Azure now writes the entire recap from structured facts and supporting event rows, including goals and the player explanation. No commentary templates are supplied to the writer or inserted into its output. AI countdown wording is rejected to prevent elapsed time being mistranslated as time remaining.

The shared story card now shows one readable paragraph. The score story, recent-action breakdown, exact timing, score path and event rows remain in a collapsed drawer. They are the audit view, not separate sections that a fan must assemble into a story.

## What the model actually does

When a fan explicitly requests **Catch Me Up**, an optionally configured Azure OpenAI deployment (the existing `matchos-explainer` GPT-4.1 mini deployment) can write the recap, rather than only selecting story IDs. It receives:

- The observed score and complete goal trajectory, including repeat equalizers and genuine lead reversals.
- Match phase, clock and incremental scope; an old goal must not be announced as new.
- Recorded shot windows and whether a comparison has sufficient coverage. Focused plans omit unrelated recent passing aggregates.
- The shared editorial plan: selected goals plus the strongest selected qualifying change, carrying original windows, rule versions and event IDs. The writer no longer replaces these with an independently retrieved set of recent patterns.
- Up to 30 recent actions, with recorded player/recipient names, outcomes, possession IDs and coordinates, plus a maximum of 60 supporting raw rows overall; aggregate facts retain their full source event IDs.

All input is synthetic and clipped to the requested match snapshot. This is bounded evidence retrieval, not a complete tracking feed, model training, or an invitation to infer control from pass counts. The combined evidence packet is capped at 32 KiB; if it does not fit, the existing rule recap is used.

For focused plans (v7), Azure interprets the selected measurements and event links and authors one complete paragraph per language, aiming for 55–90 words. The packet excludes prewritten story text and contains no canonical commentary sentences. The server never strips, replaces or inserts model sentences. Schema and reference checks, temporal scope checks, and required player/recipient/count/goal coverage checks run before a separate model request reviews the exact proposed paragraphs. Failed checks reject the whole draft and visibly fall back to the factual rule recap; they do not silently repair it. Accepted AI prose is used unchanged for display and voice. Prompts request digit counts and exact MM:SS windows, leaving surrounding language free. Checks also accept small count words, unambiguous player-name abbreviations, anchored last-ten-minute references and natural bilingual clock connectors. An immediately following explanation can refer back to the preceding measured passage; a conflicting explicit scope cannot be inherited. The deterministic checks establish limited coverage conditions, not semantic entailment: the model reviewer remains fallible and must check attribution, number meaning and equivalent facts across languages. This is not a mathematical zero-hallucination guarantee.

**Limits of validation:** known fact IDs establish referential integrity. They do not prove that every phrase follows from those facts. The second model review is fallible, including when the same deployment reviews its own draft. Focused text is labeled **AI-assisted recap · server-calculated metrics**, not “mathematically verified” or “zero hallucination.” Human evaluation remains required for public broadcast use.

Structured output uses the existing Chat Completions-compatible Azure endpoint and the [official OpenAI JSON Schema response format](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat). Unit-test provider calls are mocked; the separate live acceptance runner uses the user-configured server. See [live verification](live-azure-verification.md).

## Requests, caching and audio

- Live Radar ticks use the rule paragraph and make no new writer calls. Model writing runs only on an explicit Catch Me Up request.
- Verified story selection now governs the visible recap, voice and bilingual evidence drawer through `story_plan`. Its two reserved provider calls plus the writer/reviewer pair can reserve four calls per catch-up against the shared 100-call default process budget.
- Writer/reviewer requests use an eight-second HTTP timeout, 1,400 output-token limit, 32-KiB response cap, no redirects and an allowlisted Azure resource hostname. No browser-supplied text, prompt, key or provider URL is accepted.
- Up to 32 reviewed results are cached using the observed feed, snapshot scope, audience, selected plan IDs, deployment, endpoint and prompt version. Reused match IDs or a different cursor do not reuse another replay's paragraph. No audio is generated just by reading a card.
- Device voice uses the same server paragraph. Azure Listen sends the snapshot, audience, locale, allowlisted voice, selected plan IDs and optional opaque narrative ID. The backend reconstructs selected stories from the observed snapshot, rejecting unknown, duplicated or out-of-scope IDs; no client-supplied prose is accepted. It reads the exact cached paragraph shown on screen, with measured delivery. If the paragraph is no longer cached, the server asks for a fresh Catch Me Up instead of substituting text. The fixed **Preview voice** sample remains separate from the displayed match recap.
- Failure labels distinguish rule-based text from model-written text. Speech availability and text generation are separate services.

## Private local setup

The running development server has no persisted cloud keys. Closing the previous terminal loses its process-only configuration. Do not paste credentials into chat or put them in frontend settings.

1. Stop the existing backend on port 8000; leave the frontend running.
2. From the project root, run the launcher in PowerShell:

   ```powershell
   .\scripts\start_backend.ps1 -AI -Speech -SpeechRegion canadacentral
   ```

   It prompts privately for the **Foundry resource key**, then the **Speech resource key**. These are separate keys. It saves neither key. Use `-AI` alone for text or `-Speech` alone for audio. Model endpoint/deployment can be overridden with `-ModelEndpoint` and `-ModelDeployment`; the endpoint must end in `/openai/v1`, not `/api/projects/matchos`.

   If Windows opens `.ps1` files in Notepad, explicitly invoke PowerShell. If local execution policy blocks the script, the previously used process-only `RemoteSigned` setting can be applied to that terminal; do not weaken the machine-wide policy.

3. Refresh the app and start a new matchday because this demo's matches and session ownership are in memory.
4. Request Catch Me Up. An accepted focused recap is labeled **AI-assisted recap · server-calculated metrics**. A rule-based label means the writer is off, unconfigured, over budget, fell back, or intentionally skipped an empty quiet selection; it does not mean GPT generated the text.
5. Switch EN/ES and compare facts. Select an Azure narrator for Spanish. Device voice requires a matching installed local Spanish voice; the UI explains when it is absent. **Check voice connection** refreshes configuration status after reconnecting the backend.

## Acceptance checks

Automated checks cover writer/reviewer requests, references, schema failures, failed bilingual review, provider failure privacy, budgets, future exclusion, cache scope, retained goal evidence, screen/audio identity and cache-expiry errors. Component tests verify a single visible paragraph with analytical sections inside the collapsed drawer and honest model labeling.

The earlier paragraph-first milestone passed 164 backend tests and 51 frontend tests, along with the production build. Browser checks verified the rule paragraph, EN/ES switching, all four Palace–Newcastle goals in the drawer, the missing Spanish-device-voice explanation and a 390px layout without horizontal overflow. Voice and broadcast controls follow the story. See the [rule-based paragraph preview](paragraph-recap-preview.png); it does not depict a live model-generated recap.

The bounded live gate covers one busy and one quiet interval in both audiences and languages, plus a separately simulated provider failure. It is not a broad quality benchmark. Half/full-time and other passing/recovery patterns still need a broader live evaluation. The owner previously confirmed Azure audio playback, which does not validate the current Spanish setup.

## Shared story plan and quiet-match calibration

Explicit Catch Me Up now binds the verified selector output to a single plan containing the snapshot, covered story IDs, primary change, measurements, rule versions and evidence IDs. English and Spanish fallback prose describe that change in its historical window before reporting recent activity. Analyst wording includes rule thresholds and limitations. A quiet interval can return no qualifying change; insufficient baseline coverage is labeled separately. No new metric thresholds were tuned to make the demo look busy.

The authored matchday now separates short midfield circulation from longer forward passes during its explicit busy spells, varies lateral positions and includes intercepted passes. Recovery locations are authored per possession, rather than inheriting the previous shot endpoint. The quiet fixture has no progressive-pass, high-recovery or shot-frequency stories; its two actual recovery-to-shot chances remain inspectable. This is improved synthetic test data, not a complete realistic tracking simulation.

The main evidence drawer uses the same selected change in both languages. Azure narration reconstructs that plan and reads exactly the displayed fallback; reviewed AI narration additionally requires its matching cached identity. An empty quiet plan intentionally skips AI writing with `no_selected_story`, distinct from an Azure outage.

AI commentary revision (v7): the v6.3 authored commentary templates were removed. Rule-based fallback wording is factual again. Energy, rhythm and interpretation belong to the AI writer, with no named-commentator imitation, invented crowd reactions, player emotions, shot quality or tactical claims. The existing quiet-match selection and evidence rules remain unchanged.

## Frozen chronology revision (v8)

The AI now receives per-link observed action times and a structured separation of goal-producing links, other earlier attempts and later attempts for each observed goal in the same period. An entire ten-minute pattern cannot stand in for the build-up to an earlier goal. This context supplies facts and relationships, not commentary sentences. It does not alter the analytics thresholds or select a new story.

The writer explains the contribution once; the separate reviewer additionally reports chronology and redundancy checks. Known misleading goal-pattern framing, exact duplicated sentences and selected unsupported evaluations have local regression checks. Other semantic failures remain possible. Casual targets 35–65 words, Analyst 50–80, with room up to 95 when selected goals require it; the server never truncates or repairs the writer's sentences.

Every narrative carries a SHA-256 fingerprint over the exact writer and reviewer prompts and the version. Cache identity includes that fingerprint. The twenty-case runner records these exact prompts, all results and supporting evidence, and refuses to mix versions. See `recap-editorial-evaluation.json` for live outcomes and `fan-evaluation.md` for the unrun five-person study. A test pass or model-review pass is not a fan-comprehension result.

## Current editorial workflow (v9)

The twenty-request v8 baseline is preserved with its failures; see [editorial review](recap-editorial-review.md). The current writer gets compact selected facts and structured chronology, while its reviewer receives the full evidence packet. A single recovery-to-shot event uses a point clock and elapsed time, not an invented rolling window. Factual fallbacks retain selected scorers and goal clocks; empty limited-coverage plans skip generation intentionally.

Known positive pressure/threat and quality interpretations, internal metric names, and redundant named-player explanations are checked locally. These checks are conservative and incomplete. A focused draft with a content-check failure can receive **one AI-authored revision**, followed by the same validation and a separate model review. The server never inserts or deletes commentary sentences itself. Invalid schemas or fact references do not get that revision path. No failed semantic-review result is automatically retried.

Normal writing and review use two provider calls. A bounded revision can make that three actual calls; another pair is reserved conservatively against the shared budget, so the writer may reserve four, plus the selector's pair. Provider failures do not cause automatic cloud retries. Cached results include the complete prompt fingerprint and version. The temperature is 0.2.

The final live spot check covers one seeded goal-pattern snapshot in both perspectives and languages; it is not a full twenty-case rerun on the final version. The five-fan study remains unrun. Read the linked report before making quality or user-impact claims.
