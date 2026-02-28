import logging
from datetime import datetime

from app.models.rule import Rule, Alert
from app.services.notification.email_adapter import EmailAdapter
from app.services.notification.sms_adapter import SMSAdapter
from app.services.notification.webhook_adapter import WebhookAdapter
from app.services.notification.whatsapp_adapter import WhatsAppAdapter
from app.services.notification.telegram_adapter import TelegramAdapter

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self):
        self.email_adapter = EmailAdapter()
        self.sms_adapter = SMSAdapter()
        self.webhook_adapter = WebhookAdapter()
        self.whatsapp_adapter = WhatsAppAdapter()
        self.telegram_adapter = TelegramAdapter()
    
    async def dispatch(
        self,
        rule: Rule,
        alert: Alert,
        device_id: str
    ) -> None:
        notification_channels = rule.notification_channels or {}
        
        try:
            if notification_channels.get("email"):
                emails = notification_channels.get("email", [])
                if emails:
                    await self.email_adapter.send(
                        recipients=emails,
                        subject=f"[{alert.severity.upper()}] Alert: {rule.rule_name}",
                        body=f"Alert Details:\n\nDevice: {device_id}\nProperty: {rule.property}\nActual Value: {alert.actual_value}\nThreshold: {rule.condition} {rule.threshold}\nSeverity: {alert.severity}\nTime: {alert.created_at.isoformat()}"
                    )
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
        
        try:
            if notification_channels.get("sms"):
                numbers = notification_channels.get("sms", [])
                if numbers:
                    message = f"ALERT [{alert.severity}]: {rule.rule_name} - {device_id} {rule.property}={alert.actual_value}"
                    for number in numbers:
                        await self.sms_adapter.send(phone_number=number, message=message)
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
        
        try:
            if notification_channels.get("webhook"):
                urls = notification_channels.get("webhook", [])
                if urls:
                    payload = {
                        "alert_id": alert.alert_id,
                        "device_id": device_id,
                        "rule_name": rule.rule_name,
                        "property": rule.property,
                        "actual_value": alert.actual_value,
                        "threshold": rule.threshold,
                        "condition": rule.condition,
                        "severity": alert.severity,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    for url in urls:
                        await self.webhook_adapter.send(url=url, payload=payload)
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
        
        try:
            if notification_channels.get("whatsapp"):
                numbers = notification_channels.get("whatsapp", [])
                if numbers:
                    message = f"ALERT [{alert.severity}]: {rule.rule_name} - {device_id} {rule.property}={alert.actual_value}"
                    for number in numbers:
                        await self.whatsapp_adapter.send(phone_number=number, message=message)
        except Exception as e:
            logger.error(f"WhatsApp notification failed: {e}")
        
        try:
            if notification_channels.get("telegram"):
                chat_ids = notification_channels.get("telegram", [])
                if chat_ids:
                    message = f"⚠️ *Alert: {rule.rule_name}*\n\nDevice: {device_id}\nProperty: {rule.property}\nActual Value: {alert.actual_value}\nThreshold: {rule.condition} {rule.threshold}\nSeverity: {alert.severity}"
                    for chat_id in chat_ids:
                        await self.telegram_adapter.send(chat_id=chat_id, message=message)
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")


notification_dispatcher = NotificationDispatcher()
