# Roster expansion and simulator participation — 22 October 2026

The shared reference catalogue now contains the complete Manchester United (30 players) and Manchester City (26 players) entries from the Premier League squad-number article published 22 September 2026, rechecked 22 October. Other clubs remain curated subsets. This is a dated published list, including listed young players, not every academy player, a live transfer database or a confirmed real match lineup. Names, club assignments and shirt numbers use that source; position labels remain authored demo roles.

The Manchester synthetic replay uses an authored XI and five named bench players per club. Pass routes vary reproducibly by replay ID; all eleven starters participate, and up to five substitutions introduce new actors with stable IDs. An outgoing player cannot subsequently send or receive a pass. Goalkeepers can distribute but are excluded from generated shots. Authored goal/shot timings and analytical thresholds remain unchanged.

The backend and frontend read the same JSON catalogue. Read-only `/api/rosters/manchester-united` and `/api/rosters/manchester-city` expose the reference, dates, scope, authored lineup and bench. A local structured catalogue is sufficient for this demo; no external database or live feed is claimed. All match actions remain synthetic.

Regression checks cover player metadata, full reference counts, legal active elevens, bench eligibility, actor identity stability, pass continuity, varied routes across replay IDs and unchanged goal timing. Existing fixtures must be restarted to receive the new actors; already-recorded names are never rewritten.

Source: https://www.premierleague.com/en/news/4725682/all-20-premier-league-clubs-squad-numbers-for-202627-season

---

The following records the earlier subset review and is retained as historical context.

# Roster integration review — corrected

Reviewed 11 October 2026. The original “verified complete squads” claim is **not approved**. Passing software tests cannot establish real transfers or shirt numbers.

## Findings

- The original JSON had 113 rows across 20 clubs, with no sources or verification date. Wissa and Kerkez appeared at two clubs.
- Frontend rosters disagreed with the JSON. The simulator used a third hardcoded dictionary rather than loading the JSON.
- Synthetic actor slots `2`, `7`, `9`, `10` are not real shirt numbers. The supplied Enzo number was 5, but the dated source gives 17. Wissa's finishing slot is 10, but his shirt number is 9.
- Several club assignments conflict with the [official squad-number announcement](https://www.premierleague.com/en/news/4725682/all-20-premier-league-clubs-squad-numbers-for-202627-season), published 22 September 2026. This snapshot places Eze at Arsenal, Garnacho at Villa and Guimaraes at Arsenal. Older transfer news does not establish a current-season registration.

## Corrected scope

The table now contains **90 reference players across 20 clubs**, a curated subset, not complete squads. There were 27 club/number corrections among retained original entries, 26 unconfirmed original rows were excluded, duplicate identities were deduplicated, and five small additions filled demo chains or an otherwise empty club. Exclusion means not confirmed in this source; it does not prove a player's current whereabouts.

`backend/app/data/players_2026.json` is the shared source for backend and frontend. It records the publication/check dates, source URL and checksum, and fields verified: **name, club and shirt number at that snapshot**. Positions are authored demo roles, not verified by a shirt-number article. No player statistics or live feeds are imported.

`backend/app/rosters.py` maps authored slots to reference identities through `demo_slots`. Synthetic actor IDs and event IDs remain stable. New demo chains use members of the corresponding reference club; all passes, goals, timings and scores remain synthetic. Unknown references fall back to fictional labels.

## UI

- **Your club:** a collapsed “Meet the demo squad” drawer shows names, actual shirt numbers, demo roles and a source link. It explicitly disclaims complete squads and confirmed lineups.
- **Evidence:** displays player/recipient names and actual shirt numbers recorded in the event, separately from actor IDs. Reference events are labeled synthetic actions. Existing events are not rewritten from current roster metadata, and recipients are not inferred assists.
- **Standalone full-match scenarios:** retain their fictional players. These changes apply to Match Radar's authored fixtures.

Restart the backend and choose **New matchday** for the revised actors. Existing in-memory matches retain their recorded names.

## Verification and limits

Run `python scripts/check_roster_reference.py path/to/saved-source.html` to verify all 90 tuples against a local copy with the recorded checksum. The script makes no network calls; the source article is not redistributed. Tests cover unique IDs/numbers, resolvable slots, backend/frontend consistency, pass recipients and public-schema compatibility.

Verification completed: **104 backend tests and 37 frontend tests passed**, production build and Prettier passed, and the offline checker matched all 90 identities. Browser review confirmed the collapsed squad drawer, City's corrected #17 midfielder and evidence showing Wissa #9 and Mateta #14 on explicitly synthetic actions. See the [reference roster preview](reference-roster-preview.png). The existing Starlette test-client deprecation warning remains.

Public readability is not a public-domain declaration or permission to use logos or redistribute protected material. This review does not establish hackathon authorization for real identity metadata; confirm submission eligibility with the organizers. No official endorsement, live-current coverage or complete-squad claim is made.
