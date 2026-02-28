from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Integer, Float, Boolean, Time, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"
    
    device_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phase_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    legacy_status: Mapped[str] = mapped_column(String(50), default="active")
    last_seen_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(6), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(6), nullable=True)
    
    shifts: Mapped[List["DeviceShift"]] = relationship(
        "DeviceShift",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    health_configs: Mapped[List["ParameterHealthConfig"]] = relationship(
        "ParameterHealthConfig",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    properties: Mapped[List["DeviceProperties"]] = relationship(
        "DeviceProperties",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_tenant", "tenant_id"),
        Index("idx_device_type", "device_type"),
        Index("idx_last_seen", "last_seen_timestamp"),
        Index("idx_legacy_status", "legacy_status"),
    )


class DeviceShift(Base):
    __tablename__ = "device_shifts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(50), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    shift_name: Mapped[str] = mapped_column(String(100), nullable=False)
    shift_start: Mapped[datetime] = mapped_column(Time, nullable=False)
    shift_end: Mapped[datetime] = mapped_column(Time, nullable=False)
    maintenance_break_minutes: Mapped[int] = mapped_column(Integer, default=0)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    device: Mapped["Device"] = relationship("Device", back_populates="shifts")
    
    __table_args__ = (
        Index("idx_device_shifts_device", "device_id"),
        Index("idx_device_shifts_tenant", "tenant_id"),
    )


class ParameterHealthConfig(Base):
    __tablename__ = "parameter_health_config"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(50), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    normal_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    normal_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ignore_zero_value: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    device: Mapped["Device"] = relationship("Device", back_populates="health_configs")
    
    __table_args__ = (
        Index("idx_health_config_device", "device_id"),
        Index("idx_health_config_tenant", "tenant_id"),
        UniqueConstraint("device_id", "parameter_name", name="uk_device_parameter"),
    )


class DeviceProperties(Base):
    __tablename__ = "device_properties"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(50), ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    property_name: Mapped[str] = mapped_column(String(100), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), default="float")
    is_numeric: Mapped[bool] = mapped_column(Boolean, default=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(6), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    device: Mapped["Device"] = relationship("Device", back_populates="properties")
    
    __table_args__ = (
        Index("idx_device_properties_device", "device_id"),
        UniqueConstraint("device_id", "property_name", name="uk_device_property"),
    )
