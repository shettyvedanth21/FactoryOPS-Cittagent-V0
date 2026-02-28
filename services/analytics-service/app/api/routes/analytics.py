from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import uuid
import asyncio

from app.db.session import get_db
from app.models import AnalyticsJob
from app.api.routes.schemas import (
    AnalyticsJobCreate,
    AnalyticsJobResponse,
    AnalyticsJobStatus,
    DataAvailabilityResponse,
    MLModelInfo,
    PaginatedJobsResponse
)
from app.influx.data_loader import data_loader
from app.ml.job_runner import job_runner
from shared.response import success_response, error_response

router = APIRouter()


AVAILABLE_MODELS = [
    {
        "model_name": "isolation_forest",
        "analysis_type": "anomaly_detection",
        "description": "Isolation Forest algorithm for detecting anomalous patterns in equipment telemetry",
        "min_data_days": 7,
        "parameters": {
            "sensitivity": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "default": "medium",
                "description": "Detection sensitivity - higher sensitivity detects more anomalies"
            },
            "lookback_days": {
                "type": "integer",
                "default": 30,
                "description": "Number of days of historical data to analyze"
            },
            "target_parameters": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of parameters to analyze (default: all available)"
            }
        },
        "output_format": {
            "anomalies": "List of detected anomalies with timestamp, severity, parameters, context",
            "summary": "Total anomalies, rate, most affected parameter, health impact",
            "recommendations": "Ranked list of recommended actions"
        }
    },
    {
        "model_name": "z_score",
        "analysis_type": "anomaly_detection",
        "description": "Simple z-score based anomaly detection for basic outlier identification",
        "min_data_days": 1,
        "parameters": {
            "lookback_days": {
                "type": "integer",
                "default": 30,
                "description": "Number of days of historical data to analyze"
            },
            "target_parameters": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of parameters to analyze"
            }
        },
        "output_format": {
            "anomalies": "List of detected anomalies with z-scores"
        }
    },
    {
        "model_name": "random_forest",
        "analysis_type": "failure_prediction",
        "description": "Random Forest classifier for predicting equipment failure probability",
        "min_data_days": 30,
        "parameters": {
            "lookback_days": {
                "type": "integer",
                "default": 30,
                "description": "Number of days of historical data to analyze"
            },
            "target_parameters": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of parameters to use for prediction"
            }
        },
        "output_format": {
            "summary": "Failure risk level, probability, estimated remaining life, confidence",
            "risk_factors": "List of contributing factors with trend and context",
            "recommended_actions": "Ranked list of preventive actions"
        }
    }
]


@router.get("/models")
async def list_models():
    """List available ML models with their requirements."""
    return success_response(data=AVAILABLE_MODELS)


@router.get("/datasets/{device_id}")
async def check_data_availability(device_id: str):
    """Check data availability for a device."""
    try:
        availability = data_loader.check_data_availability(device_id)
        
        return success_response(data={
            "device_id": device_id,
            "has_data": availability.get("has_data", False),
            "days_available": availability.get("days_available", 0),
            "parameters": availability.get("parameters", []),
            "oldest_data_point": availability.get("oldest_data_point"),
            "newest_data_point": availability.get("newest_data_point")
        })
    except Exception as e:
        return error_response(
            code="DATA_AVAILABILITY_ERROR",
            message=str(e)
        )


@router.post("/run")
async def run_analysis(
    job_request: AnalyticsJobCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit an ML analysis job.
    Returns job_id immediately while job runs asynchronously.
    """
    analysis_type = job_request.analysis_type
    parameters = job_request.parameters or {}
    
    lookback_days = parameters.get("lookback_days", 30)
    
    min_days = 7 if analysis_type == "anomaly_detection" else 30
    
    try:
        availability = data_loader.check_data_availability(job_request.device_id)
        if not availability.get("has_data"):
            return error_response(
                code="NO_DATA",
                message=f"No telemetry data available for device {job_request.device_id}",
                details=[]
            )
    except Exception:
        pass
    
    job_id = str(uuid.uuid4())
    model_name = "isolation_forest" if analysis_type == "anomaly_detection" else "random_forest"
    
    now = datetime.utcnow()
    date_range_start = now - timedelta(days=lookback_days)
    date_range_end = now
    
    new_job = AnalyticsJob(
        job_id=job_id,
        device_id=job_request.device_id,
        analysis_type=analysis_type,
        model_name=model_name,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        parameters=parameters,
        status="pending",
        created_at=now,
        updated_at=now
    )
    
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    asyncio.create_task(job_runner.run_job(job_id))
    
    return success_response(data={
        "job_id": job_id,
        "status": "pending",
        "message": "Job submitted successfully. Use GET /jobs/{job_id} to check status."
    })


@router.get("/jobs")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    device_id: str = Query(None),
    analysis_type: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all analytics jobs with pagination and filters."""
    query = select(AnalyticsJob)
    
    if status:
        query = query.where(AnalyticsJob.status == status)
    if device_id:
        query = query.where(AnalyticsJob.device_id == device_id)
    if analysis_type:
        query = query.where(AnalyticsJob.analysis_type == analysis_type)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(AnalyticsJob.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    pages = (total + page_size - 1) // page_size
    
    items = []
    for job in jobs:
        items.append({
            "job_id": job.job_id,
            "device_id": job.device_id,
            "analysis_type": job.analysis_type,
            "model_name": job.model_name,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "execution_time_seconds": job.execution_time_seconds
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


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get job status by ID."""
    stmt = select(AnalyticsJob).where(AnalyticsJob.job_id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        return error_response(
            code="JOB_NOT_FOUND",
            message=f"Job {job_id} not found"
        )
    
    return success_response(data={
        "job_id": job.job_id,
        "device_id": job.device_id,
        "analysis_type": job.analysis_type,
        "model_name": job.model_name,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "error_message": job.error_message,
        "parameters": job.parameters,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "execution_time_seconds": job.execution_time_seconds
    })


@router.get("/results/{job_id}")
async def get_job_results(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get full job results (only available when job is completed)."""
    stmt = select(AnalyticsJob).where(AnalyticsJob.job_id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        return error_response(
            code="JOB_NOT_FOUND",
            message=f"Job {job_id} not found"
        )
    
    if job.status != "completed":
        return error_response(
            code="RESULTS_NOT_READY",
            message=f"Job is {job.status}. Results available only when status is 'completed'."
        )
    
    return success_response(data=job.results)


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel and delete a job."""
    stmt = select(AnalyticsJob).where(AnalyticsJob.job_id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        return error_response(
            code="JOB_NOT_FOUND",
            message=f"Job {job_id} not found"
        )
    
    if job.status == "running":
        await db.delete(job)
        await db.commit()
        
        return success_response(data={
            "job_id": job_id,
            "status": "cancelled",
            "message": "Running job cancelled and deleted"
        })
    
    await db.delete(job)
    await db.commit()
    
    return success_response(data={
        "job_id": job_id,
        "status": "deleted",
        "message": "Job deleted successfully"
    })
