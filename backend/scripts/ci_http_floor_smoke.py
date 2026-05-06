#!/usr/bin/env python3
"""
Wait for GET /health, then POST /analyze-chat on a few fixed strings.
Exit 1 if supervisor final_risk_level is below max(grooming, bullying, emotion).

CI usage (from backend/):
  DATABASE_URL=sqlite+aiosqlite:///./ci.db PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 9999 &
  sleep 3
  E2E_API_BASE=http://127.0.0.1:9999 python scripts/ci_http_floor_smoke.py
"""
from __future__ import annotations

import os
import sys
import time

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

import httpx  # noqa: E402

from app.services.analyzer_graph import supervisor_satisfies_primary_floor  # noqa: E402

SAMPLES = [
    "Don't tell your parents. This is our secret.",
    "we will bit him tommorow",
    "kill yourself",
    "Sun, mummy papa ko mat batana. Ye sirf hum dono ki private baat hai, samjha?",
    "Join our murder mystery book club at the library Saturday 3pm.",
]


def main() -> int:
    base = os.environ.get("E2E_API_BASE", "http://127.0.0.1:8000").rstrip("/")
    health_ready = False
    for i in range(45):
        try:
            h = httpx.get(f"{base}/health", timeout=2.0)
            if h.status_code == 200:
                j = h.json()
                health_body = j if isinstance(j, dict) else {}
                if (
                    health_body.get("status") == "ok"
                    and "app_build_id" in health_body
                    and "analyzer_graph_revision" in health_body
                ):
                    print("health:", health_body, file=sys.stderr)
                    health_ready = True
                    break
                print("health missing deploy fields, retry:", health_body, file=sys.stderr)
        except Exception as e:
            if i == 44:
                print("health probe failed:", e, file=sys.stderr)
                return 2
        time.sleep(1)
    if not health_ready:
        print("health never became ready (wrong server or old build)", file=sys.stderr)
        return 2

    bad = 0
    with httpx.Client(base_url=base, timeout=120.0) as client:
        for text in SAMPLES:
            r = client.post(
                "/analyze-chat",
                json={
                    "chat_text": text,
                    "platform": "simulated",
                    "language_hint": "auto",
                    "realtime": False,
                },
            )
            if r.status_code != 200:
                print("HTTP", r.status_code, text[:60], r.text[:200], file=sys.stderr)
                bad += 1
                continue
            data = r.json()
            sup = data.get("supervisor") or {}
            agents = data.get("agents") or {}
            if not supervisor_satisfies_primary_floor(sup, agents):
                print("FLOOR_FAIL", text[:80], "final=", sup.get("final_risk_level"), file=sys.stderr)
                bad += 1
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
