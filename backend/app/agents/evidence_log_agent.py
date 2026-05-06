from __future__ import annotations

import re
from typing import List, Tuple

from app.agents.types import AgentOutput


def _detect_pii(text: str) -> Tuple[bool, List[str]]:
    # Lightweight, local-only heuristics (no paid APIs).
    patterns = {
        "email_address": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "phone_number": r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b",
        "home_address_hint": r"\b(my address is|i live at|street|st\.|avenue|ave\.|road|rd\.)\b",
        "school_hint": r"\b(my school|go to school at|class teacher|principal)\b",
    }
    flags: List[str] = []
    for name, pat in patterns.items():
        if re.search(pat, text, flags=re.IGNORECASE):
            flags.append(name)
    return (len(flags) > 0), flags


async def run(chat_text: str, **_) -> AgentOutput:
    """
    Evidence Log Agent (MVP):
    - Detects PII to avoid storing unnecessarily sensitive content in logs.
    - Provides metadata hints for redaction and tamper-evident capture.
    Note: actual hash-chained evidence persistence is handled server-side in EvidenceLog.
    """
    hit, pii_flags = _detect_pii(chat_text or "")
    if not hit:
        return AgentOutput(
            "low",
            0.7,
            "No obvious PII detected; safe to proceed with tamper-evident evidence logging.",
            ["evidence_logging_ok"],
            {"pii_detected": False, "recommended_redactions": []},
        )

    return AgentOutput(
        "medium",
        0.72,
        "Potential PII detected; redact before long-term retention and keep parent summaries privacy-safe.",
        ["pii_detected", "recommend_redaction"],
        {"pii_detected": True, "recommended_redactions": pii_flags},
    )

