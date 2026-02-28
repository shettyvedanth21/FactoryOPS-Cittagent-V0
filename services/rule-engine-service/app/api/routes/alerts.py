from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.rule import Alert
from app.models.schemas import AlertResponse, AlertStatusUpdate
from app.services.alert_manager import AlertManager
from shared.response import success_response
from shared.exceptions import AlertNotFoundException, ValidationException

router = APIRouter()

alert_manager = AlertManager()


@router.get("/alerts")
async def list_alerts(
    device_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).order_by(Alert.created_at.desc())
    
    if device_id:
        query = query.where(Alert.device_id == device_id)
    if status:
        query = query.where(Alert.status == status)
    if severity:
        query = query.where(Alert.severity == severity)
    if rule_id:
        query = query.where(Alert.rule_id == rule_id)
    
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    count_query = select(Alert)
    if device_id:
        count_query = count_query.where(Alert.device_id == device_id)
    if status:
        count_query = count_query.where(Alert.status == status)
    if severity:
        count_query = count_query.where(Alert.severity == severity)
    if rule_id:
        count_query = count_query.where(Alert.rule_id == rule_id)
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    alerts_data = []
    for alert in alerts:
        alerts_data.append({
            "alert_id": alert.alert_id,
            "tenant_id": alert.tenant_id,
            "rule_id": alert.rule_id,
            "device_id": alert.device_id,
            "severity": alert.severity,
            "message": alert.message,
            "actual_value": alert.actual_value,
            "threshold_value": alert.threshold_value,
            "property_name": alert.property_name,
            "condition": alert.condition,
            "status": alert.status,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat()
        })
    
    return success_response(
        data=alerts_data,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    )


@router.get("/alerts/{alert_id}")
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).where(Alert.alert_id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise AlertNotFoundException(alert_id)
    
    return success_response(data={
        "alert_id": alert.alert_id,
        "tenant_id": alert.tenant_id,
        "rule_id": alert.rule_id,
        "device_id": alert.device_id,
        "severity": alert.severity,
        "message": alert.message,
        "actual_value": alert.actual_value,
        "threshold_value": alert.threshold_value,
        "property_name": alert.property_name,
        "condition": alert.condition,
        "status": alert.status,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "created_at": alert.created_at.isoformat(),
        "updated_at": alert.updated_at.isoformat()
    })


@router.put("/alerts/{alert_id}/ack")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).where(Alert.alert_id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise AlertNotFoundException(alert_id)
    
    if alert.status == "resolved":
        raise ValidationException([{"message": "Cannot acknowledge a resolved alert"}])
    
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(alert)
    
    return success_response(data={
        "alert_id": alert.alert_id,
        "status": alert.status,
        "acknowledged_at": alert.acknowledged_at.isoformat()
    })


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).where(Alert.alert_id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise AlertNotFoundException(alert_id)
    
    if alert.status == "resolved":
        raise ValidationException([{"message": "Alert is already resolved"}])
    
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(alert)
    
    return success_response(data={
        "alert_id": alert.alert_id,
        "status": alert.status,
        "resolved_at": alert.resolved_at.isoformat()
    })
