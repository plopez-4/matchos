# MatchOS

**Missed the action? See how it happened and understand what changed.**

MatchOS turns synthetic football events into a returning fan's recap, recorded pitch replay and inspectable evidence. The main page focuses on one match; `/?view=development` opens the separate analytics inspector.

Built for Inside the Game: Developer Hackathon. Independent prototype; no sponsorship or endorsement claimed. Real club and reference player names identify actors in fictional action, not real performances.

## Current version

`main` is the canonical version to clone and submit after release integration. Older commits and evaluation reports are development history, not alternate applications. Start with [current documentation](docs/README.md), [submission notes](docs/hackathon-submission.md) and [patch notes](CHANGELOG.md).

- One fan page: score, important moment, recorded build-up and one Catch Me Up paragraph.
- Connected explanations: verified recovery, team passes, goal-producing shot and equalizer form one move. A nearby goal is never linked by proximity alone.
- Named replay actions, such as “Watch Ismaila Sarr's equalizer.”
- Casual and Analyst perspectives, English and Spanish, using the same source facts.
- Optional Azure AI selects verified stories and writes the complete bilingual paragraph from structured observations. Local checks and a separate fallible model review can reject it in favor of a labeled factual fallback.
- Optional Azure Speech reads the displayed recap. Device speech remains available separately. Pronunciation hints address reported names and club-name joins; human listening acceptance is still needed.

The latest focused live check returned two AI recaps, one content fallback and one Azure rate-limit fallback across four requests. **Consistent AI prose quality remains unresolved.** The [editorial quality review](docs/recap-quality-v13-review.md) preserves the failed twenty-request run and subsequent corrections separately. No five-person human study has been completed.

## Core architecture

```text
Synthetic events: passes, shots, recoveries, coordinates
  -> deterministic analytics over observed windows and possessions
  -> Match Story Graph: events -> metrics -> stories
  -> grounded AI selection, whole-paragraph writing and validation
  -> fan recap, recorded replay and inspectable evidence
```

Metrics retain rule versions and source event IDs. AI receives observations and relationships, not prewritten commentary sentences. Rejected output is replaced as a whole; the server does not patch model prose. Pitch replay is schematic interpolation between recorded locations, not continuous player tracking.

The shared catalog contains United–City, Palace–Newcastle and Brighton–Fulham. Both views use `backend/app/data/demo_fixtures.json`; the Hull feed is retired. Earlier small scenarios survive only as isolated analytics test fixtures. See [data provenance](docs/full-match-data.md).

## Run locally

Requirements: Python 3.11+, Node.js 22.12+, npm and Git. In Windows Command Prompt:

```bat
git clone https://github.com/plopez-4/matchos.git
cd matchos
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip==26.2.1
.venv\Scripts\python.exe -m pip install -c backend/constraints.txt -e ".\backend[dev]"
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Keep it running. Open a second Command Prompt in `matchos`:

```bat
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open [the fan page](http://127.0.0.1:5173), or the actual port Vite prints. Choose a fixture and start replay. Demo settings contain speed (0.5×–80×) and reset. Catch Me Up pauses replay and drains the in-flight request before taking its snapshot. Backend restart clears in-memory matches.

On macOS/Linux use `python3 -m venv .venv`, `.venv/bin/python` and `npm`.

### Private Azure connections

Instead of the plain backend command above, this Windows launcher prompts for keys without displaying or saving them:

```bat
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_backend.ps1 -AI -Speech
```

Supply your own endpoint, deployment and region if they differ from the launcher's defaults. See [model setup](docs/azure-ai.md) and [Speech setup](docs/azure-narration.md). Keys belong only on the backend, never in React or GitHub. An unconfigured clone uses deterministic summaries.

## Verification

```bat
.venv\Scripts\python.exe -m pytest backend/tests
.venv\Scripts\python.exe scripts/check_secrets.py
npm.cmd --prefix frontend run format:check
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
```

Latest local backend checks: **368 tests passed**, with formatting and credential scan passing too. The unchanged frontend previously passed 61 tests and production build. Provider unit calls are mocked; live checks and failures are recorded separately. Check GitHub Actions for hosted CI results. The [five-fan test](docs/fan-evaluation.md) is prepared, with no participant results claimed.

## Scope and limitations

FastAPI and React/Vite run locally with optional Azure model and Speech services. There is no deployed Foundry Agent Service hierarchy, real match feed, full player tracking, production cloud persistence or confirmed hosted judging URL. Use one backend worker. See [security controls and limits](docs/security.md).

Next: improve AI acceptance without relaxing evidence requirements, then conduct the real fan test. A public video and judging access remain separate submission work.

## Code and license

Backend: `backend/app/` · frontend: `frontend/src/` · fixtures: `data/synthetic/` · contracts: `schemas/` · tools: `scripts/` · [contributing](CONTRIBUTING.md).

[MIT](LICENSE) covers application code. Artwork, photography and fonts have separate terms in [visual assets](docs/visual-assets.md). Confirm permissions before including third-party marks in submitted footage. Player references and historical aggregates have separate provenance. All match actions are fictional.
