"""Shared logic for optional LLM arbiters (Ollama, Gemini)."""

from __future__ import annotations

from typing import Any, Dict

RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}

ARBITER_PROMPT = """You are a child cyber-safety adjudicator. You receive a short message and compact JSON summaries of specialist agents.
Return ONLY JSON (no markdown): {"risk_level":"low|medium|high|critical","confidence":0.0-1.0,"reason":"one sentence"}
Rules:
- Escalate only for credible grooming, sexual coercion toward minors, violence toward self or others, severe bullying, weapons at school, or explicit exploitation.
- Prefer "low" for jokes, games, homework complaints, fiction discussion, or ambiguous slang without threat.
- If unsure between low and medium, choose medium only if there is plausible real harm."""


def max_agent_risk(agent_outputs: Dict[str, Any]) -> int:
    m = 0
    for name, o in (agent_outputs or {}).items():
        if name == "parent_summary":
            continue
        if not isinstance(o, dict):
            continue
        lvl = str(o.get("risk_level", "low")).lower()
        m = max(m, RANK.get(lvl, 0))
    return m


def should_run_arbiter(supervisor: Dict[str, Any], agent_outputs: Dict[str, Any]) -> bool:
    """Run cloud/local LLM arbiter only when supervisor is conservative but an agent disagrees."""
    sup_lvl = str(supervisor.get("final_risk_level", "low")).lower()
    if RANK.get(sup_lvl, 0) >= 2:
        return False
    return max_agent_risk(agent_outputs) >= 1


def build_arbiter_user_message(chat_text: str, supervisor: Dict[str, Any], agent_outputs: Dict[str, Any]) -> str:
    bits = []
    for name, o in list((agent_outputs or {}).items())[:12]:
        if not isinstance(o, dict) or name == "parent_summary":
            continue
        bits.append(f"{name}: level={o.get('risk_level')} conf={o.get('confidence')} flags={o.get('flags', [])[:4]}")
    return (
        f"Supervisor_out: risk={supervisor.get('final_risk_level')} conf={supervisor.get('final_confidence')}\n"
        f"Agents:\n" + "\n".join(bits) + f"\n\nMESSAGE:\n{chat_text[:4000]}"
    )
