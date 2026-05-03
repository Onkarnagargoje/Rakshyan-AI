from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high", "critical"]


class AgentResult(BaseModel):
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    flags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class AgentHealth(BaseModel):
    agent_name: str
    trust_score: float = Field(ge=0.0, le=1.0)
    last_latency_ms: Optional[int] = None
    last_error: Optional[str] = None
    low_confidence_rate_24h: float = Field(default=0.0, ge=0.0, le=1.0)
    conflict_rate_24h: float = Field(default=0.0, ge=0.0, le=1.0)


class MetaDiagnostics(BaseModel):
    missing_outputs: List[str] = Field(default_factory=list)
    low_confidence: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    retries: Dict[str, int] = Field(default_factory=dict)
    drift_suspected: List[str] = Field(default_factory=list)
    agent_health: List[AgentHealth] = Field(default_factory=list)

