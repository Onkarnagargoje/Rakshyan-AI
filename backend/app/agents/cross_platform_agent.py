from __future__ import annotations

from app.agents.rules import detect_cross_platform
from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    hit, patterns = detect_cross_platform(chat_text)
    if not hit:
        return AgentOutput.low("No migration to off-platform channels detected.", confidence=0.6)
    return AgentOutput(
        "medium",
        0.7,
        "Detected attempts to move the conversation to other platforms (reduced moderation/visibility).",
        ["cross_platform_migration"],
        {"matches": patterns},
    )

