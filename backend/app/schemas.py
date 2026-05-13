from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountCreate(BaseModel):
    landline: str = Field(..., min_length=8, max_length=20, description="Landline starting with 0, e.g. 0234567891")
    password: str = Field(..., min_length=1)
    label: str = ""


class AccountUpdate(BaseModel):
    label: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class AccountOut(BaseModel):
    id: int
    landline: str
    label: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotOut(BaseModel):
    id: int
    account_id: int
    customer_name: Optional[str]
    offer_name: Optional[str]
    total_gb: float
    used_gb: float
    remain_gb: float
    usage_pct: float
    effective_time_ms: int
    expire_time_ms: int
    taken_at: datetime

    class Config:
        from_attributes = True


class ForecastOut(BaseModel):
    daily_avg_gb: float
    days_until_exhaust: Optional[float]    # None if avg is 0 or quota grows
    exhaust_date_iso: Optional[str]
    will_exhaust_before_renewal: bool
    confidence: str  # "low" | "medium" | "high"
    sample_days: int


class DashboardOut(BaseModel):
    account: AccountOut
    latest: Optional[SnapshotOut]
    forecast: Optional[ForecastOut]


class AlertConfigIn(BaseModel):
    threshold_pct: float
    enabled: bool = True


class AlertConfigOut(BaseModel):
    id: int
    account_id: int
    threshold_pct: float
    enabled: bool

    class Config:
        from_attributes = True


class ManualRefreshOut(BaseModel):
    ok: bool
    snapshot: Optional[SnapshotOut]
    error: Optional[str] = None
