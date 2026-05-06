"""
Optional Google Gemini adjudicator (paid API) for borderline cases.

Enable with ENABLE_GEMINI=1 and GEMINI_API_KEY in .env. Runs after local agents
and the Ollama arbiter (if any); only raises risk, never lowers it.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from app.services.arbiter_common import ARBITER_PROMPT, RANK, build_arbiter_user_message, should_run_arbiter
from app.services.ollama_client import extract_json_object
from app.utils.settings import settings

logger = logging.getLogger(__name__)


async def maybe_gemini_arbiter(
    chat_text: str,
    *,
    supervisor: Dict[str, Any],
    agent_outputs: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not settings.enable_gemini:
        return None
    key = (settings.gemini_api_key or "").strip()
    if not key:
        return None
    if not should_run_arbiter(supervisor, agent_outputs):
        return None

    sup_lvl = str(supervisor.get("final_risk_level", "low")).lower()
    user_block = build_arbiter_user_message(chat_text, supervisor, agent_outputs)
    full_prompt = f"{ARBITER_PROMPT}\n\n{user_block}"

    try:
        import google.generativeai as genai  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("google-generativeai not installed; pip install google-generativeai")
        return None

    genai.configure(api_key=key)
    model = genai.GenerativeModel(settings.gemini_model)

    def _call() -> str:
        try:
            from google.generativeai.types import GenerationConfig

            gc = GenerationConfig(temperature=0.1, max_output_tokens=512)
        except Exception:
            gc = {"temperature": 0.1, "max_output_tokens": 512}
        resp = model.generate_content(full_prompt, generation_config=gc)
        return (getattr(resp, "text", None) or "").strip()

    try:
        raw = await asyncio.to_thread(_call)
    except Exception as e:
        logger.warning("Gemini arbiter failed: %s", e)
        return None

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
        reason = str(data.get("reason", "Gemini arbiter review."))[:500]
    except (TypeError, ValueError):
        return None

    if RANK[lvl] <= RANK.get(sup_lvl, 0):
        return None

    out = dict(supervisor)
    out["final_risk_level"] = lvl
    out["final_confidence"] = max(float(supervisor.get("final_confidence", 0.0)), conf * 0.95)
    out.setdefault("explainability", {})
    if isinstance(out["explainability"], dict):
        out["explainability"]["gemini_arbiter"] = {"reason": reason, "prior_level": sup_lvl, "model": settings.gemini_model}
    logger.info("Gemini arbiter raised risk: %s -> %s", sup_lvl, lvl)
    return out
