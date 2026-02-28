from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class AnalyticsJobCreate(BaseModel):
    device_id: str = Field(..., description="Device ID (e.g., COMPRESSOR-001)")
    analysis_type: str = Field(..., description="Type of analysis: anomaly_detection, failure_prediction")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Analysis parameters")


class AnalyticsJobResponse(BaseModel):
    job_id: str
    device_id: str
    analysis_type: str
    model_name: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[int] = None
    
    class Config:
        from_attributes = True


class AnalyticsJobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    error_message: Optional[str] = None


class DataAvailabilityResponse(BaseModel):
    device_id: str
    has_data: bool
    days_available: int
    parameters: List[str]
    oldest_data_point: Optional[datetime] = None
    newest_data_point: Optional[datetime] = None


class MLModelInfo(BaseModel):
    model_name: str
    analysis_type: str
    description: str
    min_data_days: int
    parameters: Dict[str, Any]
    output_format: Dict[str, str]


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    status: Optional[str] = None
    device_id: Optional[str] = None
    analysis_type: Optional[str] = None


class PaginatedJobsResponse(BaseModel):
    items: List[AnalyticsJobResponse]
    total: int
    page: int
    page_size: int
    pages: int
