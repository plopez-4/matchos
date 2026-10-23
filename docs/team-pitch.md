# MatchOS: Teammate Pitch & Contributor Guide

_Use this guide when pitching MatchOS to friends, collaborators, and potential hackathon teammates._

---

## 1. Quick Text / DM (Casual & Punchy)

> "Yo, I’m building a project for the Microsoft & Premier League hackathon called **MatchOS**—it’s an AI operating system for live football. Think of it like a smart 'Catch Me Up' companion for when you join a match late.
>
> Instead of giving you a boring box score or letting an LLM hallucinate fake commentary, it connects live match events into a verified graph and uses Azure AI to explain exactly what happened and what changed—backed by proof.
>
> The best part? **The foundation is already working end-to-end** (FastAPI backend, React 19 dashboard, and Azure OpenAI integration are already running and tested). We’re in prime shape to win or place high, and I’d love to have you on the team. Want to check out the repo and live demo?"

---

## 2. The Core Pitch (For a Call or Coffee Chat)

### A. The Problem Everyone Understands

Have you ever turned on a match at the 30th minute, seen 1–0, and had zero clue how the game is actually going? Match apps give you either raw numbers (possession %, shots) or endless text feeds. MatchOS solves the late-joiner problem by giving fans a personalized 10-second briefing: What happened, what changed, and direct evidence to back it up.

### B. Why It Stands Out from Other Hackathon Projects

90% of AI hackathon projects are just lazy ChatGPT wrappers that hallucinate stats. MatchOS is built differently: deterministic rules calculate facts (shot frequency spikes, goal build-ups), and Azure AI acts as an intelligent selector that has to prove its claims against real event IDs. Judges love grounded AI because it actually works in the real world.

### C. Zero Friction to Start Contributing

We’re not starting from scratch staring at an empty repo. The backend pipeline, synthetic match simulator, Azure integration, and polished React dashboard are already live and tested. Anything you touch will immediately show up in a working, slick product.

---

## 3. Skillset Match & High-Impact Ownership

Hand your friend a clear, exciting area they can own based on what they like doing:

| Skillset / Interest                   | What They Can Own in MatchOS                                                                                                        |
| :------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------- |
| **AI / Prompt Engineering / Agents**  | Take our Azure OpenAI tool flow to the next level—build a tactical analyst agent or integrate Azure AI Foundry agent orchestration. |
| **Data Science / Football Analytics** | Write new deterministic metric rules: high-turnover counters, pressing triggers, or shot momentum windows.                          |
| **Frontend / Visuals**                | Add an interactive 2D pitch view (HTML canvas/SVG) showing shot trajectories and pitch coordinates during replay.                   |
| **Product / Storytelling / Video**    | Lead the hackathon submission: script and produce the 1:45 demo video, sharpen the pitch deck, and show off the tech.               |

---

## 4. The Live Demo Hook

Before talking with them, start the app locally and show it live:

```powershell
# Terminal 1: Backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`, click **"Catch Me Up"**, expand the evidence drawer, and show them:

> _"See this? It's live. Let's finish this together and submit."_
