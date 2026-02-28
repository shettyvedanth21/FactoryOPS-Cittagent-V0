# Energy Enterprise Platform - High-Level Design (HLD)

> **Document Version:** 1.0  
> **Date:** February 2026  
> **Project Name:** Energy Enterprise (FactoryOPS)  
> **Classification:** Production Design Document

---

## 1. Executive Summary

### 1.1 Purpose

This document provides the High-Level Design (HLD) for the **Energy Enterprise Platform** - an Industrial IoT (IIoT) intelligence system designed for real-time monitoring, analytics, and management of industrial equipment at scale.

### 1.2 Scope

The platform enables:
- Real-time telemetry ingestion from 1000+ industrial devices
- Health scoring and uptime calculation for each machine
- Rule-based alerting with multi-channel notifications
- ML-powered anomaly detection and failure prediction
- Energy consumption and comparative reporting
- Data export and archival capabilities

### 1.3 Assumptions

- No user authentication required (open access system)
- 1000+ devices generating telemetry at 1-second intervals
- Data retention: 90 days for telemetry, indefinite for configurations
- Deployment on AWS cloud infrastructure

---

## 2. System Architecture

### 2.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        CLIENT LAYER                                        │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌───────────────────┐  │
│  │     Web Application         │  │   Mobile/Tablet Client     │  │   Admin Portal    │  │
│  │     (Next.js :3000)         │  │   (Responsive Web)         │  │   (Future)        │  │
│  └─────────────────────────────┘  └─────────────────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           │ HTTPS / WSS
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        API GATEWAY LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                           NGINX Reverse Proxy & Load Balancer                       │    │
│  │                    (Port 443 → Routes to Backend Services)                         │    │
│  └─────────────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
        ┌──────────────────────────────────┼──────────────────────────────────┐
        │                                  │                                  │
        ▼                                  ▼                                  ▼
┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│  Device Service   │          │   Data Service    │          │ Rule Engine Svc   │
│     (:8000)       │          │     (:8081)        │          │     (:8002)       │
│                   │          │                   │          │                   │
│ • Device CRUD     │          │ • MQTT Ingestion  │          │ • Rule Evaluation │
│ • Health Config   │          │ • InfluxDB Store │          │ • Alert Generation│
│ • Shift Mgmt      │          │ • WebSocket      │          │ • Notifications   │
└───────────────────┘          └───────────────────┘          └───────────────────┘
        │                                  │                                  │
        │                                  │                                  │
        ▼                                  ▼                                  ▼
┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│ Analytics Service │          │ Reporting Service │          │ Data Export Svc   │
│     (:8003)       │          │     (:8085)       │          │     (:8080)       │
│                   │          │                   │          │                   │
│ • ML Jobs         │          │ • Report Gen      │          │ • S3 Export       │
│ • Anomaly Det.    │          │ • Schedulers      │          │ • Checkpointing   │
│ • Failure Pred.   │          │ • PDF/CSV         │          │                   │
└───────────────────┘          └───────────────────┘          └───────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA LAYER                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │    MySQL     │  │  InfluxDB    │  │    MinIO     │  │     MQTT     │  │   Redis  │ │
│  │   (Primary)  │  │ (Time-Series)│  │   (S3 API)   │  │   (Broker)   │  │ (Cache)  │ │
│  │    :3306     │  │    :8086     │  │  :9000/:9001 │  │   :1883      │  │  :6379   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | Next.js | 16 | React framework with App Router |
| | React | 19 | UI library |
| | TypeScript | 5.x | Type safety |
| | Tailwind CSS | 3.x | Styling |
| | Recharts | 2.x | Data visualization |
| **Backend** | Python | 3.11+ | Runtime |
| | FastAPI | 0.115+ | Web framework |
| | SQLAlchemy | 2.x | ORM (async) |
| | aiomysql | 0.2+ | Async MySQL driver |
| | paho-mqtt | 1.6+ | MQTT client |
| | influxdb-client | 1.40+ | InfluxDB v2 |
| | httpx | 0.27+ | Async HTTP client |
| | boto3 | 1.35+ | AWS SDK |
| | scikit-learn | 1.5+ | ML library |
| **Infrastructure** | Docker | 25+ | Container runtime |
| | Docker Compose | 2.25+ | Orchestration |
| | AWS EKS | 1.30+ | Kubernetes (Future) |
| | AWS RDS | 8.0 | MySQL database |
| | AWS InfluxDB | Cloud | Time-series DB |
| | AWS S3 | - | Object storage |
| | EMQX | 5.3 | MQTT broker |
| | Amazon SNS | - | Notifications |

