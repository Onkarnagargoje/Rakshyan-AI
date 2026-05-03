# SafeNest AI — Open-Source Agentic Child Cyber Safety Platform (MVP)

Privacy-first, fully local, multi-agent cyber safety analysis for kids. **No paid APIs**.

## What you get (MVP)

- **FastAPI** backend with modular architecture
- **LangGraph** multi-agent workflow:
  - 10 specialized agents
  - **Supervisor Agent** aggregates results and triggers actions
  - **Meta-Agent (Agent Monitor)** performs rule-based health + drift checks, retries, and diagnostics
- **Socket.IO** realtime analysis streaming
- **PostgreSQL** persistence (Docker Compose)
- **JWT auth** (parent/admin demo users)
- **Tamper-evident logs** using SHA-256 hash chaining
- **Next.js + Tailwind** frontend:
  - Landing page
  - Child dashboard (score, badges, quizzes)
  - Parent dashboard (alerts, trends with Recharts)
  - Admin dashboard (agent health, meta diagnostics, logs)

## Repo structure

```
backend/
  app/
    agents/
    routes/
    schemas/
    services/
    models/
    utils/
frontend/
docker-compose.yml
```

## Prerequisites

- Python **3.12.x recommended** (Windows wheels available for this stack; Python 3.14 may force Rust builds)
- Node 20+ (you have Node installed)
- Docker Desktop (for PostgreSQL) — optional but recommended
- **Ollama** (local LLM runtime)

## 1) Install and run Ollama (local LLM)

1. Install Ollama from: `https://ollama.com`
2. Pull at least one model (pick one):

```powershell
ollama pull llama3
# or
ollama pull mistral
# or
ollama pull phi3
```

3. Verify it’s running:

```powershell
ollama list
```

The backend will call Ollama via `http://localhost:11434`.

## 2) Start PostgreSQL (recommended)

```powershell
docker compose up -d
```

Postgres will be exposed on `localhost:5432`.

## 3) Backend setup

```powershell
cd backend
# IMPORTANT: on Windows, create the venv with Python 3.12
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

Configure environment:

```powershell
copy .env.example .env
```

Run API:

```powershell
uvicorn app.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

## 4) Frontend setup

```powershell
cd ..\frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Demo credentials (MVP)

- Parent: `parent@example.com` / `parent123`
- Admin: `admin@example.com` / `admin123`

## Notes on local ML models (offline-friendly)

This MVP is designed to **run on low-resource systems**:

- If Hugging Face models aren’t available (or torch isn’t installed), agents **fall back** to:
  - rule-based heuristics
  - lightweight keyword patterns
  - Ollama LLM calls (optional, local)

You can enable/disable model usage via `.env`.

