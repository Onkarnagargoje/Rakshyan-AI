from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChildProfile(Base):
    """A child account linked to a parent user."""

    __tablename__ = "child_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    display_name: Mapped[str] = mapped_column(String(128), default="Child")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PairingCode(Base):
    """One-time code for Android child app to link to a child profile."""

    __tablename__ = "pairing_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("child_profiles.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    expires_at: Mapped[str] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChildDevice(Base):
    """Linked Android device; authenticates ingest via ingest token (shown once at link)."""

    __tablename__ = "child_devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("child_profiles.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(128), default="Android")
    ingest_token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    token_hint: Mapped[str] = mapped_column(String(8), default="****")  # last 4 chars of token for parent UI
    last_seen_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ParentAlert(Base):
    """High-signal notification row for parent app (push can attach later)."""

    __tablename__ = "parent_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("child_profiles.id", ondelete="CASCADE"), index=True)
    analysis_id: Mapped[int | None] = mapped_column(ForeignKey("chat_analyses.id", ondelete="SET NULL"), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(16), default="medium")
    title: Mapped[str] = mapped_column(String(255), default="Safety alert")
    summary: Mapped[str] = mapped_column(Text, default="")
    read_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ParentPushToken(Base):
    """
    Parent device push token (FCM/APNS). A parent can have multiple devices.
    We store raw tokens (treat as sensitive) and allow explicit revoke.
    """

    __tablename__ = "parent_push_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(16), default="fcm")  # fcm|apns
    platform: Mapped[str] = mapped_column(String(32), default="android")  # android|ios|web
    token: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