---

## 3. Component Design

### 3.1 Microservices Architecture

The system follows a **microservices architecture** with 6 independent services:

#### 3.1.1 Device Service (:8000)

**Responsibility:** Device registry, configuration, and health management

**Features:**
- Device CRUD operations
- Shift configuration management
- Parameter health configuration
- Health score calculation
- Uptime calculation

**API Endpoints:**
```
Devices:
  POST   /api/v1/devices                    - Create device
  GET    /api/v1/devices                    - List devices
  GET    /api/v1/devices/{id}               - Get device
  PUT    /api/v1/devices/{id}               - Update device
  DELETE /api/v1/devices/{id}               - Delete device

Shifts:
  POST   /api/v1/devices/{id}/shifts        - Create shift
  GET    /api/v1/devices/{id}/shifts        - List shifts
  PUT    /api/v1/devices/{id}/shifts/{sid}  - Update shift
  DELETE /api/v1/devices/{id}/shifts/{sid}  - Delete shift
  GET    /api/v1/devices/{id}/uptime        - Get uptime

Health Config:
  POST   /api/v1/devices/{id}/health-config           - Create config
  GET    /api/v1/devices/{id}/health-config          - List configs
  POST   /api/v1/devices/{id}/health-config/bulk      - Bulk create
  GET    /api/v1/devices/{id}/health-config/validate - Validate weights
  POST   /api/v1/devices/{id}/health-score            - Calculate score
```

**Database:** `energy_device_db`

---

#### 3.1.2 Data Service (:8081)

**Responsibility:** Telemetry ingestion, storage, and real-time distribution

**Features:**
- MQTT subscription for telemetry
- Real-time data enrichment
- InfluxDB storage
- WebSocket broadcasting
- Rule evaluation triggers
- Dead Letter Queue for failures

**API Endpoints:**
```
Telemetry:
  GET  /api/telemetry/{device_id}           - Query telemetry
  GET  /api/properties                      - Get device properties

WebSocket:
  WS   /ws/telemetry/{device_id}            - Live telemetry stream
```

**Database:** MySQL (metadata cache), InfluxDB (telemetry)

**Data Flow:**
```
MQTT Broker → Data Service → [Enrich → Store → Evaluate Rules → Broadcast]
                              │
                              ▼
                       ┌──────────────┐
                       │   InfluxDB   │
                       └──────────────┘
```

---

#### 3.1.3 Rule Engine Service (:8002)

**Responsibility:** Rule evaluation, alert generation, and notifications

**Features:**
- Threshold-based rule evaluation
- Multiple condition support (>, <, =, !=, >=, <=)
- Cooldown management
- Alert lifecycle (open → acknowledged → resolved)
- Multi-channel notifications (Email, SMS, Webhook)

**API Endpoints:**
```
Rules:
  POST   /api/v1/rules                 - Create rule
  GET    /api/v1/rules                - List rules
  GET    /api/v1/rules/{id}           - Get rule
  PUT    /api/v1/rules/{id}           - Update rule
  DELETE /api/v1/rules/{id}           - Delete rule
  POST   /api/v1/rules/evaluate      - Evaluate telemetry

Alerts:
  GET    /api/v1/alerts               - List alerts
  PUT    /api/v1/alerts/{id}/ack      - Acknowledge
  PUT    /api/v1/alerts/{id}/resolve  - Resolve
```

**Database:** `energy_rule_db`

---

#### 3.1.4 Analytics Service (:8003)

