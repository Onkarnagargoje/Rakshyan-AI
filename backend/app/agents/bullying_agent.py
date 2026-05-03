from __future__ import annotations

from app.agents.rules import detect_bullying_keywords
from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    hit, patterns = detect_bullying_keywords(chat_text)
    if not hit:
        return AgentOutput.low("No strong bullying signals detected.", confidence=0.6)

    # Heuristic severity based on strongest pattern
    flags = ["bullying_language"]
    if any("kill yourself" in p for p in patterns):
        return AgentOutput("critical", 0.85, "Detected self-harm encouragement / severe bullying language.", flags, {"matches": patterns})
    return AgentOutput("high", 0.78, "Detected abusive / insulting language patterns.", flags, {"matches": patterns})

