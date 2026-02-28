import json
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.session import get_db
from app.models.reporting import ScheduledReport
from app.models.schemas import ScheduledReportCreate, ScheduledReportUpdate
from app.scheduler.report_scheduler import scheduler
from shared.response import success_response
from shared.exceptions import FactoryOpsException

router = APIRouter()


@router.post("/schedules", status_code=201)
async def create_schedule(
    schedule_data: ScheduledReportCreate,
    db: AsyncSession = Depends(get_db)
):
    schedule_id = str(uuid.uuid4())
    
    next_run = scheduler.calculate_next_run(schedule_data.frequency.value)
    
    schedule = ScheduledReport(
        schedule_id=schedule_id,
        tenant_id="default",
        report_type=schedule_data.report_type.value,
        frequency=schedule_data.frequency.value,
        params_template=json.dumps(schedule_data.params_template),
        is_active=schedule_data.is_active,
        next_run_at=next_run
    )
    
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    
    await scheduler.add_schedule(db, schedule)
    
    return success_response(data={
        "schedule_id": schedule.schedule_id,
        "report_type": schedule.report_type,
        "frequency": schedule.frequency,
        "is_active": schedule.is_active,
        "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None
    })


@router.get("/schedules")
async def list_schedules(
    db: AsyncSession = Depends(get_db)
):
    query = select(ScheduledReport).order_by(ScheduledReport.created_at.desc())
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    schedules_data = []
    for schedule in schedules:
        schedules_data.append({
            "schedule_id": schedule.schedule_id,
            "report_type": schedule.report_type,
            "frequency": schedule.frequency,
            "is_active": schedule.is_active,
            "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
            "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None
        })
    
    return success_response(data=schedules_data)


@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    query = select(ScheduledReport).where(ScheduledReport.schedule_id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise FactoryOpsException(
            code="SCHEDULE_NOT_FOUND",
            message=f"Schedule {schedule_id} not found",
            status_code=404
        )
    
    return success_response(data={
        "schedule_id": schedule.schedule_id,
        "report_type": schedule.report_type,
        "frequency": schedule.frequency,
        "params_template": json.loads(schedule.params_template) if schedule.params_template else {},
        "is_active": schedule.is_active,
        "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        "last_status": schedule.last_status
    })


@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduledReportUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(ScheduledReport).where(ScheduledReport.schedule_id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise FactoryOpsException(
            code="SCHEDULE_NOT_FOUND",
            message=f"Schedule {schedule_id} not found",
            status_code=404
        )
    
    if schedule_data.frequency is not None:
        schedule.frequency = schedule_data.frequency.value
        schedule.next_run_at = scheduler.calculate_next_run(schedule_data.frequency.value)
    
    if schedule_data.params_template is not None:
        schedule.params_template = json.dumps(schedule_data.params_template)
    
    if schedule_data.is_active is not None:
        schedule.is_active = schedule_data.is_active
        if schedule_data.is_active:
            await scheduler.add_schedule(db, schedule)
        else:
            await scheduler.remove_schedule(schedule_id)
    
    schedule.updated_at = datetime.utcnow()
    await db.commit()
    
    return success_response(data={
        "schedule_id": schedule.schedule_id,
        "report_type": schedule.report_type,
        "frequency": schedule.frequency,
        "is_active": schedule.is_active,
        "updated_at": schedule.updated_at.isoformat()
    })


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    query = select(ScheduledReport).where(ScheduledReport.schedule_id == schedule_id)
    result = await db.execute(query)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise FactoryOpsException(
            code="SCHEDULE_NOT_FOUND",
            message=f"Schedule {schedule_id} not found",
            status_code=404
        )
    
    await scheduler.remove_schedule(schedule_id)
    
    await db.delete(schedule)
    await db.commit()
    
    return success_response(data={"message": "Schedule deleted successfully"})
