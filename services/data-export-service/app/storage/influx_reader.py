from influxdb_client import InfluxDBClient, QueryApi
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime
from typing import Optional, List
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class InfluxDataReader:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        self.query_api = self.client.query_api()
    
    def query_telemetry(
        self,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        fields: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Query telemetry data from InfluxDB for a device in a date range.
        
        Args:
            device_id: Device ID
            start_time: Start datetime
            end_time: End datetime
            fields: Optional list of fields to query
            
        Returns:
            DataFrame with telemetry data
        """
        if fields is None:
            fields = ["*"]
        
        fields_clause = ", ".join([f'mean("{f}") as "{f}"' for f in fields if f != "*"])
        if "*" in fields:
            fields_clause = "*"
        
        query = f'''
        SELECT {fields_clause}
        FROM "telemetry"
        WHERE "device_id" = '{device_id}'
        AND time >= '{start_time.isoformat()}Z'
        AND time <= '{end_time.isoformat()}Z'
        GROUP BY time(1m)
        ORDER BY time
        '''
        
        try:
            result = self.query_api.query_data_frame(query)
            
            if result.empty:
                logger.warning(f"No data found for device {device_id}")
                return pd.DataFrame()
            
            if isinstance(result, list):
                result = pd.concat(result, ignore_index=True)
            
            columns_to_drop = [c for c in ["result", "_measurement"] if c in result.columns]
            if columns_to_drop:
                result = result.drop(columns=columns_to_drop)
            
            if "_time" in result.columns:
                result = result.rename(columns={"_time": "timestamp"})
            elif "time" in result.columns:
                result = result.rename(columns={"time": "timestamp"})
            
            logger.info(f"Queried {len(result)} rows for device {device_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error querying telemetry: {str(e)}")
            raise
    
    def get_available_fields(self, device_id: str) -> List[str]:
        """Get list of available fields for a device."""
        query = f'''
        SHOW FIELD KEYS
        FROM "telemetry"
        '''
        
        try:
            result = self.query_api.query_data_frame(query)
            if result.empty:
                return []
            return result["fieldKey"].tolist() if "fieldKey" in result.columns else []
        except Exception as e:
            logger.error(f"Error getting fields: {str(e)}")
            return []


influx_reader = InfluxDataReader()
