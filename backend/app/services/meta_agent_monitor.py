from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.agents.types import RiskLevel
from app.services.analyzer_graph import _risk_rank, _run_agent, AGENT_ORDER  # MVP: reuse internal helpers


def _is_valid_output(o: Dict[str, Any]) -> bool:
    try:
        return (
            o.get("risk_level") in {"low", "medium", "high", "critical"}
            and 0.0 <= float(o.get("confidence", -1)) <= 1.0
            and isinstance(o.get("reason"), str)
            and isinstance(o.get("flags"), list)
        )
    except Exception:
        return False


def _conflict_pairs(agent_outputs: Dict[str, Dict[str, Any]]) -> List[str]:
    names = list(agent_outputs.keys())
    out: List[str] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            oa, ob = agent_outputs[a], agent_outputs[b]
            if not _is_valid_output(oa) or not _is_valid_output(ob):
                continue
            ra, rb = _risk_rank(oa["risk_level"]), _risk_rank(ob["risk_level"])
            ca, cb = float(oa["confidence"]), float(ob["confidence"])
            if abs(ra - rb) >= 2 and min(ca, cb) >= 0.65:
                out.append(f"{a}({oa['risk_level']},{ca:.2f}) vs {b}({ob['risk_level']},{cb:.2f})")
    return out


@dataclass
class AgentStats:
    trust: float = 0.8
    last_latency_ms: Optional[int] = None
    last_error: Optional[str] = None
    low_conf_hits: int = 0
    conflict_hits: int = 0
    ok_hits: int = 0


_STATS: Dict[str, AgentStats] = {name: AgentStats() for name in AGENT_ORDER}


def _update_trust(name: str, *, ok: bool, low_conf: bool, conflict: bool, error: Optional[str], latency_ms: Optional[int]) -> None:
    s = _STATS.setdefault(name, AgentStats())
    s.last_latency_ms = latency_ms
    s.last_error = error
    if ok:
        s.ok_hits += 1
        s.trust = min(1.0, s.trust + 0.01)
    if low_conf:
        s.low_conf_hits += 1
        s.trust = max(0.0, s.trust - 0.02)
    if conflict:
        s.conflict_hits += 1
        s.trust = max(0.0, s.trust - 0.03)
    if error:
        s.trust = max(0.0, s.trust - 0.06)


async def monitor_and_repair(state: Dict[str, Any], *, max_retries: int = 1) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """
    Rule-based Meta-Agent monitor.
    - Detect missing/invalid/error outputs
    - Retry failed agents
    - Flag low confidence and conflicts
    - Maintain lightweight trust scores in-memory
    """
    outputs: Dict[str, Dict[str, Any]] = dict(state.get("agent_outputs", {}) or {})
    retries: Dict[str, int] = {}
    missing: List[str] = []
    drift: List[str] = []

    # Detect missing/invalid/error
    for name in AGENT_ORDER:
        o = outputs.get(name)
        if not o:
            missing.append(name)
            continue
        status = (o.get("meta") or {}).get("status")
        if status == "error":
            missing.append(name)
        elif not _is_valid_output(o):
            drift.append(name)

    # Retry missing/error agents
    for name in list(dict.fromkeys(missing)):
        attempts = 0
        last_err: Optional[str] = None
        while attempts < max_retries:
            attempts += 1
            t0 = time.time()
            try:
                out = await _run_agent(name, state)  # reuse the same args mapping
                o = out.to_json()
                o.setdefault("meta", {})
                o["meta"]["status"] = "ok"
                o["meta"]["latency_ms"] = int((time.time() - t0) * 1000)
                outputs[name] = o
                last_err = None
                break
            except Exception as e:
                last_err = str(e)
        retries[name] = attempts
        if last_err:
            outputs[name] = {
                "risk_level": "low",
                "confidence": 0.0,
                "reason": "Agent failed after retry.",
                "flags": ["agent_error"],
                "meta": {"status": "error", "error": last_err},
            }

    # Low confidence list
    low_conf = [n for n, o in outputs.items() if _is_valid_output(o) and float(o["confidence"]) < 0.5]

    # Conflicts list
    conflicts = _conflict_pairs({k: v for k, v in outputs.items() if k in AGENT_ORDER and _is_valid_output(v)})
    conflict_agents: set[str] = set()
    for c in conflicts:
        # parse simple "a(...) vs b(...)" format
        parts = c.split(" vs ")
        if len(parts) == 2:
            conflict_agents.add(parts[0].split("(")[0])
            conflict_agents.add(parts[1].split("(")[0])

    # Update trust scores
    for name in AGENT_ORDER:
        o = outputs.get(name) or {}
        meta = o.get("meta") or {}
        status = meta.get("status")
        ok = status == "ok" and _is_valid_output(o)
        error = meta.get("error") if status == "error" else None
        latency_ms = meta.get("latency_ms")
        _update_trust(
            name,
            ok=ok,
            low_conf=name in low_conf,
            conflict=name in conflict_agents,
            error=error,
            latency_ms=latency_ms if isinstance(latency_ms, int) else None,
        )

    agent_health = []
    for name in AGENT_ORDER:
        s = _STATS.get(name, AgentStats())
        denom = max(1, s.ok_hits + s.low_conf_hits + s.conflict_hits)
        agent_health.append(
            {
                "agent_name": name,
                "trust_score": float(s.trust),
                "last_latency_ms": s.last_latency_ms,
                "last_error": s.last_error,
                "low_confidence_rate_24h": float(min(1.0, s.low_conf_hits / denom)),
                "conflict_rate_24h": float(min(1.0, s.conflict_hits / denom)),
            }
        )

    diagnostics = {
        "missing_outputs": missing,
        "low_confidence": low_conf,
        "conflicts": conflicts,
        "retries": retries,
        "drift_suspected": drift,
        "agent_health": agent_health,
    }
    return outputs, diagnostics

