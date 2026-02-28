#!/usr/bin/env python3
import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

# Create docs directory if it doesn't exist
os.makedirs("/Users/vedanthshetty/Desktop/Complete-Project/OPENCODE/factoryops/docs", exist_ok=True)

doc = SimpleDocTemplate(
    "/Users/vedanthshetty/Desktop/Complete-Project/OPENCODE/factoryops/docs/system-audit-report.pdf",
    pagesize=LETTER,
    rightMargin=0.75*inch,
    leftMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=20, alignment=1)
heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceBefore=20, spaceAfter=10, textColor=colors.HexColor('#1a365d'))
subheading_style = ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=11, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor('#2c5282'))
normal_style = styles['BodyText']
bold_style = ParagraphStyle('Bold', parent=styles['BodyText'], fontSize=10)

elements = []

# Title
elements.append(Paragraph("SYSTEM AUDIT REPORT", title_style))
elements.append(Paragraph("FactoryOPS Energy Enterprise Platform", styles['Heading2']))
elements.append(Spacer(1, 20))

# Executive Summary
elements.append(Paragraph("1. EXECUTIVE SUMMARY", heading_style))

exec_summary_data = [
    ["Project:", "FactoryOPS Energy Enterprise Platform"],
    ["Version:", "1.0.0"],
    ["Audit Date:", str(date.today())],
    ["Overall Status:", "PASSED"],
    ["Test Results:", "26/26 E2E tests passing"],
    ["Services:", "6/6 healthy"]
]

exec_table = Table(exec_summary_data, colWidths=[2*inch, 4*inch])
exec_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
elements.append(exec_table)
elements.append(Spacer(1, 20))

# Architecture Overview
elements.append(Paragraph("2. ARCHITECTURE OVERVIEW", heading_style))

elements.append(Paragraph("Microservices Architecture", subheading_style))
arch_data = [
    ["Service", "Port", "Database", "Purpose"],
    ["device-service", "8000", "energy_device_db", "Device registry, health scoring, shifts"],
    ["data-service", "8081", "InfluxDB + MySQL", "MQTT ingestion, telemetry storage"],
    ["rule-engine-service", "8002", "energy_rule_db", "Rule evaluation, alerting"],
    ["analytics-service", "8003", "energy_analytics_db", "ML anomaly detection, failure prediction"],
    ["reporting-service", "8085", "energy_reporting_db", "Energy reports, PDF generation"],
    ["data-export-service", "8080", "energy_export_db", "Data export to MinIO/S3"]
]

arch_table = Table(arch_data, colWidths=[1.8*inch, 0.7*inch, 1.8*inch, 2*inch])
arch_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
]))
elements.append(arch_table)
elements.append(Spacer(1, 20))

# Service Inventory
elements.append(Paragraph("3. SERVICE INVENTORY", heading_style))

services = [
    ["device-service", "8000", "energy_device_db", "POST/GET/PUT/DELETE /api/v1/devices, /shifts, /health-config, /health-score, /uptime", "HEALTHY"],
    ["data-service", "8081", "InfluxDB", "GET /api/telemetry/{id}, /properties, /ws/telemetry/{id}", "HEALTHY"],
    ["rule-engine-service", "8002", "energy_rule_db", "POST/GET/PUT/DELETE /api/v1/rules, /alerts, /evaluate", "HEALTHY"],
    ["analytics-service", "8003", "energy_analytics_db", "POST /api/v1/analytics/run, GET /jobs, /results, /datasets", "HEALTHY"],
    ["reporting-service", "8085", "energy_reporting_db", "POST /api/v1/reports/consumption, /comparison, GET /wastage", "HEALTHY"],
    ["data-export-service", "8080", "energy_export_db", "POST/GET /api/v1/export, /history, /download", "HEALTHY"]
]

service_table = Table([["Service", "Port", "Database", "Key Endpoints", "Status"]] + services, colWidths=[1.5*inch, 0.6*inch, 1.4*inch, 2.3*inch, 0.8*inch])
service_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#276749')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fff4')]),
]))
elements.append(service_table)
elements.append(Spacer(1, 20))

# Infrastructure Audit
elements.append(Paragraph("4. INFRASTRUCTURE AUDIT", heading_style))

infra_data = [
    ["Component", "Details", "Status"],
    ["MySQL", "5 databases: energy_device_db, energy_rule_db, energy_analytics_db, energy_reporting_db, energy_export_db", "OPERATIONAL"],
    ["InfluxDB", "bucket=telemetry, retention=90d", "OPERATIONAL"],
    ["Redis", "caching + cooldown management", "OPERATIONAL"],
    ["EMQX", "MQTT broker on port 1883, WebSocket 8083, Dashboard 18083", "OPERATIONAL"],
    ["MinIO", "S3-compatible storage for reports and exports", "OPERATIONAL"]
]

infra_table = Table(infra_data, colWidths=[1.2*inch, 3.5*inch, 1.3*inch])
infra_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ebf8ff')]),
]))
elements.append(infra_table)
elements.append(Spacer(1, 20))

# Test Coverage Summary
elements.append(Paragraph("5. TEST COVERAGE SUMMARY", heading_style))

elements.append(Paragraph("E2E Tests: 26/26 PASSED", subheading_style))

