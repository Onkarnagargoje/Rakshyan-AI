"""
Optional second-pass: local Ollama reconciles borderline cases when the
weighted supervisor is conservative but at least one specialist agent fired medium+.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.services.arbiter_common import ARBITER_PROMPT, RANK, build_arbiter_user_message, should_run_arbiter
from app.services.ollama_client import extract_json_object, ollama_chat
from app.utils.settings import settings

logger = logging.getLogger(__name__)


async def maybe_ollama_arbiter(
    chat_text: str,
    *,
    supervisor: Dict[str, Any],
    agent_outputs: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not settings.enable_ollama:
        return None
    if not should_run_arbiter(supervisor, agent_outputs):
        return None

    sup_lvl = str(supervisor.get("final_risk_level", "low")).lower()
    user = build_arbiter_user_message(chat_text, supervisor, agent_outputs)
    raw = await ollama_chat(system=ARBITER_PROMPT, user=user, temperature=0.08)
    if not raw:
        return None
    data = extract_json_object(raw)
    if not data:
        return None
    try:
        lvl = str(data.get("risk_level", "low")).lower()
        if lvl not in ("low", "medium", "high", "critical"):
            return None
        conf = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        reason = str(data.get("reason", "Ollama arbiter review."))[:500]
    except (TypeError, ValueError):
        return None

    if RANK[lvl] <= RANK.get(sup_lvl, 0):
        return None

    out = dict(supervisor)
    out["final_risk_level"] = lvl
    out["final_confidence"] = max(float(supervisor.get("final_confidence", 0.0)), conf * 0.95)
    out.setdefault("explainability", {})
    if isinstance(out["explainability"], dict):
        out["explainability"]["ollama_arbiter"] = {"reason": reason, "prior_level": sup_lvl}
    logger.info("Ollama arbiter raised risk: %s -> %s", sup_lvl, lvl)
    return out
