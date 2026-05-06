from __future__ import annotations

from app.agents.rules import (
    detect_cross_platform,
    detect_deepfake_media_trap,
    detect_fake_profile_rules,
    detect_financial_scam_coercion,
)
from app.agents.types import AgentOutput


async def run(chat_text: str, **_) -> AgentOutput:
    fake_hit, fake_p = detect_fake_profile_rules(chat_text)
    scam_hit, scam_p = detect_financial_scam_coercion(chat_text)
    deep_hit, deep_p = detect_deepfake_media_trap(chat_text)
    xplat_hit, _ = detect_cross_platform(chat_text)

    if not (fake_hit or scam_hit or deep_hit):
        return AgentOutput.low(
            "No clear fake-profile, scam, or synthetic-media trap indicators detected.",
            confidence=0.55,
        )

    flags: list[str] = ["fake_profile_suspected"]
    if scam_hit:
        flags.append("financial_scam_coercion")
    if deep_hit:
        flags.append("deepfake_media_trap")
    if scam_hit and xplat_hit:
        flags.append("off_platform_financial_lure")

    merged: list[str] = []
    for p in fake_p + scam_p + deep_p:
        if p not in merged:
            merged.append(p)

    conf = 0.68
    if deep_hit:
        conf = max(conf, 0.76)
    if scam_hit:
        conf = max(conf, 0.74)

    parts: list[str] = []
    if fake_hit:
        parts.append("suspicious account behavior")
    if scam_hit:
        parts.append("financial or gift-card pressure")
    if deep_hit:
        parts.append("deepfake / face-for-video trap language")
    reason = "Detected " + ", ".join(parts) + " patterns worth parent review."

    return AgentOutput(
        "medium",
        conf,
        reason,
        flags,
        {"matches": merged},
    )
