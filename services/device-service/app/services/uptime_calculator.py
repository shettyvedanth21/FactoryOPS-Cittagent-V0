from datetime import datetime, timedelta, time as dt_time, date
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import DeviceShift


async def get_device_shifts(
    db: AsyncSession,
    device_id: str
) -> List[DeviceShift]:
    """Get all active shifts for a device."""
    result = await db.execute(
        select(DeviceShift).where(
            and_(
                DeviceShift.device_id == device_id,
                DeviceShift.is_active == True
            )
        )
    )
    return list(result.scalars().all())


def calculate_scheduled_minutes(
    shifts: List[DeviceShift],
    start_date: date,
    end_date: date
) -> tuple[int, List[Dict[str, Any]]]:
    """
    Calculate total scheduled minutes for a device over a date range.
    
    Returns tuple of (total_minutes, shifts_evaluated).
    """
    if not shifts:
        return 0, []
    
    total_minutes = 0
    shifts_evaluated = []
    
    current_date = start_date
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        
        for shift in shifts:
            if shift.day_of_week is None or shift.day_of_week == day_of_week:
                start_minutes = shift.shift_start.hour * 60 + shift.shift_start.minute
                end_minutes = shift.shift_end.hour * 60 + shift.shift_end.minute
                
                shift_duration = end_minutes - start_minutes
                if shift_duration < 0:
                    shift_duration += 24 * 60
                
                effective_minutes = shift_duration - (shift.maintenance_break_minutes or 0)
                if effective_minutes < 0:
                    effective_minutes = 0
                
                total_minutes += effective_minutes
                
                shifts_evaluated.append({
                    "shift_name": shift.shift_name,
                    "date": current_date.isoformat(),
                    "day_of_week": day_of_week,
                    "scheduled_minutes": effective_minutes
                })
        
        current_date += timedelta(days=1)
    
    return total_minutes, shifts_evaluated


def time_to_minutes(t: dt_time) -> int:
    """Convert time to minutes since midnight."""
    return t.hour * 60 + t.minute


async def calculate_uptime(
    db: AsyncSession,
    device_id: str,
    start_date: str,
    end_date: str,
    actual_running_minutes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate uptime for a device over a date range.
    
    In Phase 1, actual_running_minutes is stubbed using last_seen_timestamp.
    Phase 2 will integrate with data-service for real telemetry.
    """
    from app.models.device import Device
    from sqlalchemy import select
    
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    if end < start:
        raise ValueError("end_date must be greater than or equal to start_date")
    
    shifts = await get_device_shifts(db, device_id)
    
    if not shifts:
        return {
            "device_id": device_id,
            "period": {"start": start_date, "end": end_date},
            "uptime_percentage": None,
            "total_scheduled_minutes": 0,
            "actual_running_minutes": 0,
            "downtime_minutes": 0,
            "shifts_evaluated": [],
            "message": "No shifts configured"
        }
    
    total_scheduled, shifts_evaluated = calculate_scheduled_minutes(shifts, start, end)
    
    if actual_running_minutes is None:
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if device and device.last_seen_timestamp:
            days_diff = (end - start).days + 1
            estimated_daily_runtime = 8 * 60
            actual_running_minutes = min(
                total_scheduled,
                days_diff * estimated_daily_runtime
            )
        else:
            actual_running_minutes = 0
    else:
        actual_running_minutes = min(actual_running_minutes, total_scheduled)
    
    downtime = max(0, total_scheduled - actual_running_minutes)
    
    uptime_pct = None
    if total_scheduled > 0:
        uptime_pct = (actual_running_minutes / total_scheduled) * 100
    
    return {
        "device_id": device_id,
        "period": {"start": start_date, "end": end_date},
        "uptime_percentage": round(uptime_pct, 2) if uptime_pct is not None else None,
        "total_scheduled_minutes": total_scheduled,
        "actual_running_minutes": actual_running_minutes,
        "downtime_minutes": downtime,
        "shifts_evaluated": shifts_evaluated
    }
