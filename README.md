# MatchOS — The AI Operating System for Live Football

Turn live football events into understandable, personalized stories with evidence you can inspect.

## Vision and first milestone
Live event ingestion → deterministic analytics → Match Story Graph → evidence-backed explanations → Catch Me Up. Personalization adapts the same facts to casual and advanced fans. See [product](docs/product.md), [architecture](docs/architecture.md), [API](docs/api.md) and [M1 plan](docs/milestone-1.md).

## Included in this scaffold
- FastAPI: validated ingestion, duplicate protection, ordered replay, count/window analytics, evidence graph and deterministic Catch Me Up.
- React/Vite: match score, shot comparisons, timeline, readable story evidence, audience selector and polling.
- Python simulator: seeded fictional ten-minute highlights scenario, no provider credentials needed.
- Shared JSON schema, integration tests, GitHub CI and PR template.

The first derived graph includes event → metric-window → story support edges. An optional [Azure AI adapter](docs/azure-ai.md) selects evidence-backed story IDs using tools, with deterministic rendering/fallback; live Azure verification is pending. AI is off by default. Persistent preferences and PostgreSQL are planned tasks. This single-process demo stores events in memory and resets on restart. Counts do not establish possession, pressure or tactical causation. It is not ready for public deployment.

## Run locally
Prerequisites: Python 3.11+; Node 22.12+ with npm. Start from this repository directory.

Terminal 1 — backend (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "./backend[dev]"
python -m uvicorn app.main:app --app-dir backend --reload
```
macOS/Linux: use `source .venv/bin/activate`. API explorer: http://localhost:8000/docs.

Terminal 2 — frontend:
```powershell
cd frontend
npm ci
npm run dev
```
Open http://localhost:5173. Vite proxies `/api` to the backend.

Terminal 3 — synthetic replay:
```powershell
python simulator/run.py --seed 7 --count 30 --interval 0.5
```
Use `--dry-run` to print JSON without the backend. This is a sparse highlights feed, not every match touch: quiet opening → increased Home shooting → goal → Away response. The complete scenario contains 30 events, a 1–0 score, five Home shots and two Away shots. At ten match minutes, the activity story compares four Home shots in minutes 5–10 with one in minutes 0–5. Seeds vary player identities while retaining the known storyline.

Replay the same seed/count twice to check deduplication. Restart the backend before using this scenario on a match containing the old random replay; event IDs have changed. Use a new match ID when changing seeds. The UI reads `demo-match` only. If the backend restarts and the event cursor moves backwards, the UI clears the previous Catch Me Up cursor.

## Checks
```powershell
python -m pytest backend/tests
python scripts/export_schema.py
cd frontend
npm run build
```
CI installs backend dependencies and uses the committed frontend lockfile.

## Layout
| Directory | Purpose |
| --- | --- |
| backend/app | FastAPI and event models |
| backend/tests | Replay, validation, cursor and evidence tests |
| frontend/src | React demo dashboard |
| simulator | Seeded replay producer |
| schemas | Generated event schema and example |
| scripts | Schema export |
| docs | Product, architecture, API, milestone, GitHub issue drafts |
| .github | CI and review template |

## Three-person team
Lead owns backend/integration and repo management. Teammate 2 owns frontend. Teammate 3 owns deterministic intelligence, story graph and AI. Integrate daily on develop; release tested milestones to main. See [CONTRIBUTING](CONTRIBUTING.md).

## Publish to GitHub
The local repository has main/develop branches. Create an empty GitHub repository named `matchos`, then replace YOUR-OWNER:
```powershell
git remote add origin https://github.com/YOUR-OWNER/matchos.git
git push -u origin main
git push -u origin develop
```
Invite both teammates, protect branches, and create [these initial issues](docs/github-issues.md). Published repository: https://github.com/plopez-4/matchos (main and develop). Collaborator invitations, branch protections and live issues still need setup.

## References and license
Scaffold follows the official [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/), [React](https://react.dev/learn/build-a-react-app-from-scratch) and [Vite](https://vite.dev/guide/) guides. MIT licensed; keep credentials and licensed provider data out of Git.
