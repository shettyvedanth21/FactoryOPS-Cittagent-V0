from typing import List, Optional
import uuid
import json
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from app.db.session import get_db
from app.models.rule import Rule
from app.models.schemas import (
    RuleCreate, RuleUpdate, RuleResponse, RuleStatusUpdate, EvaluateRequest
)
from app.services.rule_evaluator import RuleEvaluator
from shared.response import success_response, error_response
from shared.exceptions import RuleNotFoundException, ValidationException

router = APIRouter()
logger = logging.getLogger(__name__)

rule_evaluator = RuleEvaluator()


@router.get("/rules")
async def list_rules(
    status: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Rule).where(Rule.deleted_at.is_(None))
    
    if status:
        query = query.where(Rule.status == status)
    
    if device_id:
        query = query.where(Rule.device_ids.contains(json.dumps(device_id)))
    
    query = query.order_by(Rule.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    count_query = select(Rule).where(Rule.deleted_at.is_(None))
    if status:
        count_query = count_query.where(Rule.status == status)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    rules_data = []
    for rule in rules:
        rules_data.append({
            "rule_id": rule.rule_id,
            "tenant_id": rule.tenant_id,
            "rule_name": rule.rule_name,
            "description": rule.description,
            "scope": rule.scope,
            "property": rule.property,
            "condition": rule.condition,
            "threshold": rule.threshold,
            "status": rule.status,
            "severity": rule.severity,
            "notification_channels": rule.notification_channels,
            "cooldown_minutes": rule.cooldown_minutes,
            "device_ids": rule.device_ids,
            "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
            "created_at": rule.created_at.isoformat(),
            "updated_at": rule.updated_at.isoformat()
        })
    
    return success_response(
        data=rules_data,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    )


@router.post("/rules", status_code=201)
async def create_rule(
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_db)
):
    rule = Rule(
        rule_id=str(uuid.uuid4()),
        rule_name=rule_data.rule_name,
        description=rule_data.description,
        scope=rule_data.scope.value,
        property=rule_data.property,
        condition=rule_data.condition,
        threshold=rule_data.threshold,
        severity=rule_data.severity.value,
        cooldown_minutes=rule_data.cooldown_minutes,
        device_ids=rule_data.device_ids,
        notification_channels=rule_data.notification_channels,
        status="active"
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    # Send email notification for rule creation
    try:
        recipients = []
        notification_channels = rule_data.notification_channels or {}
        if isinstance(notification_channels, dict):
            email_config = notification_channels.get('email', {})
            if isinstance(email_config, dict) and email_config.get('enabled'):
                recipients = email_config.get('recipients', [])
        
        # Fall back to default recipients from env if none specified
        if not recipients:
            import os
            default = os.getenv("EMAIL_RECIPIENTS", "")
            recipients = [r.strip() for r in default.split(',') if r.strip()]
        
        if recipients:
            from app.services.notification.email_adapter import send_rule_created_notification
            rule_dict = {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "parameter": rule.property,
                "operator": rule.condition,
                "threshold": rule.threshold,
                "severity": rule.severity,
                "device_ids": rule.device_ids or [],
                "notification_channels": rule.notification_channels or {},
                "created_at": rule.created_at.isoformat() if rule.created_at else "Just now"
            }
            send_rule_created_notification(rule_dict, recipients)
    except Exception as e:
        logger.error(f"Failed to send rule creation email: {e}")
    
    return success_response(data={
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "description": rule.description,
        "scope": rule.scope,
        "property": rule.property,
        "condition": rule.condition,
        "threshold": rule.threshold,
        "status": rule.status,
        "severity": rule.severity,
        "notification_channels": rule.notification_channels,
        "cooldown_minutes": rule.cooldown_minutes,
        "device_ids": rule.device_ids,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat()
    })


@router.get("/rules/{rule_id}")
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Rule).where(
        and_(Rule.rule_id == rule_id, Rule.deleted_at.is_(None))
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise RuleNotFoundException(rule_id)
    
    return success_response(data={
        "rule_id": rule.rule_id,
        "tenant_id": rule.tenant_id,
        "rule_name": rule.rule_name,
        "description": rule.description,
        "scope": rule.scope,
        "property": rule.property,
        "condition": rule.condition,
        "threshold": rule.threshold,
        "status": rule.status,
        "severity": rule.severity,
        "notification_channels": rule.notification_channels,
        "cooldown_minutes": rule.cooldown_minutes,
        "device_ids": rule.device_ids,
        "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat()
    })


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(Rule).where(
        and_(Rule.rule_id == rule_id, Rule.deleted_at.is_(None))
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise RuleNotFoundException(rule_id)
    
    update_data = rule_data.model_dump(exclude_unset=True)
    
    if "notification_channels" in update_data and update_data["notification_channels"]:
        update_data["notification_channels"] = update_data["notification_channels"]
    
    for field, value in update_data.items():
        if value is not None:
            if field == "scope":
                setattr(rule, field, value.value)
            elif field == "condition":
                setattr(rule, field, value)
            elif field == "severity":
                setattr(rule, field, value.value)
            elif field == "notification_channels":
                setattr(rule, field, value)
            else:
                setattr(rule, field, value)
    
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    
    return success_response(data={
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "description": rule.description,
        "scope": rule.scope,
        "property": rule.property,
        "condition": rule.condition,
        "threshold": rule.threshold,
        "status": rule.status,
        "severity": rule.severity,
        "notification_channels": rule.notification_channels,
        "cooldown_minutes": rule.cooldown_minutes,
        "device_ids": rule.device_ids,
        "updated_at": rule.updated_at.isoformat()
    })


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Rule).where(
        and_(Rule.rule_id == rule_id, Rule.deleted_at.is_(None))
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise RuleNotFoundException(rule_id)
    
    rule.status = "archived"
    rule.deleted_at = datetime.utcnow()
    rule.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return success_response(data={"message": "Rule archived successfully", "rule_id": rule_id})


@router.put("/rules/{rule_id}/status")
async def update_rule_status(
    rule_id: str,
    status_data: RuleStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    query = select(Rule).where(
        and_(Rule.rule_id == rule_id, Rule.deleted_at.is_(None))
    )
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise RuleNotFoundException(rule_id)
    
    if rule.status == "archived":
        raise ValidationException([{"message": "Cannot change status of archived rule"}])
    
    if status_data.status.value == "archived" and rule.status in ["active", "paused"]:
        rule.status = "archived"
        rule.deleted_at = datetime.utcnow()
    else:
        rule.status = status_data.status.value
    
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    
    return success_response(data={
        "rule_id": rule.rule_id,
        "status": rule.status,
        "updated_at": rule.updated_at.isoformat()
    })


@router.post("/rules/evaluate")
async def evaluate_rules(
    evaluation_data: EvaluateRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await rule_evaluator.evaluate(
        db=db,
        device_id=evaluation_data.device_id,
        telemetry=evaluation_data.telemetry
    )
    
    return success_response(data=result)
