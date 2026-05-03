from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass
class AgentOutput:
    risk_level: RiskLevel
    confidence: float
    reason: str
    flags: List[str]
    meta: Dict[str, Any]

    @staticmethod
    def low(reason: str, *, confidence: float = 0.5, flags: Optional[List[str]] = None, meta: Optional[Dict[str, Any]] = None):
        return AgentOutput("low", confidence, reason, flags or [], meta or {})

    def to_json(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "confidence": float(self.confidence),
            "reason": self.reason,
            "flags": list(self.flags),
            "meta": dict(self.meta),
        }

