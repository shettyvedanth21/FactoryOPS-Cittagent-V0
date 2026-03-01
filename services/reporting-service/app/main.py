from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import reports, schedules, tariffs
from app.api.dependencies import factory_ops_exception_handler, generic_exception_handler
from app.config import settings
from shared.exceptions import FactoryOpsException
from shared.logging_config import setup_logging
from shared.response import success_response

logger = setup_logging(settings.SERVICE_NAME)


app = FastAPI(
    title="Reporting Service",
    version="1.0.0",
    description="FactoryOPS Reporting and Analytics Service"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(FactoryOpsException, factory_ops_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health")
async def health_check():
    return success_response({"status": "ok", "service": settings.SERVICE_NAME})


@app.get("/health/ready")
async def readiness_check():
    from app.db.session import engine
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return success_response({"status": "ready", "database": "connected"})
    except SQLAlchemyError as e:
        logger.error(f"Database not ready: {str(e)}")
        return JSONResponse(
            status_code=503,
            content=success_response(
                data={"status": "not ready", "database": "disconnected"}
            )
        )


app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(schedules.router, prefix="/api/v1", tags=["schedules"])
app.include_router(tariffs.router, prefix="/api/v1", tags=["tariffs"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"Reporting service starting on port 8085")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Reporting service shutting down")
    from app.scheduler.report_scheduler import scheduler
    scheduler.stop()