**Responsibility:** ML-based analytics and predictions with user-friendly results

**Features:**
- Anomaly detection with context-aware explanations
- Failure prediction with actionable recommendations
- Job queue for async processing
- Model management (Isolation Forest, Autoencoder, Random Forest, Gradient Boosting)
- Results storage with human-readable insights

**Design Principles:**
1. **Context Over Raw Data**: Always provide context - value vs normal range
2. **Reasoning Over Results**: Explain WHY the system detected something
3. **Actionability**: Every insight has a related action button
4. **Plain Language**: Non-technical presentation

**API Endpoints:**
```
Analytics:
  GET    /api/v1/analytics/models             - List ML models
  GET    /api/v1/analytics/datasets/{id}    - Available datasets
  POST   /api/v1/analytics/run               - Run analysis
  GET    /api/v1/analytics/jobs              - List jobs
  GET    /api/v1/analytics/results/{id}      - Get results
  
Analysis Types:
  - anomaly_detection: Find unusual patterns
  - failure_prediction: Predict equipment failures
  - forecasting: Predict future values
```

**Response Format (Enhanced):**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "results": {
    "summary": {
      "total_anomalies": 3,
      "severity_breakdown": {"critical": 1, "warning": 2}
    },
    "anomalies": [
      {
        "timestamp": "2026-02-20T14:30:00Z",
        "severity": "critical",
        "parameter": "temperature",
        "value": 85,
        "normal_range": {"min": 20, "max": 60},
        "context": "42% above upper normal limit",
        "possible_causes": ["Coolant low", "Sensor issue"],
        "recommendation": "Check coolant levels"
      }
    ],
    "confidence": {"score": 85, "level": "high"}
  }
}
```

**Database:** `energy_analytics_db`

---

#### 3.1.5 Reporting Service (:8085)

**Responsibility:** Report generation, scheduling, and **Energy Wastage Analysis**

**Features:**
- Energy consumption reports
- Comparative analysis
- **Energy Wastage Dashboard** (NEW - Critical Feature)
- Report scheduling
- PDF/CSV generation
- MinIO storage for reports

**New Engines:**
```
services/reporting-service/src/services/
├── energy_engine.py         (existing)
├── wastage_engine.py        (NEW)
├── demand_engine.py         (existing)
├── load_factor_engine.py   (existing)
├── cost_engine.py          (existing)
└── comparison_engine.py    (existing)
```

**Wastage Engine Functions:**
```python
def calculate_wastage(
    power_series: List[dict],
    total_kwh: float,
    runtime_hours: float,
    tariff_rate: float,
    device_metadata: dict,
    pressure_series: Optional[List[dict]] = None
) -> dict:
    """
    Calculate energy wastage using 25th percentile baseline.
    
    Formula:
    - optimal_avg_kw = percentile(power_series, 25)
    - optimal_kwh = optimal_avg_kw * runtime_hours
    - wasted_kwh = actual_kwh - optimal_kwh
    - efficiency = optimal_kwh / actual_kwh
    """
```

**API Endpoints:**
```
Reports:
  POST   /api/v1/reports/consumption    - Generate energy report
  POST   /api/v1/reports/comparison     - Generate comparison
  GET    /api/v1/reports/wastage       - Get wastage analysis (NEW)
  GET    /api/v1/reports/{id}          - Get report status
  GET    /api/v1/reports/{id}/download - Download report
  GET    /api/v1/reports/history       - Report history

Wastage:
  GET    /api/v1/wastage/{device_id}  - Device wastage
  GET    /api/v1/wastage/             - All devices wastage
```

**Database:** `energy_reporting_db`

---

#### 3.1.6 Data Export Service (:8080)

**Responsibility:** Bulk data export to S3

**Features:**
- Checkpoint-based exports
- CSV/JSON formats
- Scheduled exports
- UI integration for on-demand exports

**API Endpoints:**
```
Export:
  POST   /api/v1/export              - Start export job
  GET    /api/v1/export/{id}          - Get export status
  GET    /api/v1/export/{id}/download - Download export
  GET    /api/v1/export/history       - Export history