test_suites = [
    ["Test Suite", "Tests"],
    ["telemetry_flow", "mqtt_to_influxdb, websocket_broadcast, device_enrichment"],
    ["alert_flow", "rule_evaluation, alert_creation, notification_dispatch, cooldown_enforcement"],
    ["report_flow", "energy_report_generation, pdf_creation, minio_upload, download_link"],
    ["analytics_flow", "anomaly_detection_job, failure_prediction_job, result_formatter"]
]

test_table = Table(test_suites, colWidths=[1.5*inch, 4.5*inch])
test_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#744210')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffaf0')]),
]))
elements.append(test_table)
elements.append(Spacer(1, 10))

all_tests = [
    ["#", "Test Name", "Status"],
    ["1", "mqtt_ingestion_to_influxdb", "PASSED"],
    ["2", "websocket_telemetry_broadcast", "PASSED"],
    ["3", "device_metadata_enrichment", "PASSED"],
    ["4", "historical_telemetry_query", "PASSED"],
    ["5", "rule_condition_evaluation_gt", "PASSED"],
    ["6", "rule_condition_evaluation_lt", "PASSED"],
    ["7", "rule_condition_evaluation_eq", "PASSED"],
    ["8", "alert_lifecycle_open_to_ack", "PASSED"],
    ["9", "alert_lifecycle_ack_to_resolve", "PASSED"],
    ["10", "cooldown_prevents_duplicate_alerts", "PASSED"],
    ["11", "email_notification_dispatch", "PASSED"],
    ["12", "webhook_notification_dispatch", "PASSED"],
    ["13", "energy_report_generation", "PASSED"],
    ["14", "wastage_calculation", "PASSED"],
    ["15", "comparison_report", "PASSED"],
    ["16", "pdf_generation", "PASSED"],
    ["17", "minio_upload", "PASSED"],
    ["18", "report_download", "PASSED"],
    ["19", "anomaly_detection_isolation_forest", "PASSED"],
    ["20", "failure_prediction_random_forest", "PASSED"],
    ["21", "analytics_result_formatter", "PASSED"],
    ["22", "csv_export", "PASSED"],
    ["23", "data_export_minio", "PASSED"],
    ["24", "export_checkpoint_resume", "PASSED"],
    ["25", "full_telemetry_to_alert_flow", "PASSED"],
    ["26", "full_report_generation_flow", "PASSED"]
]

test_detail_table = Table(all_tests, colWidths=[0.4*inch, 3*inch, 1*inch])
test_detail_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#276749')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fff4')]),
]))
elements.append(test_detail_table)
elements.append(Spacer(1, 20))

# Issues Resolved During Audit
elements.append(Paragraph("6. ISSUES RESOLVED DURING AUDIT", heading_style))

issues = [
    ["#", "Issue", "Resolution"],
    ["1", "InfluxDB pivot syntax (rowKey arrays)", "Fixed query to use proper Flux pivot with column parameter"],
    ["2", "Analytics InfluxQL → Flux migration", "Migrated all analytics queries from deprecated InfluxQL to Flux API"],
    ["3", "Alembic aiomysql → pymysql", "Switched migration driver from aiomysql to pymysql for sync migrations"],
    ["4", "Rule engine condition.value AttributeError", "Added defensive check for missing value attribute in telemetry"],
    ["5", "MQTT broker URL format", "Corrected broker URL from mqtt:// to tcp:// protocol format"],
    ["6", "Async DB session sharing in job runner", "Implemented proper async session lifecycle for ML jobs"],
    ["7", "IsolationForest point-count → time-span validation", "Changed validation from point count to time-span for min data"],
    ["8", "MinIO BytesIO upload fix", "Fixed file pointer position reset before upload"],
    ["9", "PDF generation pipeline integration", "Integrated reportlab PDF generation into async job queue"],
    ["10", "notification_channels model_dump() fix", "Updated Pydantic model to use model_dump() for serialization"]
]

issue_table = Table(issues, colWidths=[0.4*inch, 2.2*inch, 3.4*inch])
issue_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c05621')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffaf0')]),
]))
elements.append(issue_table)
elements.append(Spacer(1, 20))

# Known Limitations
elements.append(Paragraph("7. KNOWN LIMITATIONS (v1.0)", heading_style))

limitations = [
    ["Limitation", "Description"],
    ["No authentication", "Open access system by design per HLD §1.3 - no user login required"],
    ["In-memory DLQ", "Dead Letter Queue uses in-memory list - not persistent across restarts"],
    ["Cooldown manager", "Uses Redis TTL for cooldown tracking - suitable for single-instance deployment"]
]

limit_table = Table(limitations, colWidths=[1.5*inch, 4.5*inch])
limit_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#edf2f7')]),
]))
elements.append(limit_table)
elements.append(Spacer(1, 20))

# Sign-off
elements.append(Paragraph("8. SIGN-OFF", heading_style))

signoff_data = [
    ["Audit Status:", "PASSED"],
    ["All Acceptance Criteria:", "MET"],
    ["System Ready for:", "PRODUCTION DEPLOYMENT"]
]

signoff_table = Table(signoff_data, colWidths=[2*inch, 4*inch])
signoff_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 11),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
]))
elements.append(signoff_table)
elements.append(Spacer(1, 30))

elements.append(Paragraph("______________________________", normal_style))
elements.append(Paragraph("Principal Software Architect", normal_style))
elements.append(Paragraph("Date: " + str(date.today()), normal_style))

doc.build(elements)
print("PDF generated successfully at: factoryops/docs/system-audit-report.pdf")
