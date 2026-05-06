from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatAnalysis, ParentAlert
from app.schemas.analysis import AnalyzeChatResponse
from app.agents import parent_summary_agent
from app.services.analyzer_graph import analyze as graph_analyze, apply_primary_floor_to_supervisor
from app.services.evidence_service import append_event
from app.services.meta_agent_monitor import monitor_and_repair
from app.services.gemini_arbiter import maybe_gemini_arbiter
from app.services.ollama_arbiter import maybe_ollama_arbiter
from app.services.realtime_emitter import emit_to_analysis
from app.services.push_notifications import send_parent_alert_push


async def execute_chat_analysis(
    db: AsyncSession,
    *,
    user_id: int,
    chat_text: str,
    platform: str = "simulated",
    language_hint: str = "auto",
    wearable: dict | None = None,
    realtime: bool = False,
    child_id: int | None = None,
    device_id: int | None = None,
) -> AnalyzeChatResponse:
    """Run LangGraph + meta monitor, persist ChatAnalysis and evidence events."""
    row = ChatAnalysis(
        user_id=user_id,
        child_id=child_id,
        device_id=device_id,
        platform=platform,
        language_hint=language_hint,
        chat_text=chat_text,
        final_risk_level="low",
        final_confidence=0,
        supervisor_output={},
        agent_outputs={},
        meta_diagnostics={},
    )
    db.add(row)
    await db.flush()

    await append_event(db, analysis_id=row.id, event_type="analysis_started", payload={"platform": platform, "child_id": child_id})

    async def _rt(agent_name: str, output: dict):
        if realtime:
            await emit_to_analysis(row.id, "analysis:agent", {"analysis_id": row.id, "agent": agent_name, "output": output})

    state = await graph_analyze(
        chat_text,
        platform=platform,
        language_hint=language_hint,
        wearable=wearable or {},
        on_agent_output=_rt if realtime else None,
    )

    sup0 = state.get("supervisor") or {}
    adj = await maybe_ollama_arbiter(chat_text, supervisor=sup0, agent_outputs=state.get("agent_outputs", {}))
    if adj:
        state["supervisor"] = adj

    sup1 = state.get("supervisor") or {}
    adj_g = await maybe_gemini_arbiter(chat_text, supervisor=sup1, agent_outputs=state.get("agent_outputs", {}))
    if adj_g:
        state["supervisor"] = adj_g

    repaired_outputs, diagnostics = await monitor_and_repair(state, max_retries=1)
    supervisor = state.get("supervisor", {})
    agents = repaired_outputs

    supervisor, floor_patched = apply_primary_floor_to_supervisor(supervisor, agents)
    if floor_patched:
        ps = await parent_summary_agent.run(supervisor_result=supervisor)
        agents = dict(agents)
        agents["parent_summary"] = ps.to_json()

    if realtime:
        await emit_to_analysis(row.id, "analysis:meta", {"analysis_id": row.id, "meta": diagnostics})

    await append_event(
        db,
        analysis_id=row.id,
        event_type="analysis_completed",
        payload={"final_risk_level": supervisor.get("final_risk_level"), "final_confidence": supervisor.get("final_confidence")},
    )

    row.agent_outputs = agents
    row.supervisor_output = supervisor
    row.meta_diagnostics = diagnostics
    row.final_risk_level = supervisor.get("final_risk_level", "low")
    row.final_confidence = int(float(supervisor.get("final_confidence", 0.0)) * 1000)

    parent_summary = (agents.get("parent_summary", {}).get("meta", {}) or {}).get("summary")
    if realtime:
        await emit_to_analysis(
            row.id,
            "analysis:final",
            {"analysis_id": row.id, "final_risk_level": row.final_risk_level, "final_confidence": float(supervisor.get("final_confidence", 0.0))},
        )

    await db.commit()
    await db.refresh(row)

    return AnalyzeChatResponse(
        analysis_id=row.id,
        final_risk_level=row.final_risk_level,  # type: ignore[arg-type]
        final_confidence=float(supervisor.get("final_confidence", 0.0)),
        supervisor=supervisor,
        agents=agents,
        meta=diagnostics,
        parent_summary=parent_summary.get("high_level") if isinstance(parent_summary, dict) else None,
    )


async def maybe_create_parent_alert(
    db: AsyncSession,
    *,
    parent_id: int,
    child_id: int,
    analysis_id: int,
    final_risk_level: str,
    summary: str,
) -> None:
    """Create a parent-facing alert when risk is elevated."""
    if final_risk_level not in {"medium", "high", "critical"}:
        return
    title = {"medium": "Safety check needed", "high": "Safety alert", "critical": "Urgent safety alert"}.get(
        final_risk_level, "Safety alert"
    )
    row = ParentAlert(
        parent_id=parent_id,
        child_id=child_id,
        analysis_id=analysis_id,
        risk_level=final_risk_level,
        title=title,
        summary=summary[:8000],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    # Best-effort push; do not fail ingestion if push is misconfigured.
    try:
        await send_parent_alert_push(db, alert=row)
    except Exception:
        pass