```

**Database:** `energy_export_db`

---

### 3.2 Database Design

#### 3.2.1 MySQL Databases

| Database | Service | Tables |
|----------|---------|--------|
| `energy_device_db` | device-service | devices, device_properties, device_shifts, parameter_health_config |
| `energy_rule_db` | rule-engine-service | rules, alerts |
| `energy_analytics_db` | analytics-service | analytics_jobs |
| `energy_export_db` | data-export-service | export_checkpoints |
| `energy_reporting_db` | reporting-service | reports, scheduled_reports, tenant_tariffs |

#### 3.2.2 InfluxDB

**Bucket:** `telemetry`

**Retention:** 90 days

**Schema:**
```
Measurement: telemetry
├── Tags
│   ├── device_id (string)
│   ├── schema_version (string)
│   └── enrichment_status (string)
└── Fields
    └── [Dynamic: any numeric field]
```

---

## 4. Feature Specifications

### 4.1 Device Management

#### 4.1.1 Device Registry
- Unique device identification
- Device metadata (name, type, manufacturer, model, location)
- Status tracking (active, inactive, maintenance, error)
- Last seen timestamp for runtime status

#### 4.1.2 Shift Configuration
- Multiple shifts per device
- Fields: name, start time, end time, maintenance break, day of week
- Used for uptime calculation

#### 4.1.3 Parameter Health Configuration
- Per-parameter health settings
- Normal range (score: 70-100%)
- Max range (score: 25-69%)
- Weight assignment (must sum to 100%)

### 4.2 Telemetry Processing

#### 4.2.1 Ingestion
- Protocol: MQTT (EMQX broker)
- Topic pattern: `telemetry/{device_id}`
- Format: JSON with dynamic fields

#### 4.2.2 Enrichment
- Add device metadata (type, location)
- Add schema version
- Add enrichment status

#### 4.2.3 Storage
- Primary: InfluxDB (time-series)
- Fallback: Dead Letter Queue (for failed writes)

#### 4.2.4 Real-time Distribution
- WebSocket for live dashboard
- 1-second refresh rate

### 4.3 Health Scoring

#### 4.3.1 Health Score Calculation
```
Prerequisites:
  - Machine state must be RUNNING
  - All weights must sum to 100%

Scoring:
  Normal Range (normal_min → normal_max):
    score = 100 - (|value - ideal_center| / half_range) × 30
    score clamped to [70, 100]
  
  Max Range (max_min → max_max):
    score = 70 - (overshoot / tolerance) × 45
    score clamped to [25, 69]
  
  Beyond Max:
    score = 25 - overshoot × 10
    score clamped to [0, 25]
  
  Final = Σ(raw_score × weight / 100)
```

#### 4.3.2 Uptime Calculation
```
For each active shift:
  effective_minutes = (shift_end - shift_start) - maintenance_break
  
