from datetime import datetime
from typing import Optional, List, Dict, Any
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi
import logging
import pandas as pd

from src.config import settings


logger = logging.getLogger(__name__)


class InfluxDBClientWrapper:
    def __init__(self):
        self._client: Optional[InfluxDBClient] = None
        self._write_api = None
        self._query_api = None
    
    def connect(self):
        """Connect to InfluxDB."""
        self._client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        self._query_api = self._client.query_api()
        logger.info("Connected to InfluxDB")
    
    def disconnect(self):
        """Disconnect from InfluxDB."""
        if self._client:
            self._client.close()
            logger.info("Disconnected from InfluxDB")
    
    def is_connected(self) -> bool:
        """Check if connected to InfluxDB."""
        try:
            health = self._client.health()
            return health.status == "pass"
        except Exception:
            return False
    
    def write_telemetry(
        self,
        device_id: str,
        fields: Dict[str, float],
        timestamp: Optional[datetime] = None,
        enrichment_status: str = "success"
    ) -> bool:
        """
        Write telemetry data to InfluxDB.
        
        Measurement: telemetry
        Tags: device_id, schema_version, enrichment_status
        Fields: all numeric values from telemetry
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            point = (
                Point("telemetry")
                .tag("device_id", device_id)
                .tag("schema_version", "v1")
                .tag("enrichment_status", enrichment_status)
            )
            
            for key, value in fields.items():
                if isinstance(value, (int, float)):
                    point.field(key, float(value))
            
            point.time(timestamp)
            
            self._write_api.write(
                bucket=settings.INFLUX_BUCKET,
                org=settings.INFLUX_ORG,
                record=point
            )
            
            logger.info(f"Wrote telemetry for device {device_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to write telemetry for {device_id}: {str(e)}")
            return False
    
    def query_telemetry(
        self,
        device_id: str,
        start: datetime,
        end: datetime,
        fields: Optional[List[str]] = None,
        aggregate: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query telemetry data from InfluxDB.
        
        Args:
            device_id: Device ID to query
            start: Start time
            end: End time
            fields: Optional list of fields to retrieve
            aggregate: Optional aggregation (1m, 5m, 1h)
        
        Returns:
            List of telemetry records
        """
        try:
            field_str = "*" if not fields else ", ".join(fields)
            
            if aggregate:
                agg_map = {"1m": "1m", "5m": "5m", "1h": "1h"}
                window = agg_map.get(aggregate, "1m")
                query = f'''
                from(bucket: "{settings.INFLUX_BUCKET}")
                |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                |> filter(fn: (r) => r._measurement == "telemetry")
                |> filter(fn: (r) => r.device_id == "{device_id}")
                |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
                |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
                '''
            else:
                query = f'''
                from(bucket: "{settings.INFLUX_BUCKET}")
                |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                |> filter(fn: (r) => r._measurement == "telemetry")
                |> filter(fn: (r) => r.device_id == "{device_id}")
                |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
                '''
            
            result = self._query_api.query_data_frame(query)
            
            if result.empty:
                return []
            
            records = []
            for _, row in result.iterrows():
                record = {"timestamp": row["_time"].isoformat() if hasattr(row["_time"], 'isoformat') else str(row["_time"])}
                for col in result.columns:
                    if col not in ["_time", "_measurement", "device_id", "schema_version", "enrichment_status"]:
                        if col in row and pd.notna(row[col]):
                            val = row[col]
                            if hasattr(val, 'item'):
                                val = val.item()
                            record[col] = val
                records.append(record)
            
            return records
        
        except Exception as e:
            logger.error(f"Failed to query telemetry for {device_id}: {str(e)}")
            return []
    
    def query_latest(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Query the latest telemetry point for a device.
        
        Returns:
            Latest telemetry record or None
        """
        try:
            query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "telemetry")
            |> filter(fn: (r) => r.device_id == "{device_id}")
            |> last()
            |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self._query_api.query_data_frame(query)
            
            if result.empty:
                return None
            
            row = result.iloc[-1]
            record = {"timestamp": str(row["_time"])}
            
            for col in result.columns:
                if col not in ["_time", "_measurement", "device_id", "schema_version", "enrichment_status"]:
                    if col in row:
                        val = row[col]
                        if hasattr(val, 'item'):
                            val = val.item()
                        record[col] = val
            
            return record
        
        except Exception as e:
            logger.error(f"Failed to query latest telemetry for {device_id}: {str(e)}")
            return None


influx_client = InfluxDBClientWrapper()


async def get_influx_client() -> InfluxDBClientWrapper:
    return influx_client
