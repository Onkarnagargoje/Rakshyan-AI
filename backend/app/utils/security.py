import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from app.utils.settings import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, *, extra: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_expires_minutes)
    payload: Dict[str, Any] = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def hash_ingest_token(plain_token: str) -> str:
    """Deterministic hash for child-device ingest tokens (not reversible)."""
    base = f"ingest:{settings.jwt_secret}:{plain_token}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

