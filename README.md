# SafeNest AI — Open-Source Agentic Child Cyber Safety Platform (MVP)

Privacy-first, multi-agent cyber safety analysis for kids. **Defaults to free/local tools** (rules + optional **Ollama**). **Optional Google Gemini** (paid API key) can be enabled for a second opinion on borderline cases—see below.

## Product direction: **Android-first**

The intended shipping path is an **Android child agent** (notification listener + optional in-app channels) and a **parent mobile app**, both talking to this backend over your network or a home hub. iOS is out of scope for deep third-party message capture; focus features and policies on **Android**.

## Multilingual + code-switching (Ollama)

When `ENABLE_OLLAMA=1`, the **regional_language** agent calls your local **Ollama** (`/api/chat`) to detect mixed languages, romanized Indic/Urdu, and safety-relevant phrasing that heuristics miss. If Ollama is offline, it falls back to fast heuristics. Tune `OLLAMA_MODEL` and `OLLAMA_TIMEOUT_SEC` in `backend/.env`.

**Hinglish / Romanized Hindi without Ollama:** `grooming` includes common **“mummy/papa ko mat batana”**-style patterns, and **regional_language** can raise a **medium** `hinglish_grooming_heuristic` when Roman-script secrecy phrasing matches. For stronger code-switching coverage, keep **`ENABLE_OLLAMA=1`** and Ollama reachable from the API host.

## Optional: Google Gemini (API key)

For **extra accuracy on ambiguous** messages, set in `backend/.env`:

