# Azure-backed grounded story selection

Status: adapter and mocked integration tests implemented; live Azure call not yet verified. AI is off by default. This uses Microsoft Foundry's Azure OpenAI-compatible model endpoint, not the hosted Foundry Agent Service.

## Behavior
1. Deterministic analytics/graph produces trusted story candidates for the catch-up window.
2. A configured model is instructed to call get_match_evidence; the app returns up to eight verified candidates with evidence IDs.
3. The model calls select_stories to order relevant candidate IDs for the audience. All candidate goals must remain included.
4. The app rejects unknown/duplicate IDs, missing goals, malformed calls and unexpected arguments.
5. Trusted story text is rendered in the selected order. AI does not generate free-form factual prose, so it cannot add unsupported claims to the displayed explanation.

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

Turn AI off with `$env:MATCHOS_AI_MODE = 'off'` and restart the backend. No model requests occur for an empty story window. Nonempty windows use two requests, each with an eight-second HTTP client timeout; connection and read timeouts are per operation. This is not a hard end-to-end deadline. Redirects are disabled, and keys are sent only to an HTTPS *.openai.azure.com /openai/v1 endpoint.

## Verification and limits
Mock tests cover the complete tool flow, unsupported/missing/duplicate selection, timeout, configuration rejection and disabled/empty behavior. They incur no Azure usage. Live testing requires user configuration and is outstanding. The current synchronous handler occupies a worker thread during model calls; deployed service needs concurrency limits, budgeting, tracing and authenticated access before public exposure. This adapter is not deployment-ready.

Official reference: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/function-calling
