# SafeNest AI — notes for developing agents

## Pipeline

`POST /analyze-chat` → **`execute_chat_analysis`** (`app/services/analysis_pipeline.py`) → **`analyzer_graph.analyze`** (LangGraph, `app/services/analyzer_graph.py`) → optional **Ollama** / **Gemini** arbiters (raise-only) → **`monitor_and_repair`** → persist **`ChatAnalysis`** (SQLite/Postgres).

## Core invariant

**`final_risk_level` ≥ max(grooming, bullying, emotion)** (ordinal order: low, medium, high, critical).

Enforced by:

- **`_aggregate_supervisor`** — weighted blend + lexicon floor + **primary-agent floor**
- **`apply_primary_floor_to_supervisor`** — last line of defense after arbiters + repair (HTTP must not contradict primaries)
- **`supervisor_satisfies_primary_floor`** / **`max_primary_safety_risk`** — tests and `scripts/e2e_score_batch.py`

Bump **`ANALYZER_GRAPH_REVISION`** in `analyzer_graph.py` when you change supervisor / floor semantics (exposed on **`GET /health`** and **`GET /version`**).

## Before “fixing” HTTP-only oddities

1. Run **one** Uvicorn from **`backend/`** using this repo’s **`.venv`** (no duplicate listener on the same port).
2. Confirm **`GET /health`** and **`GET /version`**: **`app_build_id`**, **`git_commit`**, **`analyzer_graph_revision`** match what you expect.
3. **`python scripts/e2e_score_batch.py --local`** (18 cases, in-process graph).
4. **`python scripts/e2e_score_batch.py --compare-local --base-url http://127.0.0.1:PORT`** — HTTP must match local (**0** floor violations, **0** expectation misses). If **`http_score`** is **`"N/A"`** (health probe failed), that is **deployment / wrong process**, not a model regression.

## CI (GitHub Actions)

- **Always:** `pytest tests/test_agent_regression.py` + `python scripts/e2e_score_batch.py --local`
- **Optional second job:** Uvicorn + full HTTP **`--compare-local`** (parity with local graph)

## Tuning priorities

| Area | Files |
|------|--------|
| Rules / keywords | `app/agents/rules.py`, agent modules |
| Global lexicon floor | `app/agents/risk_lexicon.py` |
| Supervisor blend / weights | `app/services/analyzer_graph.py` |
| Hinglish / code-switching | `app/agents/grooming_agent.py`, `regional_language_agent.py`; set **`ENABLE_OLLAMA=1`** when Ollama is available |
| Benign “murder mystery” etc. | `risk_lexicon.py` exclusions + `detect_violence_threats` context filters |

## Docker (demos / QA when laptop server is down)

From repo root: **`docker compose up --build api`** — builds **`backend/Dockerfile`**, wires Postgres, exposes **`http://localhost:8000`**. Then run **`e2e_score_batch.py --compare-local`** against that URL.

## README

Keep **`README.md`** “Agent handoff” and “E2E batch score” sections accurate when workflows or scripts change.
