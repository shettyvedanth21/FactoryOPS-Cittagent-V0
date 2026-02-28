from typing import Any, Optional


class FactoryOpsException(Exception):
    """Base exception for all FactoryOPS errors."""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[list] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


class DeviceNotFoundException(FactoryOpsException):
    """Raised when a device is not found."""
    
    def __init__(self, device_id: str):
        super().__init__(
            code="DEVICE_NOT_FOUND",
            message=f"Device with ID '{device_id}' not found",
            status_code=404,
            details=[{"device_id": device_id}]
        )
        self.device_id = device_id


class DuplicateDeviceException(FactoryOpsException):
    """Raised when attempting to create a device that already exists."""
    
    def __init__(self, device_id: str):
        super().__init__(
            code="DUPLICATE_DEVICE",
            message=f"Device with ID '{device_id}' already exists",
            status_code=409,
            details=[{"device_id": device_id}]
        )
        self.device_id = device_id


class ValidationException(FactoryOpsException):
    """Raised when validation fails."""
    
    def __init__(self, details: list):
        super().__init__(
            code="VALIDATION_ERROR",
            message="Validation failed",
            status_code=400,
            details=details
        )


class ServiceUnavailableException(FactoryOpsException):
    """Raised when a downstream service is unavailable."""
    
    def __init__(self, service_name: str):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=f"Service '{service_name}' is currently unavailable",
            status_code=503,
            details=[{"service": service_name}]
        )
        self.service_name = service_name


class RuleNotFoundException(FactoryOpsException):
    """Raised when a rule is not found."""
    
    def __init__(self, rule_id: int):
        super().__init__(
            code="RULE_NOT_FOUND",
            message=f"Rule with ID '{rule_id}' not found",
            status_code=404,
            details=[{"rule_id": rule_id}]
        )
        self.rule_id = rule_id


class AlertNotFoundException(FactoryOpsException):
    """Raised when an alert is not found."""
    
    def __init__(self, alert_id: int):
        super().__init__(
            code="ALERT_NOT_FOUND",
            message=f"Alert with ID '{alert_id}' not found",
            status_code=404,
            details=[{"alert_id": alert_id}]
        )
        self.alert_id = alert_id
