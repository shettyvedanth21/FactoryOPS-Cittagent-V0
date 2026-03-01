from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.config import settings
from src.influx.client import influx_client
from shared.logging_config import setup_logging
from shared.response import success_response, error_response
from shared.exceptions import FactoryOpsException


logger = setup_logging(settings.SERVICE_NAME)


app = FastAPI(
    title="Data Service",
    version="1.0.0",
    description="FactoryOPS Telemetry Data Service"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            message="An unexpected error occurred"
        )
    )


@app.on_event("startup")
async def startup_event():
    logger.info("Data service starting...")
    influx_client.connect()
    from src.mqtt.client import mqtt_client
    from src.mqtt.handler import telemetry_handler
    mqtt_client._message_handler = telemetry_handler
    logger.info(f"Connecting to MQTT broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
    mqtt_client.connect()
    import time
    time.sleep(2)
    logger.info(f"MQTT connected: {mqtt_client.is_connected()}")
    logger.info("Data service started on port 8081")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Data service shutting down...")
    influx_client.disconnect()


@app.get("/health")
async def health_check():
    return success_response({"status": "ok", "service": settings.SERVICE_NAME})


@app.get("/health/ready")
async def readiness_check():
    influx_healthy = influx_client.is_connected()
    if not influx_healthy:
        return JSONResponse(
            status_code=503,
            content=error_response(
                code="SERVICE_UNAVAILABLE",
                message="InfluxDB not ready"
            )
        )
    return success_response({"status": "ready", "influxdb": "connected"})


from src.api.routes import telemetry, websocket, properties

app.include_router(telemetry.router, prefix="/api", tags=["telemetry"])
app.include_router(websocket.router, prefix="/api", tags=["websocket"])
app.include_router(properties.router, prefix="/api", tags=["properties"])
