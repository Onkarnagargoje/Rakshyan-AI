from __future__ import annotations

import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChildDevice, ChildProfile, PairingCode, ParentAlert, ParentPushToken, User
from app.schemas.family import (
    ChildCreateRequest,
    ChildResponse,
    IngestNotificationsRequest,
    IngestNotificationsResponse,
    LinkChildRequest,
    LinkChildResponse,
    MarkReadRequest,
    PairingCodeResponse,
    ParentAlertResponse,
    PushTokenResponse,
    RegisterPushTokenRequest,
)
from app.services.analysis_pipeline import execute_chat_analysis, maybe_create_parent_alert
from app.utils.auth_deps import require_role
from app.utils.db import get_db
from app.utils.ingest_deps import get_device_from_ingest_token
from app.utils.security import hash_ingest_token, hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/family", tags=["family"])

_parent_only = require_role("parent")


def _code_alphabet() -> str:
    return string.ascii_uppercase + string.digits


async def _generate_unique_code(db: AsyncSession) -> str:
    alphabet = _code_alphabet()
    for _ in range(12):
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        exists = await db.scalar(select(PairingCode.id).where(PairingCode.code == code))
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Could not generate pairing code")


@router.get("/children", response_model=list[ChildResponse])
async def list_children(
    user: User = Depends(_parent_only),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(ChildProfile).where(ChildProfile.parent_id == user.id).order_by(ChildProfile.id.asc()))).scalars()
    return [
        ChildResponse(id=c.id, display_name=c.display_name, created_at=str(c.created_at))
        for c in rows
    ]


@router.post("/children", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    payload: ChildCreateRequest,
    user: User = Depends(_parent_only),
    db: AsyncSession = Depends(get_db),
):
    c = ChildProfile(parent_id=user.id, display_name=payload.display_name.strip() or "Child")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return ChildResponse(id=c.id, display_name=c.display_name, created_at=str(c.created_at))


@router.post("/children/{child_id}/pairing-code", response_model=PairingCodeResponse)
async def create_pairing_code(
    child_id: int,
    user: User = Depends(_parent_only),
    db: AsyncSession = Depends(get_db),
):
    child = await db.scalar(select(ChildProfile).where(ChildProfile.id == child_id, ChildProfile.parent_id == user.id))
    if not child:
        raise HTTPException(status_code=404, detail="child not found")
    await db.execute(delete(PairingCode).where(PairingCode.child_id == child_id, PairingCode.used_at.is_(None)))
    await db.flush()
    code = await _generate_unique_code(db)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    row = PairingCode(child_id=child_id, code=code, expires_at=expires_at)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return PairingCodeResponse(code=row.code, child_id=child_id, expires_at=row.expires_at.isoformat())


@router.post("/link", response_model=LinkChildResponse)
async def link_child_device(payload: LinkChildRequest, db: AsyncSession = Depends(get_db)):
    raw = payload.code.strip().upper()
    row = await db.scalar(
        select(PairingCode).where(
            PairingCode.code == raw,
            PairingCode.used_at.is_(None),
        )
    )
    if not row:
        raise HTTPException(status_code=400, detail="invalid or expired pairing code")
    exp = row.expires_at
    if getattr(exp, "tzinfo", None) is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="pairing code expired")

    plain = secrets.token_urlsafe(32)
    digest = hash_ingest_token(plain)
    hint = plain[-4:] if len(plain) >= 4 else "****"
    dev = ChildDevice(child_id=row.child_id, label=payload.device_label.strip() or "Android", ingest_token_hash=digest, token_hint=hint)
    db.add(dev)
    row.used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(dev)
    logger.info("Child device linked: child_id=%s device_id=%s", row.child_id, dev.id)
    return LinkChildResponse(child_id=row.child_id, device_id=dev.id, ingest_token=plain, token_hint=hint)


