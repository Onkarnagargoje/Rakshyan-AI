from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatAnalysis
from app.schemas.analysis import AnalyzeChatRequest, AnalyzeChatResponse, RiskReportResponse
from app.services.analyzer_graph import analyze as graph_analyze
from app.services.evidence_service import append_event, get_chain
from app.services.meta_agent_monitor import monitor_and_repair
from app.services.realtime_emitter import emit_to_analysis
from app.utils.db import get_db

router = APIRouter()


@router.post("/analyze-chat")
async def analyze_chat(payload: AnalyzeChatRequest, db: AsyncSession = Depends(get_db)) -> AnalyzeChatResponse:
    # Create a new analysis row first (so UI can subscribe by analysis_id)
    row = ChatAnalysis(
        user_id=1,  # MVP: replace with JWT user
        platform=payload.platform,
        language_hint=payload.language_hint,
        chat_text=payload.chat_text,
        final_risk_level="low",
        final_confidence=0,
        supervisor_output={},
        agent_outputs={},
        meta_diagnostics={},
    )
    db.add(row)
    await db.flush()

    await append_event(db, analysis_id=row.id, event_type="analysis_started", payload={"platform": payload.platform})

    async def _rt(agent_name: str, output: dict):
        if payload.realtime:
            await emit_to_analysis(row.id, "analysis:agent", {"analysis_id": row.id, "agent": agent_name, "output": output})

    state = await graph_analyze(
        payload.chat_text,
        platform=payload.platform,
        language_hint=payload.language_hint,
        wearable=payload.wearable or {},
        on_agent_output=_rt if payload.realtime else None,
    )

    repaired_outputs, diagnostics = await monitor_and_repair(state, max_retries=1)
    supervisor = state.get("supervisor", {})
    agents = repaired_outputs

    if payload.realtime:
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
    await db.commit()

    parent_summary = (agents.get("parent_summary", {}).get("meta", {}) or {}).get("summary")
    if payload.realtime:
        await emit_to_analysis(
            row.id,
            "analysis:final",
            {"analysis_id": row.id, "final_risk_level": row.final_risk_level, "final_confidence": float(supervisor.get("final_confidence", 0.0))},
        )
    return AnalyzeChatResponse(
        analysis_id=row.id,
        final_risk_level=row.final_risk_level,  # type: ignore[arg-type]
        final_confidence=float(supervisor.get("final_confidence", 0.0)),
        supervisor=supervisor,
        agents=agents,  # pydantic will validate into AgentResult
        meta=diagnostics,
        parent_summary=parent_summary.get("high_level") if isinstance(parent_summary, dict) else None,
    )


@router.get("/get-risk-report/{analysis_id}")
async def get_risk_report(analysis_id: int, db: AsyncSession = Depends(get_db)) -> RiskReportResponse:
    row = await db.scalar(select(ChatAnalysis).where(ChatAnalysis.id == analysis_id))
    if not row:
        raise HTTPException(status_code=404, detail="analysis not found")
    chain = await get_chain(db, analysis_id=analysis_id)
    return RiskReportResponse(
        analysis_id=row.id,
        final_risk_level=row.final_risk_level,  # type: ignore[arg-type]
        final_confidence=float(row.final_confidence / 1000.0),
        created_at=str(row.created_at),
        supervisor=row.supervisor_output or {},
        agents=row.agent_outputs or {},
        meta=row.meta_diagnostics or {},
        evidence_chain=chain,
    )

