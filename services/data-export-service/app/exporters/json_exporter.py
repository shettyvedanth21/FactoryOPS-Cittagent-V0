import pandas as pd
from io import BytesIO
import json
import logging

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export telemetry data to JSON format."""
    
    def export(self, df: pd.DataFrame) -> bytes:
        """
        Export DataFrame to JSON bytes.
        
        Args:
            df: DataFrame with telemetry data
            
        Returns:
            JSON file as bytes
        """
        if df.empty:
            logger.warning("Exporting empty DataFrame")
            return b"[]"
        
        data_dict = df.to_dict(orient="records")
        
        json_bytes = json.dumps(data_dict, indent=2, default=str).encode("utf-8")
        
        logger.info(f"Exported {len(df)} rows to JSON ({len(json_bytes)} bytes)")
        
        return json_bytes
    
    def get_content_type(self) -> str:
        return "application/json"
    
    def get_file_extension(self) -> str:
        return "json"


json_exporter = JSONExporter()
