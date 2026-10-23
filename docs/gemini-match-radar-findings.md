# Gemini Review: Matchday and Match Radar Baseline Findings

**Repository:** `C:\Users\lopez\.codex\.chatgpt-projects\g-p-6abc4d11ef2c819191fa6bba4f2af3de\matchos`  
**Date:** 2026-10-11  
**Review Type:** Automated First Review (Findings & Minimal Fixes Only)  
**Checks Executed:**

- `.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider`: **73 passed, 1 warning in 10.58s**
- `npm.cmd --prefix frontend test`: **23 passed, 0 failed**
- `npm.cmd --prefix frontend run format:check`: **Clean (All matched files use Prettier style)**
- `npm.cmd --prefix frontend run build`: **Built successfully (dist/index.html, CSS 36.77 kB, JS 278.90 kB)**
- `.venv\Scripts\python.exe -B scripts/check_secrets.py`: **Clean (No matching secret patterns)**

---

## 1. Challenge Question Verdicts

| #   | Challenge Item                                   | Verdict              | Evidence / Verification                                                                                                                                                                                                             |
| --- | ------------------------------------------------ | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Observed events only (no future leak)?**       | **PASS**             | `matchday_view` and `pulse` query only ingested events stored in `store[mid]` where `match_second <= now`. Authored role/profile metadata does not determine ranking.                                                               |
| 2   | **Window boundaries & rule score semantics?**    | **PASS (with note)** | Shot windows evaluate `(now - 300, now]` and `(now - 600, now - 300]`. Score is displayed as a 0–100 signal index, not a probability or forecast. (_See Finding 1 regarding clipping metadata_).                                    |
| 3   | **Quiet draw / one-sided barrage restraint?**    | **PASS**             | Rating $\ge 65$ and `two_way` ($\min(\text{shots}) \ge 1$ and $\ge 4$ recent shots) are strictly enforced. Quiet draws and unilateral shot barrages are excluded from recommendations.                                              |
| 4   | **Transition-based notifications & cooldown?**   | **PASS**             | Notifications trigger only on leader change (`leader_id != state["previous_leader"]`) and enforce a 600-second (10-minute) per-match cooldown. Tick retries preserve identical notification IDs.                                    |
| 5   | **Ownership, clock sync & capacity bounds?**     | **PASS**             | Advancing single matchday members via `/advance` is blocked with HTTP 409. Skipping ticks is blocked with HTTP 409. Releasing another session's matchday is blocked with HTTP 403. Quotas enforce max 64 matches and 8 per session. |
| 6   | **Stale clock / aborted view race conditions?**  | **PASS**             | In `playMatchday`, aborted requests never invoke `onView()`. Stale Catch Me Up requests are discarded via `generation.current`.                                                                                                     |
| 7   | **Safe capacity release on reset?**              | **PASS (with note)** | `DELETE /api/matchdays/{day_id}` removes matches from `store` and calls `security.expire()`. (_See Findings 2 & 3 on partial member eviction and client-side release error handling_).                                              |
| 8   | **No overclaiming or unnecessary architecture?** | **PASS**             | Transparent in-memory baseline with deterministic functions. UI and documentation explicitly disclaim real match reconstruction, engagement uplifts, or video streaming claims.                                                     |

---

## 2. Concrete Findings & Minimal Fixes

### Finding 1: Window Metadata Mismatch on Feed Clipping at Match Start

- **Severity:** Medium (Reporting & Contract Accuracy)
- **File / Function:** `backend/app/matchday.py` → `pulse()`
- **Concrete Reproduction:**
  When `now < 300` (e.g. `now = 120` seconds):
  ```python
  # line 84:
  current = [e for e in events if max(-1, now-300) < e.match_second <= now and e.type == "shot"]
  # line 108:
  "window": {"start_exclusive": max(0, now-300), "end_inclusive": now}
  ```
  `max(-1, 120 - 300) = -1`. The list comprehension includes events where `-1 < e.match_second <= 120` (which includes `match_second == 0`).  
  However, `window["start_exclusive"]` reports `max(0, 120 - 300) = 0`.  
  The returned metadata claims that second 0 is excluded from the window (`(0, 120]`), but the event list actually included second 0 (`(-1, 120]`).
- **Minimal Suggested Fix:**
  Align the filter boundary with the window metadata clipping:
  ```python
  start_sec = max(0, now - 300)
  current = [e for e in events if (start_sec if now >= 300 else -1) < e.match_second <= now and e.type == "shot"]
  ```
  Or align `start_exclusive` to report `-1` when clipped to the start of the feed.

---

### Finding 2: Incomplete Member Cleanup if Matchday Member is Pre-Evicted

- **Severity:** Medium (Quota Leak / Capacity Deadlock)
- **File / Function:** `backend/app/main.py` → `day_members()` & `release_matchday()`
- **Concrete Reproduction:**
  In `day_members(day_id)`:
  ```python
  members = [f'{day_id}-{p["role"]}' for p in matchday.PROFILES]
  if any(mid not in security.matches or security.matches[mid].get("matchday_id") != day_id for mid in members):
      raise HTTPException(404, "Matchday expired or does not exist")
  ```
  If one member match is evicted from `store` (or fails claim), `any(mid not in security.matches ...)` evaluates to `True`.  
  When the owner subsequently issues `DELETE /api/matchdays/{day_id}` to release capacity, `day_members` raises `HTTP 404`.  
  Because `release_matchday` aborts on `day_members`, the remaining 2 member matches are **never** popped from `security.matches`. They remain locked until their 4-hour TTL expires, permanently consuming 2 of the owner's 8 allowed match quota slots.
