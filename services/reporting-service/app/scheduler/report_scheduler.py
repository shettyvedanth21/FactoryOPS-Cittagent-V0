from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reporting import ScheduledReport
from app.config import settings

logger = logging.getLogger(__name__)


class ReportScheduler:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
    
    async def start(self, db: AsyncSession):
        self.scheduler = AsyncIOScheduler()
        
        query = select(ScheduledReport).where(ScheduledReport.is_active == True)
        result = await db.execute(query)
        schedules = result.scalars().all()
        
        for schedule in schedules:
            self._add_job(schedule)
        
        self.scheduler.start()
        logger.info("Report scheduler started")
    
    def stop(self):
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Report scheduler stopped")
    
    def _add_job(self, schedule: ScheduledReport):
        cron_trigger = self._get_cron_trigger(schedule.frequency)
        
        self.scheduler.add_job(
            func=self._run_scheduled_report,
            trigger=cron_trigger,
            id=schedule.schedule_id,
            args=[schedule.schedule_id],
            replace_existing=True
        )
    
    def _get_cron_trigger(self, frequency: str):
        if frequency == "daily":
            return CronTrigger(hour=0, minute=0)
        elif frequency == "weekly":
            return CronTrigger(day_of_week=0, hour=0, minute=0)
        elif frequency == "monthly":
            return CronTrigger(day=1, hour=0, minute=0)
        else:
            return CronTrigger(hour=0, minute=0)
    
    async def _run_scheduled_report(self, schedule_id: str):
        logger.info(f"Running scheduled report: {schedule_id}")
    
    async def add_schedule(
        self,
        db: AsyncSession,
        schedule: ScheduledReport
    ) -> str:
        if not self.scheduler:
            return ""
        
        self._add_job(schedule)
        return schedule.schedule_id
    
    async def remove_schedule(self, schedule_id: str):
        if self.scheduler:
            self.scheduler.remove_job(schedule_id)
    
    def calculate_next_run(self, frequency: str) -> datetime:
        now = datetime.utcnow()
        
        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        else:
            return now + timedelta(days=1)


scheduler = ReportScheduler()
