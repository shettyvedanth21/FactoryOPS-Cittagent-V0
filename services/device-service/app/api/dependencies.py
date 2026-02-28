from fastapi import Request
from fastapi.responses import JSONResponse

from shared.exceptions import FactoryOpsException
from shared.logging_config import setup_logging

logger = setup_logging("device-service")


async def factory_ops_exception_handler(request: Request, exc: FactoryOpsException):
    from shared.response import error_response
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details
        )
    )


async def generic_exception_handler(request: Request, exc: Exception):
    from shared.response import error_response
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred"
        )
    )
