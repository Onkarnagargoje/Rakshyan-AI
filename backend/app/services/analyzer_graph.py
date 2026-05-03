from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

from app.agents import (
    bullying_agent,
    grooming_agent,
    emotion_agent,
    cross_platform_agent,
    regional_language_agent,
    fake_profile_agent,
    wearable_signal_agent,
    education_agent,
    parent_summary_agent,
)
from app.agents.types import AgentOutput, RiskLevel


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
    "wearable_signal",
    "education",
]


def _risk_rank(level: RiskLevel) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}[level]


def _aggregate_supervisor(agent_outputs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    # Weighted max + consistency bonus (simple, explainable)
    weights = {
        "grooming": 1.2,
        "bullying": 1.1,
        "cross_platform": 0.8,
        "emotion": 0.7,
        "fake_profile": 0.6,
        "wearable_signal": 0.6,
        "regional_language": 0.2,
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
        "explainability": {"contributors": contributors_sorted},
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
    if agent_name == "wearable_signal":
        return await wearable_signal_agent.run(**kwargs)
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
        sup = _aggregate_supervisor(state.get("agent_outputs", {}))
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

        sup = _aggregate_supervisor(state.get("agent_outputs", {}))
        state["supervisor"] = sup
        await on_agent_output("supervisor", {"type": "supervisor", **sup})

        ps = await parent_summary_agent.run(supervisor_result=sup)
        state.setdefault("agent_outputs", {})
        state["agent_outputs"]["parent_summary"] = ps.to_json()
        await on_agent_output("parent_summary", state["agent_outputs"]["parent_summary"])

        return state

    out = await GRAPH.ainvoke(state)
    return out

