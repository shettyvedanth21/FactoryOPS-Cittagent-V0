import json
import logging
from typing import Dict, Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule, Alert
from app.services.alert_manager import alert_manager
from app.services.cooldown_manager import cooldown_manager
from app.services.notification.dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


class RuleEvaluator:
    OPERATORS = {
        ">": lambda value, threshold: value > threshold,
        "<": lambda value, threshold: value < threshold,
        "=": lambda value, threshold: abs(value - threshold) <= 0.001,
        "!=": lambda value, threshold: abs(value - threshold) > 0.001,
        ">=": lambda value, threshold: value >= threshold,
        "<=": lambda value, threshold: value <= threshold,
    }
    
    def __init__(self):
        self.notification_dispatcher = NotificationDispatcher()
    
    async def get_active_rules(self, db: AsyncSession) -> List[Rule]:
        query = select(Rule).where(
            Rule.status == "active",
            Rule.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def evaluate_condition(
        self,
        condition: str,
        actual_value: float,
        threshold: float
    ) -> bool:
        op_fn = self.OPERATORS.get(condition)
        if not op_fn:
            logger.warning(f"Unknown condition operator: {condition}")
            return False
        return op_fn(actual_value, threshold)
    
    async def evaluate(
        self,
        db: AsyncSession,
        device_id: str,
        telemetry: Dict[str, float]
    ) -> Dict[str, Any]:
        rules = await self.get_active_rules(db)
        
        triggered_alerts = []
        skipped_rules = []
        
        for rule in rules:
            try:
                if rule.scope == "selected_devices":
                    if device_id not in (rule.device_ids or []):
                        skipped_rules.append({
                            "rule_id": rule.rule_id,
                            "reason": "device not in selected devices"
                        })
                        continue
                
                if rule.property not in telemetry:
                    skipped_rules.append({
                        "rule_id": rule.rule_id,
                        "reason": f"property '{rule.property}' not in telemetry"
                    })
                    continue
                
                actual_value = telemetry[rule.property]
                
                condition_met = await self.evaluate_condition(
                    rule.condition,
                    actual_value,
                    rule.threshold
                )
                
                if not condition_met:
                    continue
                
                is_cooling_down = await cooldown_manager.is_cooling_down(
                    rule.rule_id,
                    device_id
                )
                
                if is_cooling_down:
                    skipped_rules.append({
                        "rule_id": rule.rule_id,
                        "reason": "cooldown active"
                    })
                    continue
                
                alert = await alert_manager.create_alert(
                    db=db,
                    rule=rule,
                    device_id=device_id,
                    actual_value=actual_value
                )
                
                await cooldown_manager.set_cooldown(
                    rule_id=rule.rule_id,
                    device_id=device_id,
                    minutes=rule.cooldown_minutes
                )
                
                triggered_alerts.append({
                    "alert_id": alert.alert_id,
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "device_id": device_id,
                    "property": rule.property,
                    "condition": rule.condition,
                    "threshold": rule.threshold,
                    "actual_value": actual_value,
                    "severity": rule.severity
                })
                
                try:
                    await self.notification_dispatcher.dispatch(
                        rule=rule,
                        alert=alert,
                        device_id=device_id
                    )
                except Exception as e:
                    logger.error(f"Notification dispatch failed for rule {rule.rule_id}: {e}")
                
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
                skipped_rules.append({
                    "rule_id": rule.rule_id,
                    "reason": f"error: {str(e)}"
                })
        
        return {
            "device_id": device_id,
            "evaluated": len(rules),
            "triggered": len(triggered_alerts),
            "skipped": skipped_rules,
            "alerts": triggered_alerts
        }
