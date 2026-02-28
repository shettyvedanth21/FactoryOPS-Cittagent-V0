from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class InfluxDataLoader:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.INFLUX_URL,
            token=settings.INFLUX_TOKEN,
            org=settings.INFLUX_ORG
        )
        self.query_api = self.client.query_api()

    def load_features(
        self,
        device_id: str,
        lookback_days: int,
        target_parameters: List[str]
    ) -> pd.DataFrame:
        """Load feature data from InfluxDB using Flux query language."""
        if not target_parameters:
            target_parameters = ["temperature", "vibration", "pressure", "power", "current"]

        field_conditions = " or ".join(
            [f'r["_field"] == "{p}"' for p in target_parameters]
        )

        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -{lookback_days}d)
          |> filter(fn: (r) => r["_measurement"] == "telemetry")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> filter(fn: (r) => {field_conditions})
          |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
          |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"])
        '''

        try:
            result = self.query_api.query_data_frame(query, org=settings.INFLUX_ORG)

            if result is None or (isinstance(result, pd.DataFrame) and result.empty):
                logger.warning(f"No data found for device {device_id}")
                return pd.DataFrame()

            if isinstance(result, list):
                if not result:
                    return pd.DataFrame()
                result = pd.concat(result, ignore_index=True)

            drop_cols = [c for c in ["result", "table", "_measurement", "_start", "_stop"] if c in result.columns]
            if drop_cols:
                result = result.drop(columns=drop_cols)

            if "_time" in result.columns:
                result = result.rename(columns={"_time": "timestamp"})
            
            # Drop any remaining non-numeric columns except timestamp
            non_numeric = [
                c for c in result.columns
                if c != "timestamp" and not pd.api.types.is_numeric_dtype(result[c])
            ]
            if non_numeric:
                result = result.drop(columns=non_numeric)
            
            numeric_cols = result.select_dtypes(include=["float64", "int64"]).columns
            result[numeric_cols] = result[numeric_cols].ffill().bfill()

            logger.info(f"Loaded {len(result)} data points for device {device_id}")
            return result

        except Exception as e:
            logger.error(f"Error loading features for {device_id}: {str(e)}")
            raise

    def check_data_availability(self, device_id: str) -> Dict[str, Any]:
        """Check data availability for a device using Flux."""
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -90d)
          |> filter(fn: (r) => r["_measurement"] == "telemetry")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> first()
        '''

        query_last = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -90d)
          |> filter(fn: (r) => r["_measurement"] == "telemetry")
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> last()
        '''

        try:
            first_result = self.query_api.query(query, org=settings.INFLUX_ORG)
            last_result = self.query_api.query(query_last, org=settings.INFLUX_ORG)

            first_records = [r for table in first_result for r in table.records]
            last_records = [r for table in last_result for r in table.records]

            if not first_records:
                return {
                    "has_data": False,
                    "days_available": 0,
                    "parameters": [],
                    "oldest_data_point": None,
                    "newest_data_point": None
                }

            oldest = None
            newest = None
            for r in first_records:
                if r.get_time():
                    oldest = r.get_time()
                    break
            
            for r in last_records:
                if r.get_time():
                    newest = r.get_time()
                    break
                    
            days_available = (newest - oldest).days if oldest and newest else 0

            params_query = f'''
            from(bucket: "{settings.INFLUX_BUCKET}")
              |> range(start: -90d)
              |> filter(fn: (r) => r["device_id"] == "{device_id}")
              |> keep(columns: ["_field"])
              |> distinct(column: "_field")
            '''
            params_result = self.query_api.query(params_query, org=settings.INFLUX_ORG)
            parameters = [r.get_value() for table in params_result for r in table.records]

            return {
                "has_data": len(first_records) > 0,
                "days_available": days_available,
                "parameters": parameters,
                "oldest_data_point": oldest.isoformat() if oldest else None,
                "newest_data_point": newest.isoformat() if newest else None
            }

        except Exception as e:
            logger.error(f"Error checking data availability for {device_id}: {str(e)}")
            return {
                "has_data": False,
                "days_available": 0,
                "parameters": [],
                "oldest_data_point": None,
                "newest_data_point": None
            }

    def get_available_parameters(self, device_id: str) -> List[str]:
        """Get list of available parameters for a device using Flux."""
        query = f'''
        from(bucket: "{settings.INFLUX_BUCKET}")
          |> range(start: -90d)
          |> filter(fn: (r) => r["device_id"] == "{device_id}")
          |> keep(columns: ["_field"])
          |> distinct(column: "_field")
        '''
        try:
            result = self.query_api.query(query, org=settings.INFLUX_ORG)
            return [r.get_value() for table in result for r in table.records]
        except Exception as e:
            logger.error(f"Error getting parameters for {device_id}: {str(e)}")
            return []


data_loader = InfluxDataLoader()