Uptime % = (Σ effective_minutes / Σ shift_duration) × 100
```

#### 4.3.3 Machine States
| State | Health Calculated | Description |
|-------|------------------|-------------|
| RUNNING | Yes | Actively producing |
| IDLE | No | Running but no load |
| OFF | No | Powered off |
| UNLOAD | No | Unloaded state |
| POWER CUT | No | No power |

### 4.4 Rule-Based Alerting

#### 4.4.1 Rule Structure
```
- name: Rule identifier
- scope: all_devices | selected_devices
- property: Metric to monitor
- condition: >, <, =, !=, >=, <=
- threshold: Value to compare against
- notification_channels: [email, sms, webhook]
- cooldown_minutes: Minimum time between alerts
- device_ids: Target devices (if selected)
```

#### 4.4.2 Alert Lifecycle
```
CREATED → OPEN → ACKNOWLEDGED → RESOLVED
```

#### 4.4.3 Notification Channels
| Channel | Implementation |
|---------|---------------|
| Email | SMTP via Amazon SES |
| SMS | Amazon SNS |
| Webhook | HTTP POST to configured URL |

### 4.5 Analytics (ML)

#### 4.5.1 Anomaly Detection
- Detect unusual patterns in telemetry
- Uses Isolation Forest algorithm
- Configurable sensitivity threshold

#### 4.5.2 Failure Prediction
- Predict potential equipment failures
- Uses Random Forest classifier
- Feature engineering from historical data

### 4.6 Reporting

#### 4.6.1 Energy Consumption Report
- Date range: 1-90 days
- Group by: Daily, Weekly
- Metrics: kWh, peak power, load factor, cost
- AI-generated insights
- Export: PDF, CSV

#### 4.6.2 Comparative Analysis
- Machine vs Machine comparison
- Period vs Period comparison
- Side-by-side metrics
- Performance insights

---

## 5. API Design

### 5.1 Design Principles

- RESTful API design
- JSON request/response format
- Consistent naming conventions
- Versioned APIs (`/api/v1/`)
- OpenAPI/Swagger documentation

### 5.2 Common Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-02-26T10:00:00Z"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  },
  "timestamp": "2026-02-26T10:00:00Z"
}
```

### 5.3 Rate Limits

| Endpoint | Limit |
|----------|-------|
| GET requests | 1000/minute |
| POST requests | 100/minute |
| WebSocket connections | 100/device |

---

## 6. Security Design

### 6.1 Current State
- Open access (no authentication)
- Internal network only
- TLS/SSL for external connections

### 6.2 Future Enhancements (Optional)
- JWT-based authentication
- Role-based access control (RBAC)
- API key management
- Rate limiting per tenant

---

## 7. Scalability Design

### 7.1 Horizontal Scaling

| Service | Scaling Strategy |
|---------|-----------------|
| Device Service | Stateless - auto-scale |
| Data Service | Stateless - auto-scale |
| Rule Engine | Stateless - auto-scale |
| Analytics | Stateful - queue-based |
| Reporting | Stateful - queue-based |
| Data Export | Stateless - on-demand |

### 7.2 Data Partitioning

| Data Type | Strategy |
|-----------|----------|
| Telemetry | By device_id + time |
| Devices | Single table (1000s records) |
| Rules | Single table (100s records) |
| Alerts | Partition by date |

### 7.3 Caching Strategy

| Data | Cache | TTL |
|------|-------|-----|
| Device metadata | Redis | 5 minutes |
| Health configs | Redis | 1 minute |
| Rules list | Redis | 1 minute |

---

## 8. Deployment Architecture (AWS)

### 8.1 Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        VPC (10.0.0.0/16)                             │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │   Public    │  │   Private   │  │   Private  │                  │   │
│  │  │   Subnet    │  │   Subnet    │  │   Subnet   │                  │   │
│  │  │   (AZ-a)    │  │   (AZ-a)    │  │   (AZ-b)   │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐   │   │
│  │  │              EKS Cluster (Kubernetes)                         │   │   │
│  │  │                                                                │   │   │
│  │  │   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │   │   │
│  │  │   │Device  │ │ Data   │ │ Rule   │ │Analytics│ │Reporting│    │   │   │
│  │  │   │Service │ │Service │ │Engine  │ │Service │ │Service │     │   │   │
│  │  │   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘     │   │   │
│  │  │                                                                │   │   │
│  │  │   ┌────────┐ ┌────────┐                                     │   │   │
│  │  │   │  NGINX │ │ React  │                                     │   │   │
│  │  │   │Ingress │ │  App   │                                     │   │   │
│  │  │   └────────┘ └────────┘                                     │   │   │
│  │  └────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │
│  │     RDS      │  │  InfluxDB    │  │      S3      │  │     SNS    │   │
│  │   (MySQL)   │  │   (Cloud)    │  │   (Bucket)   │  │  (Alerts)  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐                                       │
│  │  ElastiCache │  │     MQ       │  (MQTT Broker - EMQX)               │
│  │   (Redis)   │  │  (Optional)  │                                       │
│  └──────────────┘  └──────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 AWS Services Used

