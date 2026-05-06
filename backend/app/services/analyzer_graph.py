from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Optional, Tuple, TypedDict

from langgraph.graph import StateGraph, END

from app.agents import (
    bullying_agent,
    grooming_agent,
    emotion_agent,
    cross_platform_agent,
    regional_language_agent,
    fake_profile_agent,
    fraud_agent,
    wearable_signal_agent,
    education_agent,
    evidence_log_agent,
    parent_summary_agent,
)
from app.agents.risk_lexicon import lexicon_supervisor_floor
from app.agents.types import AgentOutput, RiskLevel

# Bump when supervisor aggregation / floor semantics change (shown in GET /health, /version).
ANALYZER_GRAPH_REVISION = "20260504-xenophobia-lexicon-face-lure"

PRIMARY_FLOOR_CONF: Dict[str, float] = {"low": 0.12, "medium": 0.42, "high": 0.75, "critical": 0.92}
FRAUD_FLOOR_CONF: Dict[str, float] = {"medium": 0.5, "high": 0.72, "critical": 0.9}


class AnalysisState(TypedDict, total=False):
    chat_text: str
    platform: str
    language_hint: str
    wearable: Dict[str, Any]
    agent_outputs: Dict[str, Dict[str, Any]]
    supervisor: Dict[str, Any]
    meta: Dict[str, Any]


AGENT_ORDER: List[str] = [
    "regional_language",
    "bullying",
    "grooming",
    "emotion",
    "cross_platform",
    "fake_profile",
    "fraud",
    "wearable_signal",
    "evidence_log",
    "education",
]


def _risk_rank(level: RiskLevel) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}[level]


def _agent_output_as_dict(o: Any) -> Dict[str, Any]:
    """Normalize graph/API outputs (plain dict or Pydantic AgentResult) for floor checks."""
    if o is None:
        return {}
    if isinstance(o, dict):
        return o
    md = getattr(o, "model_dump", None)
    if callable(md):
        return md()
    return {}


def max_primary_safety_risk(agent_outputs: Mapping[str, Any]) -> RiskLevel:
    """Max risk among grooming / bullying / emotion (core safety agents)."""
    max_primary: RiskLevel = "low"
    for name in ("grooming", "bullying", "emotion"):
        o = _agent_output_as_dict(agent_outputs.get(name))
        lvl = o.get("risk_level", "low")
        if isinstance(lvl, str) and lvl in ("low", "medium", "high", "critical"):
            if _risk_rank(lvl) > _risk_rank(max_primary):  # type: ignore[arg-type]
                max_primary = lvl  # type: ignore[assignment]
    return max_primary


def _get_agent_level(agent_outputs: Mapping[str, Any], name: str) -> RiskLevel:
    o = _agent_output_as_dict(agent_outputs.get(name))
    lvl = o.get("risk_level", "low")
    if isinstance(lvl, str) and lvl in ("low", "medium", "high", "critical"):
        return lvl  # type: ignore[return-value]
    return "low"


def supervisor_satisfies_primary_floor(supervisor: Mapping[str, Any], agent_outputs: Mapping[str, Any]) -> bool:
    """
    Invariant: RANK(supervisor.final_risk_level) >= RANK(max(grooming, bullying, emotion)).
    Use after graph analyze, arbiters, and monitor_and_repair (compare to repaired agent_outputs).
    """
    fin = supervisor.get("final_risk_level", "low")
    if not isinstance(fin, str) or fin not in ("low", "medium", "high", "critical"):
        return False
    return _risk_rank(fin) >= _risk_rank(max_primary_safety_risk(agent_outputs))  # type: ignore[arg-type]


