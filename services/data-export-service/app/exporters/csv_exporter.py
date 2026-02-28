import pandas as pd
from io import BytesIO
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export telemetry data to CSV format."""
    
    def export(self, df: pd.DataFrame) -> bytes:
        """
        Export DataFrame to CSV bytes.
        
        Args:
            df: DataFrame with telemetry data
            
        Returns:
            CSV file as bytes
        """
        if df.empty:
            logger.warning("Exporting empty DataFrame")
            return b""
        
        output = BytesIO()
        
        df.to_csv(output, index=False)
        
        csv_bytes = output.getvalue()
        
        logger.info(f"Exported {len(df)} rows to CSV ({len(csv_bytes)} bytes)")
        
        return csv_bytes
    
    def get_content_type(self) -> str:
        return "text/csv"
    
    def get_file_extension(self) -> str:
        return "csv"


csv_exporter = CSVExporter()
