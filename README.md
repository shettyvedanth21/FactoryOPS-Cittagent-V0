# FactoryOPS Energy Enterprise Platform

> Industrial IoT Intelligence Platform for real-time monitoring, health analytics, and predictive insights.

## Overview

FactoryOPS is an Industrial IoT (IIoT) Intelligence Platform designed to provide real-time monitoring, health analytics, and predictive insights for industrial equipment. The platform enables plant managers and maintenance teams to monitor machine health and performance in real-time, receive instant alerts when equipment parameters exceed thresholds, analyze energy consumption patterns, predict potential equipment failures before they occur, and generate compliance and performance reports.

## Architecture

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| device-service | 8000 | energy_device_db | Device registry, health scoring, shifts, uptime |
| data-service | 8081 | InfluxDB + MySQL | MQTT ingestion, telemetry storage, WebSocket |
| rule-engine-service | 8002 | energy_rule_db | Rule evaluation, alerting, notifications |
| analytics-service | 8003 | energy_analytics_db | ML anomaly detection, failure prediction |
| reporting-service | 8085 | energy_reporting_db | Energy reports, wastage, PDF generation |
| data-export-service | 8080 | energy_export_db | Data export to MinIO/S3 |

## Infrastructure

| Component | Port | Purpose |
|-----------|------|---------|
| MySQL | 3306 | Primary database (5 databases) |
| InfluxDB | 8086 | Time-series telemetry storage |
| Redis | 6379 | Caching, cooldown management |
| EMQX | 1883/8083/18083 | MQTT broker, WebSocket, dashboard |
| MinIO | 9000/9001 | S3-compatible object storage |
| Nginx | 80/443 | Reverse proxy, load balancer |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for ui-web)

### Start Infrastructure

```bash
cd infrastructure/docker
docker-compose up -d mysql influxdb redis emqx minio
sleep 30
```

### Start All Services

```bash
docker-compose up -d
```

### Verify Health

```bash
curl http://localhost:8000/health   # device-service
curl http://localhost:8081/health    # data-service
curl http://localhost:8002/health    # rule-engine-service
curl http://localhost:8003/health   # analytics-service
curl http://localhost:8085/health    # reporting-service
curl http://localhost:8080/health    # data-export-service
curl http://localhost:3000/health    # ui-web
```

## API Reference

| Service | Base URL | Key Endpoints |
|---------|----------|----------------|
| device-service | http://localhost:8000/api/v1 | /devices, /shifts, /health-config, /health-score, /uptime |
| data-service | http://localhost:8081/api | /telemetry/{id}, /properties, /ws/telemetry/{id} |
| rule-engine-service | http://localhost:8002/api/v1 | /rules, /alerts, /evaluate |
| analytics-service | http://localhost:8003/api/v1 | /analytics/run, /jobs, /results, /datasets |
| reporting-service | http://localhost:8085/api/v1 | /reports/consumption, /reports/comparison, /wastage |
| data-export-service | http://localhost:8080/api/v1 | /export, /history, /download |

## Running Tests

```bash
cd factoryops
pip install -r tests/e2e/requirements.txt
pytest tests/e2e/ -v
```

## Project Structure

```
factoryops/
├── docs/                    # Documentation (PRD, HLD, LLD, audit report)
├── infrastructure/          # Docker, MySQL init, Nginx config
├── services/                # 6 microservices
│   ├── device-service/
│   ├── data-service/
│   ├── rule-engine-service/
│   ├── analytics-service/
│   ├── reporting-service/
│   └── data-export-service/
├── shared/                  # Common utilities (response, exceptions)
├── tests/                   # E2E tests
├── ui-web/                  # Next.js frontend
└── progress.md              # Implementation tracker
```

## Known Limitations

- **No authentication** - Open access system (v1.0 by design per HLD)
- **In-memory DLQ** - Dead Letter Queue not persistent across restarts
- **Single-instance Redis** - Cooldown manager uses Redis TTL

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, aiomysql |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| ML | scikit-learn (Isolation Forest, Random Forest) |
| Database | MySQL 8.0, InfluxDB 2.7 |
| Cache | Redis 7 |
| Message Queue | EMQX 5.3 (MQTT) |
| Storage | MinIO (S3-compatible) |
| Container | Docker, Docker Compose |
| PDF | ReportLab |

---

**Version:** 1.0.0  
**Status:** Production Ready  
**E2E Tests:** 26/26 Passing
