import uuid
from datetime import datetime, timezone
from typing import Any, Optional


def success_response(
    data: Any,
    pagination: Optional[dict] = None,
    timestamp: Optional[datetime] = None,
    request_id: Optional[str] = None
) -> dict:
    """
    Returns the standard success envelope per LLD §2.2.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    return {
        "success": True,
        "data": data,
        "pagination": pagination or {},
        "timestamp": timestamp.isoformat(),
        "request_id": request_id
    }


def error_response(
    code: str,
    message: str,
    details: Optional[list] = None,
    timestamp: Optional[datetime] = None,
    request_id: Optional[str] = None
) -> dict:
    """
    Returns the standard error envelope per LLD §2.2.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or []
        },
        "timestamp": timestamp.isoformat(),
        "request_id": request_id
    }
