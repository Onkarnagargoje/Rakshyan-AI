"""Lightweight additive migrations for local SQLite (no Alembic)."""

from __future__ import annotations

from typing import Set

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _existing_columns(conn: Connection, table: str) -> Set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {str(r[1]) for r in rows}


def apply_sqlite_migrations(conn: Connection) -> None:
    if "chat_analyses" in _existing_tables(conn):
        cols = _existing_columns(conn, "chat_analyses")
        if "child_id" not in cols:
            conn.execute(text("ALTER TABLE chat_analyses ADD COLUMN child_id INTEGER"))
        if "device_id" not in cols:
            conn.execute(text("ALTER TABLE chat_analyses ADD COLUMN device_id INTEGER"))


def _existing_tables(conn: Connection) -> Set[str]:
    rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    return {str(r[0]) for r in rows}
