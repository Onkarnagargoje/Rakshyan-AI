from sqlalchemy import select

from app.models import (  # noqa: F401 — ensure all models register on Base.metadata
    Base,
    ChatAnalysis,
    ChildDevice,
    ChildProfile,
    EvidenceLog,
    PairingCode,
    ParentAlert,
    ParentPushToken,
    User,
)
from app.services.sqlite_migrate import apply_sqlite_migrations
from app.utils.db import engine, SessionLocal
from app.utils.security import hash_password
from app.utils.settings import settings


async def init_db() -> None:
    # Create tables (MVP; later switch to Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.database_url.startswith("sqlite"):
            await conn.run_sync(apply_sqlite_migrations)

    # Seed demo users if missing
    async with SessionLocal() as session:
        for email, role, pw in [
            ("parent@example.com", "parent", "parent123"),
            ("admin@example.com", "admin", "admin123"),
        ]:
            exists = await session.scalar(select(User).where(User.email == email))
            if not exists:
                session.add(User(email=email, role=role, password_hash=hash_password(pw)))
        await session.commit()

