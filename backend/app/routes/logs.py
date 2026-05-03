from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.evidence_service import list_logs
from app.utils.db import get_db

router = APIRouter()


@router.get("/logs")
async def get_logs(
    analysis_id: int | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    items = await list_logs(db, analysis_id=analysis_id, limit=limit)
    return {"items": items}

