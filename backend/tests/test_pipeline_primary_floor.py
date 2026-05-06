"""Pipeline-level invariant: supervisor.final >= max(grooming, bullying, emotion) post-repair."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base, User

# Register all ORM tables on Base.metadata for create_all
import app.models.analysis  # noqa: F401
import app.models.family  # noqa: F401
from app.services.analysis_pipeline import execute_chat_analysis
from app.services.analyzer_graph import (
    _aggregate_supervisor,
    max_primary_safety_risk,
    supervisor_satisfies_primary_floor,
)


@pytest.mark.asyncio
async def test_aggregate_supervisor_synthetic_grooming_high_not_low():
    agents = {
        "grooming": {"risk_level": "high", "confidence": 0.72, "reason": "x", "flags": []},
        "bullying": {"risk_level": "low", "confidence": 0.6, "reason": "x", "flags": []},
        "emotion": {"risk_level": "low", "confidence": 0.58, "reason": "x", "flags": []},
    }
    sup = _aggregate_supervisor(agents, chat_text="hi")
    assert sup["final_risk_level"] == "high"
    assert supervisor_satisfies_primary_floor(sup, agents)
    assert max_primary_safety_risk(agents) == "high"


@pytest.mark.asyncio
async def test_execute_chat_analysis_primary_floor_invariant():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        db.add(User(email="pytest-pipeline@local", role="parent", password_hash="unused"))
        await db.commit()
        uid = (await db.scalar(select(User.id).where(User.email == "pytest-pipeline@local")))

        texts = [
            "Don't tell your parents. This is our secret.",
            "we will bit him tommorow",
            "kill yourself",
            "Hey want to play Minecraft after school?",
        ]
        for chat in texts:
            resp = await execute_chat_analysis(
                db,
                user_id=int(uid),
                chat_text=chat,
                platform="simulated",
                language_hint="auto",
                realtime=False,
            )
            assert supervisor_satisfies_primary_floor(resp.supervisor, resp.agents), (
                chat,
                resp.supervisor.get("final_risk_level"),
                {k: resp.agents.get(k, {}).get("risk_level") for k in ("grooming", "bullying", "emotion")},
            )
