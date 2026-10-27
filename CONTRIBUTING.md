# Contributing

## Security baseline

Read [security setup and limits](docs/security.md) before changing replay or AI paths. Preserve session ownership, trusted ingestion, quotas and deterministic fallback. Run `python scripts/check_secrets.py` and the security regression tests before review. Never place Azure keys or ingestion credentials in frontend code, examples or AI handoff files. Install backend dependencies using `backend/constraints.txt`; update those resolved pins deliberately.

## Shared formatting

Use the pinned Prettier version installed by `npm ci` in `frontend`. The root `.prettierrc.json` defines two-space indentation, single JavaScript quotes, semicolons, trailing commas, a 100-character target width and LF line endings. Prettier formats JavaScript/JSX, CSS, HTML, JSON, YAML and Markdown throughout this repository. Python is outside Prettier's supported scope and is skipped.

From the repository root:

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run format
npm.cmd --prefix frontend run format:check
```

Run `format` before committing; `format:check` reports differences without editing files. GitHub's Frontend CI job fails when formatting differs. Configure that job as a required status check to prevent unformatted merges. Editor users can install the Prettier extension and enable format-on-save; the repository configuration and local package version are the source of truth. Generated schemas, npm's lockfile, local environments, build outputs and third-party assets are excluded in `.prettierignore`.

## Branches and review

`main` is the canonical release branch; `develop` is the integration branch. Branch from the latest integrated code using `feature/<issue>-<name>` or `fix/<issue>-<name>`. Link a task and request a teammate's review when available. Release through a pull request with passing Backend/Frontend CI, then tag the actual version. Keep develop synchronized after releases. Preserve history; older branches are not separate supported applications. Branch protection and required reviews must be honored.

Before review, run backend tests, frontend tests and the frontend build. Include demo steps and limitations; update docs/contracts when behavior changes. Do not commit secrets. Contract changes require maintainer agreement.

Every factual story must cite stored event IDs and its deterministic rule version. Analytics must be reproducible with documented units/windows. AI may phrase supplied facts; it must not invent metrics or evidence.

Pydantic is the event contract source. Run `python scripts/export_schema.py` and commit the generated schema after edits. Breaking changes need a schema version increment and migration plan. Test meaningful outcomes and edge cases rather than implementation details.

After publishing, repo owner sets main as default, requires one review and CI jobs Backend/Frontend on main and develop, and blocks force pushes/deletions. These settings are guidance, not automatically configured. Assign reviewers across ownership areas for integration changes.

For stacked PRs, start from the latest working prerequisite branch and target it until integrated into develop. Update CHANGELOG.md and relevant documentation for user-visible behavior; preserve asset credits and separate third-party licenses.
