# MatchOS security and code review

Reviewed: 2026-10-08. Original repository, branch `feature/match-page-polish`, commit `cd780dc`.

## Verdict

The architecture is appropriate for a local hackathon MVP. It is not ready to expose as an unrestricted public service. Secret separation and evidence validation are useful foundations, but they do not prevent API abuse, event tampering, or excessive Azure spending.

This review inspected code and local Git history, built frontend assets, dependency advisories, and isolated API behavior. It did not inspect Azure account permissions, billing settings, GitHub secret-scanning settings, remote-only branches, deleted/unreachable Git objects, hosting infrastructure, or every possible attack. No live Azure calls were made. Application code was not changed during the review.

## What is implemented well

- Azure credentials are read on the backend from environment variables. The browser uses relative `/api` requests and does not need the Azure key.
- `.env` and `.env.*` are ignored, except the placeholder `.env.example`. The only tracked environment file is `.env.example`.
- A targeted scan of 91 current tracked/untracked nonignored files, 9 built frontend files, and 237 reachable local Git blobs found no matching provider tokens, GitHub tokens, private keys, or long API-key assignments. This is a pattern-based check, not proof that every possible secret is absent. Ignored local credential files were not printed or included in the scan.
- Pydantic rejects unexpected fields and constrains names, event types, coordinates, and match time. Ingestion checks duplicate IDs, sequence order, clock order, and referenced goal-producing shots.
- Azure output selects existing story IDs; displayed factual wording is generated from deterministic rules. Invalid selections and provider errors fall back to deterministic behavior. This reduces hallucination risk; it does not establish that an incoming event is trustworthy.
- Azure endpoints require HTTPS and an allowed Azure hostname/path. Requests have timeouts, redirects are disabled, and raw provider errors are not returned to the browser.
- React renders text without an identified raw HTML injection path in the inspected source.
- CI runs backend/frontend tests, formatting, and a production frontend build. The preceding integration verification passed 50 backend tests and 20 frontend tests. Those functional checks are not a security certification.

## Fix before public exposure

### 1. Protect event writes and replay ownership

`backend/app/main.py:49` exposes `/api/events` without authentication or authorization. An isolated request with no credentials successfully inserted an event (HTTP 201). Match IDs are identifiers, not access controls. Anyone who can reach the service can submit schema-valid fictional facts into another match.

The frontend currently drives replay by submitting individual events. For a public demo, move replay generation/ingestion behind a server-owned operation using an allowlisted scenario and bounded session. Keep arbitrary event ingestion available only to a trusted simulator/service. Do not put an administrator or shared ingestion secret into the frontend. If sessions need private state, validate ownership on every relevant endpoint; intended public match reads may remain public.

### 2. Bound Azure spending and request work

`backend/app/main.py:118` exposes Catch Me Up without authentication, rate limiting, caching, or a total AI budget. Two identical isolated requests both returned HTTP 200 and invoked the explanation function twice. The provider was mocked: this demonstrates the absence of request reuse, not an actual Azure bill.

Add bounded caching by match revision, cursor, and audience; per-session/client request limits; a global concurrency limit; and a hard application AI-call budget with deterministic fallback. Bound output tokens and candidate payload size. Azure budget alerts are useful monitoring, but application limits must enforce when calls stop. A hidden key can still be abused indirectly through this API.

### 3. Cap stored data and expensive responses

`backend/app/main.py:17` keeps every match and event in a shared in-memory dictionary with no match/event cap or expiry. Schema field limits do not limit the number of accepted events. Attackers can exhaust memory or make repeated analytics increasingly expensive. Restarting loses state; multiple workers would have separate stores.

For the demo, use a bounded single-worker store with replay expiry, maximum active matches/events, request body limits, and bounded response sizes. Add persistent storage only when product requirements require it. Avoid introducing Redis, queues, and microservices just to address the current demo scale.

### 4. Configure a production boundary

The frontend development command binds to `127.0.0.1`, and documented backend startup uses localhost. That is appropriate for local use, but the review did not verify a running listener or firewall state. Do not expose Vite's development server or Uvicorn reload mode through a public tunnel.

For public hosting, serve the built frontend through HTTPS, run the API without reload, configure accepted hosts/origins and appropriate security headers, and restrict or intentionally configure management/docs endpoints. Authentication and resource controls must remain enforced at the API; CORS alone does not prevent direct API requests. See the [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html).

## Dependency checks

- `npm audit` reported zero known vulnerabilities for the frontend dependency tree checked during this review.
- An OSV query checked 29 installed Python distributions, excluding the local project itself. Only `pip` 25.0.1 was flagged; the installed application runtime packages had no matches returned by that query.
- Update the environment's pip installer before installing more packages. The returned advisory IDs were GHSA-4xh5-x5gv-qwph, GHSA-58qw-9mgm-455v, GHSA-6vgw-5pg2-w6jp, GHSA-jp4c-xjxw-mgf9, GHSA-qwm4-qh6w-59xr, GHSA-wf93-45jw-7689, and six PYSEC records. These are package-installer findings, not evidence that ordinary webpage requests can exploit MatchOS. One upstream example concerns archive extraction: [pip issue 13550](https://github.com/pypa/pip/issues/13550).
- Python dependency ranges are broad and no resolved backend lock file is committed. Add reproducible dependency locking and scheduled advisory checks. Advisory databases cannot detect every vulnerability.

## Complexity and correctness

Keep React, FastAPI, one simulator, deterministic analytics, and optional Azure selection. This is a sensible stack for the intended product. More agents, services, or model training are not needed to secure the current app.

The larger concern is repeated work: ingestion scans stored events, analytics/stories are recalculated on polling, and the scenario catalog regenerates full feeds to count them (`backend/app/full_match.py:135`). Cache immutable scenario metadata and computed match views by revision after correctness is protected. This is a performance improvement, not a reason for a distributed architecture.

Runtime validation also needs to distinguish a schema-valid event from a football-consistent event. Full-feed recipient validation checks a team prefix, not active-roster membership. Legacy goals may omit a shot reference. Tests of generated fixtures do not make arbitrary incoming data trustworthy. Add state-aware invariants where appropriate while preserving intentional legacy compatibility.

## First security milestone

1. Separate trusted ingestion from browser replay; enforce replay session ownership where needed.
2. Add data expiry/caps, request limits, and bounded response/provider payloads.
3. Add Catch Me Up caching, concurrency limits, and an application AI-call budget with fallback.
4. Update pip, lock backend dependencies, and add secret/dependency checks to CI.
5. Test denied writes, cross-session access, expired sessions, quota exhaustion, cache reuse, and deterministic fallback. Then verify the actual production HTTPS deployment.

Completion means an unauthenticated client cannot alter another session's match; repeated requests cannot cause unlimited AI calls or storage growth; no secrets are shipped to the browser; and the deployed configuration has been checked. Until then, continue development locally rather than treating the app as production-ready.
