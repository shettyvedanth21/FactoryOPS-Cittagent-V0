# FactoryOPS — PROJECT INTELLIGENCE

> Comprehensive technical documentation for AI models and engineers. This file provides complete context for understanding, extending, and maintaining the FactoryOPS Energy Enterprise Platform.

---

## 1. PROJECT DNA

### What
**FactoryOPS** is an Industrial IoT (IIoT) Intelligence Platform for real-time monitoring, health analytics, and predictive maintenance of industrial equipment. It ingests telemetry via MQTT, stores in InfluxDB, provides rule-based alerting with multi-channel notifications, runs ML analytics (anomaly detection, failure prediction), and generates energy/wastage reports with PDF export.

### Why
Industrial plants face reactive maintenance, manual monitoring, energy waste, unexpected downtime, and compliance reporting burdens. FactoryOPS provides real-time visibility, proactive alerting, energy analytics, ML-powered predictions, and automated reporting.

### Who
- **Target Users:** Plant Managers, Maintenance Engineers, Operations Teams
- **Target Industry:** Manufacturing, Industrial Production, Factories
- **Scale:** 1000+ concurrent device connections
- **Version:** 1.0.0 (Production Ready)
- **Status:** 26/26 E2E tests passing

---

## 2. ARCHITECTURE DECISIONS WITH REASONS

| Decision | Reason |
|----------|--------|
| **6 microservices over monolith** | Independent scaling, fault isolation, team ownership per domain (device, data, rules, analytics, reporting, export) |
| **MySQL + InfluxDB hybrid** | MySQL for relational configs (devices, rules), InfluxDB for high-throughput time-series telemetry |
| **MQTT (EMQX) for ingestion** | Industry standard for IoT, handles 1000+ connections, supports WebSocket bridge |
| **Redis for cooldown** | Sub-millisecond TTL operations for alert deduplication |
| **MinIO for object storage** | S3-compatible, single-node deployment without AWS dependencies |
| **FastAPI for all services** | Async-first, automatic OpenAPI docs, Pydantic validation |
| **No authentication (v1.0)** | Per HLD §1.3 - open access internal system design assumption |
| **Soft delete on devices** | Audit trail preservation, prevents accidental data loss |
| **Weights must sum to 100%** | Mathematical requirement for weighted health score calculation |
| **InfluxDB 90-day retention** | Balance between storage cost and historical analysis needs |
| **Async job queue for reports/ML** | Long-running operations don't block API; status polling pattern |
| **WebSocket for live telemetry** | Sub-second updates for dashboard; broadcast pattern |

---

## 3. KNOWN LANDMINES

These bugs were difficult to find and fix during Phase 8 integration:

| # | Bug | Root Cause | Fix |
|---|-----|------------|-----|
| 1 | **InfluxDB pivot syntax error** | Flux pivot requires `column` parameter not `rowKey` arrays | Changed from `rowKey: ["_time"]` to proper Flux pivot with column parameter |
| 2 | **Analytics queries fail** | InfluxDB v2 deprecated InfluxQL | Migrated all analytics queries from InfluxQL to Flux API |
| 3 | **Alembic migrations hang** | aiomysql driver doesn't support synchronous migrations | Switched to pymysql for migration driver |
| 4 | **Rule engine crashes on telemetry** | `condition.value` AttributeError when telemetry missing property | Added defensive `getattr(telemetry, property, None)` check |
| 5 | **MQTT connection refused** | Broker URL used `mqtt://` protocol | Changed to `tcp://` format for paho-mqtt |
| 6 | **ML jobs fail with DB error** | Async session closed before job completed | Implemented proper async session lifecycle with context manager |
| 7 | **IsolationForest validation error** | Validated minimum point count instead of time span | Changed validation to check time-span >= 7 days |
| 8 | **MinIO upload fails silently** | BytesIO file pointer at end after write | Added `seek(0)` before upload |
| 9 | **PDF generation timeout** | Synchronous PDF generation in async endpoint | Integrated reportlab into async job queue |
| 10 | **Notification channels serialization error** | Pydantic model needed `model_dump()` not `dict()` | Updated serialization in notification dispatcher |

---

## 4. GUARD PROMPT

