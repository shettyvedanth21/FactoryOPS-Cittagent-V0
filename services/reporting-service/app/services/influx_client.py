from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app.config import settings

logger = logging.getLogger(__name__)


class InfluxDBClientWrapper:
    def __init__(self):
        self._client: Optional[InfluxDBClient] = None
    
    def get_client(self) -> InfluxDBClient:
        if self._client is None:
            self._client = InfluxDBClient(
                url=settings.INFLUX_URL,
                token=settings.INFLUX_TOKEN,
                org=settings.INFLUX_ORG
            )
        return self._client
    
    async def query_telemetry(
        self,
        device_ids: List[str],
        start_time: str,
        end_time: str,
        fields: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        if fields is None:
            fields = ["power"]
        
        results = {}
        
        for device_id in device_ids:
            field_conditions = " or ".join([f'r["_field"] == "{f}"' for f in fields])
            query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["device_id"] == "{device_id}")
            |> filter(fn: (r) => {field_conditions})
            |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            try:
                client = self.get_client()
                query_api = client.query_api()
                tables = query_api.query(query)
                
                device_data = []
                for table in tables:
                    for row in table.records:
                        device_data.append({
                            "time": row.get_time().isoformat(),
                            "device_id": device_id,
                            **{field: row.values.get(field) for field in fields}
                        })
                
                results[device_id] = device_data
            except Exception as e:
                logger.error(f"Error querying InfluxDB for device {device_id}: {e}")
                results[device_id] = []
        
        return results
    
    async def aggregate_telemetry(
        self,
        device_ids: List[str],
        start_time: str,
        end_time: str,
        aggregate_window: str = "1d"
    ) -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        
        for device_id in device_ids:
            query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r["device_id"] == "{device_id}")
            |> filter(fn: (r) => r["_field"] == "power")
            |> aggregateWindow(every: {aggregate_window}, fn: mean, createEmpty: false)
            |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            try:
                client = self.get_client()
                query_api = client.query_api()
                tables = query_api.query(query)
                
                device_data = []
                for table in tables:
                    for row in table.records:
                        device_data.append({
                            "time": row.get_time().isoformat(),
                            "device_id": device_id,
                            "power": row.values.get("power", 0)
                        })
                
                results[device_id] = device_data
            except Exception as e:
                logger.error(f"Error querying InfluxDB for device {device_id}: {e}")
                results[device_id] = []
        
        return results


influx_client = InfluxDBClientWrapper()
