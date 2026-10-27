# Publication audit — 27 October 2026

The repository is public, uses `main` as its default/canonical branch and has an MIT application-code license. Third-party assets retain separate credits. The public app is available at [MatchOS](https://matchos-judging.victoriousgrass-e3cb5a12.northcentralus.azurecontainerapps.io/). These checks support publishing the current repository; they do not complete the hackathon entry.

## Checks performed

| Check                           | Result                                                                                                                                  |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Complete backend suite          | 597 passed                                                                                                                              |
| Complete frontend suite         | 89 passed                                                                                                                               |
| Shared Prettier formatting      | Passed                                                                                                                                  |
| Vite production build           | Passed                                                                                                                                  |
| Credential-pattern scan         | Passed for current files, built assets and reachable local Git history; heuristic, not proof that every credential format is detectable |
| npm advisory audit              | Zero reported vulnerabilities at the configured low threshold                                                                           |
| Pinned Python dependency audit  | No known vulnerabilities reported for `backend/constraints.txt`                                                                         |
| Public HTTPS and production app | Built root and JavaScript loaded; API health passed; production headers present; `/docs` hidden                                         |
| Fresh anonymous sessions        | Protected cookie established; a second session could not advance the first session's matchday                                           |
| Live bilingual recap            | English/Spanish response present; actual `recap_mode` was `azure`, with no fallback reason                                              |
| Checker cleanup                 | Its own temporary matchday released                                                                                                     |

Backend checks emitted a dependency deprecation warning for Starlette's httpx test-client adapter and a local pytest-cache write warning. All tests passed; neither warning was suppressed or interpreted as a failing application request. Provider unit tests use mocks and do not establish live prose accuracy.

Public access results are saved in [judging-access-oct27.json](judging-access-oct27.json). This was a point-in-time check from the development computer, not an external uptime service or a complete mobile test. Earlier owner/friend phone checks and ten screenshot-questionnaire submissions remain separate evidence.

The working-app video recording exercised the fixed United–City Version 1, shared playback, a 19:00 AI recap after the 15:11 goal, supporting events, the recorded goal replay, Casual/Analyst changes, Spanish output and Azure Spanish narration. The 1:48 final edit contains actual footage, English captions and a short app-audio sample. Its public upload remains outstanding.

## Corrections in this documentation release

- Added the actual public app and fixed-test links prominently to the README and judge instructions, plus a current logo-free preview.
- Replaced obsolete no-deployment claims in current documentation; retained dated historical audits as historical evidence.
- Updated current test counts and distinguished real hosted checks from mocked provider tests and earlier fan feedback.
- Removed retired public scenario/default claims from architecture/API instructions and documented the actual three fixtures, four versions each and shared replay clock.
- Reconciled the deployment example with the tested application image and preserved the preexisting explicit container metadata fields. The initial Consumption template is clearly distinguished from the observed Express deployment.
- Kept local Word/video deliverables and backup ZIPs outside Git publication and the Docker build context. A source backup was preserved before edits.

No production resources, secrets, budgets, replica counts, subscription settings or application behavior were changed by this audit. The deployed app image remains based on `fcacbc6aa212c199171638ddbaa3b61d2a442914`; subsequent documentation-only commits need no app redeployment. Pull-request CI separately verifies backend, frontend and container packaging before merge.

## Still required before claiming submission complete

1. Owner review and public upload of the video; test the resulting URL without sign-in and provide the companion English translation as needed.
2. Add the video, public source, hosted app and testing instructions to the hackathon project entry; complete the portal submission.
3. Keep free judging access available for the required window and check the app if capacity or hosting state changes.

A fresh full twelve-version live AI/listening matrix and broader hands-on fan tests are not completed. Do not describe model review as a guarantee, the synthetic feeds as official match data, the pitch as full-player tracking, or survey comprehension as measured engagement uplift.
