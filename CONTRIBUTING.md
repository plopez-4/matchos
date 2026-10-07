# Contributing

main is the release branch; develop is the integration branch. Branch from develop using `feature/<issue>-<name>` or `fix/<issue>-<name>`. Link a task and request one teammate's review before merging. Keep PRs small. Release through a reviewed develop → main PR and tag `v0.1.0`. Hotfixes branch from main and merge back to develop too.

Before review, run backend tests and frontend build. Include demo steps and limitations; update docs/contracts when behavior changes. Do not commit secrets. Contract changes require agreement between all three owners.

Every factual story must cite stored event IDs and its deterministic rule version. Analytics must be reproducible with documented units/windows. AI may phrase supplied facts; it must not invent metrics or evidence.

Pydantic is the event contract source. Run `python scripts/export_schema.py` and commit the generated schema after edits. Breaking changes need a schema version increment and migration plan. Test meaningful outcomes and edge cases rather than implementation details.

After publishing, repo owner sets main as default, requires one review and CI jobs Backend/Frontend on main and develop, and blocks force pushes/deletions. These settings are guidance, not automatically configured. Assign reviewers across ownership areas for integration changes.
