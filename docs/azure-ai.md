# Azure-backed grounded story selection

Status: adapter and mocked integration tests implemented; live Azure calls verified for casual and advanced summaries. AI is off by default. This uses Microsoft Foundry's Azure OpenAI-compatible model endpoint, not the hosted Foundry Agent Service.

## Behavior

1. Deterministic analytics/graph produces trusted story candidates for the catch-up window.
2. A configured model is instructed to call get_match_evidence; the app returns up to eight verified candidates with evidence IDs.
3. The model calls select_stories to order relevant candidate IDs for the audience. All candidate goals must remain included; the strongest verified shooting-activity change is added if the model omits it.
4. The app rejects unknown/duplicate IDs, missing goals, malformed calls and unexpected arguments.
5. Trusted facts are rendered into What happened and What changed sections, with simpler casual wording and detailed advanced counts. AI does not generate free-form factual prose, so it cannot add unsupported claims to the displayed explanation.

This is a bounded tool-using agent flow, not multiple autonomous agents. Casual/advanced preferences influence selection/order; count wording remains deterministic. Model-generated phrasing is a future feature requiring stronger claim verification. Evidence validity currently follows the deterministic story generator and is not an independent LLM fact-checker.

## Configuration

Need an Azure OpenAI-compatible Foundry resource and a deployed model supporting Chat Completions function calling. Use the deployment name, not merely the catalog model name. Region/model availability and access vary; verify your deployment before enabling.

Set variables in the **backend PowerShell terminal** before starting the server. Replace only the resource/deployment placeholders; enter the key at the masked prompt. Do not paste it into chat or commit it.

```powershell
$env:MATCHOS_AI_MODE = 'azure'
$env:AZURE_OPENAI_BASE_URL = 'https://YOUR-RESOURCE.openai.azure.com/openai/v1'
$env:AZURE_OPENAI_DEPLOYMENT = 'YOUR-DEPLOYMENT-NAME'
$env:AZURE_OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'Azure API key' -AsSecureString)).Password
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

The .env.example is a reference template; no file is automatically loaded. API keys stay in the server's process environment and are not returned to the browser. For deployed production use, prefer managed identity rather than a manually supplied key.

Replay the scenario and click Catch Me Up. On successful tool calls, the UI says stories were selected by Azure AI and shows an execution trace. If configuration/provider/output validation fails, it displays the rule-based summary. A fallback proves the app is available, not that live AI is working. Check explanation.mode in the API response; it must be azure to claim a successful integration.

Turn AI off with `$env:MATCHOS_AI_MODE = 'off'` and restart the backend. No model requests occur for an empty story window. Nonempty windows use two requests, each with an eight-second HTTP client timeout; connection and read timeouts are per operation. This is not a hard end-to-end deadline. Redirects are disabled, and keys are sent only to an HTTPS *.openai.azure.com or *.services.ai.azure.com /openai/v1 endpoint. The project-management URL ending in /api/projects/{name} is not the model API base URL used by this adapter.

## Verification and limits

Mock tests cover the complete tool flow, unsupported/missing/duplicate selection, timeout, configuration rejection and disabled/empty behavior. They incur no Azure usage. Earlier live testing with the configured deployment succeeded for both audiences, returning azure mode and both What happened / What changed sections. The current adapter has a process-lifetime request budget, concurrency/input/output limits and deterministic fallback; identical catch-up requests are cached. Production hosting and Azure account settings still need verification before public exposure. See [security setup](security.md).

Official reference: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/function-calling

## Focused recap verification — 2026-10-22

The focused page now exposes Casual / Analyst and English / Spanish. The writer uses audience-specific instructions and caches by audience plus evidence snapshot. Analyst fallback adds completed/attempted passes for the observed recent window, with supporting event IDs and a warning that these counts cannot establish possession or chance quality. Both languages preserve the same facts. Narration requests accept an optional audience so cached prose can be recovered for the correct perspective.

The selector retrieves evidence and validates selected stories; the prose writer receives a bounded observed evidence packet and a separate model call reviews grounding, bilingual parity, score and phase. These are bounded application-controlled steps, not a claim of autonomous multi-agent orchestration. The evidence drawer reports whether prose review passed or a rule-based fallback was used. Model review is fallible.

Current verification: 171 backend tests and 69 frontend tests passed, production frontend build passed, and the running browser showed analyst passing totals and matching Spanish facts. Provider calls in these tests were mocked. No Azure model credentials were configured for this session, so the current live Azure writer/reviewer path remains unverified. Earlier selector-only success is not proof that the current full prose workflow works live. Configure privately with `scripts/start_backend.ps1 -AI`; never put a key in a chat, URL, committed file or screenshot.
