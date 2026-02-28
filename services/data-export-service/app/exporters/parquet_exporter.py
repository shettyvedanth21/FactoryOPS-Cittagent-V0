import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class ParquetExporter:
    """Export telemetry data to Parquet format."""
    
    def export(self, df: pd.DataFrame) -> bytes:
        """
        Export DataFrame to Parquet bytes.
        
        Args:
            df: DataFrame with telemetry data
            
        Returns:
            Parquet file as bytes
        """
        if df.empty:
            logger.warning("Exporting empty DataFrame")
            return b""
        
        output = BytesIO()
        
        df.to_parquet(output, index=False, engine="pyarrow")
        
        parquet_bytes = output.getvalue()
        
        logger.info(f"Exported {len(df)} rows to Parquet ({len(parquet_bytes)} bytes)")
        
        return parquet_bytes
    
    def get_content_type(self) -> str:
        return "application/octet-stream"
    
    def get_file_extension(self) -> str:
        return "parquet"


parquet_exporter = ParquetExporter()
