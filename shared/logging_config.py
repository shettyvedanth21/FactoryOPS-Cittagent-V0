import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


class StructuredJSONFormatter(logging.Formatter):
    """
    Structured JSON formatter per LLD §15.2.
    Output format: {"timestamp": "...", "level": "...", "service": "...", "message": "..."}
    """
    
    def __init__(self, service_name: str = "unknown"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_entry.update(extra_fields)
        
        return json.dumps(log_entry)


def get_logger(service_name: str) -> logging.Logger:
    """
    Factory function to create a logger with structured JSON output.
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJSONFormatter(service_name))
        logger.addHandler(handler)
    
    return logger


def setup_logging(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for a service and return the logger.
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter(service_name))
    logger.addHandler(handler)
    
    return logger
