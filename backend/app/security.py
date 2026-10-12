"""Bounded, single-process demo security. No shared secret is sent to a browser."""
import os
import secrets
import threading
import time
from collections import OrderedDict

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse

LOCK = threading.RLock()
MAX_MATCHES = 64
MAX_EVENTS = 2500
TTL = 4 * 60 * 60
MAX_BODY = 8192
MAX_SESSIONS = 128
COOKIE = "matchos_session"
sessions = {}
matches = {}
rates = {}
catch_cache = OrderedDict()
ai_calls = 0
ai_active = 0


def production():
    return os.getenv("MATCHOS_ENV", "local") == "production"


def allowed_hosts():
    return os.getenv("MATCHOS_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")


def allowed_origins():
    return os.getenv("MATCHOS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175").split(",")


def expire(store):
    now = time.monotonic()
    for mid, meta in list(matches.items()):
        if meta["expires"] <= now or mid not in store:
            matches.pop(mid, None)
            store.pop(mid, None)
            for key in list(catch_cache):
                if key[0] == mid:
                    catch_cache.pop(key, None)
    for sid, expires in list(sessions.items()):
        if expires <= now:
            sessions.pop(sid, None)


def session(request):
    sid = request.cookies.get(COOKIE)
    if not sid or sessions.get(sid, 0) <= time.monotonic():
        raise HTTPException(401, "Replay session expired; reload the page")
    return sid


def new_session(request, response, store):
    with LOCK:
        expire(store)
        sid = request.cookies.get(COOKIE)
        if not sid or sessions.get(sid, 0) <= time.monotonic():
            if len(sessions) >= MAX_SESSIONS:
                raise HTTPException(503, "Demo session capacity reached; try later")
            sid = secrets.token_urlsafe(32)
            sessions[sid] = time.monotonic() + TTL
        response.set_cookie(COOKIE, sid, max_age=TTL, httponly=True,
                            secure=production(), samesite="strict", path="/api")
    return {"status": "ready"}


def trusted_ingestion(request):
    key = os.getenv("MATCHOS_INGEST_TOKEN", "")
    provided = request.headers.get("x-matchos-ingest-token", "")
    if len(key) < 32 or not secrets.compare_digest(key.encode(), provided.encode()):
        raise HTTPException(401, "Trusted ingestion is disabled or credentials are invalid")


def claim_match(mid, owner, store, fixture=None, scenario=None):
    expire(store)
    if mid in matches:
        if matches[mid]["owner"] != owner:
            raise HTTPException(403, "This replay belongs to another session")
        if matches[mid].get("scenario") != scenario:
            raise HTTPException(409, "Use a fresh match ID for a different scenario")
        return
    if len(matches) >= MAX_MATCHES:
        raise HTTPException(503, "Demo match capacity reached; try later")
    if sum(meta["owner"] == owner for meta in matches.values()) >= 8:
        raise HTTPException(429, "Replay limit reached for this session")
    matches[mid] = {"owner": owner, "expires": time.monotonic()+TTL,
                    "fixture": fixture, "scenario": scenario,
                    "generation": secrets.token_hex(16)}
    store[mid] = {}


def take_ai_budget():
    """Reserve at most two provider requests per briefing, even on failure."""
    global ai_calls, ai_active
    with LOCK:
        limit = int(os.getenv("MATCHOS_AI_CALL_BUDGET", "100"))
        if ai_active >= 2 or ai_calls + 2 > limit:
            return False
        ai_calls += 2
        ai_active += 1
        return True


def release_ai():
    global ai_active
    with LOCK:
        ai_active -= 1


def allow_request(key, limit):
    now = time.monotonic()
    with LOCK:
        for old in list(rates):
            if rates[old][0] + 60 <= now:
                rates.pop(old)
        if key not in rates:
            if len(rates) >= 1024:
                return False
            rates[key] = [now, 0]
        if rates[key][1] >= limit:
            return False
        rates[key][1] += 1
        return True


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request = Request(scope)
        async def respond(code, detail):
            await JSONResponse({"detail": detail}, status_code=code,
                               headers={"Cache-Control": "no-store", "Retry-After": "60"} if code == 429 else {}) (scope, receive, safe_send)
        async def safe_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([(b"x-content-type-options", b"nosniff"),
                                (b"referrer-policy", b"no-referrer"),
                                (b"x-frame-options", b"DENY"),
                                (b"cache-control", b"no-store")])
                if production():
                    headers.append((b"strict-transport-security", b"max-age=31536000"))
                    headers.append((b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"))
                    headers.append((b"permissions-policy", b"camera=(), microphone=(), geolocation=()"))
                message = dict(message, headers=headers)
            await send(message)
        if request.url.hostname not in allowed_hosts():
            return await respond(400, "Host is not allowed")
        if production() and scope.get("scheme") != "https":
            return await respond(400, "HTTPS is required")
        if production() and scope["path"] in ("/docs", "/redoc", "/openapi.json"):
            return await respond(404, "Not found")
        origin = request.headers.get("origin")
        if origin and origin not in allowed_origins():
            return await respond(403, "Origin is not allowed")
        if scope["method"] not in ("GET", "HEAD", "OPTIONS"):
            if request.headers.get("x-matchos-client") != "replay" and not request.headers.get("x-matchos-ingest-token"):
                return await respond(403, "Missing request protection header")
            if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
                return await respond(415, "JSON content type is required")
        peer = scope.get("client") or ("unknown", 0)
        if not allow_request(("global",), 10000) or not allow_request(("client", peer[0]), 2400):
            return await respond(429, "Request limit reached")
        category = "catch" if scope["path"].endswith("/catch-up") else "start" if scope["path"] in ("/api/session", "/api/replay/start", "/api/matchdays/start") else None
        if category and not allow_request((category, peer[0]), 20 if category == "catch" else 30):
            return await respond(429, "Request limit reached")
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return await respond(400, "Invalid content length")
        if length < 0 or length > MAX_BODY:
            return await respond(413, "Request body is too large")
        # Count actual chunks too: missing/forged Content-Length cannot bypass the cap.
        chunks, size = [], 0
        while True:
            chunk = await receive()
            if chunk["type"] == "http.disconnect":
                return
            size += len(chunk.get("body", b""))
            if size > MAX_BODY:
                return await respond(413, "Request body is too large")
            chunks.append(chunk)
            if not chunk.get("more_body", False):
                break
        async def bounded_receive():
            if chunks:
                return chunks.pop(0)
            return await receive()
        await self.app(scope, bounded_receive, safe_send)
