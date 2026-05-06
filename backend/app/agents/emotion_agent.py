from __future__ import annotations

import re

from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    t = chat_text or ""

    # Crisis language (prioritize)
    suicide = bool(
        re.search(
            r"\b(kill|end)\s+(myself|my\s+self|it\s+all|my\s+life)\b|"
            r"\bend\s+it\b|"
            r"\b(suicide|suicidal)\b|"
            r"\b(want|wanna)\s+to\s+die\b|"
            r"\b(better\s+off\s+dead|no\s+reason\s+to\s+live)\b|"
            r"\b(can'?t\s+go\s+on(\s+anymore)?|tired\s+of\s+living)\b|"
            r"\b(can'?t\s+do\s+this\s+anymore)\b|"
            r"\b(goodbye|cya)\s+forever\b",
            t,
            flags=re.I,
        )
    )
    self_harm = bool(
        re.search(
            r"\b(cut|burn|hurt)\s+(myself|my\s+wrist|my\s+arm|my\s+thigh)\b|"
            r"\bself[- ]?harm\b|"
            r"\brelapse\b.*\b(cut|hurt)\b",
            t,
            flags=re.I,
        )
    )

    stress = bool(re.search(r"\b(scared|afraid|panic|anxious|stressed|worried|terrified)\b", t, flags=re.I))
    sadness = bool(re.search(r"\b(sad|crying|depressed|hopeless|empty|numb|hurt)\b", t, flags=re.I))
    anger = bool(re.search(r"\b(angry|furious|rage|mad|hate\s+everyone)\b", t, flags=re.I))

    if suicide or self_harm:
        return AgentOutput(
            "critical",
            0.9,
            "Detected possible self-harm or suicidal ideation language; prioritize supportive intervention and safety resources.",
            ["crisis_language", "self_harm_or_suicide_hint"],
            {"suicide_markers": suicide, "self_harm_markers": self_harm},
        )

    flags: list[str] = []
    if stress:
        flags.append("fear_stress")
    if sadness:
        flags.append("sadness")
    if anger:
        flags.append("anger")

    if not flags:
        return AgentOutput.low("No strong negative emotion or crisis markers detected.", confidence=0.58)

    level = "medium"
    conf = 0.68
    if stress and sadness:
        level, conf = "high", 0.76

    return AgentOutput(
        level,
        conf,
        "Detected emotional distress indicators that may correlate with online risk or need for support.",
        ["emotion_distress"] + flags,
        {},
    )
