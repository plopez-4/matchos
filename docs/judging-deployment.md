# Judging deployment preparation

Status: container packaging and checks prepared; **no public deployment or judging URL is confirmed**. The local website still depends on your computer. Deployment is on hold while the user reviews credit protection and the [publication quality gates](publish-readiness.md).

## Prepared Azure request — 24 October

The [explicit ARM template](../deploy/azure-judging.json) creates only `matchos-judging-env` and `matchos-judging` on Consumption, with 0.25 vCPU, 0.5 GiB, minimum zero and maximum one replica, a single active revision, TCP probes and HTTPS ingress on port 8000. Host/origin values derive from the environment's assigned default domain. It does not create a registry, database, log workspace, private endpoint or dedicated workload profile. Streamed logs remain available; historical application logs are not stored. AI and Speech start off until their runtime secrets are attached privately.

The existing student's allowed-region policy lists Canada Central, Denmark East, North Central US, Belgium Central and Mexico Central. An earlier East US 2 request failed validation without creating resources. The template uses North Central US; the existing resource group's East US 2 location is separate from the app's location.

The [successful image publication](https://github.com/plopez-4/matchos/actions/runs/40117224844) produced the Linux AMD64 image at `ghcr.io/plopez-4/matchos-judging@sha256:ea33c7430eb75db64f257da73d4ed53e7ada5425a29ddf84dc7e3493bcc2f73f`. Its runtime config and all layers were anonymously readable. Earlier publication attempts left only provenance records and failed; the manual workflow now publishes a single-platform runtime manifest. No Azure registry credentials are required. Azure deployment and live startup remain separate verification steps.

Microsoft's public North Central US retail meters checked on 24 October were $0.000024 per active vCPU-second and $0.000003 per GiB-second. At this size, continuous active compute for 24 hours is approximately **$0.648 before free grants**, not a bill cap. Requests, outbound traffic, AI and Speech are separate. The monthly subscription grant includes 180,000 vCPU-seconds, 360,000 GiB-seconds and two million requests; remaining grant usage has not been verified. Scale-to-zero can reduce compute but loses in-memory replay sessions and can introduce cold starts. [Billing and grants](https://learn.microsoft.com/en-us/azure/container-apps/billing), [public retail price API](https://prices.azure.com/api/retail/prices), [pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/).

The final Azure review requires acceptance of deployment terms and usage billing. Resource creation remains pending the user's confirmation. Do not claim the public URL or AI/Speech connectivity is verified yet.

## Prepared image

The root Dockerfile builds the locked React frontend, installs constrained Python dependencies and serves both from one FastAPI process on port 8000. It runs as a non-root user, uses one worker, excludes private environments/logs and has Azure AI/Speech off by default. Runtime secrets must be configured privately in Azure, not in the Docker build or repository.

GitHub CI builds and starts this image. Its ingress headers are simulated locally; that test is not proof of a real Azure deployment. A future container revision should be pinned to the tested image digest.

## Azure Container Apps settings to review before creating resources

- Use the existing student subscription and an agreed resource group/region. Resource creation can consume credits; no hosting cost or quota increase has been approved or performed by these files.
- Deploy one active revision and **maximum one replica**, with one Python worker. Set a minimum of one replica during judging if avoiding cold starts/replay resets is important; this can increase credit use. Scaling to zero or restarting loses in-memory sessions and games.
- Enable external **HTTP ingress**, target port 8000, HTTPS required. Do not expose additional TCP ports, the container listener directly, or a development server.
- Use TCP readiness/liveness probes on port 8000. Direct HTTP probes lack the managed HTTPS headers and intentionally fail the production HTTPS guard.
- Set `MATCHOS_ENV=production`, `MATCHOS_PROXY_MODE=azure-container-apps`, `MATCHOS_ALLOWED_HOSTS` to the exact assigned hostname, and `MATCHOS_ALLOWED_ORIGINS` to its `https://` origin. The two `CONTAINER_APP_*` metadata values are supplied by the platform.
- Initially verify the site with AI off, then attach existing Azure model and Speech configuration through runtime secrets/secret references. Set an appropriate application AI-call budget and monitor resource capacity. Restart resets that process-local budget; it is not an account billing cap.
- Keep judging access public and free to testers. Do not require judges to supply Azure keys. Existing anonymous replay ownership cookies still protect advancement and narration.

The special proxy mode is only for Azure Container Apps HTTP ingress. Microsoft documents that this ingress overwrites `X-Forwarded-Proto` and provides the rightmost `X-Forwarded-For` address. The adapter uses only those values, validates them and keeps host/origin checks. Do not enable it on any directly reachable listener or another hosting platform. Uvicorn does not trust arbitrary forwarded chains. [Microsoft ingress documentation](https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview).

## Verify a real public URL

From another computer/network, using the repository's Python environment:

```powershell
.\.venv\Scripts\python.exe scripts/check_judging_access.py https://YOUR-HOSTNAME --recap --output docs/judging-access-result.json
```

This checks the built fan app and JavaScript, HTTPS/certificate verification, API health, production headers, hidden API explorer, fresh Secure/HttpOnly cookies, cross-session replay isolation, both recap languages and release of its own temporary matchday. It records the actual AI/fallback mode. `--require-ai` additionally fails if that request returns fallback; it can consume model capacity. No resource keys are read or printed.

Then use a fresh/incognito browser and a phone on mobile data. Start replay, request Catch Me Up, open its named action, inspect evidence and audition English/Spanish Listen. Verify recovery after an Azure cooldown, no exposed credentials and that the link remains reachable without your laptop or local servers. Do not mark judging access complete based only on CI or local tests.

## Outstanding deployment inputs

Account access, the existing student resource group, North Central US and the published image digest are confirmed. Remaining: complete the private billing verification, obtain explicit acceptance of Azure deployment terms/usage billing, create the resources, attach runtime model/Speech secrets privately, and save public access results for the assigned hostname. The public video and hackathon portal entry are separate. Plan availability through the end of judging, not only the submission deadline; see the [dated readiness review](publish-readiness.md).
