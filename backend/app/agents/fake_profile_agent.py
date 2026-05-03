from __future__ import annotations

from app.agents.rules import detect_fake_profile_rules
from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    hit, patterns = detect_fake_profile_rules(chat_text)
    if not hit:
        return AgentOutput.low("No clear fake-profile indicators detected.", confidence=0.55)
    return AgentOutput(
        "medium",
        0.68,
        "Detected suspicious account behavior patterns often associated with fake profiles.",
        ["fake_profile_suspected"],
        {"matches": patterns},
    )

