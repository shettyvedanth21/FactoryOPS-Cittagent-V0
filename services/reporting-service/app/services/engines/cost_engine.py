from typing import List, Dict, Any, Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reporting import TenantTariff
from app.config import settings

logger = logging.getLogger(__name__)


class CostEngine:
    async def calculate_cost(
        self,
        db: AsyncSession,
        tenant_id: str,
        total_kwh: float,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        tariff = await self._get_tariff(db, tenant_id)
        
        if tariff:
            rate_per_unit = tariff.rate_per_unit
            currency = tariff.currency
            peak_rate = tariff.peak_rate
            peak_start = tariff.peak_start_time
            peak_end = tariff.peak_end_time
        else:
            rate_per_unit = settings.DEFAULT_TARIFF_RATE
            currency = "INR"
            peak_rate = None
            peak_start = None
            peak_end = None
        
        total_cost = total_kwh * rate_per_unit
        
        return {
            "total_kwh": round(total_kwh, 2),
            "total_cost": round(total_cost, 2),
            "currency": currency,
            "rate_per_unit": rate_per_unit,
            "peak_rate": peak_rate,
            "peak_hours": {
                "start": peak_start,
                "end": peak_end
            } if peak_start and peak_end else None
        }
    
    async def _get_tariff(
        self,
        db: AsyncSession,
        tenant_id: str
    ) -> Optional[TenantTariff]:
        query = select(TenantTariff).where(
            TenantTariff.tenant_id == tenant_id,
            TenantTariff.is_active == True
        ).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def calculate_cost_breakdown(
        self,
        db: AsyncSession,
        tenant_id: str,
        energy_breakdown: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        results = []
        
        for device_data in energy_breakdown:
            device_id = device_data.get("device_id")
            total_kwh = device_data.get("total_kwh", 0)
            
            cost_data = await self.calculate_cost(db, tenant_id, total_kwh)
            
            results.append({
                "device_id": device_id,
                **cost_data
            })
        
        return results


cost_engine = CostEngine()
