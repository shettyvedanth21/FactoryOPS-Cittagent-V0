from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime, Boolean, Index
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class EnergyReport(Base):
    __tablename__ = "energy_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False)
    tenant_id = Column(String(50), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", index=True)
    params = Column(Text, nullable=False)
    computation_mode = Column(String(50), nullable=True)
    phase_type_used = Column(String(20), nullable=True)
    result_json = Column(Text, nullable=True)
    s3_key = Column(String(500), nullable=True)
    format = Column(String(10), default="pdf")
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_energy_reports_tenant_status', 'tenant_id', 'status'),
        Index('ix_energy_reports_tenant_type_created', 'tenant_id', 'report_type', 'created_at'),
    )


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(String(36), unique=True, nullable=False)
    tenant_id = Column(String(50), nullable=False)
    report_type = Column(String(50), nullable=False)
    frequency = Column(String(50), nullable=False)
    params_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)
    last_result_url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())


class TenantTariff(Base):
    __tablename__ = "tenant_tariffs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    tariff_name = Column(String(100), nullable=False)
    rate_per_unit = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    peak_rate = Column(Float, nullable=True)
    peak_start_time = Column(String(10), nullable=True)
    peak_end_time = Column(String(10), nullable=True)
    demand_charge = Column(Float, nullable=True)
    power_factor_penalty = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    __table_args__ = (
        Index('idx_tenant_tariffs_tenant', 'tenant_id'),
    )
