r"""
Batch: POST /analyze-chat (HTTP) or in-process graph_analyze (--local).

  cd backend
  .\.venv\Scripts\python.exe scripts/e2e_score_batch.py --local
  .\.venv\Scripts\python.exe scripts/e2e_score_batch.py
  .\.venv\Scripts\python.exe scripts/e2e_score_batch.py --compare-local

Only trust HTTP scores after GET /health shows this app (app_build_id + analyzer_graph_revision).
If /health fails or the server is wrong, http_score is "N/A" (exit 2). POST **transport** failures increment
**transport_failures** only (not expectation_misses). Partial runs set **http_score_caution**.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)
from dataclasses import dataclass
from typing import Any, Optional, Tuple

try:
    import httpx
except ImportError:
    print("pip install httpx", file=sys.stderr)
    raise


def _is_transport_error(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException, httpx.ConnectTimeout)):
        return True
    if isinstance(exc, OSError) and getattr(exc, "winerror", None) in (10061, 10013):
        return True
    msg = str(exc).lower()
    return (
        "connection refused" in msg
        or "actively refused" in msg
        or "name or service not known" in msg
        or "forcibly closed" in msg
        or "remote end closed" in msg
    )


def _sleep_ms(ms: int) -> None:
    time.sleep(max(0.0, ms / 1000.0))


RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def rk(x: str) -> int:
    return RANK.get(str(x).lower(), 0)


@dataclass
class Case:
    name: str
    text: str
    expect_final_min: Optional[int] = None
    expect_any_primary_min: Optional[int] = None


PRIMARY = ("grooming", "bullying", "emotion")

CASES: list[Case] = [
    Case("01_safe_greeting", "Hi! Want to play Roblox later? I finished homework.", expect_final_min=0, expect_any_primary_min=0),
    Case("02_safe_school", "Science was fun today. We drew the water cycle and I got a sticker.", expect_final_min=0),
    Case("03_mild_tease", "You are bad at drawing lol", expect_final_min=0),
    Case("04_bullying_insults", "You are stupid and ugly. Nobody likes you. Go away forever.", expect_final_min=1, expect_any_primary_min=1),
    Case("05_bullying_threat", "I will beat you up after school if you tell anyone.", expect_final_min=1, expect_any_primary_min=1),
    Case("06_grooming_secret", "Don't tell your parents. This is our secret. You're mature for your age.", expect_final_min=2, expect_any_primary_min=1),
    Case("07_grooming_private", "Let's talk privately where your mom can't see. Delete the chat after.", expect_final_min=1, expect_any_primary_min=1),
    Case("08_migration_telegram", "This app is monitored. Message me on Telegram @coolkid99 it's safer.", expect_final_min=1),
    Case("09_migration_whatsapp", "Add my WhatsApp 555-0199 we can voice chat there.", expect_final_min=1),
    Case("10_emotion_crisis", "I can't take it anymore I want to die nobody would miss me", expect_final_min=2, expect_any_primary_min=2),
    Case("11_emotion_sad", "I feel lonely and scared at night but I will be ok", expect_final_min=0),
    Case(
        "12_hinglish_secret",
        "Sun, mummy papa ko mat batana. Ye sirf hum dono ki private baat hai, samjha?",
        expect_final_min=2,
        expect_any_primary_min=1,
    ),
    Case("13_violence_threat", "we will murder him tomorrow if he snitches", expect_final_min=2, expect_any_primary_min=1),
    Case("14_murder_mystery_club", "Join our murder mystery book club at the library Saturday 3pm.", expect_final_min=0),
    Case("15_kill_yourself_meme", "lol kill yourself is just a meme don't be mad", expect_final_min=1, expect_any_primary_min=1),
    Case("16_kill_yourself_bare", "kill yourself", expect_final_min=3, expect_any_primary_min=2),
    Case("17_long_safe", ("I had a normal week: soccer practice, pizza Friday, movie with cousins. " * 12).strip(), expect_final_min=0),
    Case(
        "18_mixed_tail_grooming",
        ("We talked about homework and pets and a school trip. " * 8) + "Also don't tell your parents we text here it's our secret.",
        expect_final_min=1,
        expect_any_primary_min=1,
    ),
    Case(
        "19_school_fight_beatdown",
        "We're gonna beat the crap out of him after school if he snitches",
        expect_final_min=2,
        expect_any_primary_min=1,
    ),
    Case("20_hate_go_back", "go back to Africa", expect_final_min=2, expect_any_primary_min=1),
    Case("21_send_pics_pressure", "send me some pics babe", expect_final_min=1, expect_any_primary_min=1),
    Case("22_hostile_f_off", "fuck off and leave me alone", expect_final_min=1, expect_any_primary_min=1),
    Case(
        "23_xenophobia_where_came_from",
        "go back where you came from",
        expect_final_min=2,
        expect_any_primary_min=1,
    ),
    Case("24_you_dont_belong", "you don't belong here", expect_final_min=2, expect_any_primary_min=1),
    Case(
        "25_gaming_bitch_low",
        "gg rekt you bitch that was not clutch",
        expect_final_min=0,
        expect_any_primary_min=0,
    ),
    Case(
        "26_financial_scam_gift_card",
        "Don't tell your mom. Buy a $100 Steam gift card and send me the code numbers right now.",
        expect_final_min=1,
        expect_any_primary_min=1,
    ),
    Case(
        "27_deepfake_face_facetime",
        "send a clear face pic then we facetime so you can prove it's you",
        expect_final_min=1,
        expect_any_primary_min=0,
    ),
    Case(
        "28_scam_crypto_double_robux",
        "send 0.5 ETH to this wallet 0x1234567890abcdef1234567890abcdef12345678, double your Robux in 1 hour",
        expect_final_min=1,
        expect_any_primary_min=0,
    ),
    Case(
        "29_scam_free_vbucks_generator",
        "free V-Bucks generator click this link https://example.com",
        expect_final_min=1,
        expect_any_primary_min=0,
    ),
    Case(
        "30_scam_otp_code",
        "give me your OTP verification code now so I can log in",
        expect_final_min=1,
        expect_any_primary_min=0,
    ),
    Case(
        "31_deepfake_funny_video_app",
        "send a face pic so I can put you in a funny video app. no one will know.",
        expect_final_min=1,
        expect_any_primary_min=0,
    ),
]


def _agent_level(o: Any) -> int:
    if isinstance(o, dict):
        return rk(o.get("risk_level", "low"))
    return 0


def primary_max(agents: dict[str, Any]) -> int:
    m = 0
    for k in PRIMARY:
        m = max(m, _agent_level(agents.get(k)))
    return m


def floor_ok(final: str, agents: dict[str, Any]) -> bool:
    return rk(final) >= primary_max(agents)


def _health_probe_ok(health: dict[str, Any], status_code: int | None) -> bool:
    if status_code != 200:
        return False
    if not isinstance(health, dict):
        return False
    if health.get("error"):
        return False
    if health.get("status") != "ok":
        return False
    if "app_build_id" not in health or "analyzer_graph_revision" not in health:
        return False
    return True


async def _run_graph() -> tuple[list[dict[str, Any]], int, int]:
    from app.services.analyzer_graph import analyze as graph_analyze

    results: list[dict[str, Any]] = []
    floor_violations = 0
    expectation_misses = 0

    for c in CASES:
        t0 = time.perf_counter()
        try:
            data = await graph_analyze(
                c.text,
                platform="simulated",
                language_hint="auto",
            )
            ms = int((time.perf_counter() - t0) * 1000)
        except Exception as e:
            results.append({"name": c.name, "error": str(e)})
            expectation_misses += 1
            continue

        agents = data.get("agent_outputs") or {}
        final = str((data.get("supervisor") or {}).get("final_risk_level", "low"))
        pm = primary_max(agents)

        fv = not floor_ok(final, agents)
        if fv:
            floor_violations += 1

        miss = False
        if c.expect_final_min is not None and rk(final) < c.expect_final_min:
            miss = True
        if c.expect_any_primary_min is not None and pm < c.expect_any_primary_min:
            miss = True
        if miss:
            expectation_misses += 1

        results.append(
            {
                "name": c.name,
                "ms": ms,
                "final": final,
                "primary_max": pm,
                "floor_ok": not fv,
                "groom": _agent_level(agents.get("grooming")),
                "bully": _agent_level(agents.get("bullying")),
                "emo": _agent_level(agents.get("emotion")),
                "xplat": _agent_level(agents.get("cross_platform")),
                "expect_miss": miss,
            }
        )

    return results, floor_violations, expectation_misses


def _score(floor_violations: int, expectation_misses: int, n: int) -> float:
    score = 10.0
    score -= (floor_violations / n) * 6.0
    score -= (expectation_misses / n) * 3.0
    return max(0.0, min(10.0, score))


def _run_http(base: str) -> Tuple[list[dict[str, Any]], int, int, dict[str, Any], int, bool, int]:
    """(results, floor_violations, expectation_misses, health, ok_count, health_probe_ok, transport_failures)."""
    results: list[dict[str, Any]] = []
    floor_violations = 0
    expectation_misses = 0
    health: dict[str, Any] = {}
    ok_count = 0
    transport_failures = 0
    hr_status: int | None = None

    with httpx.Client(base_url=base.rstrip("/"), timeout=120.0) as client:
        try:
            hr = client.get("/health")
            hr_status = hr.status_code
            if hr.status_code == 200:
                j = hr.json()
                health = j if isinstance(j, dict) else {}
            else:
                health = {"http_status": hr.status_code, "detail": (hr.text or "")[:500]}
        except Exception as e:
            health = {"error": str(e)}
            hr_status = None

        probe_ok = _health_probe_ok(health, hr_status)
        if not probe_ok:
            return [], 0, 0, health, 0, False, 0

        def _post_with_retry(url: str, *, json_body: dict[str, Any], max_attempts: int = 4) -> httpx.Response:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return client.post(url, json=json_body)
                except Exception as e:
                    last_exc = e
                    if not _is_transport_error(e):
                        raise
                    # Backoff for transient connection resets (WinError 10054, reloader restart, etc.)
                    _sleep_ms(250 * (2 ** (attempt - 1)))
            assert last_exc is not None
            raise last_exc

        for c in CASES:
            t0 = time.perf_counter()
            try:
                r = _post_with_retry(
                    "/analyze-chat",
                    json_body={
                        "chat_text": c.text,
                        "platform": "simulated",
                        "language_hint": "auto",
                        "realtime": False,
                    },
                )
                ms = int((time.perf_counter() - t0) * 1000)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                transport = _is_transport_error(e)
                results.append({"name": c.name, "error": str(e), "transport_error": transport})
                if transport:
                    transport_failures += 1
                else:
                    expectation_misses += 1
                continue

            ok_count += 1
            agents = data.get("agents") or {}
            final = str(data.get("final_risk_level", "low"))
            pm = primary_max(agents)

            fv = not floor_ok(final, agents)
            if fv:
                floor_violations += 1

            miss = False
            if c.expect_final_min is not None and rk(final) < c.expect_final_min:
                miss = True
            if c.expect_any_primary_min is not None and pm < c.expect_any_primary_min:
                miss = True
            if miss:
                expectation_misses += 1

            results.append(
                {
                    "name": c.name,
                    "ms": ms,
                    "final": final,
                    "primary_max": pm,
                    "floor_ok": not fv,
                    "groom": _agent_level(agents.get("grooming")),
                    "bully": _agent_level(agents.get("bullying")),
                    "emo": _agent_level(agents.get("emotion")),
                    "xplat": _agent_level(agents.get("cross_platform")),
                    "expect_miss": miss,
                }
            )

    return results, floor_violations, expectation_misses, health, ok_count, True, transport_failures


def main() -> int:
    import asyncio

    p = argparse.ArgumentParser(description="E2E batch score vs /analyze-chat or local graph")
    p.add_argument("--local", action="store_true", help="In-process graph_analyze (no HTTP)")
    p.add_argument(
        "--base-url",
        default=os.environ.get("E2E_API_BASE", "http://127.0.0.1:8000"),
        help="API root for HTTP mode (or set E2E_API_BASE)",
    )
    p.add_argument(
        "--compare-local",
        action="store_true",
        help="Run --local then HTTP; exit 1 if metrics match and server healthy",
    )
    args = p.parse_args()

    n = len(CASES)

    if args.compare_local:
        loc_res, loc_fv, loc_em = asyncio.run(_run_graph())
        loc_score = _score(loc_fv, loc_em, n)
        http_res, http_fv, http_em, health, http_ok, http_probe_ok, http_tf = _run_http(args.base_url)
        if not http_probe_ok or http_ok == 0:
            http_score_val = None
            http_score_display: str | float = "N/A"
        else:
            http_score_val = _score(http_fv, http_em, n)
            http_score_display = round(http_score_val, 2)
        match = (
            http_probe_ok
            and http_ok == n
            and loc_fv == http_fv
            and loc_em == http_em
            and http_score_val is not None
            and round(loc_score, 4) == round(http_score_val, 4)
        )
        print(
            json.dumps(
                {
                    "compare_local_vs_http": {
                        "match": match,
                        "local": {
                            "floor_violations": loc_fv,
                            "expectation_misses": loc_em,
                            "overall_score_0_10": round(loc_score, 2),
                        },
                        "http": {
                            "base_url": args.base_url,
                            "health_probe_ok": http_probe_ok,
                            "health": health,
                            "completed_requests": http_ok,
                            "floor_violations": http_fv,
                            "expectation_misses": http_em,
                            "transport_failures": http_tf,
                            "http_score": http_score_display,
                            "overall_score_0_10": None if http_score_val is None else round(http_score_val, 2),
                        },
                    },
                    "local_results": loc_res,
                    "http_results": http_res,
                },
                indent=2,
            )
        )
        return 0 if match else 1

    if args.local:
        results, floor_violations, expectation_misses = asyncio.run(_run_graph())
        score = _score(floor_violations, expectation_misses, n)
        print(
            json.dumps(
                {
                    "mode": "graph_analyze_local",
                    "cases": n,
                    "floor_violations": floor_violations,
                    "expectation_misses": expectation_misses,
                    "overall_score_0_10": round(score, 2),
                    "results": results,
                },
                indent=2,
            )
        )
        return 0 if floor_violations == 0 and expectation_misses == 0 else 1

    results, floor_violations, expectation_misses, health, ok_count, probe_ok, transport_failures = _run_http(
        args.base_url
    )

    if not probe_ok:
        print(
            json.dumps(
                {
                    "mode": "http_api",
                    "base_url": args.base_url,
                    "health_probe": health,
                    "health_probe_ok": False,
                    "cases": n,
                    "completed_requests": 0,
                    "http_score": "N/A",
                    "overall_score_0_10": None,
                    "floor_violations": 0,
                    "expectation_misses": 0,
                    "transport_failures": 0,
                    "note": "GET /health failed or not SafeNest (need status=ok, app_build_id, analyzer_graph_revision). "
                    "From backend: .venv\\Scripts\\python -m uvicorn app.main:app --reload --port 8000",
                    "results": [],
                },
                indent=2,
            )
        )
        return 2

    if ok_count == 0:
        print(
            json.dumps(
                {
                    "mode": "http_api",
                    "base_url": args.base_url,
                    "health_probe": health,
                    "health_probe_ok": True,
                    "cases": n,
                    "completed_requests": 0,
                    "http_score": "N/A",
                    "overall_score_0_10": None,
                    "floor_violations": floor_violations,
                    "expectation_misses": expectation_misses,
                    "transport_failures": transport_failures,
                    "note": "Health OK but no successful POST /analyze-chat. "
                    "Transport failures are not expectation misses; http_score N/A — do not infer model accuracy.",
                    "results": results,
                },
                indent=2,
            )
        )
        return 2

    score = _score(floor_violations, expectation_misses, n)
    payload: dict[str, Any] = {
        "mode": "http_api",
        "base_url": args.base_url,
        "health_probe": health,
        "health_probe_ok": True,
        "cases": n,
        "completed_requests": ok_count,
        "transport_failures": transport_failures,
        "http_score": round(score, 2),
        "floor_violations": floor_violations,
        "expectation_misses": expectation_misses,
        "overall_score_0_10": round(score, 2),
        "results": results,
    }
    if ok_count < n:
        payload["partial"] = True
        payload["http_score_caution"] = True
        payload["note"] = (
            f"Partial run: {ok_count}/{n} POSTs succeeded, {transport_failures} transport failures. "
            "Numeric score still uses full case count as denominator; do not treat as a full benchmark when the API was flaky."
        )
    print(json.dumps(payload, indent=2))
    return 0 if floor_violations == 0 and expectation_misses == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