> **START OF SESSION**
> 
> You are working on **FactoryOPS** — an Industrial IoT platform with 6 microservices (device-service, data-service, rule-engine-service, analytics-service, reporting-service, data-export-service) plus Next.js frontend.
> 
> **Key constraints:**
> - No authentication (v1.0 by design)
> - MySQL + InfluxDB hybrid storage
> - MQTT ingestion via EMQX
> - Health scores require weights summing to 100
> - All services use FastAPI with async SQLAlchemy
> - Response envelope: `{"success": true, "data": {...}, "timestamp": "..."}`
> - Health endpoints: `/health` and `/health/ready`
> - Database: soft delete uses `deleted_at` field
> 
> **Before modifying any service:**
> 1. Check `services/*/app/config.py` for environment variables
> 2. Check `shared/` for common utilities
> 3. Verify inter-service calls in HLD §10 (telemetry flow, rule trigger)
> 4. Check database schema in `docs/database-schema.md`
> 
> **Testing:** E2E tests in `tests/e2e/` — run with `pytest tests/e2e/ -v`
> 
> **DO NOT:**
> - Add authentication without discussing design implications
> - Use blocking calls in async FastAPI endpoints
> - Change database schemas without alembic migration
> - Hardcode service URLs (use environment variables)

---

## 5. PHASE MAP

| Phase | Dates | Services | Key Deliverables |
|-------|-------|---------|------------------|
| **Phase 0** | 2026-02-27 | Infrastructure | Docker Compose (MySQL, InfluxDB, Redis, EMQX, MinIO), 5 MySQL databases, shared libraries |
| **Phase 1** | 2026-02-27 | device-service (:8000) | Device CRUD, shifts, health config, health score calculator, uptime |
| **Phase 2** | 2026-02-27 | data-service (:8081) | MQTT ingestion, InfluxDB storage, WebSocket broadcast, rule trigger |
| **Phase 3** | 2026-02-27 | rule-engine-service (:8002) | Rules CRUD, condition evaluation, alert lifecycle, 5 notification channels |
| **Phase 4** | 2026-02-27 | reporting-service (:8085) | Energy/wastage reports, PDF generation, MinIO upload, scheduled reports |
| **Phase 5** | 2026-02-27 | analytics-service (:8003) | ML job queue, Isolation Forest anomaly detection, Random Forest failure prediction |
| **Phase 6** | 2026-02-27 | data-export-service (:8080) | CSV/Parquet/JSON export, MinIO upload, checkpoint tracking |
| **Phase 7** | 2026-02-28 | ui-web (:3000) | Next.js 16 dashboard, machine detail, rules wizard, alerts, reports, analytics |
| **Phase 8** | 2026-02-28 | All | Integration testing, 26 E2E tests, system audit report |

---

## 6. HOW TO EXTEND

### Add a New Service

1. Create directory: `services/new-service/`
2. Add `app/config.py`, `app/main.py`, `app/db/session.py`
3. Add Dockerfile and requirements.txt
4. Add to `docker-compose.yml`
5. Add Alembic migrations in `alembic/versions/`
6. Add health endpoints: `/health`, `/health/ready`
7. Use response envelope from `shared/response.py`

### Add an Endpoint

1. Create route file in `services/*/app/api/routes/`
2. Import router in `main.py`
3. Use dependency injection for DB session
4. Return standard response:
   ```python
   from shared.response import success_response
   return success_response(data={"your": "data"})
   ```

### Add ML Model (Analytics Service)

1. Add model config in `app/services/models/`
2. Implement `train()` and `predict()` methods
3. Add to model registry in `app/services/model_registry.py`
4. Update `/api/v1/analytics/models` endpoint
5. Ensure async job runner handles new analysis type
6. Add result formatter for plain-language output

### Add Notification Channel

1. Create adapter in `services/rule-engine-service/app/services/notifications/adapters/`
2. Implement `send()` method with signature: `async def send(self, alert: Alert, config: NotificationConfig) -> bool`
3. Register in `notification_dispatcher.py`
4. Add to Pydantic schema for `notification_channels`

---

## 7. COMPLETE FILE MAP

### Core Documentation
```
docs/prd.md                    # Product Requirements Document
docs/hld.md                    # High-Level Design (architecture, technology stack)
docs/LLD-Energy-Enterprise-Platform.md  # Low-Level Design
docs/database-schema.md        # MySQL + InfluxDB schema with ERDs
docs/ux-wireframes.md          # UI/UX specifications
docs/system-audit-report.pdf   # Phase 8 audit report
```

