from __future__ import annotations

from app.agents.types import AgentOutput


async def run(supervisor_result: dict | None = None, **_) -> AgentOutput:
    # Must NOT expose raw chat. Provide a high-level, privacy-safe summary.
    supervisor_result = supervisor_result or {}
    level = supervisor_result.get("final_risk_level", "low")
    contributors = supervisor_result.get("top_contributors", [])
    actions = supervisor_result.get("recommended_actions", [])

    reason = "Generated privacy-safe summary for parent dashboard."
    if level in {"high", "critical"}:
        high_level = "Potential safety concern detected."
    elif level == "medium":
        high_level = "Elevated risk — parent review recommended."
    else:
        high_level = "No significant safety concerns detected."

    summary = {
        "risk_level": level,
        "high_level": high_level,
        "contributors": contributors,
        "recommended_actions": actions,
        "note": "Raw chat is not shown to parents by design.",
    }

    return AgentOutput("low", 0.85, reason, ["parent_summary_ready"], {"summary": summary})

