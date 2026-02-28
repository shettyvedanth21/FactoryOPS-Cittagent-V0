from typing import List, Dict, Any
import logging

from app.services.engines.energy_engine import energy_engine
from app.services.engines.cost_engine import cost_engine
from app.config import settings

logger = logging.getLogger(__name__)


class WastageEngine:
    async def calculate_wastage(
        self,
        db,
        tenant_id: str,
        device_ids: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        energy_data = await energy_engine.calculate_energy(
            device_ids=device_ids,
            start_date=start_date,
            end_date=end_date
        )
        
        total_wasted_kwh = 0.0
        total_consumed_kwh = 0.0
        idle_hours = 0.0
        
        device_results = []
        
        for device_data in energy_data:
            device_id = device_data["device_id"]
            total_kwh = device_data.get("total_kwh", 0)
            power_values = [d.get("power", 0) for d in device_data.get("time_series", [])]
            
            total_consumed_kwh += total_kwh
            
            idle_wastage_kwh = self._calculate_idle_wastage(power_values)
            peak_wastage_kwh = self._calculate_peak_wastage(power_values)
            pressure_wastage_kwh = self._calculate_pressure_wastage(power_values)
            
            wasted_kwh = idle_wastage_kwh + peak_wastage_kwh + pressure_wastage_kwh
            
            if wasted_kwh > total_kwh:
                wasted_kwh = total_kwh
                other_wastage = 0
            else:
                other_wastage = max(0, wasted_kwh - idle_wastage_kwh - peak_wastage_kwh - pressure_wastage_kwh)
            
            total_wasted_kwh += wasted_kwh
            idle_hours += idle_wastage_kwh / 24.0
            
            efficiency_score = 100 - (wasted_kwh / total_kwh * 100) if total_kwh > 0 else 100
            efficiency_grade = self._get_efficiency_grade(efficiency_score)
            
            device_results.append({
                "device_id": device_id,
                "wasted_kwh": round(wasted_kwh, 2),
                "efficiency_score": round(efficiency_score, 2),
                "efficiency_grade": efficiency_grade
            })
        
        total_wasted_kwh = min(total_wasted_kwh, total_consumed_kwh)
        efficiency_score = 100 - (total_wasted_kwh / total_consumed_kwh * 100) if total_consumed_kwh > 0 else 100
        efficiency_grade = self._get_efficiency_grade(efficiency_score)
        
        wasted_rupees = total_wasted_kwh * settings.DEFAULT_TARIFF_RATE
        
        breakdown = [
            {
                "source": "idle_running",
                "kwh": round(total_wasted_kwh * 0.4, 2),
                "percent": 40.0
            },
            {
                "source": "peak_hour_overuse",
                "kwh": round(total_wasted_kwh * 0.3, 2),
                "percent": 30.0
            },
            {
                "source": "pressure_inefficiency",
                "kwh": round(total_wasted_kwh * 0.2, 2),
                "percent": 20.0
            },
            {
                "source": "other",
                "kwh": round(total_wasted_kwh * 0.1, 2),
                "percent": 10.0
            }
        ]
        
        recommendations = [
            {
                "rank": 1,
                "action": "Reduce idle running in off-shift hours",
                "potential_savings_kwh": round(total_wasted_kwh * 0.4, 2),
                "potential_savings_rupees": round(total_wasted_kwh * 0.4 * settings.DEFAULT_TARIFF_RATE, 2)
            },
            {
                "rank": 2,
                "action": "Shift non-critical loads away from peak hours",
                "potential_savings_kwh": round(total_wasted_kwh * 0.3, 2),
                "potential_savings_rupees": round(total_wasted_kwh * 0.3 * settings.DEFAULT_TARIFF_RATE, 2)
            }
        ]
        
        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "summary": {
                "total_wasted_kwh": round(total_wasted_kwh, 2),
                "total_wasted_rupees": round(wasted_rupees, 2),
                "efficiency_score": round(efficiency_score, 2),
                "efficiency_grade": efficiency_grade,
                "idle_hours": round(idle_hours, 2)
            },
            "breakdown": breakdown,
            "recommendations": recommendations,
            "devices": device_results
        }
    
    def _calculate_idle_wastage(self, power_values: List[float]) -> float:
        if not power_values:
            return 0.0
        idle_values = [p for p in power_values if 0 < p < 10]
        return sum(idle_values) * 0.5
    
    def _calculate_peak_wastage(self, power_values: List[float]) -> float:
        if not power_values:
            return 0.0
        sorted_values = sorted(power_values, reverse=True)
        top_20_percent_count = max(1, len(sorted_values) // 5)
        top_values = sorted_values[:top_20_percent_count]
        avg_power = sum(power_values) / len(power_values) if power_values else 1
        peak_wastage = sum([v - avg_power for v in top_values if v > avg_power])
        return peak_wastage * 0.5
    
    def _calculate_pressure_wastage(self, power_values: List[float]) -> float:
        if not power_values:
            return 0.0
        high_power_values = [p for p in power_values if p > 100]
        return sum(high_power_values) * 0.2
    
    def _get_efficiency_grade(self, score: float) -> str:
        if score >= 80:
            return "Good"
        elif score >= 60:
            return "Moderate"
        else:
            return "Poor"


wastage_engine = WastageEngine()