### Services (Python/FastAPI)
```
services/device-service/
├── app/config.py              # Settings (DATABASE_URL, REDIS_*)
├── app/main.py                # FastAPI application entry
├── app/db/session.py          # Async SQLAlchemy session
├── app/models/device.py       # Device, DeviceShift, ParameterHealthConfig
├── app/api/routes/devices.py  # CRUD endpoints
├── app/api/routes/shifts.py   # Shift management
├── app/services/health_score.py  # Weighted health calculation
├── app/services/uptime.py    # Uptime calculation
└── alembic/versions/         # Database migrations

services/data-service/
├── src/config.py              # INFLUX_*, MQTT_*, DEVICE_SERVICE_URL
├── src/main.py               # FastAPI + WebSocket
├── src/services/
│   ├── mqtt_client.py        # paho-mqtt subscriber
│   ├── influx_client.py      # InfluxDB write/query
│   ├── telemetry_handler.py  # Parse, validate, enrich
│   └── websocket_manager.py  # Broadcast to clients
└── src/api/routes/telemetry.py

services/rule-engine-service/
├── app/config.py              # DATABASE_URL, SMTP_*, AWS_*, TWILIO_*, TELEGRAM_*
├── app/main.py
├── app/models/               # Rule, Alert SQLAlchemy models
├── app/services/
│   ├── rule_evaluator.py    # Condition engine (>, <, =, !=, >=, <=)
│   ├── cooldown_manager.py  # Redis TTL-based deduplication
│   ├── alert_manager.py     # Lifecycle (open→ack→resolve)
│   └── notifications/
│       ├── dispatcher.py     # Central notification router
│       ├── email_adapter.py  # SMTP
│       ├── sms_adapter.py    # AWS SNS
│       ├── webhook_adapter.py
│       ├── whatsapp_adapter.py
│       └── telegram_adapter.py
└── app/api/routes/rules.py, alerts.py

services/analytics-service/
├── app/config.py              # MYSQL_*, INFLUX_*, JOB_TIMEOUT_MINUTES
├── app/main.py
├── app/models/analytics_job.py
├── app/services/
│   ├── job_runner.py         # Async job queue
│   ├── data_loader.py        # InfluxDB feature extraction
│   ├── anomaly_detector.py   # Isolation Forest, Z-score
│   ├── failure_predictor.py  # Random Forest
│   └── result_formatter.py   # Plain-language output
└── app/api/routes/analytics.py

services/reporting-service/
├── app/config.py              # INFLUX_*, MINIO_*, DEFAULT_TARIFF_RATE
├── app/main.py
├── app/models/                # EnergyReport, ScheduledReport, TenantTariff
├── app/services/
│   ├── engines/              # calculation modules
│   │   ├── energy_engine.py  # kWh, avg/peak power
│   │   ├── wastage_engine.py # idle, peak, inefficiency
│   │   ├── demand_engine.py
│   │   ├── load_factor_engine.py
│   │   ├── cost_engine.py
│   │   └── comparison_engine.py
│   ├── pdf_builder.py        # ReportLab PDF generation
│   └── scheduler.py          # APScheduler for cron jobs
└── app/api/routes/reports.py

services/data-export-service/
├── app/config.py              # MINIO_*, EXPORT_TIMEOUT_MINUTES
├── app/main.py
├── app/models/export_checkpoint.py
├── app/services/
│   ├── influx_reader.py      # Query InfluxDB
│   └── minio_client.py       # S3 upload
├── app/exporters/            # Format handlers
│   ├── csv_exporter.py
│   ├── parquet_exporter.py
│   └── json_exporter.py
└── app/api/routes/export.py
```

### Frontend (Next.js)
```
ui-web/
├── app/                      # Next.js 16 App Router
│   ├── page.tsx            # Dashboard (machines grid)
│   ├── machines/            # Machine list, detail, config
│   ├── analytics/           # ML job submission, results
│   ├── reports/             # Energy, wastage, comparison
│   ├── rules/               # Rule wizard, alerts
│   └── layout.tsx           # Sidebar, header, notification bell
├── lib/
│   ├── api.ts               # API client for all services
│   └── utils.ts
└── package.json
```

### Shared
```
shared/
├── __init__.py
├── response.py               # success_response(), error_response()
├── exceptions.py            # Custom exception classes
└── logging_config.py         # Structured JSON logging
```

### Infrastructure
```
infrastructure/docker/
├── docker-compose.yml        # All services + infra
├── docker-compose.infra.yml  # Infra only (for testing)
└── mysql/init/
    └── 01_create_databases.sql  # 5 MySQL databases
```

### Tests
```
tests/e2e/
├── conftest.py              # Pytest fixtures
├── test_telemetry_flow.py   # MQTT → InfluxDB → WebSocket
├── test_alert_flow.py       # Rule → Alert → Notification
├── test_report_flow.py     # Report → PDF → MinIO → Download
└── test_analytics_flow.py  # ML job → Results
```