- `ENABLE_GEMINI=1`
- `GEMINI_API_KEY=` — create a key at [Google AI Studio](https://aistudio.google.com/apikey)
- `GEMINI_MODEL=gemini-1.5-flash` (or another supported model name)

Install dependency: `pip install google-generativeai` (already listed in `requirements.txt`). After each analysis, if the **supervisor is conservative** but **any agent is `medium+`**, the backend may call Gemini with the same adjudicator prompt as **Ollama arbiter**; Gemini **only raises** risk, never lowers it. Billing and data handling are governed by **Google’s terms**—use only if that fits your product.

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

The backend calls Ollama at `OLLAMA_BASE_URL` (default `http://localhost:11434`) for **regional / multilingual** analysis when enabled.

## 2) Start PostgreSQL (recommended)

```powershell
docker compose up -d
```

Postgres will be exposed on `localhost:5432`.

### If Docker/Postgres isn’t available (Windows-friendly fallback)

This repo supports a zero-dependency local DB for demos:

- Set `DATABASE_URL=sqlite+aiosqlite:///./safenest.db` in `backend/.env`

You’ll still get the full multi-agent pipeline, evidence logs, and dashboards—just using a local SQLite DB.

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

Run API (one command from **`backend/`** after venv + `pip install`):

```powershell
.\scripts\run_api_dev.ps1
```

On macOS/Linux: `chmod +x scripts/run_api_dev.sh && ./scripts/run_api_dev.sh`

**Docker demo** (API + Postgres on **`http://localhost:8000`**): from repo root, `docker compose up --build api` (waits for healthy Postgres).

API docs at `http://localhost:8000/docs`. OpenAPI **`info.version`** matches **`GET /health`** field **`app_build_id`** when you set **`APP_BUILD_ID`** in `.env` (defaults to `dev`) so you can confirm the running build after a pull.

Persisted analyses: **`GET /get-risk-report/{analysis_id}`** (returns supervisor, agents, evidence chain).

**Long chats / Hinglish:** the graph runs on the full `chat_text` string today. For very long threads, plan **chunked analysis** (window + merge) or keep **`ENABLE_OLLAMA=1`** with Ollama reachable so `regional_language` can go deeper on code-switching.

### Family / Android child pipeline (new)

- `POST /auth/register` — parent account (role `parent`) + JWT
- `POST /family/children` — add a child profile (Bearer parent JWT)
- `POST /family/children/{id}/pairing-code` — 8-char code, **15 min** TTL (invalidates prior unused codes)
- `POST /family/link` — child app sends `{ "code", "device_label" }` → returns **`ingest_token`** (store on device; shown once)
- `POST /family/ingest/notifications` — child app Bearer **`ingest_token`**, body `{ "items": [ { "source_app", "text" } ], "language_hint" }` → runs full agent graph; **`medium`+** creates a **`ParentAlert`**
- `GET /family/alerts` — parent lists alerts; `POST /family/alerts/mark-read` with `{ "alert_ids": [...] }`

If you already have a local `safenest.db` from an older checkout, restart the API once so startup runs SQLite **additive** migrations (`child_id` / `device_id` on `chat_analyses`), or delete `backend/safenest.db` and start fresh.

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

## Accuracy expectations (important)

**99% accuracy on arbitrary real-world chat is not a realistic guarantee** without a large labeled dataset, continuous evaluation, and calibrated models. This MVP optimizes for:

- **High recall** on serious harms (violence, grooming signals, self-harm language) via expanded rules, a **global risk lexicon floor** on the supervisor, optional **Ollama arbiter**, and optional **Gemini arbiter** (when `ENABLE_GEMINI=1` and a key is set) when agents disagree with a conservative supervisor.
- **Regression tests** so known good/bad strings do not silently regress:

```powershell
cd backend
$env:ENABLE_OLLAMA="0"   # fast deterministic CI-style run
$env:PYTHONPATH="."
pytest tests/test_agent_regression.py -v
```

CI (GitHub Actions): `.github/workflows/ci.yml` — job **`backend-test`** always runs **`pytest tests/test_agent_regression.py`** and **`python scripts/e2e_score_batch.py --local`**. Job **`backend-http-e2e`** (after tests) starts **Uvicorn** on SQLite and runs **`e2e_score_batch.py --compare-local`** so HTTP matches local (includes Hinglish case `12_hinglish_secret`). For a lighter check only, run **`scripts/ci_http_floor_smoke.py`** manually.

Tune false positives/negatives by editing `app/agents/rules.py`, `app/agents/risk_lexicon.py`, and weights in `app/services/analyzer_graph.py`.

### E2E batch score (local vs HTTP)

From `backend/` with the project venv activated:

```powershell
$env:PYTHONPATH="."
.\.venv\Scripts\python.exe scripts/e2e_score_batch.py --local
.\.venv\Scripts\python.exe scripts/e2e_score_batch.py
.\.venv\Scripts\python.exe scripts/e2e_score_batch.py --compare-local
```

- **`--local`** — in-process `graph_analyze` only (no Uvicorn; no arbiters/pipeline).
- **Default (HTTP)** — probes **`GET /health`** first; must return **`status`**, **`app_build_id`**, and **`analyzer_graph_revision`** (stale/wrong process → **`http_score`: `"N/A"`**, exit **2**). Then **`POST /analyze-chat`**. **Transport** failures increment **`transport_failures`** only (not **expectation_misses**). Partial runs add **`http_score_caution`**: numeric score is not a full benchmark. Override base with **`--base-url`** / **`E2E_API_BASE`**.
- **`--compare-local`** — runs local then HTTP; **`http.http_score`** is **`"N/A"`** if health fails or no request completes; otherwise must match local for **`floor_violations`**, **`expectation_misses`**, and score.

## Agent handoff (copy-paste)

Give the next agent **all** of the following so they do not “debug” the wrong layer:

1. **Repo path** — workspace root that contains `backend/` (e.g. `c:\Rakshyan_ai` on this machine).
2. **Unit tests** — `cd backend`, `$env:PYTHONPATH="."`, `pytest tests/test_agent_regression.py -q` (or full `pytest tests/ -q`).
3. **Local E2E baseline** — `.\.venv\Scripts\python.exe scripts/e2e_score_batch.py --local` (save the printed JSON or note `floor_violations` / `expectation_misses` / `overall_score_0_10`).
4. **Explicit task** — Run **exactly one** Uvicorn from **`backend/`** with this repo’s **`.venv`** (avoid a second process on the same port). Set **`APP_BUILD_ID`** in `.env` for deploy labels. Confirm **`GET /health`** and **`GET /version`** show the expected **`app_build_id`**, **`git_commit`** (when git is available), and **`analyzer_graph_revision`** (static marker in `analyzer_graph`). Then run **`scripts/e2e_score_batch.py`** over HTTP and **`--compare-local`** until metrics match **`--local`**. If they diverge, assume **stale process / wrong cwd / wrong port** before changing model code.
5. **Risk report** — persisted rows: **`GET /get-risk-report/{analysis_id}`**.

**Anti-pattern:** Relying on `Invoke-RestMethod` to `:8000` (or ad-hoc curls) **without** confirming the process is **your** Uvicorn on **this** checkout. An old shell, another app on 8000, or no reload will make the product look “broken” when the bug is **deployment**.

2b. **CI parity** — same as GitHub Actions gate: `pytest tests/test_agent_regression.py -q` then `python scripts/e2e_score_batch.py --local` (full suite: `pytest tests/ -q`).

## Developing agents (canonical brief)

See **[AGENTS.md](AGENTS.md)** at the repo root: pipeline, **primary-agent invariant**, **`ANALYZER_GRAPH_REVISION`**, proof order (health → local e2e → `--compare-local`), CI, and tuning file map.

## Notes on local ML models (offline-friendly)

This MVP is designed to **run on low-resource systems**:

- If Hugging Face models aren’t available (or torch isn’t installed), agents **fall back** to:
  - rule-based heuristics
  - lightweight keyword patterns
  - Ollama LLM calls (optional, local)

You can enable/disable model usage via `.env`.

