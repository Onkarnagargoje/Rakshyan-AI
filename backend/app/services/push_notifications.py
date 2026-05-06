from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ParentAlert, ParentPushToken
from app.utils.settings import settings

log = logging.getLogger(__name__)


def _load_service_account_info() -> Optional[dict]:
    if settings.fcm_service_account_json.strip():
        try:
            return json.loads(settings.fcm_service_account_json)
        except Exception:
            log.warning("FCM service account JSON is not valid; push disabled.")
            return None
    if settings.fcm_service_account_path.strip():
        try:
            with open(settings.fcm_service_account_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            log.warning("FCM service account path not found; push disabled.")
            return None
        except Exception:
            log.warning("FCM service account path could not be read; push disabled.")
            return None
    return None


async def _get_fcm_access_token() -> Optional[str]:
    """
    Obtain an OAuth2 access token for FCM HTTP v1.
    Uses google-auth if available; otherwise returns None.
    """
    info = _load_service_account_info()
    if not info:
        return None
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
    except Exception:
        log.warning("google-auth not installed; cannot send FCM push.")
        return None

    try:
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        creds.refresh(Request())
        return str(getattr(creds, "token", "") or "")
    except Exception as e:
        log.warning("Failed to obtain FCM access token: %s", e)
        return None


async def send_fcm_multicast(
    *,
    tokens: Iterable[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
) -> int:
    """
    Best-effort FCM push. Returns number of attempted sends.
    Does not raise on network/auth errors.
    """
    if not settings.enable_push:
        return 0
    if not settings.fcm_project_id.strip():
        log.warning("FCM project id missing; push disabled.")
        return 0

    tok = await _get_fcm_access_token()
    if not tok:
        return 0

    url = f"https://fcm.googleapis.com/v1/projects/{settings.fcm_project_id}/messages:send"
    headers = {"Authorization": f"Bearer {tok}"}

    attempted = 0
    async with httpx.AsyncClient(timeout=6.0) as client:
        for t in tokens:
            if not t:
                continue
            attempted += 1
            payload: Dict[str, Any] = {
                "message": {
                    "token": t,
                    "notification": {"title": title, "body": body},
                    "data": data or {},
                }
            }
            try:
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code >= 400:
                    log.info("FCM send failed status=%s body=%s", r.status_code, r.text[:400])
            except Exception as e:
                log.info("FCM send failed: %s", e)
    return attempted


async def send_parent_alert_push(db: AsyncSession, *, alert: ParentAlert) -> None:
    """
    Send push notification(s) to all parent devices registered for this parent_id.
    Best-effort; does nothing if push disabled / no tokens / no creds.
    """
    if not settings.enable_push:
        return
    rows = (
        await db.execute(
            select(ParentPushToken.token).where(
                ParentPushToken.parent_id == alert.parent_id,
                ParentPushToken.provider == "fcm",
            )
        )
    ).all()
    tokens = [r[0] for r in rows if r and r[0]]
    if not tokens:
        return

    body = (alert.summary or "").strip()
    if len(body) > 160:
        body = body[:157] + "..."
    data = {
        "alert_id": str(alert.id),
        "child_id": str(alert.child_id),
        "risk_level": str(alert.risk_level),
        "analysis_id": str(alert.analysis_id or ""),
    }
    await send_fcm_multicast(tokens=tokens, title=str(alert.title), body=body or "Safety alert", data=data)

