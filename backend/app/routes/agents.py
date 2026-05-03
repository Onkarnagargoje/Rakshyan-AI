from fastapi import APIRouter

from app.services.meta_agent_monitor import _STATS

router = APIRouter()


@router.get("/agent-status")
async def agent_status():
    agents = []
    for name, s in _STATS.items():
        agents.append(
            {
                "agent_name": name,
                "trust_score": float(s.trust),
                "last_latency_ms": s.last_latency_ms,
                "last_error": s.last_error,
                "low_confidence_rate_24h": 0.0,
                "conflict_rate_24h": 0.0,
            }
        )
    return {"agents": agents, "meta": {"status": "ok"}}

