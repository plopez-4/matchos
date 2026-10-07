# MatchOS — The AI Operating System for Live Football

Turn live football events into understandable, personalized stories with evidence you can inspect.

## Vision and first milestone
Live event ingestion → deterministic analytics → Match Story Graph → evidence-backed explanations → Catch Me Up. Personalization adapts the same facts to casual and advanced fans. See [product](docs/product.md), [architecture](docs/architecture.md), [API](docs/api.md) and [M1 plan](docs/milestone-1.md).

## Included in this scaffold
- FastAPI: validated ingestion, duplicate protection, ordered replay, count analytics, goal story nodes and deterministic Catch Me Up.
- React/Vite: match score, recent timeline, story evidence IDs, audience selector and polling.
- Python simulator: reproducible fictional events, no provider credentials needed.
- Shared JSON schema, integration tests, GitHub CI and PR template.

Full graph edges, window analytics, LLM adapters, persistent preferences and PostgreSQL are planned tasks. This single-process demo stores events in memory and resets on restart. Counts do not establish possession, pressure or tactical causation. It is not ready for public deployment.

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
Use `--dry-run` to print JSON without the backend. Replay the same seed/count twice to check deduplication. Restart the backend for a new demo; use a new match ID when changing seeds. The starter UI reads `demo-match` only.

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
Invite both teammates, protect branches, and create [these initial issues](docs/github-issues.md). Remote creation, collaborators, protection settings and issues are not yet published.

## References and license
Scaffold follows the official [FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/), [React](https://react.dev/learn/build-a-react-app-from-scratch) and [Vite](https://vite.dev/guide/) guides. MIT licensed; keep credentials and licensed provider data out of Git.