- **Minimal Suggested Fix:**
  In `release_matchday`, clean up all matches matching `day_id` owned by the session even if one member is already missing:
  ```python
  @app.delete("/api/matchdays/{day_id}")
  def release_matchday(day_id: str, request: Request):
      with security.LOCK:
          owner = security.session(request)
          security.expire(store)
          members = [f'{day_id}-{p["role"]}' for p in matchday.PROFILES]
          present = [mid for mid in members if mid in security.matches]
          if not present:
              raise HTTPException(404, "Matchday expired or does not exist")
          if any(security.matches[mid]["owner"] != owner for mid in present):
              raise HTTPException(403, "This matchday belongs to another session")
          for mid in members:
              store.pop(mid, None)
              security.matches.pop(mid, None)
          security.expire(store)
          return {"released": True}
  ```

---

### Finding 3: Frontend `reset()` Trapped if `releaseMatchday` Encounters Network Error

- **Severity:** Medium (UI Deadlock)
- **File / Function:** `frontend/src/components/Matchday.jsx` → `reset()`
- **Concrete Reproduction:**
  Lines 145–153:
  ```javascript
  try {
    if (latest.current) await releaseMatchday(dayId);
  } catch (err) {
    if (err.status !== 403 && err.status !== 404 && err.status !== 401) {
      setError(err.message);
      setStarting(false);
      return;
    }
  }
  ```
  If the network drops or the server is unreachable (where `err.status` is `undefined` or 500/503), the condition `err.status !== 403 && err.status !== 404 && err.status !== 401` evaluates to `true`.  
  The function sets `setError(err.message)`, `setStarting(false)`, and returns early without resetting the frontend state.  
  The user is clicking **"New matchday"** to reset a broken or finished session, but because the release network call failed, the UI refuses to clear the old session and traps the user in an error state.
- **Minimal Suggested Fix:**
  Server-side matchday release on reset should be best-effort; the local UI state should always reset cleanly:
  ```javascript
  try {
    if (latest.current) await releaseMatchday(dayId);
  } catch {
    // Best-effort release: continue clearing local state so the user is never locked out
  }
  ```

---

### Finding 4: Inconsistent HTTP Status Code for Capacity Rejection

- **Severity:** Low (API Contract Consistency)
- **File / Function:** `backend/app/main.py:start_matchday` vs `backend/app/security.py:claim_match`
- **Concrete Reproduction:**
  In `security.py:claim_match`:
  - Global match pool exhausted (`len(matches) >= MAX_MATCHES`): raises **HTTP 503** ("Service Unavailable").
  - Per-session quota exhausted (`sum(meta["owner"] == owner) >= 8`): raises **HTTP 429** ("Too Many Requests").
    In `main.py:start_matchday`:
  - Both conditions are checked in one `or` expression and both return **HTTP 429**:
    ```python
    if len(security.matches)+3 > security.MAX_MATCHES or sum(m["owner"] == owner for m in security.matches.values())+3 > 8:
        raise HTTPException(429, "Not enough demo capacity for three matches")
    ```
- **Minimal Suggested Fix:**
  Separate the checks to return 503 for global server capacity and 429 for session quota:
  ```python
  if len(security.matches) + 3 > security.MAX_MATCHES:
      raise HTTPException(503, "Not enough global demo capacity for three matches")
  if sum(m["owner"] == owner for m in security.matches.values()) + 3 > 8:
      raise HTTPException(429, "Not enough session replay capacity for three matches")
  ```

---

## 3. Proposal for Repetitive Progressive-Pass Stories in "What Changed"

### Issue Summary

In a 93-minute match, `progressive_pass_windows()` evaluates 18 five-minute windows per team, producing up to 36 qualifying progressive-pass stories.  
In `select_candidates(stories, limit=8)`, remaining candidate slots fill with adjacent 5-minute progressive-pass stories. `render()` then outputs redundant, repetitive sentences:

> _"Home completed 3 progressive passes in minutes 70–75..."_  
> _"Away completed 3 progressive passes in minutes 70–75..."_  
> _"Home completed 3 progressive passes in minutes 75–80..."_  
> _"Away completed 3 progressive passes in minutes 75–80..."_

### Evidence-Preserving Solution

1. **Selection Diversity in `select_candidates`:**
   Cap progressive-pass candidates to at most **one window per team** (or the peak forward-gain window) when other story kinds (shots, high recoveries, transitions) are present.
2. **Consolidated Narrative Rendering in `render`:**
   When multiple progressive-pass window stories exist for the same team, group them by `team_id` into a single consolidated summary spanning the active minutes:
   - **Casual Fan:**  
     `"Home maintained consistent forward ball progression across 3 intervals (minutes 70–85; 9 progressive passes total)."`
   - **Tactical / Advanced Fan:**  
     `"Home completed 9 progressive passes across minutes 70–85 (3 five-minute intervals meeting rule progressive-pass-v1: >= 3 passes with forward gain >= 15.0 units)."`
   - **Evidence Preservation:**  
     Collect all underlying event IDs:
     ```python
     evidence_event_ids = sorted({eid for s in team_pass_stories for eid in s['evidence_event_ids']})
     ```
   - **Non-Negotiables Preserved:**  
     Goals remain untouched in "What happened", shot frequency and transition chains remain separate, and no ungrounded tactical causality or chance-quality assumptions are made.
