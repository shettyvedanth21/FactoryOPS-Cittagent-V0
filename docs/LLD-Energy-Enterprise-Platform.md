# Low-Level Design (LLD) — Energy Enterprise Platform (FactoryOPS)

> **Document Version:** 2.0 (Enhanced)
> **Date:** February 2026
> **Project:** Energy Enterprise (FactoryOPS) — Production v1.0
> **Status:** Ready for Implementation

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [API Specification](#2-api-specification)
3. [Service Components & Folder Structure](#3-service-components--folder-structure)
4. [Business Logic — Implementation Details](#4-business-logic--implementation-details)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Frontend Architecture](#6-frontend-architecture)
7. [Notification Service](#7-notification-service)
8. [Analytics Service](#8-analytics-service)
9. [Data Export Service](#9-data-export-service)
10. [Error Handling](#10-error-handling)
11. [Security Design](#11-security-design)
12. [Configuration Management](#12-configuration-management)
13. [Testing Strategy](#13-testing-strategy)
14. [Deployment Strategy](#14-deployment-strategy)
15. [Monitoring & Observability](#15-monitoring--observability)
16. [Appendix](#16-appendix)

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐    │
│  │   Next.js Web App   │  │   Mobile Web         │  │   Admin Panel   │    │
│  │   (Port 3000)       │  │   (Responsive)       │  │   (Future)      │    │
│  └──────────┬──────────┘  └──────────┬──────────┘  └────────┬────────┘    │
└─────────────┼─────────────────────────┼──────────────────────┼─────────────┘
              │ HTTPS / WSS             │                      │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   NGINX REVERSE PROXY (Port 443)                            │
│             SSL Termination → Load Balancing → Routing                      │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
     ┌─────────────────────────────┼──────────────────────────┐
     │                             │                          │
     ▼                             ▼                          ▼
┌──────────────┐       ┌──────────────────┐       ┌──────────────────────┐
│Device Service│       │  Data Service    │       │  Rule Engine Service │
│  (Port 8000) │       │  (Port 8081)     │       │    (Port 8002)       │
│              │       │                  │       │                      │
│ Device CRUD  │       │ MQTT Ingestion   │       │ Rule Evaluation      │
│ Health Config│       │ InfluxDB Store   │       │ Alert Generation     │
│ Shift Mgmt   │       │ WebSocket Push   │       │ Notification Dispatch│
│ Uptime Calc  │       │ Data Enrichment  │       │ Cooldown Management  │
└──────────────┘       └──────────────────┘       └──────────────────────┘
     │                                                         │
     ▼                             ▼                          ▼
┌──────────────┐       ┌──────────────────┐       ┌──────────────────────┐
│  Analytics   │       │Reporting Service │       │  Data Export Service │
│  (Port 8003) │       │  (Port 8085)     │       │    (Port 8080)       │
│              │       │                  │       │                      │
│ ML Jobs      │       │ Energy Reports   │       │ CSV/Parquet Export   │
│ Anomaly Det. │       │ Wastage Engine   │       │ S3 Upload            │
│ Failure Pred.│       │ PDF/CSV Gen      │       │ Checkpoint Tracking  │
└──────────────┘       └──────────────────┘       └──────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  MySQL   │  │ InfluxDB │  │  MinIO   │  │   EMQX   │  │   Redis    │  │
│  │ :3306    │  │  :8086   │  │ :9000    │  │  :1883   │  │   :6379    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Service Communication Matrix

| From Service     | To Service       | Protocol        | Purpose                          |
|-----------------|-----------------|-----------------|----------------------------------|
| UI              | device-service   | HTTP REST       | Device CRUD, shifts, health      |
| UI              | data-service     | HTTP/WebSocket  | Telemetry queries, live stream   |
| UI              | rule-engine      | HTTP REST       | Rules CRUD, alerts               |
| UI              | reporting-service| HTTP REST       | Reports, wastage                 |
| UI              | analytics-service| HTTP REST       | ML jobs, results                 |
| data-service    | device-service   | HTTP REST       | Device metadata enrichment       |
| data-service    | rule-engine      | HTTP REST       | Rule evaluation trigger          |
| data-service    | InfluxDB         | InfluxDB client | Telemetry write                  |
| data-service    | EMQX             | MQTT            | Subscribe to telemetry topics    |
| rule-engine     | notification-svc | Internal call   | Dispatch alerts                  |
| reporting-svc   | InfluxDB         | InfluxDB client | Aggregate telemetry queries      |
| analytics-svc   | InfluxDB         | InfluxDB client | ML feature extraction            |

### 1.3 Port Allocation

| Service             | Port  | Protocol       |
|--------------------|-------|----------------|
| UI (Next.js)        | 3000  | HTTP           |
| device-service      | 8000  | HTTP           |
| data-export-service | 8080  | HTTP           |
| data-service        | 8081  | HTTP/WebSocket |
| rule-engine-service | 8002  | HTTP           |
| analytics-service   | 8003  | HTTP           |
| reporting-service   | 8085  | HTTP           |
| EMQX MQTT           | 1883  | MQTT           |
| EMQX WebSocket      | 8083  | WebSocket      |
| EMQX Dashboard      | 18083 | HTTP           |
| InfluxDB            | 8086  | HTTP           |
| MySQL               | 3306  | TCP            |
| Redis               | 6379  | TCP            |
| MinIO API           | 9000  | HTTP           |
| MinIO Console       | 9001  | HTTP           |

---

## 2. API Specification

### 2.1 Design Standards

| Standard         | Implementation                            |
|-----------------|-------------------------------------------|
| Protocol        | REST over HTTP/1.1                        |
| Format          | JSON (Content-Type: application/json)     |
| Versioning      | URL path: `/api/v1/`                      |
| Authentication  | API Key header: `X-API-Key`               |
| Rate Limiting   | 1000 req/min (GET), 100 req/min (POST)    |
| Pagination      | `?page=1&limit=50` (max 500)              |
| Sorting         | `?sort_by=created_at&order=desc`          |
| Filtering       | `?status=active&device_type=compressor`   |

### 2.2 Standard Response Envelopes

**Success:**
```json
{
  "success": true,
  "data": {},
  "pagination": { "page": 1, "limit": 50, "total": 120 },
  "timestamp": "2026-02-27T10:00:00Z",
  "request_id": "uuid-v4"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "ERR_CODE",
    "message": "Human-readable message",
    "details": [{ "field": "device_id", "message": "required" }]
  },
  "timestamp": "2026-02-27T10:00:00Z",
  "request_id": "uuid-v4"
}
```

### 2.3 Device Service API — Port 8000

#### Devices

| Method | Endpoint                          | Description                   | Status Codes       |
|--------|-----------------------------------|-------------------------------|--------------------|
| GET    | `/api/v1/devices`                 | List devices (paginated)      | 200                |
| POST   | `/api/v1/devices`                 | Create device                 | 201, 400, 409      |
| GET    | `/api/v1/devices/{device_id}`     | Get device by ID              | 200, 404           |
| PUT    | `/api/v1/devices/{device_id}`     | Update device                 | 200, 404, 400      |
| DELETE | `/api/v1/devices/{device_id}`     | Soft-delete device            | 200, 404           |
| POST   | `/api/v1/devices/bulk-import`     | Bulk import from CSV          | 202                |
| GET    | `/api/v1/devices/{device_id}/uptime` | Get uptime summary         | 200, 404           |
| POST   | `/api/v1/devices/{device_id}/heartbeat` | Update last_seen       | 200                |

**POST /api/v1/devices — Request:**
```json
{
  "device_id": "COMPRESSOR-001",
  "device_name": "Main Compressor",
  "device_type": "compressor",
  "location": "Plant A - Building 1",
  "phase_type": "three",
  "manufacturer": "Atlas Copco",
  "model": "GA37+",
  "metadata_json": { "rated_power_kw": 37, "install_date": "2022-01-15" }
}
```

**GET /api/v1/devices — Query Params:**
```
?page=1&limit=50&status=running&device_type=compressor&search=compressor
```

**GET /api/v1/devices/{device_id} — Response (with computed fields):**
```json
{
  "success": true,
  "data": {
    "device_id": "COMPRESSOR-001",
    "device_name": "Main Compressor",
    "device_type": "compressor",
    "location": "Plant A - Building 1",
    "phase_type": "three",
    "runtime_status": "running",
    "last_seen_timestamp": "2026-02-27T09:58:00Z",
    "health_score": 82.5,
    "health_grade": "Good",
    "uptime_percent": 94.2,
    "created_at": "2026-01-10T00:00:00Z"
  }
}
```

#### Shifts

| Method | Endpoint                                          | Description       |
|--------|---------------------------------------------------|-------------------|
| GET    | `/api/v1/devices/{device_id}/shifts`              | List shifts       |
| POST   | `/api/v1/devices/{device_id}/shifts`              | Create shift      |
| GET    | `/api/v1/devices/{device_id}/shifts/{id}`         | Get shift         |
| PUT    | `/api/v1/devices/{device_id}/shifts/{id}`         | Update shift      |
| DELETE | `/api/v1/devices/{device_id}/shifts/{id}`         | Delete shift      |

**POST /api/v1/devices/{device_id}/shifts — Request:**
```json
{
  "shift_name": "Morning Shift",
  "shift_start": "06:00",
  "shift_end": "14:00",
  "maintenance_break_minutes": 30,
  "day_of_week": null
}
```

#### Health Configuration

| Method | Endpoint                                              | Description              |
|--------|-------------------------------------------------------|--------------------------|
| GET    | `/api/v1/devices/{device_id}/health-config`           | List configs             |
| POST   | `/api/v1/devices/{device_id}/health-config`           | Create single config     |
| POST   | `/api/v1/devices/{device_id}/health-config/bulk`      | Bulk create configs      |
| PUT    | `/api/v1/devices/{device_id}/health-config/{id}`      | Update config            |
| DELETE | `/api/v1/devices/{device_id}/health-config/{id}`      | Delete config            |
| GET    | `/api/v1/devices/{device_id}/health-config/validate`  | Validate weights sum     |
| POST   | `/api/v1/devices/{device_id}/health-score`            | Compute health score now |

**POST /api/v1/devices/{device_id}/health-config/bulk — Request:**
```json
{
  "configs": [
    {
      "parameter_name": "temperature",
      "normal_min": 20,
      "normal_max": 55,
      "max_min": 10,
      "max_max": 75,
      "weight": 30.0
    },
    {
      "parameter_name": "vibration",
      "normal_min": 0,
      "normal_max": 5,
      "max_min": 0,
      "max_max": 10,
      "weight": 40.0
    },
    {
      "parameter_name": "pressure",
      "normal_min": 4,
      "normal_max": 8,
      "max_min": 2,
      "max_max": 12,
      "weight": 30.0
    }
  ]
}
```

### 2.4 Data Service API — Port 8081

| Method | Endpoint                              | Description                              |
|--------|---------------------------------------|------------------------------------------|
| GET    | `/api/telemetry/{device_id}`          | Query historical telemetry               |
| GET    | `/api/properties`                     | Get all device properties                |
| GET    | `/api/properties/{device_id}`         | Get properties for specific device       |
| WS     | `/ws/telemetry/{device_id}`           | Live telemetry stream (1s refresh)       |
| GET    | `/api/telemetry/{device_id}/latest`   | Get latest telemetry snapshot            |

**GET /api/telemetry/{device_id} — Query Params:**
```
?start=2026-02-20T00:00:00Z&end=2026-02-27T00:00:00Z&fields=power,temperature&aggregate=1m
```

**WebSocket Message Format:**
```json
{
  "device_id": "COMPRESSOR-001",
  "timestamp": "2026-02-27T10:00:01Z",
  "data": {
    "power": 5200,
    "voltage": 228,
    "current": 22.8,
    "temperature": 45,
    "pressure": 5.2,
    "vibration": 2.3
  }
}
```

### 2.5 Rule Engine API — Port 8002

#### Rules

| Method | Endpoint                              | Description              | Status Codes   |
|--------|---------------------------------------|--------------------------|----------------|
| GET    | `/api/v1/rules`                       | List rules               | 200            |
| POST   | `/api/v1/rules`                       | Create rule              | 201, 400       |
| GET    | `/api/v1/rules/{rule_id}`             | Get rule                 | 200, 404       |
| PUT    | `/api/v1/rules/{rule_id}`             | Update rule              | 200, 404       |
| DELETE | `/api/v1/rules/{rule_id}`             | Archive rule             | 200, 404       |
| PUT    | `/api/v1/rules/{rule_id}/status`      | Pause or Activate        | 200, 404       |
| POST   | `/api/v1/rules/evaluate`              | Trigger evaluation (internal) | 200       |

**POST /api/v1/rules — Request:**
```json
{
  "rule_name": "High Temperature Alert",
  "description": "Trigger when compressor temp exceeds threshold",
  "scope": "selected",
  "device_ids": ["COMPRESSOR-001", "COMPRESSOR-002"],
  "property": "temperature",
  "condition": ">",
  "threshold": 70,
  "severity": "critical",
  "cooldown_minutes": 15,
  "notifications": {
    "email": ["ops@factory.com"],
    "sms": ["+919876543210"],
    "whatsapp": ["+919876543210"],
    "telegram": ["-1001234567890"],
    "webhook": ["https://hooks.slack.com/services/xxx"]
  }
}
```

**PUT /api/v1/rules/{rule_id}/status — Request:**
```json
{ "status": "paused" }
```

#### Alerts

| Method | Endpoint                              | Description              |
|--------|---------------------------------------|--------------------------|
| GET    | `/api/v1/alerts`                      | List alerts (paginated)  |
| GET    | `/api/v1/alerts/{alert_id}`           | Get alert details        |
| PUT    | `/api/v1/alerts/{alert_id}/ack`       | Acknowledge alert        |
| PUT    | `/api/v1/alerts/{alert_id}/resolve`   | Resolve alert            |

**GET /api/v1/alerts — Query Params:**
```
?device_id=COMPRESSOR-001&status=open&severity=critical&page=1&limit=50
```

### 2.6 Reporting API — Port 8085

| Method | Endpoint                              | Description                    |
|--------|---------------------------------------|--------------------------------|
| POST   | `/api/v1/reports/consumption`         | Generate energy consumption    |
| POST   | `/api/v1/reports/comparison`          | Comparative device report      |
| GET    | `/api/v1/reports/{report_id}`         | Get report status/result       |
| GET    | `/api/v1/reports/{report_id}/download`| Download PDF or CSV            |
| GET    | `/api/v1/reports/history`             | List past reports              |
| GET    | `/api/v1/reports/wastage`             | Get energy wastage dashboard   |
| POST   | `/api/v1/schedules`                   | Create scheduled report        |
| GET    | `/api/v1/schedules`                   | List schedules                 |
| PUT    | `/api/v1/schedules/{id}`              | Update schedule                |
| DELETE | `/api/v1/schedules/{id}`              | Delete schedule                |

**POST /api/v1/reports/consumption — Request:**
```json
{
  "device_ids": ["COMPRESSOR-001", "COMPRESSOR-002"],
  "start_date": "2026-02-01",
  "end_date": "2026-02-27",
  "group_by": "daily",
  "include_wastage": true,
  "format": "pdf"
}
```

**GET /api/v1/reports/wastage — Query Params:**
```
?device_ids=COMPRESSOR-001,COMPRESSOR-002&start_date=2026-02-01&end_date=2026-02-27
```

**Wastage Response:**
```json
{
  "success": true,
  "data": {
    "period": { "start": "2026-02-01", "end": "2026-02-27" },
    "summary": {
      "total_wasted_kwh": 1240.5,
      "total_wasted_rupees": 10544.25,
      "efficiency_score": 71,
      "efficiency_grade": "Moderate",
      "idle_hours": 42.5
    },
    "breakdown": [
      { "source": "idle_running", "kwh": 520.0, "percent": 41.9 },
      { "source": "peak_hour_overuse", "kwh": 380.5, "percent": 30.7 },
      { "source": "pressure_inefficiency", "kwh": 220.0, "percent": 17.7 },
      { "source": "other", "kwh": 120.0, "percent": 9.7 }
    ],
    "recommendations": [
      { "rank": 1, "action": "Reduce idle running in off-shift hours", "potential_savings_kwh": 520, "potential_savings_rupees": 4420 },
      { "rank": 2, "action": "Shift non-critical loads away from peak hours", "potential_savings_kwh": 380, "potential_savings_rupees": 3230 }
    ],
    "devices": [
      {
        "device_id": "COMPRESSOR-001",
        "wasted_kwh": 820.0,
        "efficiency_score": 68,
        "efficiency_grade": "Moderate"
      }
    ]
  }
}
```

### 2.7 Analytics API — Port 8003

| Method | Endpoint                                  | Description                    |
|--------|-------------------------------------------|--------------------------------|
| GET    | `/api/v1/analytics/models`                | List available ML models       |
| GET    | `/api/v1/analytics/datasets/{device_id}`  | Check data availability        |
| POST   | `/api/v1/analytics/run`                   | Submit ML job                  |
| GET    | `/api/v1/analytics/jobs`                  | List all jobs                  |
| GET    | `/api/v1/analytics/jobs/{job_id}`         | Get job status                 |
| GET    | `/api/v1/analytics/results/{job_id}`      | Get detailed results           |
| DELETE | `/api/v1/analytics/jobs/{job_id}`         | Cancel/delete job              |

**POST /api/v1/analytics/run — Request:**
```json
{
  "device_id": "COMPRESSOR-001",
  "analysis_type": "anomaly_detection",
  "parameters": {
    "lookback_days": 30,
    "sensitivity": "medium",
    "target_parameters": ["temperature", "vibration", "pressure"]
  }
}
```

### 2.8 Data Export API — Port 8080

| Method | Endpoint                         | Description               |
|--------|----------------------------------|---------------------------|
| POST   | `/api/v1/export`                 | Start export job          |
| GET    | `/api/v1/export/{id}`            | Get export status         |
| GET    | `/api/v1/export/{id}/download`   | Download exported file    |
| GET    | `/api/v1/export/history`         | List past exports         |
| DELETE | `/api/v1/export/{id}`            | Cancel export             |

---

## 3. Service Components & Folder Structure

### 3.1 Device Service

```
services/device-service/
├── app/
│   ├── main.py                    # FastAPI app initialization
│   ├── api/
│   │   ├── routes/
│   │   │   ├── devices.py         # Device CRUD
│   │   │   ├── shifts.py          # Shift management
│   │   │   ├── health.py          # Health config + score
│   │   │   └── uptime.py          # Uptime calculations
│   │   └── dependencies.py        # Shared FastAPI deps
│   ├── models/
│   │   ├── device.py              # SQLAlchemy Device, Shift, HealthConfig
│   │   ├── device_properties.py   # DeviceProperties model
│   │   └── schemas.py             # Pydantic request/response schemas
│   ├── services/
│   │   ├── device_service.py      # Device CRUD business logic
│   │   ├── health_calculator.py   # Health score computation
│   │   └── uptime_calculator.py   # Uptime calculation
│   ├── db/
│   │   ├── session.py             # SQLAlchemy async session
│   │   └── migrations/            # Alembic migrations
│   ├── cache/
│   │   └── redis_client.py        # Redis cache
│   └── config.py                  # Settings (pydantic-settings)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── Dockerfile
└── requirements.txt
```

### 3.2 Data Service

```
services/data-service/
├── src/
│   ├── main.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── telemetry.py       # Historical telemetry REST
│   │   │   ├── websocket.py       # WS live stream
│   │   │   └── properties.py      # Device properties endpoint
│   ├── mqtt/
│   │   ├── client.py              # EMQX MQTT subscriber
│   │   └── handler.py             # Message dispatch
│   ├── services/
│   │   ├── telemetry_service.py   # InfluxDB read/write
│   │   ├── enrichment.py          # Metadata enrichment
│   │   ├── rule_trigger.py        # POST to rule-engine
│   │   └── websocket_manager.py   # WS connection registry
│   ├── influx/
│   │   └── client.py              # InfluxDB client wrapper
│   └── config.py
├── tests/
├── Dockerfile
└── requirements.txt
```

### 3.3 Rule Engine Service

```
services/rule-engine-service/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── rules.py           # Rules CRUD + status
│   │   │   └── alerts.py          # Alert management
│   ├── models/
│   │   ├── rule.py                # Rule, Alert SQLAlchemy models
│   │   └── schemas.py
│   ├── services/
│   │   ├── rule_evaluator.py      # Rule evaluation logic
│   │   ├── alert_manager.py       # Alert lifecycle
│   │   ├── cooldown_manager.py    # Cooldown tracking in Redis
│   │   └── notification/
│   │       ├── dispatcher.py      # Central notification dispatcher
│   │       ├── email_adapter.py   # SMTP via smtplib
│   │       ├── sms_adapter.py     # AWS SNS
│   │       ├── whatsapp_adapter.py# Twilio WhatsApp
│   │       ├── telegram_adapter.py# Telegram Bot API
│   │       └── webhook_adapter.py # HTTP webhook
│   ├── db/
│   └── config.py
├── tests/
├── Dockerfile
└── requirements.txt
```

### 3.4 Reporting Service

```
services/reporting-service/
├── src/
│   ├── main.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── reports.py         # Report generation
│   │   │   ├── wastage.py         # Wastage dashboard
│   │   │   └── schedules.py       # Scheduled reports
│   ├── engines/
│   │   ├── energy_engine.py       # kWh, avg/peak power
│   │   ├── demand_engine.py       # Peak demand analysis
│   │   ├── load_factor_engine.py  # Load factor
│   │   ├── cost_engine.py         # Cost using tariff
│   │   ├── wastage_engine.py      # Wastage + efficiency
│   │   ├── comparison_engine.py   # Device comparisons
│   │   └── insight_engine.py      # AI text insights
│   ├── pdf/
│   │   └── builder.py             # reportlab PDF generation
│   ├── scheduler/
│   │   └── report_scheduler.py    # APScheduler tasks
│   ├── storage/
│   │   └── minio_client.py        # S3-compatible storage
│   └── config.py
├── tests/
├── Dockerfile
└── requirements.txt
```

### 3.5 Analytics Service

```
services/analytics-service/
├── src/
│   ├── main.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── analytics.py       # ML job submission
│   │   │   └── models.py          # Available models
│   ├── models/
│   │   └── schemas.py
│   ├── ml/
│   │   ├── job_runner.py          # Async job execution
│   │   ├── anomaly/
│   │   │   ├── isolation_forest.py
│   │   │   └── z_score.py
│   │   ├── prediction/
│   │   │   ├── failure_predictor.py
│   │   │   └── feature_extractor.py
│   │   └── result_formatter.py    # User-friendly output
│   ├── influx/
│   │   └── data_loader.py         # Load feature data from InfluxDB
│   └── config.py
├── tests/
├── Dockerfile
└── requirements.txt
```

### 3.6 Data Export Service

```
services/data-export-service/
├── src/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       └── export.py
│   ├── exporters/
│   │   ├── csv_exporter.py
│   │   ├── parquet_exporter.py
│   │   └── json_exporter.py
│   ├── storage/
│   │   └── minio_client.py
│   └── config.py
├── Dockerfile
└── requirements.txt
```

### 3.7 Frontend (Next.js 16)

```
ui-web/
├── app/
│   ├── layout.tsx                 # Root layout, theme provider
│   ├── page.tsx                   # Redirect to /machines
│   ├── machines/
│   │   ├── page.tsx               # Machines list
│   │   └── [device_id]/
│   │       ├── page.tsx           # Machine dashboard
│   │       ├── telemetry/page.tsx # Telemetry tab
│   │       ├── charts/page.tsx    # Charts tab
│   │       └── config/page.tsx    # Config tab
│   ├── rules/
│   │   ├── page.tsx               # Rules list
│   │   ├── create/page.tsx        # 4-step rule wizard
│   │   └── [rule_id]/page.tsx     # Rule details
│   ├── alerts/page.tsx            # Alerts list
│   ├── reports/
│   │   ├── page.tsx               # Report history
│   │   ├── energy/page.tsx        # Energy consumption
│   │   └── comparison/page.tsx    # Comparative analysis
│   ├── analytics/page.tsx         # ML analytics
│   ├── wastage/page.tsx           # Energy wastage dashboard
│   └── settings/page.tsx          # System settings
├── components/
│   ├── ui/                        # shadcn/ui base components
│   ├── machines/
│   │   ├── MachineCard.tsx
│   │   ├── MachineGrid.tsx
│   │   ├── StatusBadge.tsx
│   │   └── HealthScoreBadge.tsx
│   ├── dashboard/
│   │   ├── KPICard.tsx
│   │   ├── TelemetryTable.tsx
│   │   ├── LiveChart.tsx
│   │   └── ParameterRow.tsx
│   ├── rules/
│   │   ├── RuleWizard.tsx
│   │   ├── RuleWizardStep1_Scope.tsx
│   │   ├── RuleWizardStep2_Property.tsx
│   │   ├── RuleWizardStep3_Condition.tsx
│   │   └── RuleWizardStep4_Notify.tsx
│   ├── charts/
│   │   ├── TimeSeriesChart.tsx
│   │   ├── BarChart.tsx
│   │   └── PieChart.tsx
│   ├── reports/
│   │   ├── ReportBuilder.tsx
│   │   └── WastageKPICard.tsx
│   ├── notifications/
│   │   └── NotificationBell.tsx
│   └── layout/
│       ├── Sidebar.tsx
│       ├── TopBar.tsx
│       └── ThemeToggle.tsx
├── hooks/
│   ├── useWebSocket.ts            # WS connection + reconnect
│   ├── useDevices.ts              # SWR device queries
│   ├── useAlerts.ts
│   └── useReports.ts
├── lib/
│   ├── api.ts                     # Axios client
│   ├── constants.ts
│   └── utils.ts
├── store/
│   ├── useThemeStore.ts           # Zustand theme state
│   └── useNotificationStore.ts    # Notification bell state
└── types/
    ├── device.ts
    ├── rule.ts
    ├── alert.ts
    └── report.ts
```

---

## 4. Business Logic — Implementation Details

### 4.1 Health Score Calculator

**Algorithm:**

```python
# services/device-service/app/services/health_calculator.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HealthConfigEntry:
    parameter_name: str
    normal_min: Optional[float]
    normal_max: Optional[float]
    max_min: Optional[float]
    max_max: Optional[float]
    weight: float  # Must sum to 100 across all configs for a device

def calculate_parameter_score(
    value: float,
    normal_min: Optional[float],
    normal_max: Optional[float],
    max_min: Optional[float],
    max_max: Optional[float]
) -> float:
    """
    Scoring logic:
    - Value in [normal_min, normal_max] → 100 (full score)
    - Value between normal and max ranges → linear interpolation 50–99
    - Value outside max range → 0
    - Missing bounds → skip (contribute 0, weight redistributed)
    """
    if value is None:
        return None  # Parameter not present

    # Within normal range = full score
    if normal_min is not None and normal_max is not None:
        if normal_min <= value <= normal_max:
            return 100.0

    # Below normal_min — check max_min
    if normal_min is not None and value < normal_min:
        if max_min is not None:
            if value < max_min:
                return 0.0
            # Linear interpolation: max_min → 50, normal_min → 100
            ratio = (value - max_min) / (normal_min - max_min)
            return 50.0 + (ratio * 50.0)
        return 50.0

    # Above normal_max — check max_max
    if normal_max is not None and value > normal_max:
        if max_max is not None:
            if value > max_max:
                return 0.0
            # Linear interpolation: normal_max → 100, max_max → 50
            ratio = (max_max - value) / (max_max - normal_max)
            return 50.0 + (ratio * 50.0)
        return 50.0

    return 100.0

def calculate_health_score(
    telemetry: dict,
    configs: List[HealthConfigEntry]
) -> dict:
    """
    Returns health_score (0–100) and health_grade.
    Weights are normalized if some parameters are missing.
    """
    total_weight = 0.0
    weighted_score = 0.0

    for config in configs:
        value = telemetry.get(config.parameter_name)
        if value is None:
            continue  # Skip missing parameters

        score = calculate_parameter_score(
            value,
            config.normal_min,
            config.normal_max,
            config.max_min,
            config.max_max
        )
        weighted_score += score * config.weight
        total_weight += config.weight

    if total_weight == 0:
        return {"health_score": None, "health_grade": "Unknown"}

    # Normalize for missing parameters
    final_score = round(weighted_score / total_weight, 2)

    grade = (
        "Excellent" if final_score >= 90 else
        "Good"      if final_score >= 70 else
        "Fair"      if final_score >= 50 else
        "Poor"
    )

    return {
        "health_score": final_score,
        "health_grade": grade,
        "parameter_scores": {
            c.parameter_name: calculate_parameter_score(
                telemetry.get(c.parameter_name), c.normal_min, c.normal_max,
                c.max_min, c.max_max
            )
            for c in configs if telemetry.get(c.parameter_name) is not None
        }
    }
```

### 4.2 Uptime Calculator

```python
# services/device-service/app/services/uptime_calculator.py

from datetime import datetime, timedelta, time
from typing import List, Optional

@dataclass
class Shift:
    shift_name: str
    shift_start: time
    shift_end: time
    maintenance_break_minutes: int
    day_of_week: Optional[int]  # None = all days

def calculate_shift_minutes(shifts: List[Shift], period_start: datetime, period_end: datetime) -> float:
    """
    Total planned operational minutes in the period based on shifts.
    Handles overnight shifts (e.g., 22:00 → 06:00).
    """
    total_minutes = 0.0
    current_day = period_start.date()

    while current_day <= period_end.date():
        day_of_week = current_day.weekday()  # 0=Monday

        for shift in shifts:
            if shift.day_of_week is not None and shift.day_of_week != day_of_week:
                continue

            # Determine shift window
            start_dt = datetime.combine(current_day, shift.shift_start)
            end_dt = datetime.combine(current_day, shift.shift_end)

            # Handle overnight shifts
            if shift.shift_end <= shift.shift_start:
                end_dt += timedelta(days=1)

            # Clip to period
            start_dt = max(start_dt, period_start)
            end_dt = min(end_dt, period_end)

            if end_dt > start_dt:
                shift_minutes = (end_dt - start_dt).total_seconds() / 60
                net_minutes = shift_minutes - shift.maintenance_break_minutes
                total_minutes += max(net_minutes, 0)

        current_day += timedelta(days=1)

    return total_minutes

def calculate_uptime(
    shifts: List[Shift],
    last_seen_timestamps: List[datetime],  # All timestamps where device was "running"
    period_start: datetime,
    period_end: datetime,
    running_threshold_seconds: int = 70  # If gap > 70s during shift → considered down
) -> dict:
    """
    Uptime = (minutes device was running during shift) / (total shift minutes) × 100
    Device is "running" if it emitted a telemetry heartbeat within the last threshold.
    """
    planned_minutes = calculate_shift_minutes(shifts, period_start, period_end)

    if planned_minutes == 0:
        return {"uptime_percent": 0.0, "planned_minutes": 0, "running_minutes": 0}

    # Calculate running minutes by checking consecutive heartbeats
    sorted_ts = sorted(last_seen_timestamps)
    running_minutes = 0.0

    for i in range(len(sorted_ts) - 1):
        t1 = sorted_ts[i]
        t2 = sorted_ts[i + 1]
        gap = (t2 - t1).total_seconds()

        # If gap is small, device was running continuously
        if gap <= running_threshold_seconds:
            overlap = min(t2, period_end) - max(t1, period_start)
            if overlap.total_seconds() > 0:
                running_minutes += overlap.total_seconds() / 60

    uptime_percent = round((running_minutes / planned_minutes) * 100, 2)

    return {
        "uptime_percent": min(uptime_percent, 100.0),
        "planned_minutes": round(planned_minutes, 2),
        "running_minutes": round(running_minutes, 2),
        "downtime_minutes": round(planned_minutes - running_minutes, 2)
    }
```

### 4.3 Rule Evaluator

```python
# services/rule-engine-service/app/services/rule_evaluator.py

import operator
from typing import Optional
from datetime import datetime, timedelta
import uuid

OPERATORS = {
    ">":  operator.gt,
    "<":  operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

async def evaluate_rules(
    device_id: str,
    telemetry: dict,
    timestamp: datetime,
    db_session,
    redis_client,
    notification_dispatcher
):
    """
    Called by data-service for every telemetry message.
    Steps:
    1. Fetch all active rules that match device_id
    2. For each rule, evaluate condition
    3. Check cooldown in Redis
    4. Create alert + dispatch notification if triggered
    """
    rules = await db_session.execute(
        "SELECT * FROM rules WHERE status = 'active' AND "
        "(scope = 'all' OR JSON_CONTAINS(device_ids, :did))",
        {"did": f'"{device_id}"'}
    )

    for rule in rules:
        # Get telemetry value for the rule's target property
        actual_value = telemetry.get(rule["property"])
        if actual_value is None:
            continue

        # Evaluate condition
        op_fn = OPERATORS.get(rule["condition"])
        if op_fn is None or not op_fn(actual_value, rule["threshold"]):
            continue

        # Check cooldown (Redis key: cooldown:{rule_id}:{device_id})
        cooldown_key = f"cooldown:{rule['rule_id']}:{device_id}"
        if await redis_client.exists(cooldown_key):
            continue  # In cooldown, skip notification

        # Create alert record
        alert_id = str(uuid.uuid4())
        await db_session.execute(
            "INSERT INTO alerts (alert_id, rule_id, device_id, severity, status, "
            "property, condition, threshold_value, actual_value, message, triggered_at) "
            "VALUES (:alert_id, :rule_id, :device_id, :severity, 'open', "
            ":property, :condition, :threshold, :actual, :message, :ts)",
            {
                "alert_id": alert_id,
                "rule_id": rule["rule_id"],
                "device_id": device_id,
                "severity": rule["severity"],
                "property": rule["property"],
                "condition": rule["condition"],
                "threshold": rule["threshold"],
                "actual": actual_value,
                "message": f"{rule['property']} is {actual_value} ({rule['condition']} {rule['threshold']})",
                "ts": timestamp
            }
        )
        await db_session.commit()

        # Set cooldown
        cooldown_secs = (rule.get("cooldown_minutes") or 15) * 60
        await redis_client.setex(cooldown_key, cooldown_secs, "1")

        # Dispatch notification
        await notification_dispatcher.dispatch(
            alert_id=alert_id,
            rule=rule,
            device_id=device_id,
            actual_value=actual_value,
            timestamp=timestamp
        )
```

### 4.4 Wastage Engine

```python
# services/reporting-service/src/engines/wastage_engine.py

import numpy as np
from typing import List, Tuple

def calculate_wastage(
    timestamps: List[float],          # Unix epoch seconds
    power_series: List[float],        # Watts
    rated_power_kw: float,            # Device rated power
    tariff_rate: float,               # ₹ per kWh
    shift_periods: List[Tuple[float, float]]  # (start_epoch, end_epoch)
) -> dict:
    """
    Calculates energy wastage for a given period.
    """
    if not power_series:
        return _empty_result()

    power_kw = np.array(power_series) / 1000.0

    # Total energy consumed
    duration_hours = (timestamps[-1] - timestamps[0]) / 3600.0
    actual_kwh = float(np.trapz(power_kw, np.array(timestamps) / 3600.0))

    # Optimal baseline = 25th percentile of non-idle power
    non_idle_mask = power_kw > (0.3 * rated_power_kw)
    if non_idle_mask.sum() < 10:
        optimal_avg_kw = float(np.percentile(power_kw, 25))
    else:
        optimal_avg_kw = float(np.percentile(power_kw[non_idle_mask], 25))

    runtime_hours = float(non_idle_mask.sum()) * (duration_hours / len(power_kw))
    optimal_kwh = optimal_avg_kw * runtime_hours
    wasted_kwh = max(actual_kwh - optimal_kwh, 0)
    wasted_rupees = wasted_kwh * tariff_rate

    # Idle detection
    idle_threshold_kw = 0.3 * rated_power_kw
    idle_mask = power_kw < idle_threshold_kw
    idle_hours = float(idle_mask.sum()) * (duration_hours / len(power_kw))

    # Idle wastage = power consumed while idle
    idle_power_kw = power_kw[idle_mask]
    idle_wastage_kwh = float(np.trapz(
        idle_power_kw,
        np.array(timestamps)[idle_mask] / 3600.0
    )) if idle_mask.sum() > 1 else 0.0

    # Peak hour wastage (simple heuristic: top 20% power values)
    peak_threshold = np.percentile(power_kw, 80)
    peak_mask = power_kw > peak_threshold
    peak_wastage_kwh = max(
        float(np.trapz(
            power_kw[peak_mask] - optimal_avg_kw,
            np.array(timestamps)[peak_mask] / 3600.0
        )), 0.0
    ) if peak_mask.sum() > 1 else 0.0

    # Pressure / other wastage
    other_kwh = max(wasted_kwh - idle_wastage_kwh - peak_wastage_kwh, 0)

    # Efficiency score
    if actual_kwh > 0:
        efficiency_score = round(min((optimal_kwh / actual_kwh) * 100, 100), 1)
    else:
        efficiency_score = 100.0

    efficiency_grade = (
        "Excellent" if efficiency_score >= 85 else
        "Good"      if efficiency_score >= 70 else
        "Moderate"  if efficiency_score >= 50 else
        "Poor"
    )

    return {
        "actual_kwh": round(actual_kwh, 2),
        "optimal_kwh": round(optimal_kwh, 2),
        "wasted_kwh": round(wasted_kwh, 2),
        "wasted_rupees": round(wasted_rupees, 2),
        "idle_hours": round(idle_hours, 2),
        "efficiency_score": efficiency_score,
        "efficiency_grade": efficiency_grade,
        "breakdown": [
            {"source": "idle_running",        "kwh": round(idle_wastage_kwh, 2)},
            {"source": "peak_hour_overuse",    "kwh": round(peak_wastage_kwh, 2)},
            {"source": "other",                "kwh": round(other_kwh, 2)},
        ]
    }

def _empty_result():
    return {
        "actual_kwh": 0, "optimal_kwh": 0, "wasted_kwh": 0,
        "wasted_rupees": 0, "idle_hours": 0,
        "efficiency_score": 0, "efficiency_grade": "Unknown",
        "breakdown": []
    }
```

### 4.5 Runtime Status Determination

```python
# Device runtime_status is computed at read time (not stored)
# Logic in device-service GET /api/v1/devices

OFFLINE_THRESHOLD_SECONDS = 70  # 70 seconds without heartbeat = offline

def compute_runtime_status(last_seen_timestamp: Optional[datetime]) -> str:
    """
    running  → last_seen within 70 seconds
    stopped  → last_seen > 70 seconds ago
    unknown  → never seen
    """
    if last_seen_timestamp is None:
        return "unknown"
    
    delta = (datetime.utcnow() - last_seen_timestamp).total_seconds()
    return "running" if delta <= OFFLINE_THRESHOLD_SECONDS else "stopped"
```

---

## 5. Data Flow Diagrams

### 5.1 Telemetry Ingestion Flow

```
DEVICE/SIMULATOR
  │ MQTT publish: topic = "telemetry/{device_id}"
  │ Payload: { "power": 5200, "voltage": 228, "temperature": 45 }
  ▼
EMQX BROKER (:1883)
  │ Persistent TCP MQTT connection
  ▼
DATA SERVICE — MQTT Handler
  │ 1. Parse JSON payload
  │ 2. Validate schema (required field: device_id or topic-derived)
  │ 3. Add schema_version tag
  ▼
DATA SERVICE — Enrichment
  │ HTTP GET device-service /api/v1/devices/{device_id}
  │ (Redis cached for 5 min → fallback to DB)
  │ Attaches: device_name, device_type, location
  ▼
PARALLEL FAN-OUT (asyncio.gather):
  ├── InfluxDB Write
  │     Measurement: telemetry
  │     Tags: device_id, schema_version, enrichment_status
  │     Fields: all numeric telemetry values
  │     Timestamp: from payload or server time
  │
  ├── Rule Engine Trigger
  │     HTTP POST rule-engine /api/v1/rules/evaluate
  │     { device_id, timestamp, telemetry_dict }
  │     (Fire-and-forget with timeout = 2s)
  │
  ├── WebSocket Broadcast
  │     WS Manager → push to all subscribers of device_id
  │
  └── Device Heartbeat Update
        HTTP POST device-service /api/v1/devices/{device_id}/heartbeat
        { last_seen: timestamp }
```

### 5.2 Rule Evaluation & Notification Flow

```
DATA SERVICE → POST /api/v1/rules/evaluate { device_id, telemetry }
  │
  ▼
RULE ENGINE SERVICE
  │ 1. Fetch active rules for device_id from MySQL
  │    (Redis cached rules list, TTL 60s)
  │
  ├── For each rule:
  │     a. Read telemetry[rule.property]
  │     b. Evaluate: actual_value {condition} threshold
  │     c. If FALSE → skip
  │     d. Check Redis cooldown key
  │     e. If IN COOLDOWN → skip
  │
  │     f. Create Alert record in MySQL (status=open)
  │     g. Set Redis cooldown key (TTL = cooldown_minutes × 60)
  │     h. Dispatch notification (async)
  │
  ▼
NOTIFICATION DISPATCHER
  │ Reads rule.notifications JSON for channels
  │
  ├── email    → EmailAdapter (SMTP)
  ├── sms      → SMSAdapter (AWS SNS)
  ├── whatsapp → WhatsAppAdapter (Twilio)
  ├── telegram → TelegramAdapter (Bot API)
  └── webhook  → WebhookAdapter (HTTP POST)
  │
  ▼
NOTIFICATION LOG
  │ INSERT into notification_logs (status, response_id, error_message)
```

### 5.3 Report Generation Flow

```
USER → POST /api/v1/reports/consumption { device_ids, start, end, group_by }
  │
  ▼
REPORTING SERVICE
  │ 1. Create energy_reports record (status = pending)
  │ 2. Return { report_id }
  │ 3. Submit to background task queue (asyncio background task)
  │
ASYNC JOB:
  │ a. Query InfluxDB for power time-series
  │    Flux query with aggregation (hourly/daily/weekly window mean)
  │
  │ b. Energy Engine
  │    total_kwh = trapz(power_kw, time_hours)
  │    avg_power_kw = mean(power_kw)
  │    peak_power_kw = max(power_kw)
  │
  │ c. Demand Engine
  │    peak_demand = max 15-min rolling average of power
  │    peak_timestamp = argmax of peak demand
  │
  │ d. Load Factor Engine
  │    load_factor = avg_power / peak_demand
  │    classification = lookup table
  │
  │ e. Cost Engine
  │    total_cost = total_kwh × tariff.rate_per_unit
  │    peak_cost = peak_kwh × tariff.peak_rate
  │
  │ f. Wastage Engine (if include_wastage=true)
  │    wasted_kwh, efficiency_score, breakdown
  │
  │ g. Insight Engine
  │    Generates 3–5 text insights (rule-based + optionally LLM)
  │
  │ h. Assemble result_json
  │ i. Generate PDF via reportlab (if format=pdf)
  │ j. Upload to MinIO: reports/{tenant_id}/{report_id}.pdf
  │ k. Update energy_reports record (status=completed, s3_key)
  │
USER → GET /api/v1/reports/{report_id}
  │ status=completed → presigned_url for download
```

### 5.4 WebSocket Live Telemetry

```
UI Client
  │ WS connect: ws://host/ws/telemetry/COMPRESSOR-001
  │ Sends: { "subscribe": "COMPRESSOR-001" }
  │
  ▼
DATA SERVICE — WebSocket Manager
  │ Registers connection: connections[device_id] = [ws1, ws2, ...]
  │ Maintains heartbeat ping every 30s
  │
  │ On new telemetry for COMPRESSOR-001:
  │   → iterate connections[device_id]
  │   → send JSON message to each connected client
  │
  │ On client disconnect:
  │   → remove from connections registry
  │
UI receives 1-second updates → renders live table + updates gauge charts
```

---

## 6. Frontend Architecture

### 6.1 State Management

| State Category   | Tool      | Notes                                      |
|-----------------|-----------|---------------------------------------------|
| Server data      | SWR       | Device list, rules, alerts (auto-revalidate) |
| Live telemetry   | useState  | Fed from WebSocket hook                     |
| Theme            | Zustand   | Persisted to localStorage                   |
| Notifications    | Zustand   | Bell count, read/unread                     |
| Form state       | react-hook-form | Rule wizard, config forms             |

### 6.2 Data Fetching Strategy

```typescript
// hooks/useDevices.ts
import useSWR from 'swr';
import { apiClient } from '@/lib/api';

export function useDevices(filters?: DeviceFilters) {
  const key = ['/api/v1/devices', filters];
  const { data, error, isLoading, mutate } = useSWR(
    key,
    () => apiClient.get('/api/v1/devices', { params: filters }).then(r => r.data),
    { refreshInterval: 30_000 }  // Re-fetch every 30s for status updates
  );
  return { devices: data?.data, error, isLoading, refresh: mutate };
}

// hooks/useWebSocket.ts
export function useWebSocket(deviceId: string) {
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/ws/telemetry/${deviceId}`);
      ws.onmessage = (e) => setTelemetry(JSON.parse(e.data));
      ws.onclose = () => setTimeout(connect, 3000);  // Auto-reconnect
      wsRef.current = ws;
    };
    connect();
    return () => wsRef.current?.close();
  }, [deviceId]);

  return { telemetry };
}
```

### 6.3 Rule Creation Wizard — 4 Steps

```
Step 1 — Scope
  ├── Radio: "All Devices" | "Selected Devices"
  └── If Selected: Multi-select device list (searchable)

Step 2 — Property
  ├── API call: GET /api/properties?device_ids=[...] → available parameters
  ├── Dropdown: Select parameter (power, temperature, vibration, ...)
  └── Auto-shows unit and current value preview

Step 3 — Condition
  ├── Dropdown: >, <, >=, <=, ==, !=
  ├── Number input: threshold value
  ├── Select severity: Critical | Warning | Info
  └── Number input: cooldown_minutes (default 15)

Step 4 — Notifications
  ├── Email: Add recipients (+ button, email validation)
  ├── SMS: Add phone numbers (+91 prefix)
  ├── WhatsApp: Add numbers
  ├── Telegram: Add chat IDs
  └── Webhook: Add URLs
```

### 6.4 Machines Page Card Layout

```
[Device Card]
┌─────────────────────────────────┐
│ ● RUNNING  |  COMPRESSOR-001   │
│ Main Compressor                 │
│ Plant A - Building 1            │
│                                 │
│ Health: ████████░░ 82 (Good)    │
│ Uptime: 94.2%                   │
│ Last Seen: 2 seconds ago        │
│                                 │
│         [Open Dashboard →]      │
└─────────────────────────────────┘
```

### 6.5 Machine Dashboard Tab Layout

```
[Machine Dashboard]
Tab: Overview | Telemetry | Charts | Config

── Overview ──
KPIs: Health Score | Uptime % | Param Efficiency | Total kWh

── Telemetry (Live) ──
Refreshes every 1 second via WebSocket
Columns: Parameter | Value | Unit | Status (color-coded)

── Charts ──
Date range picker (1d, 7d, 30d, custom)
Multi-parameter line chart (Recharts)

── Config ──
Sub-tabs: Shift Config | Health Config
```

---

## 7. Notification Service

### 7.1 Notification Dispatcher

```python
# services/rule-engine-service/app/services/notification/dispatcher.py

from typing import Optional
import asyncio

class NotificationDispatcher:
    def __init__(self, db_session, notification_config_cache):
        self.db = db_session
        self.config_cache = notification_config_cache

    async def dispatch(self, alert_id, rule, device_id, actual_value, timestamp):
        """
        Dispatches notifications to all channels configured in rule.notifications.
        Failures in one channel don't block others.
        Logs all attempts to notification_logs.
        """
        channels = rule.get("notification_channels_json") or {}
        context = self._build_context(rule, device_id, actual_value, timestamp, alert_id)

        tasks = []
        if channels.get("email"):
            tasks.append(self._send_email(channels["email"], context, alert_id, rule))
        if channels.get("sms"):
            tasks.append(self._send_sms(channels["sms"], context, alert_id, rule))
        if channels.get("whatsapp"):
            tasks.append(self._send_whatsapp(channels["whatsapp"], context, alert_id, rule))
        if channels.get("telegram"):
            tasks.append(self._send_telegram(channels["telegram"], context, alert_id, rule))
        if channels.get("webhook"):
            tasks.append(self._send_webhook(channels["webhook"], context, alert_id, rule))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Errors are logged; no exception propagation

    def _build_context(self, rule, device_id, actual_value, timestamp, alert_id) -> dict:
        return {
            "device_id": device_id,
            "rule_name": rule["rule_name"],
            "property": rule["property"],
            "condition": rule["condition"],
            "threshold": rule["threshold"],
            "actual_value": actual_value,
            "severity": rule["severity"],
            "timestamp": timestamp.isoformat(),
            "alert_id": alert_id,
            "alert_message": f"{rule['property']} is {actual_value} (threshold: {rule['condition']} {rule['threshold']})"
        }
```

### 7.2 Email Adapter

```python
# services/rule-engine-service/app/services/notification/email_adapter.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailAdapter:
    def __init__(self, smtp_host, smtp_port, smtp_user, smtp_password, from_email):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email

    def render_template(self, template: str, context: dict) -> str:
        for key, value in context.items():
            template = template.replace("{{" + key + "}}", str(value))
        return template

    async def send(self, recipients: list, context: dict, subject_template: str, body_template: str) -> str:
        subject = self.render_template(subject_template, context)
        body = self.render_template(body_template, context)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, recipients, msg.as_string())

        return "email_sent"
```

**Default Email Template:**
```html
<h2>⚠️ Alert: {{rule_name}}</h2>
<p><b>Device:</b> {{device_id}}</p>
<p><b>Parameter:</b> {{property}}</p>
<p><b>Actual Value:</b> {{actual_value}}</p>
<p><b>Threshold:</b> {{condition}} {{threshold}}</p>
<p><b>Severity:</b> {{severity}}</p>
<p><b>Time:</b> {{timestamp}}</p>
```

### 7.3 SMS Adapter (AWS SNS)

```python
import boto3

class SMSAdapter:
    def __init__(self, aws_access_key, aws_secret_key, aws_region):
        self.client = boto3.client(
            "sns",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )

    async def send(self, phone_numbers: list, context: dict, body_template: str) -> list:
        message = f"[{context['severity'].upper()}] {context['rule_name']}: "
                  f"{context['property']} is {context['actual_value']} "
                  f"on device {context['device_id']}"

        message_ids = []
        for phone in phone_numbers:
            response = self.client.publish(
                PhoneNumber=phone,
                Message=message[:160],  # SMS limit
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional"
                    }
                }
            )
            message_ids.append(response["MessageId"])
        return message_ids
```

### 7.4 Telegram Adapter

```python
import httpx

class TelegramAdapter:
    BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.url = self.BASE_URL.format(token=bot_token)

    async def send(self, chat_ids: list, context: dict, body_template: str) -> list:
        message = (
            f"🚨 *{context['rule_name']}*\n"
            f"Device: `{context['device_id']}`\n"
            f"Parameter: `{context['property']}`\n"
            f"Value: `{context['actual_value']}` (threshold: {context['condition']} {context['threshold']})\n"
            f"Severity: *{context['severity'].upper()}*\n"
            f"Time: {context['timestamp']}"
        )

        results = []
        async with httpx.AsyncClient() as client:
            for chat_id in chat_ids:
                resp = await client.post(self.url, json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                })
                results.append(resp.json().get("result", {}).get("message_id"))
        return results
```

### 7.5 Webhook Adapter

```python
import httpx

class WebhookAdapter:
    async def send(self, webhook_urls: list, context: dict) -> list:
        payload = {
            "alert_id": context["alert_id"],
            "rule_name": context["rule_name"],
            "device_id": context["device_id"],
            "property": context["property"],
            "actual_value": context["actual_value"],
            "threshold": context["threshold"],
            "condition": context["condition"],
            "severity": context["severity"],
            "timestamp": context["timestamp"],
            "message": context["alert_message"]
        }

        results = []
        async with httpx.AsyncClient(timeout=5.0) as client:
            for url in webhook_urls:
                try:
                    resp = await client.post(url, json=payload)
                    results.append({"url": url, "status": resp.status_code})
                except Exception as e:
                    results.append({"url": url, "error": str(e)})
        return results
```

### 7.6 Notification Credential Storage Schema

Credentials are stored in `notification_configs` table (per the database schema), encrypted at rest using AES-256 via a KMS-managed key before storage.

| Field            | Encrypted? | Notes                        |
|-----------------|-----------|------------------------------|
| smtp_password   | Yes       | Email password               |
| aws_secret_key  | Yes       | SNS secret                   |
| twilio_auth_token| Yes      | WhatsApp/SMS                 |
| telegram_bot_token| Yes    | Telegram                     |
| webhook_secret  | Yes       | HMAC webhook signing secret  |

**Encryption approach:**
```python
from cryptography.fernet import Fernet

class CredentialEncryption:
    def __init__(self, kms_key: bytes):
        self.fernet = Fernet(kms_key)

    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()
```

---

## 8. Analytics Service

### 8.1 ML Job Lifecycle

```
Job Status FSM:
  pending → running → completed
                   → failed
  pending → cancelled
```

### 8.2 Anomaly Detection — Isolation Forest

```python
# services/analytics-service/src/ml/anomaly/isolation_forest.py

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetector:
    def __init__(self, contamination=0.05, sensitivity="medium"):
        contamination_map = {"low": 0.02, "medium": 0.05, "high": 0.10}
        self.contamination = contamination_map.get(sensitivity, 0.05)

    def run(self, feature_matrix: np.ndarray, timestamps: list, parameter_names: list) -> dict:
        """
        feature_matrix: (n_samples, n_features)
        Returns anomaly timestamps, scores, and user-friendly summary.
        """
        scaler = StandardScaler()
        X = scaler.fit_transform(feature_matrix)

        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = model.fit_predict(X)  # -1 = anomaly, 1 = normal
        scores = -model.decision_function(X)  # Higher = more anomalous

        anomaly_indices = np.where(predictions == -1)[0]
        anomalies = [
            {
                "timestamp": timestamps[i],
                "anomaly_score": round(float(scores[i]), 4),
                "parameter_contributions": {
                    name: round(float(abs(X[i, j])), 3)
                    for j, name in enumerate(parameter_names)
                }
            }
            for i in anomaly_indices
        ]

        return {
            "analysis_type": "anomaly_detection",
            "total_samples": len(timestamps),
            "anomalies_found": len(anomalies),
            "anomaly_rate_percent": round((len(anomalies) / len(timestamps)) * 100, 2),
            "anomalies": sorted(anomalies, key=lambda x: x["anomaly_score"], reverse=True)[:50],
            "summary": self._generate_summary(anomalies, parameter_names, feature_matrix)
        }

    def _generate_summary(self, anomalies, parameter_names, X) -> str:
        if not anomalies:
            return "No significant anomalies detected in the selected period."
        count = len(anomalies)
        top_param = max(
            parameter_names,
            key=lambda p: sum(a["parameter_contributions"].get(p, 0) for a in anomalies)
        )
        return (
            f"Detected {count} anomalous events. "
            f"'{top_param}' shows the highest deviation and may warrant inspection."
        )
```

### 8.3 Failure Prediction — Rolling Feature Extraction

```python
# services/analytics-service/src/ml/prediction/feature_extractor.py

import pandas as pd
import numpy as np

def extract_rolling_features(df: pd.DataFrame, window_hours: int = 6) -> pd.DataFrame:
    """
    Extracts statistical features over rolling windows for failure prediction.
    """
    window = f"{window_hours}h"
    features = pd.DataFrame(index=df.index)

    for col in df.select_dtypes(include=[np.number]).columns:
        features[f"{col}_mean"] = df[col].rolling(window).mean()
        features[f"{col}_std"]  = df[col].rolling(window).std()
        features[f"{col}_max"]  = df[col].rolling(window).max()
        features[f"{col}_min"]  = df[col].rolling(window).min()
        features[f"{col}_trend"] = df[col].rolling(window).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0,
            raw=True
        )

    return features.dropna()
```

### 8.4 User-Friendly Result Formatter

```python
# services/analytics-service/src/ml/result_formatter.py

def format_for_display(raw_result: dict) -> dict:
    """
    Transforms ML output into business-friendly language.
    """
    if raw_result["analysis_type"] == "anomaly_detection":
        count = raw_result["anomalies_found"]
        rate = raw_result["anomaly_rate_percent"]

        if count == 0:
            status = "Healthy"
            message = "Your equipment is operating normally. No unusual patterns detected."
            color = "green"
        elif rate < 5:
            status = "Minor Anomalies"
            message = f"Found {count} minor anomalies. Continue monitoring."
            color = "yellow"
        else:
            status = "Attention Required"
            message = f"Detected {count} anomalies ({rate}% of readings). Recommend inspection."
            color = "red"

        return {
            "status": status,
            "status_color": color,
            "message": message,
            "summary": raw_result.get("summary"),
            "details": raw_result
        }
    return raw_result
```

---

## 9. Data Export Service

### 9.1 Export Flow

```python
# services/data-export-service/src/exporters/csv_exporter.py

import csv
import io
from influxdb_client import InfluxDBClient

class CSVExporter:
    def __init__(self, influx_client: InfluxDBClient, minio_client):
        self.influx = influx_client
        self.minio = minio_client

    async def export(self, device_id: str, start: str, end: str, export_id: int) -> str:
        """
        Exports telemetry to CSV in chunks (handles 90 days of 1s data = ~7.8M rows).
        Returns S3 key.
        """
        query = f'''
        from(bucket: "telemetry")
          |> range(start: {start}, stop: {end})
          |> filter(fn: (r) => r.device_id == "{device_id}")
          |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        output = io.StringIO()
        writer = None
        records_count = 0

        query_api = self.influx.query_api()
        for record in query_api.query_stream(query):
            row = dict(record.values)
            row["timestamp"] = record.get_time().isoformat()

            if writer is None:
                writer = csv.DictWriter(output, fieldnames=list(row.keys()))
                writer.writeheader()

            writer.writerow(row)
            records_count += 1

        csv_bytes = output.getvalue().encode("utf-8")
        s3_key = f"exports/{device_id}/{export_id}.csv"
        await self.minio.put_object("energy-exports", s3_key, csv_bytes)

        return s3_key, records_count
```

---

## 10. Error Handling

### 10.1 HTTP Error Codes

| Code              | HTTP Status | Description                  |
|------------------|-------------|------------------------------|
| ERR_NOT_FOUND    | 404         | Resource not found           |
| ERR_VALIDATION   | 400         | Request validation failed    |
| ERR_UNAUTHORIZED | 401         | Missing or invalid API key   |
| ERR_FORBIDDEN    | 403         | Access not permitted         |
| ERR_CONFLICT     | 409         | Resource already exists      |
| ERR_INTERNAL     | 500         | Internal server error        |
| ERR_TIMEOUT      | 504         | Upstream timeout             |
| ERR_EXTERNAL     | 502         | External service error       |
| ERR_RATE_LIMIT   | 429         | Rate limit exceeded          |

### 10.2 Service-Specific Errors

**Device Service:**
| Code                 | Description                               |
|---------------------|-------------------------------------------|
| DEVICE_NOT_FOUND    | device_id does not exist                  |
| DEVICE_EXISTS       | device_id already registered              |
| INVALID_DEVICE_TYPE | device_type not in allowed list           |
| SHIFT_CONFLICT      | Overlapping shift times detected          |
| WEIGHTS_NOT_100     | Health config weights don't sum to 100    |
| HEALTH_CONFIG_EMPTY | No health configs found for device        |

**Rule Engine:**
| Code                   | Description                             |
|-----------------------|-----------------------------------------|
| RULE_NOT_FOUND        | rule_id does not exist                  |
| RULE_DISABLED         | Rule is paused or archived              |
| INVALID_CONDITION     | Condition operator not supported        |
| NOTIFICATION_FAILED   | All notification channels failed        |
| COOLDOWN_ACTIVE       | Alert suppressed due to cooldown        |

**Reporting:**
| Code               | Description                               |
|-------------------|-------------------------------------------|
| REPORT_NOT_FOUND  | report_id does not exist                  |
| REPORT_FAILED     | Async report generation failed            |
| INVALID_DATE_RANGE| Date range exceeds 90 days limit          |
| NO_DATA_FOUND     | No telemetry available for date range     |
| TARIFF_NOT_FOUND  | No tariff configured for tenant           |

### 10.3 Global Exception Handler

```python
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uuid, logging

logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={
        "success": False,
        "error": {
            "code": "ERR_VALIDATION",
            "message": "Validation failed",
            "details": [
                {"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]}
                for e in exc.errors()
            ]
        },
        "request_id": str(uuid.uuid4())
    })

@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={
        "success": False,
        "error": {"code": "ERR_INTERNAL", "message": "An internal error occurred"},
        "request_id": str(uuid.uuid4())
    })
```

### 10.4 Circuit Breaker Pattern

```python
# For external dependencies (InfluxDB, EMQX, notification APIs)
# Use tenacity for retry with exponential backoff

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def write_to_influxdb(client, record):
    await client.write(record)
```

---

## 11. Security Design

### 11.1 API Authentication

```python
# All services share the same API key validation middleware

from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail={
            "code": "ERR_UNAUTHORIZED",
            "message": "Invalid or missing API key"
        })
    return api_key
```

### 11.2 Sensitive Data Protection

| Data                    | Protection                        |
|------------------------|-----------------------------------|
| Notification credentials| AES-256 encryption at rest        |
| Webhook secrets        | AES-256 encryption at rest        |
| API keys               | Hashed with bcrypt before storage |
| Telemetry data         | TLS in transit                    |
| Reports (PDF/CSV)      | Presigned S3 URLs (TTL: 1 hour)   |
| Database connections   | TLS required for MySQL/InfluxDB   |

### 11.3 Input Validation

All API inputs are validated with Pydantic models:
- Device IDs: `^[A-Za-z0-9\-_]{1,50}$`
- Date ranges: Max 90 days
- Phone numbers: E.164 format validation
- Webhook URLs: HTTPS only (reject HTTP)
- Threshold values: Must be finite float

### 11.4 SQL Injection Prevention

All database queries use SQLAlchemy parameterized queries. No raw SQL string formatting is permitted.

### 11.5 Rate Limiting (NGINX)

```nginx
limit_req_zone $binary_remote_addr zone=api_general:10m rate=1000r/m;
limit_req_zone $binary_remote_addr zone=api_write:10m rate=100r/m;

location /api/ {
    limit_req zone=api_general burst=50 nodelay;
}
location ~* /api/v1/(devices|rules)$ {
    limit_req zone=api_write burst=20 nodelay;
    limit_except GET { limit_req zone=api_write; }
}
```

---

## 12. Configuration Management

### 12.1 Environment Variables per Service

**device-service:**
```env
DATABASE_URL=mysql+aiomysql://user:pass@mysql:3306/energy_device_db
REDIS_URL=redis://redis:6379/0
API_KEY=changeme-secret-key
LOG_LEVEL=INFO
OFFLINE_THRESHOLD_SECONDS=70
```

**data-service:**
```env
INFLUX_URL=http://influxdb:8086
INFLUX_TOKEN=my-token
INFLUX_ORG=energy
INFLUX_BUCKET=telemetry
MQTT_HOST=emqx
MQTT_PORT=1883
MQTT_TOPIC_PATTERN=telemetry/#
DEVICE_SERVICE_URL=http://device-service:8000
RULE_ENGINE_URL=http://rule-engine:8002
REDIS_URL=redis://redis:6379/1
```

**rule-engine-service:**
```env
DATABASE_URL=mysql+aiomysql://user:pass@mysql:3306/energy_rule_db
REDIS_URL=redis://redis:6379/2
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=alerts@factory.com
SMTP_PASSWORD_ENCRYPTED=<encrypted>
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY_ENCRYPTED=<encrypted>
AWS_REGION=ap-south-1
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN_ENCRYPTED=<encrypted>
TELEGRAM_BOT_TOKEN_ENCRYPTED=<encrypted>
ENCRYPTION_KEY=<fernet-key>
```

**reporting-service:**
```env
DATABASE_URL=mysql+aiomysql://user:pass@mysql:3306/energy_reporting_db
INFLUX_URL=http://influxdb:8086
INFLUX_TOKEN=my-token
MINIO_URL=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=energy-reports
DEFAULT_TARIFF_RATE=8.5
```

### 12.2 Feature Flags

```python
# config.py
class Settings(BaseSettings):
    # Feature flags
    ENABLE_ML_ANALYTICS: bool = True
    ENABLE_WASTAGE_DASHBOARD: bool = True
    ENABLE_SCHEDULED_REPORTS: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    MAX_DEVICES_PER_IMPORT: int = 500
    MAX_REPORT_DATE_RANGE_DAYS: int = 90
```

---

## 13. Testing Strategy

### 13.1 Test Pyramid

| Layer           | Coverage Target | Tools                               |
|----------------|-----------------|-------------------------------------|
| Unit Tests      | 80%             | pytest, pytest-asyncio, unittest.mock |
| Integration     | 60%             | httpx AsyncClient, test DB          |
| E2E (API)       | Key flows       | pytest + real services (Docker)     |

### 13.2 Unit Test Examples

```python
# tests/unit/test_health_calculator.py

import pytest
from app.services.health_calculator import calculate_parameter_score, calculate_health_score

def test_score_within_normal_range():
    score = calculate_parameter_score(45, normal_min=20, normal_max=55, max_min=10, max_max=75)
    assert score == 100.0

def test_score_above_max_range():
    score = calculate_parameter_score(80, normal_min=20, normal_max=55, max_min=10, max_max=75)
    assert score == 0.0

def test_score_linear_interpolation():
    score = calculate_parameter_score(65, normal_min=20, normal_max=55, max_min=10, max_max=75)
    # 65 is midway between normal_max(55) and max_max(75) → expect ~75
    assert 70 <= score <= 80

def test_health_score_weighted():
    telemetry = {"temperature": 45, "vibration": 2.0}
    configs = [
        HealthConfigEntry("temperature", 20, 55, 10, 75, weight=60.0),
        HealthConfigEntry("vibration", 0, 5, 0, 10, weight=40.0),
    ]
    result = calculate_health_score(telemetry, configs)
    assert result["health_score"] == 100.0
    assert result["health_grade"] == "Excellent"
```

```python
# tests/unit/test_rule_evaluator.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.rule_evaluator import evaluate_rules

@pytest.mark.asyncio
async def test_rule_triggers_when_condition_met():
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = False  # No cooldown
    mock_dispatcher = AsyncMock()

    mock_db.execute.return_value = [
        {"rule_id": "r1", "rule_name": "High Temp", "property": "temperature",
         "condition": ">", "threshold": 70, "severity": "critical",
         "cooldown_minutes": 15, "notification_channels_json": {}}
    ]

    await evaluate_rules(
        device_id="COMP-001",
        telemetry={"temperature": 85},
        timestamp=...,
        db_session=mock_db,
        redis_client=mock_redis,
        notification_dispatcher=mock_dispatcher
    )

    mock_dispatcher.dispatch.assert_called_once()

@pytest.mark.asyncio
async def test_rule_suppressed_during_cooldown():
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = True  # In cooldown
    mock_dispatcher = AsyncMock()
    # ... setup
    mock_dispatcher.dispatch.assert_not_called()
```

### 13.3 Integration Test — Device CRUD

```python
# tests/integration/test_device_api.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_and_fetch_device():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create
        res = await client.post("/api/v1/devices",
            json={"device_id": "TEST-001", "device_name": "Test", "device_type": "compressor"},
            headers={"X-API-Key": "test-key"}
        )
        assert res.status_code == 201

        # Fetch
        res = await client.get("/api/v1/devices/TEST-001", headers={"X-API-Key": "test-key"})
        assert res.json()["data"]["device_id"] == "TEST-001"

@pytest.mark.asyncio
async def test_duplicate_device_returns_409():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/api/v1/devices",
            json={"device_id": "DUP-001", "device_name": "Dup", "device_type": "motor"},
            headers={"X-API-Key": "test-key"}
        )
        res = await client.post("/api/v1/devices",
            json={"device_id": "DUP-001", "device_name": "Dup", "device_type": "motor"},
            headers={"X-API-Key": "test-key"}
        )
        assert res.status_code == 409
        assert res.json()["error"]["code"] == "DEVICE_EXISTS"
```

---

## 14. Deployment Strategy

### 14.1 Docker Compose (Development / Staging)

```yaml
# docker-compose.yml
version: "3.9"

services:
  device-service:
    build: ./services/device-service
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=mysql+aiomysql://energyuser:pass@mysql:3306/energy_device_db
      - REDIS_URL=redis://redis:6379/0
    depends_on: [mysql, redis]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  data-service:
    build: ./services/data-service
    ports: ["8081:8081"]
    environment:
      - INFLUX_URL=http://influxdb:8086
      - MQTT_HOST=emqx
    depends_on: [influxdb, emqx, redis]

  rule-engine:
    build: ./services/rule-engine-service
    ports: ["8002:8002"]
    depends_on: [mysql, redis]

  analytics-service:
    build: ./services/analytics-service
    ports: ["8003:8003"]
    depends_on: [mysql, influxdb]

  reporting-service:
    build: ./services/reporting-service
    ports: ["8085:8085"]
    depends_on: [mysql, influxdb, minio]

  data-export-service:
    build: ./services/data-export-service
    ports: ["8080:8080"]
    depends_on: [influxdb, minio]

  ui-web:
    build: ./ui-web
    ports: ["3000:3000"]

  mysql:
    image: mysql:8.0
    ports: ["3306:3306"]
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_USER: energyuser
      MYSQL_PASSWORD: pass
    volumes:
      - mysql_data:/var/lib/mysql
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql

  influxdb:
    image: influxdb:2.7
    ports: ["8086:8086"]
    volumes:
      - influx_data:/var/lib/influxdb2

  emqx:
    image: emqx/emqx:5.3
    ports: ["1883:1883", "8083:8083", "18083:18083"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    volumes:
      - minio_data:/data

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  nginx:
    image: nginx:alpine
    ports: ["443:443", "80:80"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/certs:/etc/nginx/certs

volumes:
  mysql_data:
  influx_data:
  minio_data:
```

### 14.2 Kubernetes — Production (AWS EKS)

```yaml
# kubernetes/device-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: device-service
  namespace: energy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: device-service
  template:
    metadata:
      labels:
        app: device-service
    spec:
      containers:
      - name: device-service
        image: energy-enterprise/device-service:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: device-service-secrets
        resources:
          requests: { memory: "256Mi", cpu: "250m" }
          limits:   { memory: "512Mi", cpu: "500m" }
        livenessProbe:
          httpGet: { path: /health, port: 8000 }
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet: { path: /health/ready, port: 8000 }
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: device-service
  namespace: energy
spec:
  selector:
    app: device-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: device-service-hpa
  namespace: energy
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: device-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 14.3 Database Migrations

All schema changes managed via **Alembic**:
```bash
# Create migration
alembic revision --autogenerate -m "add_device_groups_table"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 14.4 CI/CD Pipeline

```
GitHub Push → GitHub Actions
  ├── lint (ruff, eslint)
  ├── unit tests (pytest)
  ├── build Docker images
  ├── push to ECR
  └── deploy to EKS (Helm)
```

---

## 15. Monitoring & Observability

### 15.1 Key Metrics

| Metric                         | Type      | Service          |
|-------------------------------|-----------|------------------|
| `http_requests_total`          | Counter   | All services     |
| `http_request_duration_seconds`| Histogram | All services     |
| `mqtt_messages_received_total` | Counter   | data-service     |
| `influxdb_write_latency_seconds`| Histogram| data-service     |
| `rule_evaluations_total`       | Counter   | rule-engine      |
| `alerts_generated_total`       | Counter   | rule-engine      |
| `notifications_sent_total`     | Counter   | rule-engine      |
| `notification_failures_total`  | Counter   | rule-engine      |
| `report_generation_duration`   | Histogram | reporting        |
| `active_websocket_connections` | Gauge     | data-service     |
| `ml_job_duration_seconds`      | Histogram | analytics        |

### 15.2 Log Format (Structured JSON)

```json
{
  "timestamp": "2026-02-27T10:00:00.000Z",
  "level": "INFO",
  "service": "rule-engine-service",
  "trace_id": "abc123def456",
  "span_id": "def456",
  "device_id": "COMPRESSOR-001",
  "rule_id": "rule-uuid",
  "event": "alert_created",
  "alert_id": "alert-uuid",
  "severity": "critical"
}
```

### 15.3 Health Check Endpoints

```python
@app.get("/health")
async def liveness():
    return {"status": "ok", "service": settings.SERVICE_NAME}

@app.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    checks = {}
    # Check MySQL
    try:
        await db.execute(text("SELECT 1"))
        checks["mysql"] = "up"
    except Exception:
        checks["mysql"] = "down"
    # Check Redis
    try:
        await redis.ping()
        checks["redis"] = "up"
    except Exception:
        checks["redis"] = "down"

    all_ok = all(v == "up" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ok" if all_ok else "degraded", "checks": checks}
    )
```

### 15.4 Alerting Rules (Prometheus/Grafana)

| Alert               | Condition                     | Severity | Action              |
|--------------------|-------------------------------|----------|---------------------|
| High Error Rate     | error_rate_5m > 5%            | Critical | Page on-call        |
| High P95 Latency    | p95_latency_1m > 2s           | Warning  | Slack #ops          |
| Service Down        | health_check fails × 3        | Critical | Page on-call        |
| MQTT Lag            | mqtt_queue_depth > 10000      | Warning  | Slack #ops          |
| InfluxDB Write Fail | influx_write_errors > 100/min | Critical | Page on-call        |
| Disk Usage          | disk_usage > 85%              | Warning  | Slack #ops          |
| Notification Failures| notification_fail_rate > 20% | Warning  | Slack #alerts       |

---

## 16. Appendix

### 16.1 Database — Connection Pool Configuration

| Service             | Pool Size | Max Overflow | Timeout |
|--------------------|-----------|-------------|---------|
| device-service     | 20        | 10          | 30s     |
| rule-engine        | 20        | 10          | 30s     |
| reporting-service  | 30        | 20          | 60s     |
| analytics-service  | 20        | 10          | 60s     |
| data-export-service| 10        | 5           | 30s     |

### 16.2 Redis Key Conventions

| Key Pattern                        | TTL       | Purpose                       |
|-----------------------------------|-----------|-------------------------------|
| `device:{device_id}:meta`          | 5 min     | Cached device metadata        |
| `device:{device_id}:health_config` | 1 min     | Cached health configs         |
| `rules:active_list`                | 1 min     | Cached active rules           |
| `cooldown:{rule_id}:{device_id}`   | Configurable | Rule alert cooldown        |
| `device:{device_id}:properties`    | 10 min    | Device property definitions   |
| `ws:subscribers:{device_id}`       | Session   | WebSocket connection registry |

### 16.3 MQTT Topic Convention

| Topic Pattern                     | Publisher   | Subscriber     |
|----------------------------------|-------------|----------------|
| `telemetry/{device_id}`           | IoT device  | data-service   |
| `telemetry/{device_id}/ack`       | data-service| IoT device     |

### 16.4 File Naming Conventions

| Type         | Convention                          | Example                         |
|-------------|-------------------------------------|---------------------------------|
| Device ID   | `{TYPE}-{NUMBER}` uppercase         | `COMPRESSOR-001`                |
| Report S3   | `reports/{tenant}/{report_id}.pdf`  | `reports/t1/abc123.pdf`         |
| Export S3   | `exports/{device_id}/{export_id}.csv`| `exports/COMP-001/42.csv`      |
| Audit logs  | Action uppercase                    | `CREATE`, `UPDATE`, `DELETE`    |

### 16.5 Supported Device Types

```python
DEVICE_TYPES = [
    "compressor", "motor", "pump", "hvac", "fan", "conveyor",
    "chiller", "boiler", "generator", "transformer", "other"
]
```

### 16.6 Health Grade Thresholds

| Score Range | Grade     | Color  |
|------------|-----------|--------|
| 90–100     | Excellent | Green  |
| 70–89      | Good      | Blue   |
| 50–69      | Fair      | Yellow |
| 0–49       | Poor      | Red    |

### 16.7 Supported ML Analysis Types

| analysis_type        | Algorithm              | Min Data Required |
|---------------------|------------------------|-------------------|
| `anomaly_detection`  | Isolation Forest       | 7 days            |
| `failure_prediction` | Rolling Feature + RF   | 30 days           |

---

**Document Version:** 2.0 (Enhanced)
**Prepared by:** Engineering Team
**Date:** February 2026
**Status:** Ready for Implementation
