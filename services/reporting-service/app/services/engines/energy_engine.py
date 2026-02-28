from typing import List, Dict, Any
from datetime import datetime
import logging

from app.services.influx_client import influx_client

logger = logging.getLogger(__name__)


class EnergyEngine:
    async def calculate_energy(
        self,
        device_ids: List[str],
        start_date: str,
        end_date: str,
        group_by: str = "daily"
    ) -> List[Dict[str, Any]]:
        aggregate_window = self._get_aggregate_window(group_by)
        
        telemetry_data = await influx_client.aggregate_telemetry(
            device_ids=device_ids,
            start_time=start_date,
            end_time=end_date,
            aggregate_window=aggregate_window
        )
        
        results = []
        
        for device_id, data in telemetry_data.items():
            if not data:
                results.append({
                    "device_id": device_id,
                    "period": start_date,
                    "total_kwh": 0.0,
                    "avg_power_w": 0.0,
                    "peak_power_w": 0.0,
                    "running_hours": 0.0,
                    "time_series": []
                })
                continue
            
            power_values = [d.get("power", 0) for d in data if d.get("power") is not None]
            
            total_kwh = sum(power_values) * self._get_interval_hours(group_by)
            avg_power_w = sum(power_values) / len(power_values) if power_values else 0
            peak_power_w = max(power_values) if power_values else 0
            
            running_hours = len([p for p in power_values if p > 0]) * self._get_interval_hours(group_by)
            
            results.append({
                "device_id": device_id,
                "period": start_date,
                "total_kwh": round(total_kwh, 2),
                "avg_power_w": round(avg_power_w, 2),
                "peak_power_w": round(peak_power_w, 2),
                "running_hours": round(running_hours, 2),
                "time_series": [
                    {
                        "time": d["time"],
                        "power": d.get("power", 0)
                    }
                    for d in data
                ]
            })
        
        return results
    
    def _get_aggregate_window(self, group_by: str) -> str:
        mapping = {
            "hourly": "1h",
            "daily": "1d",
            "weekly": "1w",
            "monthly": "1mo"
        }
        return mapping.get(group_by, "1d")
    
    def _get_interval_hours(self, group_by: str) -> float:
        mapping = {
            "hourly": 1.0,
            "daily": 24.0,
            "weekly": 168.0,
            "monthly": 720.0
        }
        return mapping.get(group_by, 24.0)


energy_engine = EnergyEngine()
