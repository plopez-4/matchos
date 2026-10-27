# Hosted judging deployment

Updated 27 October 2026. [MatchOS is live](https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io/). Local frontend/backend servers do not need to run for judges to use this URL. The [fixed test hub](https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io/testing.html) provides all twelve authored versions.

## Deployed application

- Service: Azure Container Apps, North Central US; app `matchos-judging` in resource group `rg-plopez4-2657`, environment `matchos-judging-env`.
- The observed deployment uses the Express hosting path. The checked-in ARM template describes a separate Consumption deployment example; do not treat it as an exported description of the running Express resource.
- Application image: `ghcr.io/plopez-4/matchos-judging@sha256:0eb79015dd925d9c72b69fe98e96e3194732780befd0fcf37e06ece83a985f5b`.
- Image source: commit `fcacbc6aa212c199171638ddbaa3b61d2a442914`, [successful image publication](https://github.com/plopez-4/matchos/actions/runs/40374840094). Later documentation-only commits do not require redeploying this app image.
- One backend worker, 0.25 vCPU/0.5 GiB, zero-to-one replicas, HTTPS managed ingress targeting port 8000, TCP startup/readiness/liveness probes and one active revision. This is a bounded in-memory prototype, not a multi-instance production architecture.
- Azure model and Speech configuration are supplied privately as runtime environment/secret references. They are not embedded in the image or browser bundle. The default image has both providers off until configured.

The student spending limit was checked as On during the owner's 25 October setup. That is a dated observation, not a current balance statement, a new billing guarantee or permission to remove protection. This documentation audit did not change Azure resources, pricing tiers, replicas, budgets, secrets or the subscription.

## Template versus an existing app update

The [ARM example](../deploy/azure-judging.json) creates a Consumption environment and app with exact derived hosts/origins and explicit `CONTAINER_APP_NAME` / `CONTAINER_APP_ENV_DNS_SUFFIX` metadata. It pins the tested application image above, creates no registry/database/log workspace and starts AI/Speech off. It requires the target subscription's region/policy support and normal Azure deployment approval.

For the existing hosted app, preserve its runtime secrets and provider settings when updating an image. Reapplying the initial template can replace configuration and turn providers off. A documented example is not an instruction to recreate the owner's running resource.

The owner can update only the image in Azure Cloud Shell Bash:

```bash
az containerapp update \
  --resource-group rg-plopez4-2657 \
  --name matchos-judging \
  --image ghcr.io/plopez-4/matchos-judging@sha256:0eb79015dd925d9c72b69fe98e96e3194732780befd0fcf37e06ece83a985f5b \
  --only-show-errors --output none
```

No update is needed solely for this repository documentation refresh. For a future application change, wait for the new image workflow to pass, inspect its digest and pin that tested image instead. Keep keys out of commands, screenshots, commits and build arguments.

## Ingress and media requirements

Use external managed HTTP ingress with HTTPS required and no additional directly reachable listener. `MATCHOS_ENV=production`, `MATCHOS_PROXY_MODE=azure-container-apps`, exact allowed hosts/origins and both container metadata values are required. Do not enable this proxy adapter on a different or directly exposed server. The adapter validates managed forwarded protocol/client-address values; origin and ownership checks stay enforced.

The production CSP allows `media-src 'self' blob:` so fetched Azure narration clips can play. Scripts and ordinary connection targets remain same-origin. Production API explorer routes return 404. Cookies are Secure, HttpOnly and SameSite=Strict. A user can read public synthetic match data but cannot advance or narrate another session's replay.

## Current public verification

The [27 October result](judging-access-oct27.json) passed built frontend/assets, API health, production security headers, hidden API docs, a fresh protected cookie, two-session ownership isolation, a bilingual recap with `recap_mode: azure`, and cleanup of the checker's own temporary matchday. It is a point-in-time check from the development computer, not an uptime monitor or a full AI-quality evaluation.

To repeat, from an installed repository environment:

```cmd
.venv\Scripts\python.exe scripts/check_judging_access.py https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io --recap
```

`--recap` may consume bounded model capacity. `--require-ai` additionally fails when that request falls back; ordinary deterministic fallback is supported behavior. This checker does not read or print resource keys. Check a fresh/incognito browser and a phone on a separate network as well; desktop checks do not establish every mobile/audio behavior.

## Operating limits and remaining delivery

Share the public root or test-hub link, not a `?day=...` link copied from a particular browser. The frontend can recover an inaccessible shared replay by creating a fresh owned matchday. Ownership is not relaxed.

Storage, sessions, caches and provider counters are process-local. A cold start/restart loses games and resets those counters. The AI/Speech application budgets limit process usage, not lifetime dollars or subscription charges. A shared store and shared atomic quotas would be needed before adding replicas/workers. Do not increase capacity automatically for judging.

The hosted app must remain accessible for the required judging period; see the [submission checklist](hackathon-submission.md). Uploading the local video and completing the portal entry remain separate tasks. Broader hands-on testing and a full twelve-version AI/listening matrix remain uncompleted quality evidence.
