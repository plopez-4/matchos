# Shared demo migration — 22 October 2026

The owner selected the original stadium/competition-branded page as the main user view. `/` now opens it; `/?view=development` opens the focused Matchday testing view. The older `?view=single` main-page URL and `?view=matchday` development URL remain compatible. This supersedes the earlier decision to make the focused view the public default.

Both views use the same three fixture definitions: United–City, Palace–Newcastle, Brighton–Fulham. A shared JSON manifest supplies fixture IDs and club names; both feeds come from the current Matchday generator and bundled roster references. The dashboard uses an explicit reproducible seed, while development matchdays vary participation by their match ID. These are fictional actions with reference identities, not imported real match events or official lineups.

The separate full-match generator containing fictional names has been replaced with a thin adapter. The Hull JSONL export has been removed and all current exports regenerated. Public replay routes reject the retired Hull and short placeholder scenarios. Small legacy fixtures remain internal analytics regression inputs so existing rule checks are preserved; old evaluation reports and reference club lists are retained as records, not playable demo feeds.

Development playback now identifies a held snapshot and offers one prominent Continue match action. AI prompt v10 asks each sentence to add distinct information without generic praise or repeated contribution explanations; it still authors the whole paragraph and retains existing validation/revision/fallback behavior. This prompt change has not yet had a live Azure prose evaluation in this session.

Main and development branding/navigation are explicit. No public deployment or real fan study has been performed.

## Code/data cleanup — 23 October 2026

The old unnamed short scenarios are now isolated in `backend/tests/legacy_scenarios.py`. Production `backend/app/simulation.py` generates only the current named fixtures by default and rejects retired IDs. They are retained as test inputs to protect deterministic analytics; they are not loaded into the running app. Unreachable club-picker, broadcast-overlay, old recap/translation and simulator-guide modules have been removed, along with their exclusive CSS and retired-feature tests. The current roster stays on the backend; the browser no longer imports its full player database. See `docs/code-cleanup.md` for the scope and verification.
