from __future__ import annotations

from app.agents.types import AgentOutput


async def run(wearable: dict | None = None, **_) -> AgentOutput:
    # Mock wearable inputs: {"heart_rate": int, "stress_score": float}
    wearable = wearable or {}
    hr = wearable.get("heart_rate")
    stress = wearable.get("stress_score")

    if hr is None and stress is None:
        return AgentOutput.low("No wearable signals provided.", confidence=0.5, flags=["wearable_missing"])

    flags: list[str] = []
    level = "low"
    conf = 0.6
    reason = "Wearable signals appear within normal bounds."

    if isinstance(hr, (int, float)) and hr >= 120:
        flags.append("high_heart_rate")
        level, conf = "medium", 0.7
        reason = "Elevated heart rate may indicate stress during interaction."

    if isinstance(stress, (int, float)) and stress >= 0.8:
        flags.append("high_stress_score")
        level, conf = "high", 0.78
        reason = "High stress score anomaly detected."

    return AgentOutput(level, conf, reason, ["wearable_anomaly"] + flags if flags else ["wearable_ok"], {"wearable": wearable})

