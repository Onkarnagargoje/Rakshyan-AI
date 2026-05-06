from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChildDevice
from app.utils.db import get_db
from app.utils.security import hash_ingest_token

bearer_ingest = HTTPBearer(auto_error=False)


async def get_device_from_ingest_token(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_ingest),
    db: AsyncSession = Depends(get_db),
) -> ChildDevice:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing ingest token")
    h = hash_ingest_token(creds.credentials)
    dev = await db.scalar(select(ChildDevice).where(ChildDevice.ingest_token_hash == h))
    if not dev:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ingest token")
    return dev
