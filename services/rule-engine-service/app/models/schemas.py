from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RuleScope(str, Enum):
    ALL_DEVICES = "all_devices"
    SELECTED_DEVICES = "selected_devices"


class RuleStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ConditionOperator(str, Enum):
    GT = ">"
    LT = "<"
    EQ = "="
    NEQ = "!="
    GTE = ">="
    LTE = "<="


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class NotificationChannels(BaseModel):
    email: List[str] = Field(default_factory=list)
    sms: List[str] = Field(default_factory=list)
    whatsapp: List[str] = Field(default_factory=list)
    telegram: List[str] = Field(default_factory=list)
    webhook: List[str] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "NotificationChannels":
        """Create from empty dict or None."""
        if data is None or data == {}:
            return cls()
        return cls(**data)


class RuleCreate(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scope: RuleScope = RuleScope.SELECTED_DEVICES
    property: str = Field(..., min_length=1, max_length=100)
    condition: str  # Accept string like ">", "<", etc.
    threshold: float
    severity: AlertSeverity = AlertSeverity.WARNING
    cooldown_minutes: int = Field(default=15, ge=1)
    device_ids: List[str] = Field(default_factory=list)
    notification_channels: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("device_ids")
    @classmethod
    def validate_device_ids(cls, v, info):
        scope = info.data.get("scope")
        if scope == RuleScope.SELECTED_DEVICES and not v:
            raise ValueError("device_ids must be non-empty when scope is 'selected_devices'")
        return v


class RuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scope: Optional[RuleScope] = None
    property: Optional[str] = Field(None, min_length=1, max_length=100)
    condition: Optional[ConditionOperator] = None
    threshold: Optional[float] = None
    severity: Optional[AlertSeverity] = None
    cooldown_minutes: Optional[int] = Field(None, ge=1)
    device_ids: Optional[List[str]] = None
    notification_channels: Optional[NotificationChannels] = None


class RuleStatusUpdate(BaseModel):
    status: RuleStatus


class RuleResponse(BaseModel):
    rule_id: str
    tenant_id: Optional[str] = None
    rule_name: str
    description: Optional[str] = None
    scope: str
    property: str
    condition: str
    threshold: float
    status: str
    severity: str
    notification_channels: Dict[str, Any]
    cooldown_minutes: int
    device_ids: List[str]
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    alert_id: str
    tenant_id: Optional[str] = None
    rule_id: str
    device_id: str
    severity: str
    message: str
    actual_value: Optional[float] = None
    threshold_value: Optional[float] = None
    property_name: Optional[str] = None
    condition: Optional[str] = None
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluateRequest(BaseModel):
    device_id: str
    telemetry: Dict[str, float]


class AlertStatusUpdate(BaseModel):
    status: AlertStatus
