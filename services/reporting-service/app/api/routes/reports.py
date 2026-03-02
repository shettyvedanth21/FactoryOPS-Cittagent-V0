import json
import uuid
import logging
from datetime import datetime
from typing import Optional
from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.reporting import EnergyReport, ScheduledReport, TenantTariff
from app.models.schemas import (
    ConsumptionReportRequest, ComparisonReportRequest, WastageReportRequest,
    ScheduledReportCreate, ScheduledReportUpdate,
    TenantTariffCreate, TenantTariffUpdate
)
from app.services.engines.energy_engine import energy_engine
from app.services.engines.wastage_engine import wastage_engine
from app.services.engines.comparison_engine import comparison_engine
from app.services.engines.cost_engine import cost_engine
from app.services.pdf.builder import pdf_builder
from app.storage.minio_client import minio_client
from app.scheduler.report_scheduler import scheduler
from app.config import settings
from shared.response import success_response
from shared.exceptions import FactoryOpsException

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/reports/consumption", status_code=202)
async def create_consumption_report(
    request: ConsumptionReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    report_id = str(uuid.uuid4())
    
    report = EnergyReport(
        report_id=report_id,
        tenant_id="default",
        report_type="consumption",
        status="pending",
        params=json.dumps(request.model_dump()),
        format=request.format.value,
        progress=0
    )
    db.add(report)
    await db.commit()
    
    background_tasks.add_task(
        process_consumption_report,
        report_id,
        request.model_dump()
    )
    
    return success_response(data={
        "report_id": report_id,
        "status": "pending"
    })


@router.post("/reports/comparison", status_code=202)
async def create_comparison_report(
    request: ComparisonReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    report_id = str(uuid.uuid4())
    
    report = EnergyReport(
        report_id=report_id,
        tenant_id="default",
        report_type="comparison",
        status="pending",
        params=json.dumps(request.model_dump()),
        format=request.format.value,
        progress=0
    )
    db.add(report)
    await db.commit()
    
    background_tasks.add_task(
        process_comparison_report,
        report_id,
        request.model_dump()
    )
    
    return success_response(data={
        "report_id": report_id,
        "status": "pending"
    })


@router.get("/reports/history")
async def list_reports(
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(EnergyReport).order_by(EnergyReport.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    count_query = select(EnergyReport)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    reports_data = []
    for report in reports:
        reports_data.append({
            "report_id": report.report_id,
            "report_type": report.report_type,
            "status": report.status,
            "format": report.format,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "completed_at": report.completed_at.isoformat() if report.completed_at else None
        })
    
    return success_response(
        data=reports_data,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    )


@router.get("/reports/wastage")
async def get_wastage_report(
    device_ids: str,
    start_date: str,
    end_date: str,
    db: AsyncSession = Depends(get_db)
):
    device_id_list = device_ids.split(",")
    
    result = await wastage_engine.calculate_wastage(
        db=db,
        tenant_id="default",
        device_ids=device_id_list,
        start_date=start_date,
        end_date=end_date
    )
    
    return success_response(data=result)


@router.get("/reports/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    query = select(EnergyReport).where(EnergyReport.report_id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise FactoryOpsException(
            code="REPORT_NOT_FOUND",
            message=f"Report {report_id} not found",
            status_code=404
        )
    
    return success_response(data={
        "report_id": report.report_id,
        "report_type": report.report_type,
        "status": report.status,
        "progress": report.progress,
        "s3_key": report.s3_key,
        "format": report.format,
        "error_message": report.error_message,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "completed_at": report.completed_at.isoformat() if report.completed_at else None
    })


@router.get("/reports/{report_id}/download")
async def download_report(report_id: str, db: AsyncSession = Depends(get_db)):
    query = select(EnergyReport).where(EnergyReport.report_id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise FactoryOpsException(
            code="REPORT_NOT_FOUND",
            message=f"Report {report_id} not found",
            status_code=404
        )
    
    if report.status == "failed":
        raise FactoryOpsException(
            code="REPORT_FAILED",
            message=report.error_message or "Report generation failed",
            status_code=400
        )
    
    if report.status in ["pending", "processing"]:
        raise FactoryOpsException(
            code="REPORT_NOT_READY",
            message=f"Report is {report.status}",
            status_code=400
        )
    
    if report.status != "completed" or not report.s3_key:
        raise FactoryOpsException(
            code="REPORT_NOT_READY",
            message=f"Report is not ready for download",
            status_code=400
        )
    
    url = await minio_client.generate_download_url(report.s3_key)
    
    return success_response(data={
        "download_url": url
    })


async def process_consumption_report(report_id: str, params: dict):
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        query = select(EnergyReport).where(EnergyReport.report_id == report_id)
        result = await db.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            return
        
        try:
            report.status = "processing"
            await db.commit()
            
            energy_data = await energy_engine.calculate_energy(
                device_ids=params.get("device_ids", []),
                start_date=params.get("start_date"),
                end_date=params.get("end_date"),
                group_by=params.get("group_by", "daily")
            )
            
            # Calculate costs for each device
            for device in energy_data:
                cost_data = await cost_engine.calculate_cost(
                    db=db,
                    tenant_id="default",
                    total_kwh=device.get("total_kwh", 0)
                )
                device["cost_inr"] = cost_data.get("total_cost", 0)
            
            # Build daily breakdown from time_series
            # Each time_series entry with group_by=daily is one data point per day
            # power is in Watts, convert to kWh using interval hours
            daily_breakdown = []
            if energy_data:
                interval_hours = {
                    "hourly": 1.0, "daily": 24.0,
                    "weekly": 168.0, "monthly": 720.0
                }.get(params.get("group_by", "daily"), 24.0)

                date_totals = {}
                for device in energy_data:
                    for ts in device.get("time_series", []):
                        date = str(ts.get("time", ""))[:10]
                        power_w = float(ts.get("power", 0) or 0)
                        # Watts * hours / 1000 = kWh
                        kwh = power_w * interval_hours / 1000.0
                        if date:
                            date_totals[date] = date_totals.get(date, 0) + kwh

                for date in sorted(date_totals):
                    daily_breakdown.append({
                        "date": date,
                        "kwh": round(date_totals[date], 2)
                    })
            
            # Enrich result_json with device names from device-service
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"{settings.DEVICE_SERVICE_URL}/api/v1/devices",
                        params={"limit": 1000}
                    )
                    if resp.status_code == 200:
                        device_list = resp.json().get("data", [])
                        device_name_map = {
                            d["device_id"]: d.get("device_name", d["device_id"])
                            for d in device_list
                        }
                        # Inject device_name into each device in result
                        for dev in energy_data:
                            dev["device_name"] = device_name_map.get(
                                dev["device_id"], dev["device_id"]
                            )
            except Exception as e:
                logger.warning(f"Could not fetch device names: {e}")
            
            result_json = {
                "report_id": report_id,
                "devices": energy_data,
                "daily_breakdown": daily_breakdown,
                "tariff_rate": settings.DEFAULT_TARIFF_RATE,
                "tariff_currency": "INR"
            }
            
            report.result_json = json.dumps(result_json)
            report.progress = 75
            await db.commit()
            
            try:
                pdf_bytes = pdf_builder.build_consumption_report(
                    data=result_json,
                    start_date=params.get("start_date", ""),
                    end_date=params.get("end_date", "")
                )
                s3_key = await minio_client.upload_report(
                    report_id=report_id,
                    content=BytesIO(pdf_bytes),
                    format=params.get("format", "pdf"),
                    tenant_id="default"
                )
                report.s3_key = s3_key
            except Exception as pdf_error:
                logger.warning(f"PDF/upload failed for {report_id}: {str(pdf_error)}")
            
            report.status = "completed"
            report.progress = 100
            report.completed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            logger.error(f"Report {report_id} failed: {str(e)}", exc_info=True)
            report.status = "failed"
            report.error_message = str(e)
            await db.commit()


async def process_comparison_report(report_id: str, params: dict):
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        query = select(EnergyReport).where(EnergyReport.report_id == report_id)
        result = await db.execute(query)
        report = result.scalar_one_or_none()
        
        if not report:
            return
        
        try:
            report.status = "processing"
            await db.commit()
            
            comparison_data = await comparison_engine.compare_devices(
                device_ids=params.get("device_ids", []),
                start_date=params.get("start_date"),
                end_date=params.get("end_date")
            )
            
            result_json = comparison_data
            
            report.result_json = json.dumps(result_json)
            report.status = "completed"
            report.progress = 100
            report.completed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            logger.error(f"Report {report_id} failed: {str(e)}", exc_info=True)
            report.status = "failed"
            report.error_message = str(e)
            await db.commit()
