import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


def build_alert_email_html(alert_data: Dict[str, Any]) -> tuple[str, str]:
    """Returns (subject, html_body)"""
    device = alert_data.get('device_id', 'Unknown Device')
    parameter = alert_data.get('parameter', alert_data.get('property', 'Unknown'))
    value = alert_data.get('actual_value', alert_data.get('value', 'N/A'))
    threshold = alert_data.get('threshold', 'N/A')
    operator = alert_data.get('operator', alert_data.get('condition', '>'))
    severity = str(alert_data.get('severity', 'warning')).upper()
    rule_name = alert_data.get('rule_name', 'Alert Rule')
    timestamp = alert_data.get('triggered_at', alert_data.get('timestamp', 'N/A'))

    severity_color = {'CRITICAL': '#dc2626', 'WARNING': '#d97706', 'INFO': '#2563eb'}.get(severity, '#d97706')
    severity_bg = {'CRITICAL': '#fef2f2', 'WARNING': '#fffbeb', 'INFO': '#eff6ff'}.get(severity, '#fffbeb')
    severity_icon = {'CRITICAL': '🚨', 'WARNING': '⚠️', 'INFO': 'ℹ️'}.get(severity, '⚠️')

    subject = f"[{severity}] FactoryOPS Alert: {parameter} {operator} {threshold} on {device}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>FactoryOPS Alert</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px;background:#f1f5f9;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);padding:28px 40px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td>
          <div style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:4px;">FactoryOPS Monitoring</div>
          <div style="color:#ffffff;font-size:22px;font-weight:700;">Alert Notification</div>
        </td>
        <td align="right" valign="middle">
          <div style="background:{severity_color};color:#fff;padding:6px 16px;border-radius:20px;font-size:12px;font-weight:800;letter-spacing:1.5px;">{severity_icon} {severity}</div>
        </td>
      </tr></table>
    </td>
  </tr>

  <!-- Alert Banner -->
  <tr>
    <td style="background:{severity_bg};border-left:5px solid {severity_color};padding:14px 40px;">
      <p style="margin:0;color:{severity_color};font-size:14px;font-weight:700;">{rule_name} has been triggered</p>
      <p style="margin:4px 0 0;color:#64748b;font-size:13px;">Immediate attention may be required</p>
    </td>
  </tr>

  <!-- Details Card -->
  <tr>
    <td style="padding:32px 40px 24px;">
      <p style="margin:0 0 16px;color:#94a3b8;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">Alert Details</p>
      <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:10px;overflow:hidden;border:1px solid #e2e8f0;">
        <tr style="background:#f8fafc;">
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">🏭 Device</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;font-weight:700;border-bottom:1px solid #e2e8f0;">{device}</td>
        </tr>
        <tr>
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">📊 Parameter</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;border-bottom:1px solid #e2e8f0;">{parameter}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">📈 Actual Value</td>
          <td style="padding:13px 18px;border-bottom:1px solid #e2e8f0;">
            <span style="background:{severity_color};color:#fff;padding:3px 12px;border-radius:20px;font-size:13px;font-weight:800;">{value}</span>
          </td>
        </tr>
        <tr>
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">🎯 Threshold</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;border-bottom:1px solid #e2e8f0;">{operator} {threshold}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;">🕐 Time</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;">{timestamp}</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- CTA Button -->
  <tr>
    <td style="padding:0 40px 36px;">
      <a href="http://localhost:3000/alerts"
         style="display:inline-block;background:linear-gradient(135deg,#1e293b,#334155);color:#ffffff;padding:13px 30px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:700;letter-spacing:0.5px;">
        View Alert in FactoryOPS →
      </a>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#f8fafc;padding:18px 40px;border-top:1px solid #e2e8f0;">
      <p style="margin:0;color:#94a3b8;font-size:12px;">This is an automated notification from <strong>FactoryOPS</strong>. Do not reply to this email.</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return subject, html


class EmailAdapter:
    async def send(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        alert_data: Optional[Dict[str, Any]] = None
    ) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP not configured, skipping email notification")
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_USER
            msg["To"] = ", ".join(recipients)
            
            if alert_data:
                _, html_body = build_alert_email_html(alert_data)
                msg.attach(MIMEText(html_body, 'html'))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise


