from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReportType(str, Enum):
    CONSUMPTION = "consumption"
    COMPARISON = "comparison"
    WASTAGE = "wastage"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ComputationMode(str, Enum):
    DIRECT_POWER = "direct_power"
    DERIVED_SINGLE = "derived_single"
    DERIVED_THREE = "derived_three"


class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ConsumptionReportRequest(BaseModel):
    device_ids: List[str]
    start_date: str
    end_date: str
    group_by: str = "daily"
    include_wastage: bool = False
    format: ReportFormat = ReportFormat.PDF
    computation_mode: Optional[ComputationMode] = None


class ComparisonReportRequest(BaseModel):
    device_ids: List[str]
    start_date: str
    end_date: str
    format: ReportFormat = ReportFormat.PDF


class WastageReportRequest(BaseModel):
    device_ids: List[str]
    start_date: str
    end_date: str


class ScheduledReportCreate(BaseModel):
    report_type: ReportType
    frequency: Frequency
    params_template: Dict[str, Any]
    is_active: bool = True


class ScheduledReportUpdate(BaseModel):
    frequency: Optional[Frequency] = None
    params_template: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TenantTariffCreate(BaseModel):
    tariff_name: str
    rate_per_unit: float
    currency: str = "INR"
    peak_rate: Optional[float] = None
    peak_start_time: Optional[str] = None
    peak_end_time: Optional[str] = None
    demand_charge: Optional[float] = None
    power_factor_penalty: Optional[float] = None
    is_active: bool = True


class TenantTariffUpdate(BaseModel):
    tariff_name: Optional[str] = None
    rate_per_unit: Optional[float] = None
    peak_rate: Optional[float] = None
    peak_start_time: Optional[str] = None
    peak_end_time: Optional[str] = None
    demand_charge: Optional[float] = None
    power_factor_penalty: Optional[float] = None
    is_active: Optional[bool] = None


class EnergyReportResponse(BaseModel):
    report_id: str
    tenant_id: Optional[str] = None
    report_type: str
    status: str
    params: Dict[str, Any]
    result_json: Optional[Dict[str, Any]] = None
    s3_key: Optional[str] = None
    format: str
    error_message: Optional[str] = None
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduledReportResponse(BaseModel):
    schedule_id: str
    tenant_id: Optional[str] = None
    report_type: str
    frequency: str
    params_template: Dict[str, Any]
    is_active: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_status: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantTariffResponse(BaseModel):
    id: int
    tenant_id: str
    tariff_name: str
    rate_per_unit: float
    currency: str
    peak_rate: Optional[float] = None
    peak_start_time: Optional[str] = None
    peak_end_time: Optional[str] = None
    demand_charge: Optional[float] = None
    power_factor_penalty: Optional[float] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
