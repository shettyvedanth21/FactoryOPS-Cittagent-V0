from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import UptimeResponse
from app.services import device_service, uptime_calculator
from shared.response import success_response
from shared.exceptions import DeviceNotFoundException


router = APIRouter()


@router.get("/devices/{device_id}/uptime")
async def get_uptime(
    device_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Get uptime statistics for a device over a date range."""
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
    
    try:
        uptime = await uptime_calculator.calculate_uptime(
            db, device_id, start_date, end_date
        )
        return success_response(uptime)
    except ValueError as e:
        from shared.response import error_response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content=error_response(
                code="VALIDATION_ERROR",
                message=str(e)
            )
        )
