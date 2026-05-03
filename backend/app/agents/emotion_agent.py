from __future__ import annotations

import re

from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    # MVP heuristic (HF model can be plugged in later)
    stress = bool(re.search(r"\b(scared|afraid|panic|anxious|stressed|worried)\b", chat_text, flags=re.I))
    sadness = bool(re.search(r"\b(sad|crying|depressed|hurt)\b", chat_text, flags=re.I))
    anger = bool(re.search(r"\b(angry|furious|rage|mad)\b", chat_text, flags=re.I))

    flags = []
    if stress:
        flags.append("fear_stress")
    if sadness:
        flags.append("sadness")
    if anger:
        flags.append("anger")

    if not flags:
        return AgentOutput.low("No strong negative emotion markers detected.", confidence=0.55)

    level = "medium"
    conf = 0.66
    if stress and sadness:
        level, conf = "high", 0.74

    return AgentOutput(level, conf, "Detected emotional distress indicators that may correlate with risk.", ["emotion_distress"] + flags, {})

