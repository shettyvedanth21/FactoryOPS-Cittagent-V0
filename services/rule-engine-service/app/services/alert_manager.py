import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule, Alert


class AlertManager:
    async def create_alert(
        self,
        db: AsyncSession,
        rule: Rule,
        device_id: str,
        actual_value: float
    ) -> Alert:
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id=rule.rule_id,
            device_id=device_id,
            severity=rule.severity,
            message=f"[{rule.severity.upper()}] {rule.property} {rule.condition} {rule.threshold} (actual: {actual_value})",
            actual_value=actual_value,
            threshold_value=rule.threshold,
            property_name=rule.property,
            condition=rule.condition,
            status="open"
        )
        
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        
        rule.last_triggered_at = datetime.utcnow()
        await db.commit()
        
        return alert
    
    async def acknowledge_alert(
        self,
        db: AsyncSession,
        alert_id: str,
        acknowledged_by: Optional[str] = None
    ) -> Optional[Alert]:
        from sqlalchemy import select
        query = select(Alert).where(Alert.alert_id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        if alert.status == "resolved":
            raise ValueError("Cannot acknowledge a resolved alert")
        
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        if acknowledged_by:
            alert.acknowledged_by = acknowledged_by
        alert.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(alert)
        
        return alert
    
    async def resolve_alert(
        self,
        db: AsyncSession,
        alert_id: str
    ) -> Optional[Alert]:
        from sqlalchemy import select
        query = select(Alert).where(Alert.alert_id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one_or_none()
        
        if not alert:
            return None
        
        if alert.status == "resolved":
            raise ValueError("Alert is already resolved")
        
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(alert)
        
        return alert
    
    def is_valid_transition(self, current_status: str, new_status: str) -> bool:
        valid_transitions = {
            "open": ["acknowledged", "resolved"],
            "acknowledged": ["resolved"],
            "resolved": []
        }
        return new_status in valid_transitions.get(current_status, [])


alert_manager = AlertManager()
