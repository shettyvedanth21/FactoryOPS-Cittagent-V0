from datetime import datetime, time as dt_time
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.device import Device, DeviceShift
from app.models.schemas import ShiftCreate, ShiftUpdate, ShiftResponse
from app.services import device_service
from shared.response import success_response
from shared.exceptions import DeviceNotFoundException


router = APIRouter()


def parse_time(time_str: str) -> dt_time:
    """Parse HH:MM string to time object."""
    hour, minute = map(int, time_str.split(":"))
    return dt_time(hour, minute)


@router.post("/devices/{device_id}/shifts", status_code=201)
async def create_shift(
    device_id: str,
    shift_data: ShiftCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new shift for a device."""
    try:
        await device_service.get_device(db, device_id)
    except DeviceNotFoundException:
        from shared.response import error_response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content=error_response(
                code="DEVICE_NOT_FOUND",
                message=f"Device '{device_id}' not found"
            )
        )
    
    shift = DeviceShift(
        device_id=device_id,
        shift_name=shift_data.shift_name,
        shift_start=parse_time(shift_data.shift_start),
        shift_end=parse_time(shift_data.shift_end),
        maintenance_break_minutes=shift_data.maintenance_break_minutes or 0,
        day_of_week=shift_data.day_of_week,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(shift)
    await db.flush()
    await db.refresh(shift)
    
    return success_response(ShiftResponse.model_validate(shift).model_dump())


@router.get("/devices/{device_id}/shifts")
async def get_shifts(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all shifts for a device."""
    try:
        await device_service.get_device(db, device_id)
    except DeviceNotFoundException:
        from shared.response import error_response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content=error_response(
                code="DEVICE_NOT_FOUND",
                message=f"Device '{device_id}' not found"
            )
        )
    
    result = await db.execute(
        select(DeviceShift).where(
            and_(
                DeviceShift.device_id == device_id,
                DeviceShift.is_active == True
            )
        )
    )
    shifts = result.scalars().all()
    
    shift_list = [ShiftResponse.model_validate(s).model_dump() for s in shifts]
    return success_response(shift_list)


@router.put("/devices/{device_id}/shifts/{shift_id}")
async def update_shift(
    device_id: str,
    shift_id: int,
    shift_data: ShiftUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a shift."""
    result = await db.execute(
        select(DeviceShift).where(
            and_(
                DeviceShift.id == shift_id,
                DeviceShift.device_id == device_id
            )
        )
    )
    shift = result.scalar_one_or_none()
    
    if not shift:
        from shared.response import error_response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content=error_response(
                code="SHIFT_NOT_FOUND",
                message=f"Shift {shift_id} not found for device {device_id}"
            )
        )
    
    update_data = shift_data.model_dump(exclude_unset=True)
    
    if "shift_start" in update_data:
        update_data["shift_start"] = parse_time(update_data["shift_start"])
    if "shift_end" in update_data:
        update_data["shift_end"] = parse_time(update_data["shift_end"])
    
    for field, value in update_data.items():
        setattr(shift, field, value)
    
    shift.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(shift)
    
    return success_response(ShiftResponse.model_validate(shift).model_dump())


@router.delete("/devices/{device_id}/shifts/{shift_id}")
async def delete_shift(
    device_id: str,
    shift_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a shift (hard delete)."""
    result = await db.execute(
        select(DeviceShift).where(
            and_(
                DeviceShift.id == shift_id,
                DeviceShift.device_id == device_id
            )
        )
    )
    shift = result.scalar_one_or_none()
    
    if not shift:
        from shared.response import error_response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content=error_response(
                code="SHIFT_NOT_FOUND",
                message=f"Shift {shift_id} not found for device {device_id}"
            )
        )
    
    await db.delete(shift)
    await db.flush()
    
    return success_response({"message": "Shift deleted successfully"})
