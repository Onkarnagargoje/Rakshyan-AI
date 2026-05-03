from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.agent import AgentResult, MetaDiagnostics, RiskLevel


class AnalyzeChatRequest(BaseModel):
    platform: str = "simulated"
    language_hint: str = "auto"
    chat_text: str = Field(min_length=1, max_length=20000)
    wearable: Optional[Dict[str, Any]] = None
    realtime: bool = True


class AnalyzeChatResponse(BaseModel):
    analysis_id: int
    final_risk_level: RiskLevel
    final_confidence: float = Field(ge=0.0, le=1.0)
    supervisor: Dict[str, Any]
    agents: Dict[str, AgentResult]
    meta: MetaDiagnostics
    parent_summary: Optional[str] = None


class RiskReportResponse(BaseModel):
    analysis_id: int
    final_risk_level: RiskLevel
    final_confidence: float = Field(ge=0.0, le=1.0)
    created_at: str
    supervisor: Dict[str, Any]
    agents: Dict[str, AgentResult]
    meta: MetaDiagnostics
    evidence_chain: List[Dict[str, Any]]

