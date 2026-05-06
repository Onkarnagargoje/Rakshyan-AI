from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatAnalysis
from app.schemas.analysis import AnalyzeChatRequest, AnalyzeChatResponse, RiskReportResponse
from app.services.analysis_pipeline import execute_chat_analysis
from app.services.evidence_service import get_chain
from app.utils.auth_deps import get_optional_user
from app.utils.db import get_db

router = APIRouter()


@router.post("/analyze-chat")
async def analyze_chat(
    payload: AnalyzeChatRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
) -> AnalyzeChatResponse:
    return await execute_chat_analysis(
        db,
        user_id=(user.id if user else 1),
        chat_text=payload.chat_text,
        platform=payload.platform,
        language_hint=payload.language_hint,
        wearable=payload.wearable,
        realtime=payload.realtime,
        child_id=None,
        device_id=None,
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