@router.post("/ingest/notifications", response_model=IngestNotificationsResponse)
async def ingest_notifications(
    payload: IngestNotificationsRequest,
    dev: ChildDevice = Depends(get_device_from_ingest_token),
    db: AsyncSession = Depends(get_db),
):
    child = await db.scalar(select(ChildProfile).where(ChildProfile.id == dev.child_id))
    if not child:
        raise HTTPException(status_code=400, detail="child profile missing")

    parts = []
    for it in payload.items:
        src = (it.source_app or "app").strip()
        parts.append(f"[{src}] {it.text.strip()}")
    combined = "\n---\n".join(parts)[:20000]

    await db.execute(
        update(ChildDevice)
        .where(ChildDevice.id == dev.id)
        .values(last_seen_at=datetime.now(timezone.utc))
    )
    await db.commit()

    result = await execute_chat_analysis(
        db,
        user_id=child.parent_id,
        chat_text=combined,
        platform="android_notifications",
        language_hint=payload.language_hint,
        wearable=None,
        realtime=False,
        child_id=child.id,
        device_id=dev.id,
    )

    summary = result.parent_summary or ""
    if not summary and result.supervisor:
        acts = result.supervisor.get("recommended_actions") or []
        summary = "; ".join(str(a) for a in acts[:3]) if acts else result.final_risk_level

    await maybe_create_parent_alert(
        db,
        parent_id=child.parent_id,
        child_id=child.id,
        analysis_id=result.analysis_id,
        final_risk_level=result.final_risk_level,
        summary=summary or "Elevated risk from child device signals.",
    )
    alert_created = result.final_risk_level in {"medium", "high", "critical"}
    if alert_created:
        logger.info(
            "Parent alert (stub FCM): parent_id=%s child_id=%s analysis_id=%s level=%s",
            child.parent_id,
            child.id,
            result.analysis_id,
            result.final_risk_level,
        )
    return IngestNotificationsResponse(
        analysis_id=result.analysis_id,
        final_risk_level=result.final_risk_level,
        final_confidence=result.final_confidence,
        parent_alert_created=alert_created,
    )


@router.get("/alerts", response_model=list[ParentAlertResponse])
async def list_alerts(
    user: User = Depends(_parent_only),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    limit = min(max(limit, 1), 100)
    rows = (
        await db.execute(
            select(ParentAlert)
            .where(ParentAlert.parent_id == user.id)
            .order_by(ParentAlert.id.desc())
            .limit(limit)
        )
    ).scalars()
    out: list[ParentAlertResponse] = []
    for a in rows:
        out.append(
            ParentAlertResponse(
                id=a.id,
                child_id=a.child_id,
                analysis_id=a.analysis_id,
                risk_level=a.risk_level,
                title=a.title,
                summary=a.summary,
                read_at=a.read_at.isoformat() if a.read_at else None,
                created_at=str(a.created_at),
            )
        )
    return out


@router.post("/alerts/mark-read")
async def mark_alerts_read(
    payload: MarkReadRequest,
    user: User = Depends(_parent_only),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    await db.execute(
        update(ParentAlert)
        .where(ParentAlert.parent_id == user.id, ParentAlert.id.in_(payload.alert_ids))
        .values(read_at=now)
    )
    await db.commit()
    return {"ok": True, "updated": len(payload.alert_ids)}


@router.post("/push-tokens", response_model=PushTokenResponse)
async def register_push_token(
    payload: RegisterPushTokenRequest,
    user: User = Depends(_parent_only),
    db: AsyncSession = Depends(get_db),
):
    prov = (payload.provider or "fcm").strip().lower()
    plat = (payload.platform or "android").strip().lower()
    tok = payload.token.strip()
    if prov not in {"fcm", "apns"}:
        raise HTTPException(status_code=400, detail="unsupported provider")
    if not tok:
        raise HTTPException(status_code=400, detail="missing token")

    # Idempotent register: if token exists, reassign to this parent.
    row = await db.scalar(select(ParentPushToken).where(ParentPushToken.token == tok))
    if row:
        row.parent_id = user.id
        row.provider = prov
        row.platform = plat
    else:
        row = ParentPushToken(parent_id=user.id, provider=prov, platform=plat, token=tok)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return PushTokenResponse(id=row.id, provider=row.provider, platform=row.platform, created_at=str(row.created_at))


@router.delete("/push-tokens")
async def revoke_push_token(
    token: str,
    user: User = Depends(_parent_only),
    db: AsyncSession = Depends(get_db),
):
    tok = (token or "").strip()
    if not tok:
        raise HTTPException(status_code=400, detail="missing token")
    await db.execute(delete(ParentPushToken).where(ParentPushToken.parent_id == user.id, ParentPushToken.token == tok))
    await db.commit()
    return {"ok": True}
