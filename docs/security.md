# Security setup and operating limits

Implemented in the original repository on 2026-10-08. These safeguards protect the bounded hackathon demo. They do not replace verification of the eventual hosting environment, Azure permissions/billing, or GitHub account settings.

## Local development

Keep API credentials in the backend terminal environment or a private ignored environment file. Never put them in `VITE_*`, browser code, screenshots, handoff documents, or GitHub. `.env.example` is a template; the application does not automatically load `.env` files.

Ordinary browser replay and the default seed-7 CLI replay need no shared secret. They create an anonymous cookie session and advance server-generated events. Reads of synthetic matches are public, so a viewer may open a CLI match using `?match=<id>`. Anyone with a match link can view its synthetic events; they cannot advance it without its owner's session.

Use a fresh match ID for a new CLI session, for example `--match-id demo-20261008-a`. A different browser/session cannot take over an existing replay. An expired/restarted session requires a fresh replay. The current browser client renews an expired anonymous session once and creates a new owned matchday for a specifically identified shared-session link failure; it does not take over the original replay. The browser chooses a unique ID when opened without a match query.

For trusted custom event feeds/seeds only, generate a random token of at least 32 characters and set `MATCHOS_INGEST_TOKEN` privately in both the backend and simulator terminal environments. Leave it empty otherwise. The browser never receives this token. Trusted feeds still have schema/order/storage checks and cannot modify browser-owned replay IDs.

Install reproducibly:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip==26.2.1
.venv\Scripts\python.exe -m pip install -c backend/constraints.txt -e "./backend[dev]"
npm.cmd --prefix frontend ci
```

## Enforced demo limits

| Resource                             | Limit                                                                        |
| ------------------------------------ | ---------------------------------------------------------------------------- |
| Request body                         | 8 KiB, including bodies without Content-Length                               |
| Active cookie sessions               | 128                                                                          |
| Session and match lifetime           | Fixed four hours, not extended by reads                                      |
| Active matches                       | 64 total; eight per owner                                                    |
| Events per match                     | 2,500                                                                        |
| General requests                     | 2,400 per direct client IP/minute; 10,000 globally/minute                    |
| Session/replay start requests        | 30 per direct client IP/minute combined                                      |
| Catch Me Up requests                 | 20 per direct client IP/minute                                               |
| Rate-counter entries                 | 1,024 maximum; fail closed at capacity                                       |
| Cached catch-up responses            | 32, keyed by match/revision/cursor/audience/AI mode                          |
| Catch-up computation                 | One at a time; busy requests fail quickly with 429                           |
| Azure call budget                    | `MATCHOS_AI_CALL_BUDGET`, default 100 provider requests per process lifetime |
| Azure call reservation               | Two requests reserved per selection attempt, including failures              |
| Azure selection concurrency          | Two maximum, including direct adapter callers                                |
| Evidence payload / provider response | 32 KiB / 64 KiB; oversized responses discarded                               |
| Model output                         | Selector: 512 completion tokens; writer/reviewer: 1,400 per request          |
| Provider timeout                     | Eight seconds per HTTP operation; redirects disabled                         |

Response sizes and computation are also bounded by the event cap, bounded event fields, and fixed candidate limit. The provider response check discards oversized responses after receipt; it is not a streaming transport byte cap. Requests to missing matches return an empty public view; arbitrary catch-up cache keys cannot grow beyond the cache limit.

Use **one API worker**. Storage, sessions, quotas, and caches are process-local and reset on restart. A shared store and atomic shared quotas are required before using multiple workers/instances. Restarting resets the AI budget; do not rely on it as a permanent account billing cap. Set a budget appropriate to your student credit, monitor Azure consumption, and keep AI off when it is not needed.

## Production configuration

1. Build the frontend with `npm.cmd --prefix frontend run build`.
2. Set `MATCHOS_ENV=production`, `MATCHOS_ALLOWED_HOSTS` to the exact public hostname(s), and `MATCHOS_ALLOWED_ORIGINS` to the exact HTTPS origin(s). Values are comma-separated; no wildcard matching is used. Remove local/test origins and hosts.
3. Run the API without `--reload`, with one worker. Bind it behind an HTTPS reverse proxy. Restrict direct access to the backend port and trust forwarded scheme/IP headers only from that proxy. Uvicorn's `--forwarded-allow-ips` must contain only the actual trusted proxy address(es), never an unrestricted wildcard.
4. Production mode serves `frontend/dist` and the API from the same origin, requires HTTPS, uses Secure/HttpOnly/SameSite=Strict cookies, disables API documentation routes, and sets CSP, HSTS, frame/content-type/referrer/permissions headers. Inline styles remain allowed for dynamic kit colors; scripts are restricted to the same origin.
5. Verify real HTTPS responses/cookies, proxy client-address handling, unauthorized writes, cross-session ownership, quota rejection, and Azure fallback before advertising the public URL. Vite dev/preview and Uvicorn reload are local development tools.

The public Container Apps deployment is documented in [judging deployment](judging-deployment.md), with a [dated access check](judging-access-oct27.json). Application controls cannot verify Azure RBAC, leaked keys outside this repository, DNS/TLS configuration, or repository settings. No user accounts or private fan data are stored in the current demo.

### Container Apps HTTP ingress

The prepared container can use the explicit `azure-container-apps` proxy mode described in [judging deployment](judging-deployment.md). This mode requires Azure environment metadata and managed HTTP ingress with no directly reachable/additional TCP listener. It accepts the platform-overwritten protocol and only the platform-provided rightmost client IP, validating both. Host/origin checks and production Secure cookies remain enforced. Other environments retain the default proxy behavior; arbitrary forwarded headers are not trusted. This mode has local tests and passed the 27 October public HTTPS/session check. That check is a point-in-time observation, not a continuous availability guarantee.

### Model provider cooldown

Selection and writing share a bounded deployment cooldown on 429 responses, honor valid wait headers, and return factual fallback without automatic retries. Throttled results do not permanently occupy a snapshot cache. This is process-local backoff, not a quota increase or a billing cap. See [capacity verification](recap-capacity-oct24.md).

## Collaboration rules

- Both coding assistants should work from the original repository and preserve these security tests.
- New endpoints must use the same trust boundary and bounded storage/request/provider rules.
- Never solve browser access by embedding the ingestion token or Azure key in frontend configuration.
- Dependency updates must refresh `backend/constraints.txt`, run tests, and pass advisory checks. CI performs npm and Python audits plus a heuristic secret scan; weekly runs check newly published advisories.
- The secret scan checks current files, built assets, and reachable local Git history without printing possible credential values. It cannot recognize every secret format. Enable GitHub secret scanning/push protection where available and rotate any credential exposed elsewhere.

The initial findings remain in [the dated audit](security-and-code-review.md). Its pre-fix verdict is historical; this document describes the implemented baseline.

## Historical baseline verification

The counts and local checks below describe the original security baseline. For current release checks, see [27 October verification](release-verification-oct27.md).

The baseline passed 63 backend tests and 20 frontend tests, formatting, a production build, dependency consistency, and the current-files/bundle/Git-history secret-pattern check. Both complete full-match scenarios were advanced through the owned replay API. A real localhost HTTP simulator smoke test passed without a shared ingestion token. An isolated production-mode smoke test verified the built frontend, HTTPS controls, headers, cookie setup, hidden docs and replay advancement. Azure calls were mocked or disabled throughout these security checks.

The environment's pip installer was updated from 25.0.1 to 26.2.1; the follow-up OSV query returned no advisories for that installed version. No public deployment or GitHub settings changes were performed. Restart the local API/frontend and reload the webpage to use this baseline.
