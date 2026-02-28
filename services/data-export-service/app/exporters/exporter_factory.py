from typing import Dict, Any
from app.exporters.csv_exporter import csv_exporter
from app.exporters.parquet_exporter import parquet_exporter
from app.exporters.json_exporter import json_exporter


class ExporterFactory:
    """Factory for creating exporters based on format."""
    
    _exporters = {
        "csv": csv_exporter,
        "parquet": parquet_exporter,
        "json": json_exporter
    }
    
    @classmethod
    def get_exporter(cls, format: str):
        """Get exporter for the specified format."""
        exporter = cls._exporters.get(format.lower())
        if exporter is None:
            raise ValueError(f"Unsupported export format: {format}")
        return exporter
    
    @classmethod
    def get_supported_formats(cls):
        """Get list of supported formats."""
        return list(cls._exporters.keys())


exporter_factory = ExporterFactory()
