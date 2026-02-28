from fastapi import APIRouter, Query
import httpx

from src.config import settings
from shared.response import success_response, error_response


router = APIRouter()


@router.get("/properties")
async def get_all_properties(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all device properties across all devices."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.DEVICE_SERVICE_URL}/api/v1/properties",
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
