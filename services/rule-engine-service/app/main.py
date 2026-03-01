from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import rules, alerts
from app.api.dependencies import factory_ops_exception_handler, generic_exception_handler
from app.config import settings
from shared.exceptions import FactoryOpsException
from shared.logging_config import setup_logging
from shared.response import success_response


logger = setup_logging(settings.SERVICE_NAME)


app = FastAPI(
    title="Rule Engine Service",
    version="1.0.0",
    description="FactoryOPS Rule Engine and Alert Management Service"
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


app.include_router(rules.router, prefix="/api/v1", tags=["rules"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"Rule engine service starting on port 8002")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Rule engine service shutting down")
    from app.services.cooldown_manager import cooldown_manager
    await cooldown_manager.close()
