import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExportCheckpoint
from app.storage.influx_reader import influx_reader
from app.storage.minio_client import minio_client
from app.exporters.exporter_factory import exporter_factory

logger = logging.getLogger(__name__)


class ExportJobRunner:
    """Async job runner for data export tasks."""
    
    async def run_export_job(self, export_id: str, db: AsyncSession):
        """Run an export job asynchronously."""
        try:
            result = await self._run_export_internal(export_id, db)
            return result
        except Exception as e:
            logger.error(f"Export job {export_id} failed: {str(e)}")
            await self._update_export_status(
                export_id, db,
                status="failed",
                error_message=str(e)
            )
            raise
    
    async def _run_export_internal(self, export_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Internal method to run the export job."""
        stmt = select(ExportCheckpoint).where(ExportCheckpoint.export_id == export_id)
        result = await db.execute(stmt)
        export_job = result.scalar_one_or_none()
        
        if not export_job:
            raise ValueError(f"Export job {export_id} not found")
        
        await self._update_export_status(
            export_id, db,
            status="in_progress"
        )
        
        df = influx_reader.query_telemetry(
            export_job.device_id,
            export_job.start_time,
            export_job.end_time
        )
        
        if df.empty:
            await self._update_export_status(
                export_id, db,
                status="completed",
                records_exported=0,
                completed_at=datetime.utcnow()
            )
            return {
                "export_id": export_id,
                "status": "completed",
                "records_exported": 0,
                "message": "No data found for the specified time range"
            }
        
        exporter = exporter_factory.get_exporter(export_job.format)
        
        export_bytes = exporter.export(df)
        
        s3_key = f"exports/{export_job.device_id}/{export_id}.{export_job.format}"
        
        content_type = exporter.get_content_type()
        
        minio_client.upload_file(
            data=export_bytes,
            s3_key=s3_key,
            content_type=content_type
        )
        
        file_size = len(export_bytes)
        
        await self._update_export_status(
            export_id, db,
            status="completed",
            s3_key=s3_key,
            records_exported=len(df),
            file_size_bytes=file_size,
            completed_at=datetime.utcnow()
        )
        
        logger.info(f"Export job {export_id} completed: {len(df)} records")
        
        return {
            "export_id": export_id,
            "status": "completed",
            "records_exported": len(df),
            "file_size_bytes": file_size,
            "s3_key": s3_key
        }
    
    async def _update_export_status(
        self,
        export_id: str,
        db: AsyncSession,
        status: str = None,
        s3_key: str = None,
        records_exported: int = None,
        file_size_bytes: int = None,
        error_message: str = None,
        completed_at: datetime = None
    ):
        """Update export job status in database."""
        update_values = {}
        
        if status is not None:
            update_values["status"] = status
        if s3_key is not None:
            update_values["s3_key"] = s3_key
        if records_exported is not None:
            update_values["records_exported"] = records_exported
        if file_size_bytes is not None:
            update_values["file_size_bytes"] = file_size_bytes
        if error_message is not None:
            update_values["error_message"] = error_message
        if completed_at is not None:
            update_values["completed_at"] = completed_at
        
        stmt = (
            update(ExportCheckpoint)
            .where(ExportCheckpoint.export_id == export_id)
            .values(**update_values)
        )
        
        await db.execute(stmt)
        await db.commit()


export_job_runner = ExportJobRunner()
