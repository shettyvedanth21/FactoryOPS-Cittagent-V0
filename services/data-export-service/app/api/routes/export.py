from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from datetime import datetime
import uuid

from app.db.session import get_db
from app.models import ExportCheckpoint
from app.api.routes.schemas import (
    ExportCreateRequest,
    ExportResponse,
    ExportStatusResponse,
    ExportHistoryResponse
)
from app.services.export_job_runner import export_job_runner
from app.storage.minio_client import minio_client
from shared.response import success_response, error_response

router = APIRouter()


@router.post("")
async def create_export(
    request: ExportCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new export job."""
    if request.format not in ["csv", "parquet", "json"]:
        return error_response(
            code="INVALID_FORMAT",
            message="Format must be one of: csv, parquet, json"
        )
    
    if request.start_date >= request.end_date:
        return error_response(
            code="INVALID_DATE_RANGE",
            message="Start date must be before end date"
        )
    
    export_id = str(uuid.uuid4())
    
    new_export = ExportCheckpoint(
        export_id=export_id,
        device_id=request.device_id,
        export_type=request.export_type,
        format=request.format,
        start_time=request.start_date,
        end_time=request.end_date,
        status="pending",
        created_at=datetime.utcnow()
    )
    
    db.add(new_export)
    await db.commit()
    await db.refresh(new_export)
    
    import asyncio
    asyncio.create_task(export_job_runner.run_export_job(export_id, db))
    
    return success_response(
        data={
            "export_id": export_id,
            "status": "pending",
            "message": "Export job created. Use GET /export/{id} to check status."
        },
        status_code=202
    )


@router.get("/{export_id}")
async def get_export_status(
    export_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get export job status and metadata."""
    stmt = select(ExportCheckpoint).where(ExportCheckpoint.export_id == export_id)
    result = await db.execute(stmt)
    export_job = result.scalar_one_or_none()
    
    if not export_job:
        return error_response(
            code="EXPORT_NOT_FOUND",
            message=f"Export job {export_id} not found"
        )
    
    return success_response(data={
        "export_id": export_job.export_id,
        "device_id": export_job.device_id,
        "status": export_job.status,
        "format": export_job.format,
        "export_type": export_job.export_type,
        "start_time": export_job.start_time.isoformat(),
        "end_time": export_job.end_time.isoformat(),
        "records_exported": export_job.records_exported,
        "file_size_bytes": export_job.file_size_bytes,
        "s3_key": export_job.s3_key,
        "error_message": export_job.error_message,
        "created_at": export_job.created_at.isoformat(),
        "completed_at": export_job.completed_at.isoformat() if export_job.completed_at else None
    })


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get download URL for completed export."""
    stmt = select(ExportCheckpoint).where(ExportCheckpoint.export_id == export_id)
    result = await db.execute(stmt)
    export_job = result.scalar_one_or_none()
    
    if not export_job:
        return error_response(
            code="EXPORT_NOT_FOUND",
            message=f"Export job {export_id} not found"
        )
    
    if export_job.status != "completed":
        return error_response(
            code="EXPORT_NOT_COMPLETED",
            message=f"Export is {export_job.status}. Cannot download until completed."
        )
    
    if not export_job.s3_key:
        return error_response(
            code="NO_FILE",
            message="No file available for download"
        )
    
    try:
        download_url = minio_client.get_presigned_url(export_job.s3_key)
        
        return success_response(data={
            "export_id": export_id,
            "download_url": download_url,
            "expires_in_hours": 1
        })
    except Exception as e:
        return error_response(
            code="DOWNLOAD_ERROR",
            message=f"Error generating download URL: {str(e)}"
        )


@router.get("/history")
async def get_export_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    device_id: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List export history with pagination and filters."""
    query = select(ExportCheckpoint)
    
    if device_id:
        query = query.where(ExportCheckpoint.device_id == device_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(ExportCheckpoint.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    exports = result.scalars().all()
    
    pages = (total + page_size - 1) // page_size
    
    items = []
    for exp in exports:
        items.append({
            "export_id": exp.export_id,
            "device_id": exp.device_id,
            "status": exp.status,
            "format": exp.format,
            "records_exported": exp.records_exported,
            "file_size_bytes": exp.file_size_bytes,
            "s3_key": exp.s3_key,
            "created_at": exp.created_at.isoformat(),
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None
        })
    
    return success_response(
        data=items,
        pagination={
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages
        }
    )


@router.delete("/{export_id}")
async def delete_export(
    export_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel and delete an export job."""
    stmt = select(ExportCheckpoint).where(ExportCheckpoint.export_id == export_id)
    result = await db.execute(stmt)
    export_job = result.scalar_one_or_none()
    
    if not export_job:
        return error_response(
            code="EXPORT_NOT_FOUND",
            message=f"Export job {export_id} not found"
        )
    
    if export_job.s3_key and export_job.status == "completed":
        try:
            minio_client.delete_object(export_job.s3_key)
        except Exception as e:
            pass
    
    await db.delete(export_job)
    await db.commit()
    
    return success_response(data={
        "export_id": export_id,
        "status": "deleted",
        "message": "Export job deleted successfully"
    })
