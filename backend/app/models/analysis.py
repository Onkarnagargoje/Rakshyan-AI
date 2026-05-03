from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChatAnalysis(Base):
    __tablename__ = "chat_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    platform: Mapped[str] = mapped_column(String(64), default="simulated")
    language_hint: Mapped[str] = mapped_column(String(64), default="auto")
    chat_text: Mapped[str] = mapped_column(String, default="")

    final_risk_level: Mapped[str] = mapped_column(String(16), default="low")
    final_confidence: Mapped[int] = mapped_column(Integer, default=0)  # store 0-1000

    supervisor_output: Mapped[dict] = mapped_column(JSON, default=dict)
    agent_outputs: Mapped[dict] = mapped_column(JSON, default=dict)
    meta_diagnostics: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceLog(Base):
    __tablename__ = "evidence_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("chat_analyses.id", ondelete="CASCADE"), index=True)

    ts_ms: Mapped[int] = mapped_column(Integer, index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64), index=True)