---

## 8. ENVIRONMENT VARIABLES REFERENCE

### Device Service (port 8000)
| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | mysql+aiomysql://root:rootpassword@mysql:3306/energy_device_db | MySQL connection |
| `REDIS_HOST` | redis | Redis for caching |
| `REDIS_PORT` | 6379 | Redis port |
| `SERVICE_NAME` | device-service | Service identifier |
| `LOG_LEVEL` | INFO | Logging level |

### Data Service (port 8081)
| Variable | Default | Purpose |
|----------|---------|---------|
| `DEVICE_SERVICE_URL` | http://device-service:8000 | For metadata enrichment |
| `RULE_ENGINE_URL` | http://rule-engine-service:8002 | For rule evaluation trigger |
| `INFLUX_URL` | http://influxdb:8086 | InfluxDB endpoint |
| `INFLUX_TOKEN` | factoryops-admin-token | InfluxDB auth |
| `INFLUX_ORG` | factoryops | InfluxDB organization |
| `INFLUX_BUCKET` | telemetry | InfluxDB bucket |
| `MQTT_BROKER` | emqx | MQTT broker hostname |
| `MQTT_PORT` | 1883 | MQTT port |
| `DEVICE_DB_*` | mysql, 3306, energy_device_db, root, rootpassword | Device DB access |

### Rule Engine Service (port 8002)
| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | mysql+aiomysql://root:rootpassword@mysql:3306/energy_rule_db | MySQL connection |
| `SMTP_HOST` | smtp.gmail.com | Email server |
| `SMTP_PORT` | 587 | Email port |
| `SMTP_USER` | (empty) | SMTP username |
| `SMTP_PASSWORD` | (empty) | SMTP password |
| `AWS_ACCESS_KEY_ID` | (empty) | For SNS SMS |
| `AWS_SECRET_ACCESS_KEY` | (empty) | AWS secret |
| `AWS_REGION` | us-east-1 | AWS region |
| `TWILIO_ACCOUNT_SID` | (empty) | For WhatsApp |
| `TWILIO_AUTH_TOKEN` | (empty) | Twilio auth |
| `TELEGRAM_BOT_TOKEN` | (empty) | Telegram bot |

### Analytics Service (port 8003)
| Variable | Default | Purpose |
|----------|---------|---------|
| `MYSQL_HOST` | localhost | MySQL host |
| `MYSQL_PORT` | 3306 | MySQL port |
| ` | root | MySQL user |
| `MYMYSQL_USER`SQL_PASSWORD` | password | MySQL password |
| `MYSQL_DATABASE` | energy_analytics_db | Database name |
| `INFLUX_URL` | http://localhost:8086 | InfluxDB endpoint |
| `INFLUX_TOKEN` | my-token | InfluxDB token |
| `INFLUX_ORG` | factoryops | InfluxDB org |
| `INFLUX_BUCKET` | telemetry | InfluxDB bucket |
| `REDIS_HOST` | localhost | Redis host |
| `MAX_CONCURRENT_JOBS` | 3 | Parallel ML jobs |
| `JOB_TIMEOUT_MINUTES` | 30 || Variable | Default Reporting Service (port 8085)
 | Purpose |
| Job timeout |

###----------|---------|---------|
| `DATABASE_URL` | mysql+aiomysql://root:rootpassword@mysql:3306/energy_reporting_db | MySQL connection |
| `INFLUX_URL` | http://influxdb:8086 | InfluxDB endpoint |
| `INFLUX_TOKEN` | my-super-secret-token | InfluxDB token |
| `MINIO_ENDPOINT` | minio:9000 | MinIO S3 endpoint |
| `MINIO_ACCESS_KEY` | minioadmin | MinIO access |
| `MINIO_SECRET_KEY` | minioadmin | MinIO secret |
| `MINIO_BUCKET` | reports | MinIO bucket |
| `MINIO_SECURE` | false | Use TLS |
| `DEFAULT_TARIFF_RATE` | 8.5 | Default ₹/kWh |
| `DEVICE_SERVICE_URL` | http://device-service:8000 | For device metadata |

