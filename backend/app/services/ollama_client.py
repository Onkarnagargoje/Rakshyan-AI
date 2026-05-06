from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

import httpx

from app.utils.settings import settings

logger = logging.getLogger(__name__)

_MAX_CHAT_CHARS = 6000


async def ollama_chat(
    *,
    system: str,
    user: str,
    temperature: float = 0.1,
) -> Optional[str]:
    """
    Call local Ollama /api/chat. Returns assistant message content or None on failure.
    """
    if not settings.enable_ollama:
        return None
    base = settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/chat"
    payload: Dict[str, Any] = {
        "model": settings.ollama_model,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user[:_MAX_CHAT_CHARS]},
        ],
    }
    timeout = getattr(settings, "ollama_timeout_sec", 60)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            msg = (data.get("message") or {}).get("content")
            if isinstance(msg, str) and msg.strip():
                return msg.strip()
    except httpx.HTTPStatusError as e:
        logger.warning("Ollama HTTP error: %s", e)
    except Exception as e:
        logger.warning("Ollama request failed: %s", e)
    return None


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort parse of first JSON object from model output."""
    if not text:
        return None
    t = text.strip()
    # Strip markdown fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", t)
    if fence:
        t = fence.group(1).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", t)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None
