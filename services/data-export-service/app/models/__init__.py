from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class ExportCheckpoint(Base):
    __tablename__ = "export_checkpoints"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    export_id = Column(String(36), unique=True, nullable=False, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    export_type = Column(String(50), nullable=False, default="full")
    format = Column(String(20), nullable=False, default="csv")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    records_exported = Column(Integer, default=0)
    s3_key = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_export_checkpoints_device", "device_id"),
        Index("idx_export_checkpoints_status", "status"),
        Index("idx_export_checkpoints_created", "created_at"),
    )
