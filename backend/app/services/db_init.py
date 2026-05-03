from sqlalchemy import select

from app.models import Base, User
from app.utils.db import engine, SessionLocal
from app.utils.security import hash_password


async def init_db() -> None:
    # Create tables (MVP; later switch to Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

