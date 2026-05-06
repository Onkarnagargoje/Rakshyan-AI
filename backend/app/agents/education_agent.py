from __future__ import annotations



from app.agents.rules import detect_deepfake_media_trap, detect_financial_scam_coercion

from app.agents.types import AgentOutput





async def run(chat_text: str, **_) -> AgentOutput:

    # Education recommendations are derived from detected themes (placeholder until quiz DB exists).

    topics: list[str] = []

    lower = (chat_text or "").lower()

    if any(k in lower for k in ["secret", "don't tell", "meet up", "send pic"]):

        topics.append("Grooming awareness: secrets & boundaries")

    if any(k in lower for k in ["whatsapp", "telegram", "discord", "snap"]):

        topics.append("Safe communication: staying on-platform")

    if any(k in lower for k in ["idiot", "ugly", "go die", "loser"]):

        topics.append("Bullying response: block/report and get help")



    if detect_financial_scam_coercion(chat_text)[0]:

        topics.append("Scams & money pressure: never share gift-card codes, card numbers, or wire/crypto under threat")

    if detect_deepfake_media_trap(chat_text)[0]:

        topics.append("Deepfakes & face traps: verify callers, avoid nudify apps, and be cautious with face-only video asks")



    if not topics:

        topics = ["General cyber safety basics (privacy, blocking, reporting)"]



    return AgentOutput(

        "low",

        0.8,

        "Generated recommended safety learning content based on conversation themes.",

        ["education_recommendation"],

        {"topics": topics},

    )

