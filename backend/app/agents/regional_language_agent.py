from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, cast

from app.agents.types import AgentOutput, RiskLevel
from app.services.ollama_client import extract_json_object, ollama_chat
from app.utils.settings import settings


def _heuristic_scan(chat_text: str, language_hint: str) -> Dict[str, Any]:
    devanagari = bool(re.search(r"[\u0900-\u097F]", chat_text))
    common_hinglish = bool(
        re.search(r"\b(yaar|bhai|behen|matlab|kya|kyu|nahi|haan|chal|acha|theek|pagal|uth|mar)\b", chat_text, flags=re.I)
    )
    urdu_arabic = bool(re.search(r"[\u0600-\u06FF]", chat_text))
    non_latin_ratio = _non_latin_ratio(chat_text)
    needs_llm = (
        devanagari
        or common_hinglish
        or urdu_arabic
        or non_latin_ratio > 0.08
        or (language_hint not in {"", "auto", "en", "english"})
    )
    return {
        "devanagari": devanagari,
        "hinglish_markers": common_hinglish,
        "urdu_script": urdu_arabic,
        "non_latin_ratio": non_latin_ratio,
        "language_hint": language_hint,
        "needs_llm": needs_llm,
    }


# Romanized Hindi / Hinglish secrecy or parental concealment (when Ollama is off).
_ROMAN_HINDI_GROOMING = re.compile(
    r"\b(mummy|papa|maa|baap|mummy\s+papa|parents)\s+ko\s+mat\s+(batana|batao|bata)\b|"
    r"\bmat\s+(batana|batao)\b.{0,80}\b(mummy|papa|parents)\b|"
    r"\b(sirf|sirf)\s+(hum|hum\s+dono).{0,50}\b(secret|raaz|private)\b",
    re.I,
)


def _non_latin_ratio(text: str) -> float:
    if not text.strip():
        return 0.0
    non = sum(1 for c in text if ord(c) > 127 and not c.isspace())
    return non / max(1, len(text))


_REGIONAL_SYSTEM = """You are a multilingual child-safety language analyst for code-switching chats (e.g. Hinglish, Tanglish, Urdu+English, Arabic+English, Spanish+English).
Tasks:
1) List detected languages using BCP-47 style tags (e.g. en, hi-Latn, hi-Deva, ta-Taml, ur-Arab).
2) Say if the speaker mixes languages (code-switching) in one message or thread snippet.
3) Note if slang, romanization, or transliteration could hide bullying, threats, sexual grooming, or self-harm — especially across languages.
4) Output ONLY valid JSON (no markdown, no prose) with this exact shape:
{"languages":["en"],"code_switching":false,"risk_level":"low","confidence":0.0,"reason":"","flags":[]}
risk_level must be one of: low, medium, high, critical.
confidence is 0.0 to 1.0.
flags: short snake_case strings (e.g. hinglish_grooming_hint, mixed_script_threat)."""


async def _ollama_multilingual_analysis(chat_text: str, heuristics: Dict[str, Any]) -> Optional[AgentOutput]:
    user = (
        "Analyze this message for languages, code-switching, and safety-relevant phrasing.\n"
        f"Heuristic hints (may be incomplete): {heuristics}\n\n"
        f"MESSAGE:\n{chat_text}"
    )
    raw = await ollama_chat(system=_REGIONAL_SYSTEM, user=user, temperature=0.15)
    if not raw:
        return None
    data = extract_json_object(raw)
    if not data:
        return None
    try:
        lvl = str(data.get("risk_level", "low")).lower()
        if lvl not in ("low", "medium", "high", "critical"):
            lvl = "low"
        conf = float(data.get("confidence", 0.55))
        conf = max(0.0, min(1.0, conf))
        reason = str(data.get("reason") or "Multilingual analysis (Ollama).").strip() or "Multilingual analysis."
        flags_raw = data.get("flags", [])
        flags: List[str] = [str(f) for f in flags_raw] if isinstance(flags_raw, list) else ["multilingual_review"]
        langs = data.get("languages", [])
        lang_list = [str(x) for x in langs] if isinstance(langs, list) else []
        meta: Dict[str, Any] = {
            "languages": lang_list[:12],
            "code_switching": bool(data.get("code_switching", False)),
            "ollama": True,
            "heuristics": heuristics,
        }
        return AgentOutput(cast(RiskLevel, lvl), conf, reason, flags[:12], meta)
    except (TypeError, ValueError):
        return None


async def run(chat_text: str, language_hint: str = "auto", **_) -> AgentOutput:
    """
    Regional / multilingual agent: heuristics + optional Ollama for code-switching
    and low-resource phrasing (Hinglish, mixed script, etc.).
    """
    heuristics = _heuristic_scan(chat_text or "", language_hint or "auto")

    if settings.enable_ollama and heuristics["needs_llm"]:
        ollama_out = await _ollama_multilingual_analysis(chat_text, heuristics)
        if ollama_out is not None:
            return ollama_out

    if _ROMAN_HINDI_GROOMING.search(chat_text or ""):
        return AgentOutput(
            "medium",
            0.64,
            "Romanized Hindi/Hinglish suggests secret-keeping or parental concealment; enable Ollama (ENABLE_OLLAMA=1) for deeper multilingual adjudication.",
            ["hinglish_grooming_heuristic"],
            {**heuristics, "ollama": False},
        )

    if not heuristics["needs_llm"] and (language_hint or "auto").lower() in {"en", "english"}:
        return AgentOutput.low(
            "No strong multilingual or code-switching signals; English-only heuristic.",
            confidence=0.62,
            flags=[],
            meta={**heuristics, "ollama": False},
        )

    return AgentOutput(
        "low",
        0.58,
        "Detected regional / mixed-language or code-switching patterns; heuristic pass (enable Ollama for deeper analysis).",
        ["regional_language_detected", "code_switching_possible"],
        {**heuristics, "ollama": False},
    )
