from typing import List, Dict, Any
import logging

from app.services.engines.energy_engine import energy_engine

logger = logging.getLogger(__name__)


class ComparisonEngine:
    async def compare_devices(
        self,
        device_ids: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        energy_data = await energy_engine.calculate_energy(
            device_ids=device_ids,
            start_date=start_date,
            end_date=end_date,
            group_by="daily"
        )
        
        ranked_by_kwh = sorted(
            energy_data,
            key=lambda x: x.get("total_kwh", 0),
            reverse=True
        )
        
        ranked_by_efficiency = sorted(
            energy_data,
            key=lambda x: x.get("running_hours", 0) / (x.get("total_kwh", 0.001) or 0.001),
            reverse=True
        )
        
        ranked_by_uptime = sorted(
            energy_data,
            key=lambda x: x.get("running_hours", 0),
            reverse=True
        )
        
        best_performer = ranked_by_kwh[0] if ranked_by_kwh else None
        worst_performer = ranked_by_kwh[-1] if ranked_by_kwh else None
        
        avg_kwh = sum(d.get("total_kwh", 0) for d in energy_data) / len(energy_data) if energy_data else 0
        avg_running_hours = sum(d.get("running_hours", 0) for d in energy_data) / len(energy_data) if energy_data else 0
        
        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "devices": [
                {
                    "device_id": d["device_id"],
                    "total_kwh": d.get("total_kwh", 0),
                    "avg_power_w": d.get("avg_power_w", 0),
                    "peak_power_w": d.get("peak_power_w", 0),
                    "running_hours": d.get("running_hours", 0),
                    "rank_by_consumption": next((i + 1 for i, x in enumerate(ranked_by_kwh) if x["device_id"] == d["device_id"]), 0),
                    "rank_by_efficiency": next((i + 1 for i, x in enumerate(ranked_by_efficiency) if x["device_id"] == d["device_id"]), 0),
                    "rank_by_uptime": next((i + 1 for i, x in enumerate(ranked_by_uptime) if x["device_id"] == d["device_id"]), 0)
                }
                for d in energy_data
            ],
            "best_performer": best_performer["device_id"] if best_performer else None,
            "worst_performer": worst_performer["device_id"] if worst_performer else None,
            "average": {
                "total_kwh": round(avg_kwh, 2),
                "running_hours": round(avg_running_hours, 2)
            }
        }


comparison_engine = ComparisonEngine()