| Service | Purpose | Configuration |
|---------|---------|---------------|
| EKS | Container orchestration | 3 nodes, t3.xlarge |
| RDS MySQL | Primary database | db.r6g.xlarge, Multi-AZ |
| InfluxDB Cloud | Time-series DB | Pay-per-query |
| S3 | Object storage | Standard, lifecycle policy |
| SNS | Notifications | SMS, Email |
| ElastiCache | Redis cache | cache.r6g.large |
| ALB | Load balancer | Application type |
| Route 53 | DNS | Private hosted zone |
| ACM | SSL certificates | Auto-renew |
| CloudWatch | Logging | Log retention 30 days |

---

## 9. Monitoring & Observability

### 9.1 Metrics

| Metric | Source | Alert |
|--------|--------|-------|
| Service health | Kubernetes | Pod down |
| API latency | NGINX | > 500ms |
| Error rate | Application | > 1% |
| CPU usage | CloudWatch | > 80% |
| Memory usage | CloudWatch | > 85% |
| Disk usage | CloudWatch | > 90% |
| MQTT messages | EMQX | Queue depth > 1000 |

### 9.2 Logging

- Application logs: CloudWatch Logs
- Access logs: S3 bucket
- Audit logs: Separate log group

### 9.3 Alerting

| Channel | Trigger |
|---------|---------|
| Email (SNS) | Critical errors |
| Slack (Webhook) | Deployment events |

---

## 10. Data Flow Diagrams

### 10.1 Telemetry Flow

```
Device/Sensor
     │
     │ MQTT (telemetry/DEVICE_001)
     ▼
┌─────────────┐
│   EMQX      │  (MQTT Broker :1883)
│  Broker     │
└──────┬──────┘
       │
       │ MQTT Subscribe
       ▼
┌─────────────┐
│ Data Service│  (:8081)
│  Ingestion  │
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Enrichment │    │  InfluxDB   │    │ Rule Engine │
│ (Metadata)  │    │  (Storage)  │    │ (:8002)     │
└──────┬──────┘    └─────────────┘    └──────┬──────┘
       │                                       │
       │                                       ▼
       │                              ┌─────────────┐
       │                              │   Alerts    │
       │                              │ +Notifs     │
       │                              └─────────────┘
       │
       ▼
┌─────────────┐
│  WebSocket  │ ───► UI Dashboard
│  Broadcast  │
└─────────────┘
```

### 10.2 Report Generation Flow

```
User Request
     │
     ▼
┌─────────────┐
│  Reporting  │
│  Service    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│         Async Job Queue               │
└──────┬───────────────────────┬────────┘
       │                       │
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│   InfluxDB  │         │    MinIO    │
│  (Query)    │         │   (Store)   │
└──────┬──────┘         └─────────────┘
       │
       ▼
┌─────────────┐
│   Report    │
│  Generator  │
│ (PDF/CSV)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Download  │ ◄── User
│    Link     │
└─────────────┘
```

---

## 11. Non-Functional Requirements

### 11.1 Performance

| Metric | Target |
|--------|--------|
| API Response Time | < 200ms (p95) |
| Telemetry Ingestion | 10,000 msg/sec |
| WebSocket Latency | < 100ms |
| Report Generation | < 60 seconds |
| ML Analysis | < 5 minutes |

### 11.2 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| Recovery Time | < 15 minutes |
| Data Loss | Zero (DLQ protection) |

### 11.3 Security

| Requirement | Implementation |
|-------------|----------------|
| Encryption at rest | AWS KMS |
| Encryption in transit | TLS 1.3 |
| Network isolation | VPC, Security Groups |
| Access control | IAM roles |

---

## 11. Code Quality Standards

### 11.1 Error Handling

| Requirement | Implementation |
|-------------|----------------|
| Global Exception Handler | All services shall have global exception handlers |
| Structured Errors | Return consistent error format with codes |
| Graceful Degradation | System shall not crash on non-critical errors |
| Logging | All errors shall be logged with context |

