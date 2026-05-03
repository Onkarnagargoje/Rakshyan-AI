from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.socketio_app import sio


async def emit_to_analysis(analysis_id: int, event: str, payload: Dict[str, Any]) -> None:
    await sio.emit(event, payload, room=f"analysis:{analysis_id}")

