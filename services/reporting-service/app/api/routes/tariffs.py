from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.session import get_db
from app.models.reporting import TenantTariff
from app.models.schemas import TenantTariffCreate, TenantTariffUpdate
from shared.response import success_response
from shared.exceptions import FactoryOpsException

router = APIRouter()


@router.post("/tariffs", status_code=201)
async def create_tariff(
    tariff_data: TenantTariffCreate,
    db: AsyncSession = Depends(get_db)
):
    tariff = TenantTariff(
        tenant_id="default",
        tariff_name=tariff_data.tariff_name,
        rate_per_unit=tariff_data.rate_per_unit,
        currency=tariff_data.currency,
        peak_rate=tariff_data.peak_rate,
        peak_start_time=tariff_data.peak_start_time,
        peak_end_time=tariff_data.peak_end_time,
        demand_charge=tariff_data.demand_charge,
        power_factor_penalty=tariff_data.power_factor_penalty,
        is_active=tariff_data.is_active
    )
    
    db.add(tariff)
    await db.commit()
    await db.refresh(tariff)
    
    return success_response(data={
        "id": tariff.id,
        "tariff_name": tariff.tariff_name,
        "rate_per_unit": tariff.rate_per_unit,
        "currency": tariff.currency,
        "is_active": tariff.is_active
    })


@router.get("/tariffs")
async def list_tariffs(
    db: AsyncSession = Depends(get_db)
):
    query = select(TenantTariff).order_by(TenantTariff.created_at.desc())
    result = await db.execute(query)
    tariffs = result.scalars().all()
    
    tariffs_data = []
    for tariff in tariffs:
        tariffs_data.append({
            "id": tariff.id,
            "tariff_name": tariff.tariff_name,
            "rate_per_unit": tariff.rate_per_unit,
            "currency": tariff.currency,
            "peak_rate": tariff.peak_rate,
            "peak_start_time": tariff.peak_start_time,
            "peak_end_time": tariff.peak_end_time,
            "is_active": tariff.is_active,
            "created_at": tariff.created_at.isoformat() if tariff.created_at else None
        })
    
    return success_response(data=tariffs_data)


@router.get("/tariffs/{tariff_id}")
async def get_tariff(tariff_id: int, db: AsyncSession = Depends(get_db)):
    query = select(TenantTariff).where(TenantTariff.id == tariff_id)
    result = await db.execute(query)
    tariff = result.scalar_one_or_none()
    
    if not tariff:
        raise FactoryOpsException(
            code="TARIFF_NOT_FOUND",
            message=f"Tariff {tariff_id} not found",
            status_code=404
        )
    
    return success_response(data={
        "id": tariff.id,
        "tariff_name": tariff.tariff_name,
        "rate_per_unit": tariff.rate_per_unit,
        "currency": tariff.currency,
        "peak_rate": tariff.peak_rate,
        "peak_start_time": tariff.peak_start_time,
        "peak_end_time": tariff.peak_end_time,
        "demand_charge": tariff.demand_charge,
        "power_factor_penalty": tariff.power_factor_penalty,
        "is_active": tariff.is_active,
        "created_at": tariff.created_at.isoformat() if tariff.created_at else None,
        "updated_at": tariff.updated_at.isoformat() if tariff.updated_at else None
    })


@router.put("/tariffs/{tariff_id}")
async def update_tariff(
    tariff_id: int,
    tariff_data: TenantTariffUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(TenantTariff).where(TenantTariff.id == tariff_id)
    result = await db.execute(query)
    tariff = result.scalar_one_or_none()
    
    if not tariff:
        raise FactoryOpsException(
            code="TARIFF_NOT_FOUND",
            message=f"Tariff {tariff_id} not found",
            status_code=404
        )
    
    update_data = tariff_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(tariff, field, value)
    
    tariff.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(tariff)
    
    return success_response(data={
        "id": tariff.id,
        "tariff_name": tariff.tariff_name,
        "rate_per_unit": tariff.rate_per_unit,
        "is_active": tariff.is_active,
        "updated_at": tariff.updated_at.isoformat()
    })


@router.delete("/tariffs/{tariff_id}")
async def delete_tariff(tariff_id: int, db: AsyncSession = Depends(get_db)):
    query = select(TenantTariff).where(TenantTariff.id == tariff_id)
    result = await db.execute(query)
    tariff = result.scalar_one_or_none()
    
    if not tariff:
        raise FactoryOpsException(
            code="TARIFF_NOT_FOUND",
            message=f"Tariff {tariff_id} not found",
            status_code=404
        )
    
    await db.delete(tariff)
    await db.commit()
    
    return success_response(data={"message": "Tariff deleted successfully"})
