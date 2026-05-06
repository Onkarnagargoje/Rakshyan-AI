from __future__ import annotations

from app.agents.rules import detect_scam_fraud
from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    hit, patterns, tier = detect_scam_fraud(chat_text)
    if not hit:
        return AgentOutput.low("No clear scam/fraud indicators detected.", confidence=0.6)

    if tier == "high":
        return AgentOutput(
            "high",
            0.82,
            "Detected likely scam/fraud targeting the child (money/crypto/OTP coercion or doubling claims).",
            ["scam_fraud", "financial_coercion"],
            {"matches": patterns, "tier": tier},
        )

    return AgentOutput(
        "medium",
        0.72,
        "Detected scam/fraud lure language (free currency, suspicious links, account reset/trade scams).",
        ["scam_fraud"],
        {"matches": patterns, "tier": tier},
    )

