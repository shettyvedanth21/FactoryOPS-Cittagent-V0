from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query
import httpx

from src.influx.client import influx_client
from src.config import settings
from shared.response import success_response, error_response


router = APIRouter()


@router.get("/telemetry/{device_id}")
async def get_telemetry(
    device_id: str,
    start: str = Query(..., description="Start time (ISO 8601)"),
    end: str = Query(..., description="End time (ISO 8601)"),
    fields: Optional[str] = Query(None, description="Comma-separated fields"),
    aggregate: Optional[str] = Query(None, description="Aggregation (1m, 5m, 1h)"),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get telemetry data for a device within a time range."""
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        return error_response(
            code="VALIDATION_ERROR",
            message="Invalid date format. Use ISO 8601."
        )
    
    field_list = fields.split(",") if fields else None
    
    records = influx_client.query_telemetry(
        device_id=device_id,
        start=start_dt,
        end=end_dt,
        fields=field_list,
        aggregate=aggregate
    )
    
    total = len(records)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_records = records[start_idx:end_idx]
    
    return success_response(
        data=paginated_records,
        pagination={
            "page": page,
            "limit": limit,
            "total": total
        }
    )


@router.get("/telemetry/{device_id}/latest")
async def get_latest_telemetry(device_id: str):
    """Get the latest telemetry data point for a device."""
    latest = influx_client.query_latest(device_id)
    
    if latest is None:
        return success_response(
            data=None,
            pagination={"page": 1, "limit": 1, "total": 0}
        )
    
    return success_response(data=latest)


@router.get("/properties")
async def get_all_properties(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all device properties across all devices."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.DEVICE_SERVICE_URL}/api/v1/devices/properties",
                params={"page": page, "limit": limit}
            )
            
            if response.status_code != 200:
                return error_response(
                    code="FETCH_ERROR",
                    message="Failed to fetch properties"
                )
            
            data = response.json()
            return success_response(
                data=data.get("data", []),
                pagination=data.get("pagination", {})
            )
    
    except Exception as e:
        return error_response(
            code="FETCH_ERROR",
            message=f"Failed to fetch properties: {str(e)}"
        )


@router.get("/properties/{device_id}")
async def get_device_properties(device_id: str):
    """Get properties for a specific device."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.DEVICE_SERVICE_URL}/api/v1/devices/{device_id}/properties"
            )
            
            if response.status_code != 200:
                return error_response(
                    code="FETCH_ERROR",
                    message=f"Failed to fetch properties for device {device_id}"
                )
            
            data = response.json()
            return success_response(data=data.get("data", []))
    
    except Exception as e:
        return error_response(
            code="FETCH_ERROR",
            message=f"Failed to fetch properties: {str(e)}"
        )
