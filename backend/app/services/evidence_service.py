from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EvidenceLog
from app.utils.logging import build_chain_entry


GENESIS_HASH = "0" * 64


async def append_event(
    db: AsyncSession,
    *,
    analysis_id: int,
    event_type: str,
    payload: Dict[str, Any],
) -> EvidenceLog:
    prev = await db.scalar(
        select(EvidenceLog).where(EvidenceLog.analysis_id == analysis_id).order_by(EvidenceLog.id.desc()).limit(1)
    )
    prev_hash = prev.hash if prev else GENESIS_HASH

    entry = build_chain_entry(prev_hash=prev_hash, event_type=event_type, payload=payload)
    row = EvidenceLog(
        analysis_id=analysis_id,
        ts_ms=entry.ts_ms,
        event_type=entry.event_type,
        payload=entry.payload,
        prev_hash=entry.prev_hash,
        hash=entry.hash,
    )
    db.add(row)
    await db.flush()
    return row


async def get_chain(db: AsyncSession, *, analysis_id: int, limit: int = 500) -> List[Dict[str, Any]]:
    rows = (
        await db.execute(
            select(EvidenceLog)
            .where(EvidenceLog.analysis_id == analysis_id)
            .order_by(EvidenceLog.id.asc())
            .limit(limit)
        )
    ).scalars()
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "ts_ms": r.ts_ms,
                "event_type": r.event_type,
                "payload": r.payload,
                "prev_hash": r.prev_hash,
                "hash": r.hash,
            }
        )
    return out


async def list_logs(
    db: AsyncSession,
    *,
    analysis_id: Optional[int] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    q = select(EvidenceLog).order_by(EvidenceLog.id.desc()).limit(limit)
    if analysis_id is not None:
        q = select(EvidenceLog).where(EvidenceLog.analysis_id == analysis_id).order_by(EvidenceLog.id.desc()).limit(limit)

    rows = (await db.execute(q)).scalars()
    return [
        {
            "id": r.id,
            "analysis_id": r.analysis_id,
            "ts_ms": r.ts_ms,
            "event_type": r.event_type,
            "payload": r.payload,
            "prev_hash": r.prev_hash,
            "hash": r.hash,
        }
        for r in rows
    ]

