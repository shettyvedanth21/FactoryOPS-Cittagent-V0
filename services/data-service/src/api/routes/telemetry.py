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
    """Get all device properties (fields) from InfluxDB."""
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
        |> range(start: -7d)
        |> filter(fn: (r) => r._measurement == "telemetry")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> limit(n:10)
        '''
        
        result = influx_client._query_api.query_data_frame(query)
        
        if isinstance(result, list):
            if len(result) == 0:
                return success_response(data=[], pagination={"page": page, "limit": limit, "total": 0})
            result = result[0]
        
        if result.empty:
            return success_response(data=[], pagination={"page": page, "limit": limit, "total": 0})
        
        device_fields = {}
        for _, row in result.iterrows():
            device_id = row.get("device_id")
            if device_id:
                if device_id not in device_fields:
                    device_fields[device_id] = set()
                for col in result.columns:
                    if col not in ["_time", "_measurement", "device_id", "schema_version", "enrichment_status", "_start", "_stop", "result", "table"]:
                        device_fields[device_id].add(col)
        
        all_props = []
        for device_id, fields in device_fields.items():
            for field in fields:
                all_props.append({
                    "property_name": field,
                    "device_id": device_id,
                    "data_type": "numeric"
                })
        
        total = len(all_props)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated = all_props[start_idx:end_idx]
        
        return success_response(
            data=paginated,
            pagination={"page": page, "limit": limit, "total": total}
        )
    
    except Exception as e:
        return error_response(
            code="FETCH_ERROR",
            message=f"Failed to fetch properties: {str(e)}"
        )


@router.get("/properties/{device_id}")
async def get_device_properties(device_id: str):
    """Get properties (fields) for a specific device from InfluxDB."""
    try:
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
        |> range(start: -7d)
        |> filter(fn: (r) => r._measurement == "telemetry")
        |> filter(fn: (r) => r.device_id == "{device_id}")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> limit(n:1)
        '''
        
        result = influx_client._query_api.query_data_frame(query)
        
        if isinstance(result, list) or result.empty or len(result) == 0:
            return success_response(data=[])
        
        row = result.iloc[0]
        fields = []
        for col in result.columns:
            if col not in ["_time", "_measurement", "device_id", "schema_version", "enrichment_status", "_start", "_stop", "result", "table"]:
                fields.append({
                    "property_name": col,
                    "device_id": device_id,
                    "data_type": "numeric"
                })
        
        return success_response(data=fields)
    
    except Exception as e:
        return error_response(
            code="FETCH_ERROR",
            message=f"Failed to fetch properties: {str(e)}"
        )
