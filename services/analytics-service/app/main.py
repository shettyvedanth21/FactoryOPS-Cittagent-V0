from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.routes import analytics
from app.config import settings
from shared.exceptions import FactoryOpsException
from shared.logging_config import setup_logging
from shared.response import success_response, error_response


logger = setup_logging(settings.SERVICE_NAME)


app = FastAPI(
    title="Analytics Service",
    version="1.0.0",
    description="FactoryOPS ML Analytics Service - Anomaly Detection & Failure Prediction"
)


@app.exception_handler(FactoryOpsException)
async def factory_ops_exception_handler(request: Request, exc: FactoryOpsException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details
        )
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error_response(
            code="INTERNAL_ERROR",
            message="An internal error occurred"
        )
    )


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


app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"Analytics service starting on port {settings.PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Analytics service shutting down")
