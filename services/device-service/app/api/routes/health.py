from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import (
    HealthConfigCreate,
    HealthConfigBulkCreate,
    HealthConfigResponse,
    HealthScoreRequest,
    HealthScoreResponse,
    HealthConfigValidateResponse
)
from app.services import device_service, health_calculator
from shared.response import success_response
from shared.exceptions import DeviceNotFoundException


router = APIRouter()


@router.post("/devices/{device_id}/health-config", status_code=201)
async def create_health_config(
    device_id: str,
    config_data: HealthConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create or update a health config for a device."""
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
    
    config = await health_calculator.create_health_config(
        db, device_id, config_data.model_dump()
    )
    
    return success_response(HealthConfigResponse.model_validate(config).model_dump())


@router.get("/devices/{device_id}/health-config")
async def get_health_configs(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all health configs for a device."""
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
    
    configs = await health_calculator.get_health_configs(db, device_id)
    config_list = [HealthConfigResponse.model_validate(c).model_dump() for c in configs]
    
    return success_response(config_list)


@router.post("/devices/{device_id}/health-config/bulk", status_code=201)
async def bulk_create_health_config(
    device_id: str,
    bulk_data: HealthConfigBulkCreate,
    db: AsyncSession = Depends(get_db)
):
    """Bulk create health configs (replace all active configs)."""
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
    
    configs = await health_calculator.bulk_create_health_configs(
        db, device_id, [c.model_dump() for c in bulk_data.configs]
    )
    
    config_list = [HealthConfigResponse.model_validate(c).model_dump() for c in configs]
    return success_response(config_list)


@router.get("/devices/{device_id}/health-config/validate")
async def validate_health_config(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate that health config weights sum to 100."""
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
    
    validation = await health_calculator.validate_weights(db, device_id)
    return success_response(HealthConfigValidateResponse(**validation).model_dump())


@router.post("/devices/{device_id}/health-score")
async def calculate_health_score(
    device_id: str,
    request: HealthScoreRequest,
    db: AsyncSession = Depends(get_db)
):
    """Calculate health score based on telemetry."""
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
    
    configs = await health_calculator.get_health_configs(db, device_id)
    
    result = health_calculator.calculate_health_score(configs, request.telemetry)
    
    return success_response(HealthScoreResponse(**result).model_dump())


@router.delete("/devices/{device_id}/health-config/{config_id}")
async def delete_health_config(
    device_id: str,
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a health config."""
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
    
    deleted = await health_calculator.delete_health_config(db, config_id)
    
    if not deleted:
        from shared.response import error_response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content=error_response(
                code="CONFIG_NOT_FOUND",
                message=f"Health config '{config_id}' not found"
            )
        )
    
    return success_response({"deleted": True})


@router.get("/devices/{device_id}/health-score/latest")
async def get_latest_health_score(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Calculate health score based on latest telemetry."""
    import httpx
    
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
    
    configs = await health_calculator.get_health_configs(db, device_id)
    
    if not configs:
        return success_response({
            "score": None,
            "grade": "N/A",
            "message": "No health configs configured"
        })
    
    try:
        async with httpx.AsyncClient() as client:
            telemetry_resp = await client.get(
                f"http://data-service:8081/api/telemetry/{device_id}/latest",
                timeout=10.0
            )
            telemetry_resp.raise_for_status()
            telemetry_data = telemetry_resp.json()
            
            if not telemetry_data.get("success") or not telemetry_data.get("data"):
                return success_response({
                    "score": None,
                    "grade": "N/A",
                    "message": "No telemetry data available"
                })
            
            telemetry = telemetry_data["data"]
            meta_fields = ['timestamp', 'result', 'table', '_start', '_stop', '_result']
            clean_telemetry = {k: v for k, v in telemetry.items() if k not in meta_fields and isinstance(v, (int, float))}
            
            result = health_calculator.calculate_health_score(configs, clean_telemetry)
            
            score = result.get("health_score", 0)
            if score >= 90:
                grade = "A"
            elif score >= 75:
                grade = "B"
            elif score >= 60:
                grade = "C"
            elif score >= 40:
                grade = "D"
            else:
                grade = "F"
            
            return success_response({
                "score": round(score, 1),
                "grade": grade,
                "breakdown": result.get("breakdown", []),
                "message": None
            })
            
    except Exception as e:
        return success_response({
            "score": None,
            "grade": "N/A",
            "message": f"Error calculating score: {str(e)}"
        })
