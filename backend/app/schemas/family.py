from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=128)


class ChildCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=128, default="My child")


class ChildResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    created_at: str


class PairingCodeResponse(BaseModel):
    code: str
    child_id: int
    expires_at: str


class LinkChildRequest(BaseModel):
    code: str = Field(min_length=4, max_length=16)
    device_label: str = Field(default="Android", max_length=128)


class LinkChildResponse(BaseModel):
    child_id: int
    device_id: int
    ingest_token: str
    token_hint: str


class IngestItem(BaseModel):
    source_app: str = Field(default="unknown", max_length=128)
    text: str = Field(min_length=1, max_length=8000)
    ts_ms: Optional[int] = None


class IngestNotificationsRequest(BaseModel):
    items: List[IngestItem] = Field(min_length=1, max_length=50)
    language_hint: str = Field(default="auto", max_length=64)


class IngestNotificationsResponse(BaseModel):
    analysis_id: int
    final_risk_level: str
    final_confidence: float
    parent_alert_created: bool


class ParentAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    analysis_id: Optional[int]
    risk_level: str
    title: str
    summary: str
    read_at: Optional[str]
    created_at: str


class MarkReadRequest(BaseModel):
    alert_ids: List[int] = Field(min_length=1, max_length=100)


class RegisterPushTokenRequest(BaseModel):
    provider: str = Field(default="fcm", max_length=16)
    platform: str = Field(default="android", max_length=32)
    token: str = Field(min_length=10, max_length=4096)


class PushTokenResponse(BaseModel):
    id: int
    provider: str
    platform: str
    created_at: str
