# Unused code and old data cleanup — 23 October 2026

Scope: the active `matchos` checkout. Synced `sources/`, sibling checkouts, current roster references, dependencies and user history were not removed.

## Removed from runtime

- Nine frontend source modules unreachable from the app's entry point: the old CatchUpPanel, MatchStoryBriefing, SimulatorGuide, ClubFollowCard, BroadcastOverlay, ListenRecap alias and their retired broadcast/club-preference/translation helpers.
- Two unused recap-invitation helpers and the unused club lookup/roster exports associated with those screens.
- The frontend's import of the complete player-reference JSON. Current player identities still arrive with recorded events; the backend retains its reference roster data and roster API.
- 137 CSS selectors tied to retired classes absent from all remaining runtime JS/JSX. Shared vector, narrator, main-page and development-panel styles remain.
- Fake fallback club names `Home FC` / `Away FC`; missing names use neutral `Home` / `Away` labels instead.

The old anonymous ten-minute scenarios were moved from production `backend/app/simulation.py` into `backend/tests/legacy_scenarios.py`. Their exact expected event IDs and math remain covered by the existing regression checks. Production imports none of those constants and now defaults to the reference-identity United–City feed. Both direct generation and public replay routes reject retired Hull/short scenario IDs.

Unit tests deliberately retain anonymous synthetic inputs. They are test data, not published squad identities or selectable matches. No claim is made that roster metadata was newly verified against an official live source during this cleanup.

## Tests and review material

Exclusive tests for deleted experimental UI features were removed. Mixed test files were split/trimmed so current pitch geometry, recorded vectors, event evidence and real shirt-number checks remain. The resulting 58 frontend checks replace the previous 76; 18 checks for retired behavior were removed. No backend analytics checks were dropped; a new default-feed/retired-generator check brings the backend total to 304.

Historical narrative evaluations and screenshots remain review evidence. They are not imported by the app and were not treated as runtime memory. Old club-picker/broadcast design documents are labeled as historical. The Gemini handoff and ZIP were refreshed to describe the cleaned code and include its current tests.

## Verification

- 304 backend checks passed; the existing Starlette/httpx deprecation warning remains.
- 58 frontend checks passed; production build passed.
- A fresh backend import did not load the test-only legacy generator; default replay events contain reference team/player identities.
- A static import walk found no remaining unreachable JS/JSX/CSS source files under `frontend/src`.
- A browser smoke check showed the branded page, current United–City names and current replay controls after CSS cleanup. It was not a real fan study or a new live Azure prose evaluation.

Vite's production output changed from approximately **321.55 kB JavaScript + 58.77 kB CSS** to **308.95 kB JavaScript + 46.12 kB CSS**, about **25.25 kB less shipped code before compression**. Combined gzip size fell from approximately 111.01 kB to 105.11 kB. These are build sizes, not measured browser/server RAM savings; no runtime memory benchmark was performed.

The detailed removal list and metrics are in `code-cleanup-audit.json`.