def apply_primary_floor_to_supervisor(
    supervisor: Dict[str, Any], agent_outputs: Mapping[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    """
    After arbiters / monitor, ensure HTTP responses never violate the primary-agent floor.
    Returns (patched_supervisor, changed).
    """
    out = dict(supervisor)
    fin = str(out.get("final_risk_level", "low"))
    if fin not in ("low", "medium", "high", "critical"):
        fin = "low"
        out["final_risk_level"] = fin
    max_p = max_primary_safety_risk(agent_outputs)
    if _risk_rank(max_p) <= _risk_rank(fin):  # type: ignore[arg-type]
        return out, False
    prior = fin
    out["final_risk_level"] = max_p  # type: ignore[assignment]
    out["final_confidence"] = max(
        float(out.get("final_confidence", 0.0)),
        float(PRIMARY_FLOOR_CONF.get(max_p, 0.75)),  # type: ignore[arg-type]
    )
    exp = out.setdefault("explainability", {})
    if isinstance(exp, dict):
        nexp = dict(exp)
        nexp["pipeline_primary_floor"] = {"prior_level": prior, "raised_to": max_p}
        out["explainability"] = nexp
    if max_p in ("high", "critical"):
        out["recommended_actions"] = [
            "Notify parent/guardian with privacy-safe summary",
            "Suggest child to stop conversation and block/report user",
            "Escalate to admin review if repeated incidents",
        ]
    elif max_p == "medium":
        out["recommended_actions"] = [
            "Recommend safety checklist",
            "Monitor follow-up messages for escalation",
        ]
    return out, True


def _aggregate_supervisor(agent_outputs: Dict[str, Dict[str, Any]], *, chat_text: str = "") -> Dict[str, Any]:
    # Weighted max + consistency bonus (simple, explainable)
    weights = {
        "grooming": 1.2,
        "bullying": 1.1,
        "cross_platform": 0.8,
        "emotion": 0.7,
        "fake_profile": 0.6,
        "fraud": 0.9,
        "wearable_signal": 0.6,
        "regional_language": 0.2,
        "evidence_log": 0.3,
        "education": 0.1,
    }
    score = 0.0
    contributors: List[Dict[str, Any]] = []
    for name, out in agent_outputs.items():
        lvl = out["risk_level"]
        conf = float(out["confidence"])
        w = float(weights.get(name, 1.0))
        s = (_risk_rank(lvl) / 3.0) * conf * w
        score += s
        if _risk_rank(lvl) >= 1:
            contributors.append({"agent": name, "risk_level": lvl, "confidence": conf, "flags": out.get("flags", [])})

    # Normalize to 0..1-ish (cap)
    norm = min(1.0, score / 2.5)
    if norm >= 0.85:
        final = "critical"
    elif norm >= 0.6:
        final = "high"
    elif norm >= 0.35:
        final = "medium"
    else:
        final = "low"

    contributors_sorted = sorted(contributors, key=lambda c: (_risk_rank(c["risk_level"]), c["confidence"]), reverse=True)

    lex = lexicon_supervisor_floor(chat_text)
    if lex:
        lex_lvl, lex_conf, lex_reason, lex_flags = lex
        if _risk_rank(lex_lvl) > _risk_rank(final):
            final = lex_lvl
            norm = max(float(norm), float(lex_conf) * 0.92)
        contributors_sorted.insert(
            0,
            {
                "agent": "risk_lexicon",
                "risk_level": lex_lvl,
                "confidence": lex_conf,
                "flags": lex_flags,
                "reason": lex_reason,
            },
        )

    # Floor: core safety agents must not be drowned out by low-weight agents (prevents false "low").
    max_primary = max_primary_safety_risk(agent_outputs)
    if _risk_rank(max_primary) > _risk_rank(final):  # type: ignore[arg-type]
        final = max_primary  # type: ignore[assignment]
        norm = max(float(norm), float(PRIMARY_FLOOR_CONF.get(final, norm)))

    # Floor: scam/fraud signals should not return overall "low" when the fraud agent is confident.
    fraud_lvl = _get_agent_level(agent_outputs, "fraud")
    if _risk_rank(fraud_lvl) > _risk_rank(final):  # type: ignore[arg-type]
        final = fraud_lvl  # type: ignore[assignment]
        norm = max(float(norm), float(FRAUD_FLOOR_CONF.get(final, norm)))

    # Policy: cross-platform migration is parent-actionable even without other harms.
    # If cross_platform is medium with decent confidence, do not return overall "low".
    cp = _agent_output_as_dict(agent_outputs.get("cross_platform"))
    cp_lvl = str(cp.get("risk_level", "low"))
    cp_conf = float(cp.get("confidence", 0.0) or 0.0)
    if cp_lvl == "medium" and cp_conf >= 0.7 and _risk_rank(final) < _risk_rank("medium"):
        final = "medium"  # type: ignore[assignment]
        norm = max(float(norm), 0.55)

    top = contributors_sorted[:3]

    actions = []
    if final in {"high", "critical"}:
        actions = [
            "Notify parent/guardian with privacy-safe summary",
            "Suggest child to stop conversation and block/report user",
            "Escalate to admin review if repeated incidents",
        ]
    elif final == "medium":
        actions = ["Recommend safety checklist", "Monitor follow-up messages for escalation"]

    return {
        "final_risk_level": final,
        "final_confidence": float(norm),
        "top_contributors": top,
        "recommended_actions": actions,
        "explainability": {"contributors": contributors_sorted, "lexicon_floor": bool(lex)},
    }


async def _run_agent(agent_name: str, state: AnalysisState) -> AgentOutput:
    kwargs = {
        "chat_text": state.get("chat_text", ""),
        "platform": state.get("platform", "simulated"),
        "language_hint": state.get("language_hint", "auto"),
        "wearable": state.get("wearable", {}),
    }
    if agent_name == "bullying":
        return await bullying_agent.run(**kwargs)
    if agent_name == "grooming":
        return await grooming_agent.run(**kwargs)
    if agent_name == "emotion":
        return await emotion_agent.run(**kwargs)
    if agent_name == "cross_platform":
        return await cross_platform_agent.run(**kwargs)
    if agent_name == "regional_language":
        return await regional_language_agent.run(**kwargs)
    if agent_name == "fake_profile":
        return await fake_profile_agent.run(**kwargs)
    if agent_name == "fraud":
        return await fraud_agent.run(**kwargs)
    if agent_name == "wearable_signal":
        return await wearable_signal_agent.run(**kwargs)
    if agent_name == "evidence_log":
        return await evidence_log_agent.run(**kwargs)
    if agent_name == "education":
        return await education_agent.run(**kwargs)
    raise ValueError(f"unknown agent: {agent_name}")


def build_graph():
    g = StateGraph(AnalysisState)

    async def run_all_agents(state: AnalysisState) -> AnalysisState:
        outputs: Dict[str, Dict[str, Any]] = {}
        for name in AGENT_ORDER:
            t0 = time.time()
            try:
                out = await _run_agent(name, state)
                outputs[name] = out.to_json()
                outputs[name]["meta"]["latency_ms"] = int((time.time() - t0) * 1000)
                outputs[name]["meta"]["status"] = "ok"
            except Exception as e:
                outputs[name] = AgentOutput("low", 0.0, "Agent failed.", ["agent_error"], {"error": str(e)}).to_json()
                outputs[name]["meta"]["status"] = "error"
        state["agent_outputs"] = outputs
        return state

    async def supervisor(state: AnalysisState) -> AnalysisState:
        sup = _aggregate_supervisor(
            state.get("agent_outputs", {}),
            chat_text=state.get("chat_text", "") or "",
        )
        state["supervisor"] = sup
        return state

    async def parent_summary(state: AnalysisState) -> AnalysisState:
        out = await parent_summary_agent.run(supervisor_result=state.get("supervisor", {}))
        # keep as a pseudo-agent output for convenience
        state.setdefault("agent_outputs", {})
        state["agent_outputs"]["parent_summary"] = out.to_json()
        return state

    g.add_node("run_all_agents", run_all_agents)
    # Node names must not collide with state keys in LangGraph
    g.add_node("supervisor_node", supervisor)
    g.add_node("parent_summary_node", parent_summary)

    g.set_entry_point("run_all_agents")
    g.add_edge("run_all_agents", "supervisor_node")
    g.add_edge("supervisor_node", "parent_summary_node")
    g.add_edge("parent_summary_node", END)
    return g.compile()


GRAPH = build_graph()


async def analyze(
    chat_text: str,
    *,
    platform: str = "simulated",
    language_hint: str = "auto",
    wearable: Optional[Dict[str, Any]] = None,
    on_agent_output: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    state: AnalysisState = {
        "chat_text": chat_text,
        "platform": platform,
        "language_hint": language_hint,
        "wearable": wearable or {},
    }
    # If realtime callback is requested, run the main node manually with callbacks
    if on_agent_output:
        # run_all_agents sequentially with streaming updates
        outputs: Dict[str, Dict[str, Any]] = {}
        for name in AGENT_ORDER:
            t0 = time.time()
            try:
                out_agent = await _run_agent(name, state)
                o = out_agent.to_json()
                o.setdefault("meta", {})
                o["meta"]["latency_ms"] = int((time.time() - t0) * 1000)
                o["meta"]["status"] = "ok"
                outputs[name] = o
            except Exception as e:
                o = AgentOutput("low", 0.0, "Agent failed.", ["agent_error"], {"error": str(e)}).to_json()
                o.setdefault("meta", {})
                o["meta"]["status"] = "error"
                outputs[name] = o
            await on_agent_output(name, outputs[name])
        state["agent_outputs"] = outputs

        sup = _aggregate_supervisor(
            state.get("agent_outputs", {}),
            chat_text=state.get("chat_text", "") or "",
        )
        state["supervisor"] = sup
        await on_agent_output("supervisor", {"type": "supervisor", **sup})

        ps = await parent_summary_agent.run(supervisor_result=sup)
        state.setdefault("agent_outputs", {})
        state["agent_outputs"]["parent_summary"] = ps.to_json()
        await on_agent_output("parent_summary", state["agent_outputs"]["parent_summary"])

        return state

    out = await GRAPH.ainvoke(state)
    return out

