from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import DeviceCreate, DeviceUpdate, DeviceResponse, PaginationInfo
from app.services import device_service
from shared.response import success_response, error_response


router = APIRouter()


@router.post("/devices", status_code=201)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device."""
    device = await device_service.create_device(db, device_data)
    device.status = device_service.compute_device_status(device)
    return success_response(DeviceResponse.model_validate(device).model_dump())


@router.get("/devices")
async def get_devices(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    status: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of devices."""
    devices, total = await device_service.get_devices(
        db, page, limit, status, device_type, search
    )
    
    device_list = []
    for device in devices:
        device_dict = DeviceResponse.model_validate(device).model_dump()
        device_dict["status"] = device_service.compute_device_status(device)
        device_list.append(device_dict)
    
    return success_response(
        data=device_list,
        pagination=PaginationInfo(page=page, limit=limit, total=total).model_dump()
    )


@router.get("/devices/{device_id}")
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a device by ID."""
    device = await device_service.get_device(db, device_id)
    device_dict = DeviceResponse.model_validate(device).model_dump()
    device_dict["status"] = device_service.compute_device_status(device)
    return success_response(device_dict)


@router.put("/devices/{device_id}")
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a device."""
    device = await device_service.update_device(db, device_id, device_data)
    device_dict = DeviceResponse.model_validate(device).model_dump()
    device_dict["status"] = device_service.compute_device_status(device)
    return success_response(device_dict)


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a device."""
    await device_service.delete_device(db, device_id)
    return success_response({"message": "Device deleted successfully"})


@router.post("/devices/{device_id}/heartbeat")
async def update_heartbeat(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Update device heartbeat."""
    device = await device_service.update_heartbeat(db, device_id)
    device_dict = DeviceResponse.model_validate(device).model_dump()
    device_dict["status"] = device_service.compute_device_status(device)
    return success_response(device_dict)


@router.post("/devices/bulk-import", status_code=202)
async def bulk_import_devices(
    csv_data: str,
    db: AsyncSession = Depends(get_db)
):
    """Bulk import devices from CSV."""
    result = await device_service.bulk_import_devices(db, csv_data)
    return success_response(result)