**Error Response Format:**
```json
{
  "success": false,
  "error": {
    "code": "ERR_CODE",
    "message": "Human-readable message",
    "details": {}
  },
  "timestamp": "2026-02-26T10:00:00Z"
}
```

### 11.2 Logging Standards

| Requirement | Implementation |
|-------------|----------------|
| Structured Logging | Use JSON format with context |
| Log Levels | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Correlation IDs | Track requests across services |
| Sensitive Data | Never log passwords, tokens, secrets |

**Log Format:**
```json
{
  "timestamp": "2026-02-26T10:00:00Z",
  "level": "INFO",
  "service": "device-service",
  "message": "Device created",
  "device_id": "MACHINE-001",
  "user": "system"
}
```

### 11.3 Testing Requirements

| Type | Coverage Target | Description |
|------|-----------------|-------------|
| Unit Tests | 80% | All business logic functions |
| Integration Tests | 60% | API endpoints, database operations |
| E2E Tests | Critical paths | User journeys |

**Test Framework:**
- Backend: pytest
- Frontend: Jest + React Testing Library
- E2E: Playwright

### 11.4 API Design Standards

| Requirement | Standard |
|-------------|----------|
| Versioning | `/api/v1/` prefix |
| Naming | kebab-case for endpoints |
| HTTP Methods | GET (read), POST (create), PUT (update), DELETE (remove) |
| Status Codes | 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Server Error |
| Rate Limiting | 1000 req/min GET, 100 req/min POST |

### 11.5 Code Review Standards

| Check | Description |
|-------|-------------|
| Linting | All code passes linting (ruff, eslint) |
| Type Checking | TypeScript strict mode, Python type hints |
| Security | No hardcoded secrets, validate inputs |
| Documentation | Public APIs documented |

---

## 12. Development Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] AWS infrastructure setup
- [ ] CI/CD pipeline configuration
- [ ] Core microservices deployment

### Phase 2: Core Features (Week 3-4)
- [ ] Device management
- [ ] Telemetry ingestion
- [ ] Basic dashboards

### Phase 3: Intelligence (Week 5-6)
- [ ] Health scoring
- [ ] Rule engine
- [ ] Notifications

### Phase 4: Analytics & Reports (Week 7-8)
- [ ] ML analytics
- [ ] Report generation
- [ ] Data export

### Phase 5: Testing & Optimization (Week 9-10)
- [ ] Load testing
- [ ] Security audit
- [ ] Performance tuning
- [ ] Documentation

---

## 13. Appendix

### 13.1 Port Mapping

| Service | Internal | External |
|---------|----------|----------|
| UI Web | 3000 | 443 (ALB) |
| Device Service | 8000 | 443 |
| Data Service | 8081 | 443 |
| Rule Engine | 8002 | 443 |
| Analytics | 8003 | 443 |
| Reporting | 8085 | 443 |
| Data Export | 8080 | 443 |
| EMQX | 1883 | 1883 |
| InfluxDB | 8086 | Internal |

### 13.2 Environment Variables

```
# Database
MYSQL_HOST=energy-db.xxxx.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=***

# InfluxDB
INFLUX_URL=https://xxx.influxcloud.io
INFLUX_TOKEN=***

# MQTT
MQTT_BROKER=emqx.xxx.amazonaws.com
MQTT_PORT=1883

# AWS
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=***
AWS_SECRET_ACCESS_KEY=***
S3_BUCKET=energy-enterprise-reports

# Notifications
SNS_ARN=arn:aws:sns:xxx
SMTP_HOST=email-smtp.xxx.amazonaws.com
SMTP_USER=***
SMTP_PASSWORD=***
```

### 13.3 API Documentation URLs

| Service | Swagger URL |
|---------|-------------|
| Device Service | https://api.energy.com/device/v1/docs |
| Data Service | https://api.energy.com/data/v1/docs |
| Rule Engine | https://api.energy.com/rule/v1/docs |
| Analytics | https://api.energy.com/analytics/v1/docs |
| Reporting | https://api.energy.com/reports/v1/docs |

---

**End of Document**

