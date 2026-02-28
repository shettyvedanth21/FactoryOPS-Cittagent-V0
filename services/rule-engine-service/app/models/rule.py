import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Rule(Base):
    __tablename__ = "rules"

    rule_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(50), nullable=True, index=True)
    rule_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scope = Column(String(50), default="selected_devices")
    property = Column(String(100), nullable=False)
    condition = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String(50), default="active", index=True)
    severity = Column(String(20), default="warning")
    notification_channels = Column(JSON, nullable=False)
    cooldown_minutes = Column(Integer, default=15)
    device_ids = Column(JSON, nullable=False)
    last_triggered_at = Column(DateTime(6), nullable=True)
    created_at = Column(DateTime(6), nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(6), nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    deleted_at = Column(DateTime(6), nullable=True)

    alerts = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "rule_id" not in kwargs:
            kwargs["rule_id"] = str(uuid.uuid4())
        super().__init__(**kwargs)


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(50), nullable=True, index=True)
    rule_id = Column(String(36), ForeignKey("rules.rule_id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    severity = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    actual_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    property_name = Column(String(100), nullable=True)
    condition = Column(String(20), nullable=True)
    status = Column(String(50), default="open", index=True)
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime(6), nullable=True)
    resolved_at = Column(DateTime(6), nullable=True)
    created_at = Column(DateTime(6), nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime(6), nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    rule = relationship("Rule", back_populates="alerts")

    def __init__(self, **kwargs):
        if "alert_id" not in kwargs:
            kwargs["alert_id"] = str(uuid.uuid4())
        super().__init__(**kwargs)
