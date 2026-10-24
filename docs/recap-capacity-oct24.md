# Recap reliability and capacity — 24 October

## Implemented

Story selection and paragraph writing now share a bounded, deployment-specific cooldown. An Azure 429 records `retry-after-ms`, `retry-after` seconds or HTTP date; the longer valid wait is honored. Missing/invalid headers use a sixty-second default. During the wait neither stage makes another provider call or reserves more of the application call budget. No automatic retry loop or sleeping web request was added. A new request can try after expiry; successfully reviewed prose can still come from its snapshot cache.

A rate-limit fallback is no longer stored indefinitely in the outer Catch Me Up cache. Its English/Spanish label says the AI is temporarily busy while retaining factual summary authorship. The status endpoint exposes only the remaining wait, not provider errors or credentials. Existing capacity, concurrency and AI-call budgets remain enforced. This reduces repeated calls during throttling; it does **not** increase Azure quota or establish the resource's actual TPM/RPM allocation.

Microsoft documents the wait headers and that output-token allowances contribute to rate-limit estimates. [Azure quota guidance](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/quota).

## Recap evidence

A captured halftime sample on the old version passed model review but added unsupported momentum/rhythm claims. That draft is now an EN/ES regression fixture. Missing-connection feedback additionally supplies the actual recoverer, scorer, clocks, team total, elapsed time and score effect, without inserting commentary sentences.

The [single v14 live sample](recap-v14-halftime-live.json) returned AI prose after one model revision. It correctly distinguished Lewis's one pass from the team's three passes, with correct source actors and goal chronology. It still repeats the equalizer across sentences. One accepted pair does not establish reliable writing or improved engagement; the failed twenty-request run and earlier regressions remain preserved.

## Verification

391 backend tests, 62 frontend tests, production frontend build, formatting and credential scan passed locally. Tests simulate time without waiting and cover selector-to-writer and writer-to-selector throttling, expiry/recovery, header parsing, bounded state, budget preservation, safe fallback and retryable snapshot caching. The temporary draft capture is removed.

Read-only portal inspection confirmed `matchos-explainer` uses GPT-4.1 mini (2025-04-14), Global Standard, with a current allocation of **10,000 tokens per minute**. The edit form displayed a 5,000,000 upper bound; that is not proof that all capacity is available. No allocation was changed, and requests-per-minute capacity was not confirmed.

Judging access is still not deployed. [Container preparation and public-access verification](judging-deployment.md) are separate from text-model correctness. The existing student resource group contains Foundry, its project and Speech, with no website host. Public deployment, external browser/phone testing and the five-fan study remain outstanding.
