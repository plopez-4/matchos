# Judging deployment preparation

Status: container packaging and checks prepared; **no public deployment or judging URL is confirmed**. The local website still depends on your computer.

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

Azure account access, chosen resource group/region, credit-use approval, image registry/revision and assigned hostname remain to be supplied/confirmed. Once available, deploy the tested image, attach secrets privately and save the real public check result. The public video and hackathon portal entry are separate.
