from __future__ import annotations

from app.agents.rules import detect_grooming_rules
from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    hit, patterns = detect_grooming_rules(chat_text)
    if not hit:
        return AgentOutput.low("No strong grooming patterns detected.", confidence=0.55)

    flags = ["grooming_pattern"]
    # Escalate if secrecy or meeting request exists
    if any("secret" in p or "don't tell" in p for p in patterns):
        return AgentOutput("critical", 0.82, "Detected secrecy/manipulation language commonly used in grooming.", flags, {"matches": patterns})
    if any("meet" in p for p in patterns):
        return AgentOutput("high", 0.78, "Detected attempted escalation to offline meeting.", flags, {"matches": patterns})
    return AgentOutput("high", 0.72, "Detected trust-building / boundary-testing patterns.", flags, {"matches": patterns})

