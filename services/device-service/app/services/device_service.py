import uuid
from datetime import datetime, timedelta, time
from typing import Optional, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.device import Device
from app.models.schemas import DeviceCreate, DeviceUpdate, DeviceResponse
from shared.exceptions import DeviceNotFoundException, DuplicateDeviceException


def compute_device_status(device: Device) -> str:
    """Compute device status based on last_seen_timestamp and legacy_status."""
    if device.legacy_status == "error":
        return "error"
    if device.legacy_status == "maintenance":
        return "maintenance"
    if device.last_seen_timestamp:
        if (datetime.utcnow() - device.last_seen_timestamp) <= timedelta(seconds=60):
            return "running"
    return "stopped"


async def create_device(db: AsyncSession, device_data: DeviceCreate) -> Device:
    """Create a new device."""
    result = await db.execute(
        select(Device).where(Device.device_id == device_data.device_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise DuplicateDeviceException(device_data.device_id)
    
    now = datetime.utcnow()
    device = Device(
        device_id=device_data.device_id,
        device_name=device_data.device_name,
        device_type=device_data.device_type,
        location=device_data.location,
        phase_type=device_data.phase_type,
        manufacturer=device_data.manufacturer,
        model=device_data.model,
        metadata_json=device_data.metadata_json,
        legacy_status="active",
        created_at=now,
        updated_at=now,
    )
    
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device


async def get_device(db: AsyncSession, device_id: str) -> Device:
    """Get a device by ID (not deleted)."""
    result = await db.execute(
        select(Device).where(
            and_(Device.device_id == device_id, Device.deleted_at.is_(None))
        )
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise DeviceNotFoundException(device_id)
    
    return device


async def get_devices(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    device_type: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple[List[Device], int]:
    """Get paginated list of devices (not deleted)."""
    query = select(Device).where(Device.deleted_at.is_(None))
    
    if device_type:
        query = query.where(Device.device_type == device_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Device.device_id.ilike(search_term),
                Device.device_name.ilike(search_term),
                Device.location.ilike(search_term)
            )
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return list(devices), total


async def update_device(
    db: AsyncSession,
    device_id: str,
    device_data: DeviceUpdate,
) -> Device:
    """Update a device."""
    device = await get_device(db, device_id)
    
    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    device.updated_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(device)
    return device


async def delete_device(db: AsyncSession, device_id: str) -> None:
    """Soft delete a device."""
    device = await get_device(db, device_id)
    device.deleted_at = datetime.utcnow()
    await db.flush()


async def update_heartbeat(db: AsyncSession, device_id: str) -> Device:
    """Update device last_seen_timestamp."""
    device = await get_device(db, device_id)
    device.last_seen_timestamp = datetime.utcnow()
    device.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(device)
    return device


async def bulk_import_devices(db: AsyncSession, csv_data: str) -> dict:
    """Bulk import devices from CSV data."""
    import csv
    from io import StringIO
    
    devices_created = 0
    devices_skipped = 0
    errors = []
    
    reader = csv.DictReader(StringIO(csv_data))
    
    for row in reader:
        try:
            device_data = DeviceCreate(
                device_id=row.get("device_id", "").strip(),
                device_name=row.get("device_name", "").strip(),
                device_type=row.get("device_type", "").strip(),
                location=row.get("location", "").strip() or None,
                phase_type=row.get("phase_type", "").strip() or None,
                manufacturer=row.get("manufacturer", "").strip() or None,
                model=row.get("model", "").strip() or None,
            )
            await create_device(db, device_data)
            devices_created += 1
        except DuplicateDeviceException:
            devices_skipped += 1
        except Exception as e:
            errors.append(f"Row {row.get('device_id', 'unknown')}: {str(e)}")
    
    await db.commit()
    
    job_id = str(uuid.uuid4())
    return {
        "job_id": job_id,
        "status": "completed",
        "devices_created": devices_created,
        "devices_skipped": devices_skipped,
        "errors": errors
    }
