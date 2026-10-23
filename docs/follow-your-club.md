# Follow your club

> Historical design record: this experimental frontend feature was removed from the active code on 23 October 2026. It is not available in the current main or development view.

Match Radar now pairs a familiar fixture with discovery: choose a club, see its current synthetic story in **Your club**, then inspect an evidence-backed recommendation in **Elsewhere worth watching**. **Catch me up on my club** opens the existing catch-up experience with that match's evidence and timeline. Selecting a club does not reset replay, change its clock, automatically switch matches or consume an AI call.

All 20 clubs have lightweight name, ID, three-letter code and representative home-kit color metadata in `frontend/src/utils/teams.js`. The roster follows the [official 2026–27 opening-round announcement](https://www.premierleague.com/en/news/4675508/premier-league-fixture-schedulereleased-for-season-202627), checked 11 October 2026. Colors are presentation approximations rather than an official palette or a guarantee of a particular fixture's kit. No club crests, player database, real event feeds or extra fixtures are added.

The choice is validated against the club list and stored only in this browser's local storage under a versioned key. Clear it with **Just here for the football**. If storage is blocked, the current visit still works. Resetting a matchday preserves the club preference; reload restores it when storage is available.

## Club picker

The chosen club also has a collapsed **Meet the demo squad** drawer with the shared, dated reference subset and actual shirt numbers. It is not a complete squad or a confirmed lineup. See the [roster review and provenance](roster-integration-review.md); match actions remain synthetic.

**Who do you support?** opens a 20-club tile grid with original SVG shirt illustrations, representative colors, names and three-letter codes. No crests, sponsors or official kit artwork are included. Six clubs carry **In this demo** badges for the existing synthetic fixtures. Selected tiles expose `aria-pressed` and show an outline plus a checkmark. Native buttons support keyboard selection and visible focus; reduced-motion styling removes hover movement.

After selection the grid collapses to **Following [club]** with **Change club**. The neutral choice collapses it to **Here for the football** and clears the saved club; on a subsequent reload with no club preference, the picker opens again. On phones the expanded grid uses two columns. Changing the preference still does not start or reset replay or switch the currently inspected match.

See the [club picker preview](club-picker-preview.png). Browser review verified club selection, collapsed/expanded states, neutral selection by keyboard, and a 390px viewport with two columns and no page overflow.

The three authored fixtures remain Manchester United–Manchester City, Crystal Palace–Newcastle United and Brighton–Fulham. Choosing another club displays **no fixture in this three-match synthetic demo**, while retaining discovery. This does not mean that club has no real fixture today.

Discovery excludes the chosen club's fixture and applies the existing backend eligibility flag, rating and tie breaks (most recent shot, then match ID) to the remaining matches. It never boosts a rating because of club preference or promotes an ineligible quiet game. No eligible other fixture means a quiet state; full-time matchdays never recommend watching finished action. Existing backend alerts are shown only when their target matches the displayed discovery recommendation; this change does not introduce personalized cloud notifications or OS push.

## Manual review

1. Open **Matchday & Radar**, choose Manchester United and start a synthetic matchday.
2. Your club shows the derby even when it is quiet; at approximately 18:00 its early burst is excluded from Elsewhere. Select Arsenal to confirm the honest unavailable-fixture state and global discovery.
3. Choose Manchester United again and advance to 75:30. Elsewhere shows Palace–Newcastle's repeated equalizers with their recorded evidence.
4. Open Catch Me Up for your club, then another match; summaries and event lists must belong to the selected match. Reload to confirm the preference remains; start a new matchday to confirm the club stays selected.
5. Select Palace/Newcastle while the derby is quiet: Elsewhere should stay silent rather than recommending the chosen fixture or Brighton's quiet draw. At full time, all scores remain accessible but discovery stays quiet.

Three streams demonstrate concurrent match handling, not verified production scalability or measured engagement uplift. Those require separate load tests and fan trials.