### Data Export Service (port 8080)
| Variable | Default | Purpose |
|----------|---------|---------|
| `MYSQL_HOST` | localhost | MySQL host |
| `MYSQL_PORT` | 3306 | MySQL port |
| `MYSQL_USER` | root | MySQL user |
| `MYSQL_PASSWORD` | password | MySQL password |
| `MYSQL_DATABASE` | energy_export_db | Database name |
| `INFLUX_URL` | http://localhost:8086 | InfluxDB endpoint |
| `INFLUX_TOKEN` | my-token | InfluxDB token |
| `MINIO_ENDPOINT` | localhost:9000 | MinIO endpoint |
| `MINIO_BUCKET` | exports | MinIO bucket |
| `EXPORT_TIMEOUT_MINUTES` | 30 | Export timeout |

---

## 9. INTER-SERVICE CONTRACT

### Data Service → Device Service (Enrichment)
```
POST http://device-service:8000/api/v1/devices/{device_id}
Headers: Content-Type: application/json
Response: { "success": true, "data": { device metadata } }
```

### Data Service → Rule Engine (Evaluation Trigger)
```
POST http://rule-engine-service:8002/api/v1/rules/evaluate
Headers: Content-Type: application/json
Payload: {
  "device_id": "COMPRESSOR-001",
  "telemetry": { "power": 5200, "temperature": 45, ... },
  "timestamp": "2026-02-28T10:00:00Z"
}
Response: { "success": true, "data": { "triggered": true/false } }
```

### Reporting Service → Device Service (Device Metadata)
```
GET http://device-service:8000/api/v1/devices/{device_id}
Headers: Content-Type: application/json
Response: { "success": true, "data": { device info } }
```

### Reporting Service → InfluxDB (Telemetry Query)
```
POST http://influxdb:8086/api/v2/query
Headers: Authorization: Token {INFLUX_TOKEN}, Content-Type: application/json
Flux Query: from(bucket:"telemetry") |> range(start: {start}, stop: {end}) |> filter(fn: (r) => r.device_id == "{device_id}")
```

### All Services → MinIO (S3 Upload)
```
PUT http://minio:9000/{bucket}/{key}
Headers: x-amz-content-sha256: sha256, Content-Type: application/octet-stream
MinIO credentials: {MINIO_ACCESS_KEY}:{MINIO_SECRET_KEY}
```

---

## 10. DATABASE SCHEMA SUMMARY

### MySQL Databases (5 total)

#### 1. energy_device_db (device-service)
| Table | Primary Key | Key Columns | Relationships |
|-------|-------------|-------------|---------------|
| devices | device_id (VARCHAR 50) | tenant_id, device_type, last_seen_timestamp, legacy_status | - |
| device_shifts | id (INT AUTO) | device_id (FK→devices), day_of_week | device_id→devices |
| parameter_health_config | id (INT AUTO) | device_id (FK→devices), parameter_name (UK) | device_id→devices |
| device_properties | id (INT AUTO) | device_id (FK→devices), property_name (UK) | device_id→devices |

#### 2. energy_rule_db (rule-engine-service)
| Table | Primary Key | Key Columns | Relationships |
|-------|-------------|-------------|---------------|
| rules | rule_id (VARCHAR 36 UUID) | tenant_id, property, status, scope | - |
| alerts | alert_id (VARCHAR 36 UUID) | rule_id (FK→rules), device_id (FK→devices), status | rule_id→rules, device_id→devices |

#### 3. energy_analytics_db (analytics-service)
| Table | Primary Key | Key Columns | Relationships |
|-------|-------------|-------------|---------------|
| analytics_jobs | id (VARCHAR 36 UUID) | job_id (UNIQUE), device_id, status, analysis_type | - |

#### 4. energy_reporting_db (reporting-service)
| Table | Primary Key | Key Columns | Relationships |
|-------|-------------|-------------|---------------|
| energy_reports | id (INT AUTO) | report_id (UNIQUE), tenant_id, status, report_type | - |
| scheduled_reports | id (INT AUTO) | schedule_id (UNIQUE), tenant_id, frequency, is_active | - |
| tenant_tariffs | id (INT AUTO) | tenant_id, tariff_name (UK), is_active | - |

#### 5. energy_export_db (data-export-service)
| Table | Primary Key | Key Columns | Relationships |
|-------|-------------|-------------|---------------|
| export_checkpoints | id (INT AUTO) | device_id, status, format, start_time, end_time | - |

### InfluxDB (data-service)
| Bucket | Measurement | Tags (Indexed) | Fields (Dynamic) |
|--------|-------------|----------------|------------------|
| telemetry | telemetry | device_id, schema_version, enrichment_status | All numeric telemetry (power, voltage, temperature, etc.) |

**Retention:** 90 days (auto-delete)

---

*Last Updated: 2026-02-28*
*FactoryOPS v1.0.0 — Production Ready*
