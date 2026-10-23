# Spanish Palace–Newcastle pronunciation reproduction

The owner reported mispronunciation of **Harvey Barnes**, **Ismaila Sarr**, and consecutive club names in the 62:30 Crystal Palace–Newcastle recap.

Changes:

- Spanish-only candidates `Járvi Barns` and `Ismaíla Sar`, including accented `Ismaïla Sarr` and supported short forms. The displayed names remain unchanged.
- Whole-name hints for Crystal Palace and Newcastle United, plus Palace/Newcastle shortened forms.
- One 120 ms SSML break after the first club when two known club names are connected with Spanish `y` or `e`. The original conjunction, score and text remain intact. This applies to all known club-name pairs and introduces no pause between player-name pairs.
- English speech, match facts, timestamps, recap wording, voice profiles and client playback logic are unchanged.

The player hints are pronunciation candidates in response to a reported failure. Club profile sources verify name spelling/identity, not the sound of these aliases. Listening acceptance remains pending.

## Live reproduction

An independent owned replay of the existing `palace-newcastle-90` fixture was advanced sequentially through all 383 recorded events up to **62:30**. Its two goal stories and 60:10 recovery-to-shot story reconstruct the owner's exact pasted Spanish recap. The protected narration endpoint returned MP3 audio in both configured Spanish voices, with the same evidence-bound snapshot and selected story IDs. No arbitrary-text API was introduced, and no provider key was read.

- [Matchday/Jorge audio](spanish-palace-voice-matchday.mp3)
- [Warm/Dalia audio](spanish-palace-voice-warm.mp3)
- [Recap text and clip metadata](spanish-palace-voice-fix.json)

Successful synthesis verifies that Azure accepts the markup. It does not prove the reported sound is fixed; compare the actual clips. The existing roster audit refreshes only the four clips containing Barnes or Sarr. All unchanged English/Spanish recordings are retained.
