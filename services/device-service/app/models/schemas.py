from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
import re


DEVICE_TYPES = [
    "compressor", "motor", "pump", "conveyor", "robot", "hv_switchgear",
    "transformer", "generator", "chiller", "ahu", "ahu_fan", "boiler",
    "steam_turbine", "lighting", "hvac", "crusher", "grinder", "mill",
    "saw", "oven", "furnace", "press", "injection_molder", "extruder",
    "sensor", "meter", "other"
]


DEVICE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{1,49}$")


class DeviceCreate(BaseModel):
    device_id: str = Field(..., pattern=r"^[A-Z][A-Z0-9_-]{1,49}$")
    device_name: str = Field(..., min_length=1, max_length=255)
    device_type: str
    location: Optional[str] = Field(None, max_length=500)
    phase_type: Optional[str] = Field(None, pattern="^(single|three)$")
    manufacturer: Optional[str] = Field(None, max_length=255)
    model: Optional[str] = Field(None, max_length=255)
    metadata_json: Optional[str] = None
    
    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v):
        if v.lower() not in DEVICE_TYPES:
            raise ValueError(f"device_type must be one of: {', '.join(DEVICE_TYPES)}")
        return v.lower()


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_type: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    phase_type: Optional[str] = Field(None, pattern="^(single|three)$")
    manufacturer: Optional[str] = Field(None, max_length=255)
    model: Optional[str] = Field(None, max_length=255)
    metadata_json: Optional[str] = None
    
    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v):
        if v is not None and v.lower() not in DEVICE_TYPES:
            raise ValueError(f"device_type must be one of: {', '.join(DEVICE_TYPES)}")
        return v.lower() if v else v


class DeviceResponse(BaseModel):
    device_id: str
    tenant_id: Optional[str] = None
    device_name: str
    device_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    phase_type: Optional[str] = None
    legacy_status: str = "active"
    last_seen_timestamp: Optional[datetime] = None
    metadata_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    status: Optional[str] = None
    uptime_pct: Optional[float] = None
    
    model_config = {"from_attributes": True}


class ShiftCreate(BaseModel):
    shift_name: str = Field(..., min_length=1, max_length=100)
    shift_start: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    shift_end: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    maintenance_break_minutes: Optional[int] = Field(0, ge=0)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)


class ShiftUpdate(BaseModel):
    shift_name: Optional[str] = Field(None, min_length=1, max_length=100)
    shift_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    shift_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    maintenance_break_minutes: Optional[int] = Field(None, ge=0)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    is_active: Optional[bool] = None


class ShiftResponse(BaseModel):
    id: int
    device_id: str
    tenant_id: Optional[str] = None
    shift_name: str
    shift_start: datetime
    shift_end: datetime
    maintenance_break_minutes: int
    day_of_week: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class HealthConfigCreate(BaseModel):
    parameter_name: str = Field(..., min_length=1, max_length=100)
    normal_min: Optional[float] = None
    normal_max: Optional[float] = None
    max_min: Optional[float] = None
    max_max: Optional[float] = None
    weight: float = Field(..., ge=0.0, le=100.0)
    ignore_zero_value: Optional[bool] = False


class HealthConfigBulkCreate(BaseModel):
    configs: List[HealthConfigCreate]


class HealthConfigResponse(BaseModel):
    id: int
    device_id: str
    tenant_id: Optional[str] = None
    parameter_name: str
    normal_min: Optional[float] = None
    normal_max: Optional[float] = None
    max_min: Optional[float] = None
    max_max: Optional[float] = None
    weight: float
    ignore_zero_value: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class HealthScoreRequest(BaseModel):
    telemetry: dict[str, float]


class HealthScoreBreakdown(BaseModel):
    parameter: str
    score: float
    weight: float
    value: float
    status: str


class HealthScoreResponse(BaseModel):
    health_score: float
    grade: str
    breakdown: List[HealthScoreBreakdown]
    evaluated_parameters: int
    skipped_parameters: int


class HealthConfigValidateResponse(BaseModel):
    valid: bool
    total_weight: float
    message: str


class UptimeResponse(BaseModel):
    device_id: str
    period: dict
    uptime_percentage: Optional[float]
    total_scheduled_minutes: int
    actual_running_minutes: int
    downtime_minutes: int
    shifts_evaluated: List[dict]


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int


class PaginatedResponse(BaseModel):
    data: List[Any]
    pagination: PaginationInfo
