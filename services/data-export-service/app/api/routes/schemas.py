from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ExportCreateRequest(BaseModel):
    device_id: str = Field(..., description="Device ID (e.g., COMPRESSOR-001)")
    start_date: datetime = Field(..., description="Start date for export")
    end_date: datetime = Field(..., description="End date for export")
    format: str = Field("csv", description="Export format: csv, parquet, json")
    export_type: str = Field("full", description="Export type: full, incremental")


class ExportResponse(BaseModel):
    export_id: str
    device_id: str
    status: str
    format: str
    records_exported: Optional[int] = None
    file_size_bytes: Optional[int] = None
    s3_key: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExportStatusResponse(BaseModel):
    export_id: str
    device_id: str
    status: str
    format: str
    export_type: str
    start_time: datetime
    end_time: datetime
    records_exported: Optional[int] = None
    file_size_bytes: Optional[int] = None
    s3_key: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ExportHistoryResponse(BaseModel):
    items: List[ExportResponse]
    total: int
    page: int
    page_size: int
    pages: int
