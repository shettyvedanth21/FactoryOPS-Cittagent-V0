from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.routes import devices, shifts, health, uptime
from app.api.dependencies import factory_ops_exception_handler, generic_exception_handler
from app.config import settings
from shared.exceptions import FactoryOpsException
from shared.logging_config import setup_logging
from shared.response import success_response, error_response


logger = setup_logging(settings.SERVICE_NAME)


app = FastAPI(
    title="Device Service",
    version="1.0.0",
    description="FactoryOPS Device Management Service"
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
            content=error_response(
                code="SERVICE_UNAVAILABLE",
                message="Database not ready",
                details=[{"database": str(e)}]
            )
        )


app.include_router(devices.router, prefix="/api/v1", tags=["devices"])
app.include_router(shifts.router, prefix="/api/v1", tags=["shifts"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(uptime.router, prefix="/api/v1", tags=["uptime"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"Device service starting on port 8000")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Device service shutting down")
