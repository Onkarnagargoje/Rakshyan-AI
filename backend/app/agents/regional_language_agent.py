from __future__ import annotations

import re

from app.agents.types import AgentOutput


async def run(chat_text: str, language_hint: str = "auto", **_) -> AgentOutput:
    # MVP: detect Hinglish/Hindi/Marathi presence; later: IndicBERT/MuRIL classifier.
    devanagari = bool(re.search(r"[\u0900-\u097F]", chat_text))
    common_hinglish = bool(re.search(r"\b(yaar|bhai|behen|matlab|kya|kyu|nahi|haan)\b", chat_text, flags=re.I))

    if not devanagari and not common_hinglish and language_hint in {"en", "english"}:
        return AgentOutput.low("No regional language handling needed for this message.", confidence=0.6)

    return AgentOutput(
        "low",
        0.6,
        "Detected potential Hinglish/Hindi/Marathi content; routing through regional-language-aware processing.",
        ["regional_language_detected"],
        {"devanagari": devanagari, "hinglish_markers": common_hinglish, "language_hint": language_hint},
    )