def build_rule_created_email_html(rule_data: dict) -> tuple[str, str]:
    """Returns (subject, html_body) for rule creation confirmation"""
    rule_name = rule_data.get('rule_name', 'New Rule')
    rule_id = rule_data.get('rule_id', 'N/A')
    severity = str(rule_data.get('severity', 'warning')).upper()
    parameter = rule_data.get('parameter', rule_data.get('conditions', [{}])[0].get('parameter', 'N/A') if rule_data.get('conditions') else 'N/A')
    operator = rule_data.get('operator', rule_data.get('conditions', [{}])[0].get('operator', '>') if rule_data.get('conditions') else '>')
    threshold = rule_data.get('threshold', rule_data.get('conditions', [{}])[0].get('threshold', 'N/A') if rule_data.get('conditions') else 'N/A')
    device_count = len(rule_data.get('device_ids', []))
    channels = ', '.join([k for k, v in rule_data.get('notification_channels', {}).items() if v])
    created_at = rule_data.get('created_at', 'Just now')

    severity_color = {'CRITICAL': '#dc2626', 'WARNING': '#d97706', 'INFO': '#2563eb'}.get(severity, '#d97706')

    subject = f"[FactoryOPS] Rule Created: {rule_name}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Rule Created</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px;background:#f1f5f9;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);padding:28px 40px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td>
          <div style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:4px;">FactoryOPS Monitoring</div>
          <div style="color:#ffffff;font-size:22px;font-weight:700;">Rule Created Successfully</div>
        </td>
        <td align="right" valign="middle">
          <div style="background:#16a34a;color:#fff;padding:6px 16px;border-radius:20px;font-size:12px;font-weight:800;letter-spacing:1px;">✓ ACTIVE</div>
        </td>
      </tr></table>
    </td>
  </tr>

  <!-- Green Banner -->
  <tr>
    <td style="background:#f0fdf4;border-left:5px solid #16a34a;padding:14px 40px;">
      <p style="margin:0;color:#16a34a;font-size:14px;font-weight:700;">A new monitoring rule has been created and is now active</p>
      <p style="margin:4px 0 0;color:#64748b;font-size:13px;">You will receive alerts when the trigger condition is met</p>
    </td>
  </tr>

  <!-- Rule Details -->
  <tr>
    <td style="padding:32px 40px 24px;">
      <p style="margin:0 0 16px;color:#94a3b8;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;">Rule Details</p>
      <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:10px;overflow:hidden;border:1px solid #e2e8f0;">
        <tr style="background:#f8fafc;">
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">📋 Rule Name</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:14px;font-weight:700;border-bottom:1px solid #e2e8f0;">{rule_name}</td>
        </tr>
        <tr>
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">🔑 Rule ID</td>
          <td style="padding:13px 18px;color:#64748b;font-size:12px;font-family:monospace;border-bottom:1px solid #e2e8f0;">{rule_id}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">⚡ Trigger</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;border-bottom:1px solid #e2e8f0;"><code style="background:#f1f5f9;padding:2px 8px;border-radius:4px;">{parameter} {operator} {threshold}</code></td>
        </tr>
        <tr>
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">🚨 Severity</td>
          <td style="padding:13px 18px;border-bottom:1px solid #e2e8f0;">
            <span style="background:{severity_color};color:#fff;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;">{severity}</span>
          </td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">🏭 Devices</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;border-bottom:1px solid #e2e8f0;">{device_count} device(s)</td>
        </tr>
        <tr>
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;border-bottom:1px solid #e2e8f0;">🔔 Channels</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;border-bottom:1px solid #e2e8f0;">{channels or 'None configured'}</td>
        </tr>
        <tr style="background:#f8fafc;">
          <td style="padding:13px 18px;color:#64748b;font-size:13px;font-weight:600;width:38%;">🕐 Created</td>
          <td style="padding:13px 18px;color:#1e293b;font-size:13px;">{created_at}</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- CTA -->
  <tr>
    <td style="padding:0 40px 36px;">
      <a href="http://localhost:3000/rules"
         style="display:inline-block;background:linear-gradient(135deg,#1e293b,#334155);color:#ffffff;padding:13px 30px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:700;">
        View Rules in FactoryOPS →
      </a>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="background:#f8fafc;padding:18px 40px;border-top:1px solid #e2e8f0;">
      <p style="margin:0;color:#94a3b8;font-size:12px;">This is an automated confirmation from <strong>FactoryOPS</strong>. Do not reply to this email.</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return subject, html


def send_rule_created_notification(rule_data: dict, recipients: list):
    """Send email notification when a new rule is created"""
    import os
    smtp_server = os.getenv("SMTP_HOST", os.getenv("SMTP_SERVER", "smtp.gmail.com"))
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("SMTP_USER", os.getenv("EMAIL_SENDER"))
    password = os.getenv("SMTP_PASSWORD", os.getenv("EMAIL_PASSWORD"))

    if not sender or not password:
        logger.warning("Email not configured — skipping rule creation notification")
        return False

    if not recipients:
        logger.warning("No recipients for rule creation notification")
        return False

    subject, html_body = build_rule_created_email_html(rule_data)

    msg = MIMEMultipart('alternative')
    msg['From'] = f"FactoryOPS Alerts <{sender}>"
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info(f"Rule creation email sent to {recipients}")
        return True
    except Exception as e:
        logger.error(f"Failed to send rule creation email: {e}")
        return False
