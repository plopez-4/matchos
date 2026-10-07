# MatchOS
### The AI Operating System for Live Football

MatchOS turns a stream of football events into a match story fans can understand and verify. It connects recorded actions to emerging patterns, explains what changed, and helps returning viewers catch up without watching every missed minute.

Built for **Inside the Game: Developer Hackathon**, with synthetic football data, a React match experience, and an evidence-first path to Microsoft-powered AI.

[Explore the code](https://github.com/plopez-4/matchos) · [Working demo feature](https://github.com/plopez-4/matchos/pull/1) · [Azure AI development](https://github.com/plopez-4/matchos/pull/2)

## What we're building

A fan joins a match late. The score tells them who is winning, but they still need context: what happened, how the game changed, and which developments deserve attention.

MatchOS brings those answers together:

| Feature | What it gives the fan |
| --- | --- |
| **Live match view** | A score, event timeline and recorded match statistics that update during replay. |
| **Match intelligence** | Reproducible comparisons that reveal changes in recorded activity. |
| **Match Story Graph** | Connections from events to calculated patterns to explanations, with inspectable evidence. |
| **Catch Me Up** | A summary of events and stories since the viewer's last check. |
| **Personalization** | Casual or advanced explanations built from the same underlying facts. |
| **Evidence-backed AI** | An agent retrieves trusted stories and chooses what to explain; the app checks the selection before displaying it. |

Our first audience is football fans. The longer-term goal is to make the same intelligence useful to broadcasters, studios and streaming experiences.

## See the first match story

The current feature replays a fictional ten-minute highlights scenario: a quiet opening, increased Home shooting activity, a goal, and an Away response.

At the end, MatchOS can explain:

> Home recorded 4 shots in minutes 5–10, compared with 1 in the previous five minutes.

Open **Inspect supporting events** to see the shots behind that statement. Then select **Catch Me Up**:

> Recorded events since your last check: 30. Goals: 1. Home scored at 9:31. Home recorded 4 shots in minutes 5–10, compared with 1 in the previous five minutes.

Request it again without new events and the summary reports zero new events. The viewer cursor advances only after a successful response.

This comparison describes recorded shooting activity. It does not establish possession, tactical pressure or why the goal happened.

## Development status

**This is an actively developed hackathon prototype.** Features are being reviewed in pull requests before integration.

| Location | What's available |
| --- | --- |
| `main` / `develop` | Initial FastAPI and React foundation, synthetic replay, count analytics and basic Catch Me Up. |
| [`feature/evidence-backed-stories`](https://github.com/plopez-4/matchos/tree/feature/evidence-backed-stories) · [PR #1](https://github.com/plopez-4/matchos/pull/1) | Scripted highlights, five-minute shot comparisons, event/metric/story support graph, readable evidence and richer Catch Me Up. Backend and frontend GitHub checks passed. |
| [`feature/grounded-ai-explanations`](https://github.com/plopez-4/matchos/tree/feature/grounded-ai-explanations) · [Draft PR #2](https://github.com/plopez-4/matchos/pull/2) | Optional Azure-backed tool flow for story selection, validation, execution trace and deterministic fallback. Local tests pass; live Azure calls verified for casual and advanced summaries. |

The AI adapter is off by default. It uses a Microsoft Foundry Azure OpenAI-compatible model endpoint. The model selects supported story IDs; trusted text is rendered by the app. Free-form AI narration and hosted Foundry Agent Service deployment are future work.

## How MatchOS works

```text
Synthetic football events
          |
          v
Validated ingestion and ordered event storage
          |
          v
Deterministic counts and time-window analytics
          |
          v
Match Story Graph: events -> metrics -> stories
          |
          v
Evidence retrieval and validated AI story selection
          |
          v
Live match cards + personalized Catch Me Up
```

The intelligence layer calculates the facts. Story nodes retain supporting event IDs and versioned rules. The optional AI layer retrieves these candidates and selects their order for the audience. Invalid selections or provider failures fall back to the deterministic summary.

## Try the working demo

**Requirements:** Python 3.11+, Node.js 22.12+, npm and Git. If Windows cannot find `python`, try the Python launcher `py` after installing Python.

Clone the working demo branch while PR #1 is under review:

```powershell
git clone --branch feature/evidence-backed-stories https://github.com/plopez-4/matchos.git
cd matchos
```

### 1. Backend terminal

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e "./backend[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

Open the [API explorer](http://localhost:8000/docs). Keep this terminal running.

### 2. Frontend terminal

Open a second terminal in the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open [MatchOS](http://localhost:5173). Keep this terminal running too.

### 3. Simulator terminal

Open a third terminal in the repository root:

```powershell
.\.venv\Scripts\python.exe simulator/run.py --seed 7 --count 30 --interval 0.5
```

Watch the timeline, a **1–0 score**, and the shooting-activity story appear. Inspect its evidence and try Catch Me Up twice.

On macOS/Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. Use `python3` to create the environment if needed.

**Replay notes:** the scenario contains 30 recorded highlights, five Home shots and two Away shots. It is a sparse fixture, not a complete match feed. Replaying the same seed/count does not duplicate events. Restart the backend for a fresh match or before replacing the older random replay. The UI currently displays `demo-match` only.

For the draft Azure feature, use its branch and follow the [Azure configuration guide](https://github.com/plopez-4/matchos/blob/feature/grounded-ai-explanations/docs/azure-ai.md). Credentials stay on the backend; never commit keys.

## Technology and repository

| Area | Technology / location |
| --- | --- |
| Backend | Python, FastAPI, Pydantic · `backend/app/` |
| Frontend | React, Vite · `frontend/src/` |
| Synthetic data | Seeded Python scenario · `simulator/` |
| Shared contract | Versioned JSON Schema · `schemas/` |
| Verification | pytest, mocked provider tests, frontend builds, GitHub Actions |
| Microsoft integration | Azure OpenAI-compatible Foundry model endpoint, under development |
| Documentation | Product, architecture, API, milestone and submission plans · `docs/` |

### Run checks

From the repository root, with backend dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
cd frontend
npm run build
```

The evidence-story feature has seven backend checks. The draft AI feature has eighteen, including tool-flow and failure tests. Mock tests do not require Azure credentials.

## What we're working on next

- Verify the Azure tool flow against a real model deployment.
- Expand synthetic match realism and support more evidence-backed patterns.
- Persist events, story history and viewer preferences.
- Polish the fan experience and prepare a functioning demo under two minutes.
- Confirm category-specific hero technologies and remaining submission requirements.

Current storage is in memory and resets on restart. The backend supports one process, and the graph is computed from current events rather than persisted history. Authentication, bounded queries and deployment controls remain future work.

## Team workflow

Use `develop` for integration and `main` for tested releases. Create feature branches, keep changes focused, and submit pull requests with demo steps and verification. Backend/integration, frontend, and intelligence/AI are the main ownership areas.

See [CONTRIBUTING](CONTRIBUTING.md), the [milestone plan](docs/milestone-1.md), and the [initial task drafts](docs/github-issues.md).

## License

[MIT](LICENSE). All demo teams, players and match events are fictional. No real Premier League match data is included.
