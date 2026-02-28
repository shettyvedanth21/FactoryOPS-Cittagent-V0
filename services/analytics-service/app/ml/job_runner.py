import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models import AnalyticsJob
from app.influx.data_loader import data_loader
from app.ml.anomaly.isolation_forest import isolation_forest_detector, DataInsufficientError
from app.ml.anomaly.z_score import z_score_detector
from app.ml.prediction.failure_predictor import failure_predictor
from app.ml.result_formatter import result_formatter

logger = logging.getLogger(__name__)


class JobRunner:

    async def run_job(self, job_id: str) -> Dict[str, Any]:
        """Run an ML job with its own dedicated DB session."""
        async with async_session_maker() as db:
            try:
                result = await self._run_job_internal(job_id, db)
                return result
            except Exception as e:
                logger.error(f"Job {job_id} failed: {str(e)}")
                try:
                    await self._update_job_status(
                        job_id, db,
                        status="failed",
                        error_message=str(e)
                    )
                except Exception:
                    pass
                raise

    async def _run_job_internal(self, job_id: str, db: AsyncSession) -> Dict[str, Any]:
        stmt = select(AnalyticsJob).where(AnalyticsJob.job_id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        await self._update_job_status(
            job_id, db,
            status="running",
            started_at=datetime.utcnow(),
            progress=0.0,
            message="Loading data..."
        )

        lookback_days = job.parameters.get("lookback_days", 30) if job.parameters else 30
        target_parameters = job.parameters.get("target_parameters", []) if job.parameters else []
        sensitivity = job.parameters.get("sensitivity", "medium") if job.parameters else "medium"

        df = data_loader.load_features(
            job.device_id,
            lookback_days,
            target_parameters
        )

        if df.empty:
            raise DataInsufficientError(f"No data available for device {job.device_id}")

        await self._update_job_status(
            job_id, db,
            progress=30.0,
            message="Running analysis..."
        )

        if job.analysis_type == "anomaly_detection":
            results = await self._run_anomaly_detection(
                df, sensitivity, lookback_days, job.device_id
            )
        elif job.analysis_type == "failure_prediction":
            results = await self._run_failure_prediction(
                df, target_parameters, lookback_days, job.device_id
            )
        else:
            raise ValueError(f"Unknown analysis type: {job.analysis_type}")

        await self._update_job_status(
            job_id, db,
            progress=90.0,
            message="Formatting results..."
        )

        started_at = job.started_at or datetime.utcnow()
        execution_time = int((datetime.utcnow() - started_at).total_seconds())

        await self._update_job_status(
            job_id, db,
            status="completed",
            progress=100.0,
            message="Analysis complete",
            completed_at=datetime.utcnow(),
            results=results,
            execution_time_seconds=execution_time
        )

        logger.info(f"Job {job_id} completed successfully")
        return results

    async def _run_anomaly_detection(self, df, sensitivity, lookback_days, device_id):
        try:
            anomalies = isolation_forest_detector.detect(
                df, sensitivity=sensitivity, device_id=device_id
            )
        except DataInsufficientError:
            anomalies = z_score_detector.detect(df, device_id=device_id)

        return result_formatter.format_anomaly_results(
            anomalies, df, sensitivity, lookback_days
        )

    async def _run_failure_prediction(self, df, target_parameters, lookback_days, device_id):
        prediction_result = failure_predictor.predict(
            df,
            target_parameters=target_parameters,
            device_id=device_id
        )

        days_available = prediction_result.get("days_available", 0)

        return result_formatter.format_failure_prediction_results(
            prediction_result["failure_probability"],
            prediction_result["risk_factors"],
            prediction_result.get("feature_importances", {}),
            days_available,
            lookback_days
        )

    async def _update_job_status(
        self,
        job_id: str,
        db: AsyncSession,
        status: str = None,
        error_message: str = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        progress: float = None,
        message: str = None,
        results: dict = None,
        execution_time_seconds: int = None
    ):
        update_values = {"updated_at": datetime.utcnow()}

        if status is not None:
            update_values["status"] = status
        if error_message is not None:
            update_values["error_message"] = error_message
        if started_at is not None:
            update_values["started_at"] = started_at
        if completed_at is not None:
            update_values["completed_at"] = completed_at
        if progress is not None:
            update_values["progress"] = progress
        if message is not None:
            update_values["message"] = message
        if results is not None:
            update_values["results"] = results
        if execution_time_seconds is not None:
            update_values["execution_time_seconds"] = execution_time_seconds

        stmt = (
            update(AnalyticsJob)
            .where(AnalyticsJob.job_id == job_id)
            .values(**update_values)
        )

        await db.execute(stmt)
        await db.commit()


job_runner = JobRunner()
