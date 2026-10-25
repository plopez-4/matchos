# Gemini handoff: simplify MatchOS voice options

## Task

Make a small voice-settings cleanup. Keep only **Automatic (Azure when connected)** and **Warm storyteller** in both the main fan screen and the development view. Remove the visible **Device voice (basic)** and **Matchday narrator** choices. Default both views to Automatic. Keep English and Spanish labels and playback working.

Project directory (Windows):

`C:\Users\lopez\.codex\.chatgpt-projects\g-p-6abc4d11ef2c819191fa6bba4f2af3de\matchos`

Do not edit the parent project's `sources/` directory; it is read-only reference material. Read applicable AGENTS.md instructions before editing. Preserve unrelated local changes.

## Files to inspect and edit

All paths below are relative to the project directory above.

- `frontend/src/components/NarratorControls.jsx`: owns both dropdowns. Compact mode starts at `auto`; full mode currently starts at `matchday`. The shared `choice` dropdown and the separately rendered full dropdown both need cleanup. Consider reusing one dropdown. Review error/status copy that tells users to choose the removed device option.
- `frontend/src/utils/narratorVoice.js`: resolves the selection. **Automatic currently maps to `matchday` when Azure is available and `device` otherwise.** Preserve that internal behavior unless there is a concrete reason to change it. Removing a visible choice does not mean deleting its internal implementation.
- `frontend/test/narrator-voice.test.js`: verifies automatic resolution and explicit profiles. Update relevant expectations for any actual behavior changes.
- `frontend/src/api.js`: narration and preview requests send `voice_profile`; inspect for compatibility, avoid unnecessary edits.
- `backend/app/narration.py`: Azure profiles. Warm uses Ryan (English) / Dalia (Spanish); automatic currently relies on the internal matchday profile, Davis / Jorge. **Do not delete matchday while Automatic depends on it.**
- `backend/app/main.py`: narration request schemas currently accept `warm` and `matchday`. Keep compatible with the resolver; do not send `auto` directly to an API that does not accept it.
- `backend/app/narration_text.py`: existing name, team, and time pronunciation handling. Preserve it.
- `frontend/src/utils/speechRecap.js`, `frontend/src/utils/audioPlayback.js`: existing device fallback and playback lifecycle. Preserve stop/cancel and resource cleanup.
- `backend/tests/test_narration.py`, `backend/tests/test_narration_text.py`, `frontend/test/speech-recap.test.js`: relevant regression coverage.
- `docs/azure-narration.md`: update voice-choice instructions if needed.

## Scope and checks

1. Inspect current code and git status. This handoff describes the inspected state; recheck before editing.
2. Make the two-choice cleanup in both layouts, including English/Spanish copy. Keep Automatic's internal Azure/device fallback and Warm's existing Azure profiles.
3. Run `npm test` and `npm run build` from `frontend`. If backend code changes, run the relevant narration tests using the project's `.venv\Scripts\python.exe` from the project root: `-m pytest backend/tests/test_narration.py backend/tests/test_narration_text.py`.
4. Check both layouts and both languages. With Azure connected, audition Automatic and Warm, including consecutive team names, Harvey Barnes, Ismaila Sarr, and match times. Verify stop, replay, and language switching. Check Automatic's unavailable-Azure fallback/status too. If you cannot actually listen, report that limitation rather than claiming pronunciation is verified.
5. Return a concise Markdown report: files changed, checks run and results, actual listening checks, and any remaining problem.

Do not change recap generation, synthetic matches, Radar, analytics, or the evidence graph for this task. Do not deploy, increase Azure limits, create resources, or change spending settings. Do not print or save keys. Keep live audio checks small; use existing Azure configuration if available. No paid recap-generation batch is needed.

## Release context after this cleanup

The latest completed release was PR #18, merged at `fd0bac696f41eab533cac1d9edf3b671c0abd5bd`; the working tree was clean before this handoff was added. The recap writer version was `fan-narrative-v25-route-and-clock-wording`. That candidate has not completed a fresh full live nine-match acceptance run. See `docs/publish-readiness.md` and `docs/recap-v23-nine-match-review-oct24.md` for evidence and remaining gates.

Later work remains: final AI recap acceptance, five real fan tests, actual mobile/audio walkthrough, and a public judging link. Hosting is on hold pending the user's spending decision. Focus this task on voice cleanup only.
