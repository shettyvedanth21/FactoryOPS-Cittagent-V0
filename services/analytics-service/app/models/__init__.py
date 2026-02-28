from sqlalchemy import Column, String, Float, Text, DateTime, JSON, Index, Integer
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class AnalyticsJob(Base):
    __tablename__ = "analytics_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)  # anomaly_detection, failure_prediction
    model_name = Column(String(100), nullable=False)
    date_range_start = Column(DateTime, nullable=False)
    date_range_end = Column(DateTime, nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    progress = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    results = Column(JSON, nullable=True)
    accuracy_metrics = Column(JSON, nullable=True)
    execution_time_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_analytics_jobs_status", "status"),
        Index("idx_analytics_jobs_created", "created_at"),
        Index("idx_analytics_jobs_device", "device_id"),
    )
