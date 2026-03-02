# FactoryOPS — PROJECT INTELLIGENCE
> Complete technical context for AI models and engineers. Drop this file at the start of any session to get full context.
> **Last Updated: 2026-03-02 (Day 4)**

---

## 1. PROJECT DNA

**FactoryOPS** is an Industrial IoT (IIoT) Intelligence Platform for real-time monitoring, health analytics, and predictive maintenance of industrial equipment. It ingests telemetry via MQTT, stores in InfluxDB, provides rule-based alerting with multi-channel notifications, runs ML analytics, and generates energy/wastage reports with PDF export.

- **Stack:** 6 Python/FastAPI microservices + Next.js frontend
- **Version:** 1.0.0
- **Local dev:** Mac, project root at `/Users/vedanthshetty/Desktop/OPENCODE/factoryops/`
- **Docker:** `factoryops/infrastructure/docker/docker-compose.yml`
- **Status:** All services running and healthy

---

## 2. SERVICE PORTS

| Service | Port | Container Name |
|---------|------|----------------|
| device-service | 8000 | factoryops_device_service |
| data-service | 8081 | factoryops_data_service |
| rule-engine-service | 8002 | factoryops_rule_engine_service |
| analytics-service | 8003 | factoryops_analytics_service |
| reporting-service | 8085 | factoryops_reporting_service |
| data-export-service | 8080 | factoryops_data_export_service |
| ui-web (Next.js) | 3000 | factoryops_ui_web |
| MySQL | 3306 | factoryops_mysql |
| InfluxDB | 8086 | factoryops_influxdb |
| Redis | 6379 | factoryops_redis |
| EMQX (MQTT) | 1883/8083 | factoryops_emqx |
| MinIO | 9000/9001 | factoryops_minio |

---

## 3. KNOWN LANDMINES (ALL BUGS FOUND DAYS 1–4)

| # | Bug | Root Cause | Fix Applied |
|---|-----|------------|-------------|
| 1 | InfluxDB pivot syntax | Flux `pivot` requires `column` param | Changed `rowKey` to correct Flux pivot |
| 2 | Analytics queries fail | InfluxDB v2 dropped InfluxQL | Migrated to Flux API |
| 3 | Alembic migrations hang | aiomysql blocks sync migrations | Switch to pymysql for migrations |
| 4 | Rule engine crashes on telemetry | `condition.value` AttributeError | `getattr(telemetry, property, None)` |
| 5 | MQTT connection refused | Wrong `mqtt://` prefix | Changed to `tcp://` for paho-mqtt |
| 6 | ML jobs fail with DB error | Async session closed early | Proper async session context manager |
| 7 | IsolationForest validation | Checked point count not time span | Validate time-span >= 7 days |
| 8 | MinIO upload fails silently | BytesIO pointer at end | `seek(0)` before upload |
| 9 | PDF generation timeout | Sync PDF in async endpoint | Moved to async job queue |
| 10 | Notification serialization error | Pydantic needed `model_dump()` | Updated serialization |
| 11 | **Device dropdowns empty** | Frontend sent `limit=500`, backend max was `le=100` | Backend changed `le=100` → `le=1000` in `device-service/app/api/routes/devices.py` line 28 |
| 12 | **FastAPI route order** | Generic `/{report_id}` route registered before `/history` and `/wastage` | Reordered routes: specific routes first, generic `/{id}` last in `reporting-service/app/api/routes/reports.py` |
| 13 | **PDF download broken** | Frontend checked `url` field, API returns `download_url` | Fixed field mapping in `ui-web/lib/api/reports.ts` |
| 14 | **MinIO presigned URL signature mismatch** | MinIO signs URL for `minio:9000` (internal), browser tries `localhost:9000` — signature cryptographically invalid | Added `127.0.0.1 minio` to Mac `/etc/hosts`. Removed hostname replacement in `minio_client.py` — return URL as-is |
| 15 | **Wastage page no data** | UI called `/api/v1/wastage`, correct is `/api/v1/reports/wastage` | Fixed by route order fix (Bug #12) |
| 16 | **Health score calculation** | Weights not summing correctly | Fixed weight normalization |
| 17 | **Rules pause/resume** | Missing action endpoints | Added pause/resume endpoints to rule-engine |
| 18 | **Rule creation emails** | Email adapter not wired | Implemented email_adapter.py with SMTP |
| 19 | **Daily chart only 2 bars** | `daily_breakdown` built wrong: power values not converted to kWh | Fixed in `routes.py`: `kwh = power_w * interval_hours / 1000.0` |
| 20 | **PDF header background invisible** | `matplotlib add_axes` with `bbox_inches='tight'` clips `transAxes` patches outside axes frame | Switched to `bbox_inches=None` with `PdfPages` |
| 21 | **KPI cards show only colored bar, no box** | Same matplotlib clipping issue as #20 | Fixed with `clip_on=True` and proper zorder in mpatches.Rectangle |

---

## 4. SYSTEM CONFIGURATION (Critical — Do Not Change)

### Mac `/etc/hosts` — REQUIRED for PDF downloads
```
127.0.0.1  minio
```
Without this, PDF download from browser fails with `SignatureDoesNotMatch`. MinIO presigned URLs are signed for `minio:9000` hostname. Browser must resolve `minio` → `127.0.0.1`.

### Default Tariff Rate
- `DEFAULT_TARIFF_RATE = 8.5` in `reporting-service/app/config.py`
- Unit: Rs./kWh (Indian Rupees per kilowatt-hour)
- Used when no custom tariff in `tenant_tariffs` table
- **Do not change** without manager approval

### Devices in System
| Device ID | Device Name | Type | Location |
|-----------|-------------|------|----------|
| COMPRESSOR-002 | Backup Air Compressor | compressor | Factory Floor B |
| COMPRESSOR-003 | Main Air Compressor | compressor | Factory Floor A |
| TEST-ALERT-BE064A | Test Alert Device | test | - |

### ML Analytics Note
- Requires minimum **7 days of telemetry data** in InfluxDB
- Simulator started 2026-02-28 — will be ready ~2026-03-07
- "No telemetry data available" until then — **expected behavior, not a bug**

---

## 5. FILES MODIFIED DAYS 1–4

### Backend
```
factoryops/services/device-service/app/api/routes/devices.py
  → Line 28: le=100 → le=1000  (Bug #11)

factoryops/services/reporting-service/app/api/routes/reports.py
  → Route order: /history and /wastage BEFORE /{report_id}  (Bug #12)
  → Added httpx import for device name enrichment
  → process_consumption_report: fetches device_name from device-service
  → process_consumption_report: fixed daily_breakdown calc (Bug #19)
    kwh = power_w * interval_hours / 1000.0

factoryops/services/reporting-service/app/storage/minio_client.py
  → Removed hostname replacement (Bug #14)
  → Returns presigned URL as-is (signed for minio:9000)

factoryops/services/reporting-service/app/services/pdf/builder.py
  → Complete rewrite using matplotlib PdfPages + absolute inch positioning
  → Uses bbox_inches=None (NOT bbox_inches='tight') to prevent clipping
  → Key functions: draw_header(), draw_kpi_cards(), draw_table(),
    draw_bar_chart(), draw_insights(), draw_note(), draw_footer()
  → _add_ax(fig, left, bottom, width, height) — all coords in inches

factoryops/services/rule-engine-service/app/services/notification/email_adapter.py
  → New file: SMTP email adapter

factoryops/services/rule-engine-service/app/api/routes/rules.py
  → Added pause/resume endpoints

factoryops/services/reporting-service/requirements.txt
  → Added: matplotlib==3.9.0, httpx==0.27.0
```

### Frontend
```
factoryops/ui-web/app/reports/energy/page.tsx
  → limit 500 → 100, improved handleDownload()

factoryops/ui-web/app/wastage/page.tsx
  → limit 500 → 100

factoryops/ui-web/app/analytics/page.tsx
  → limit 500 → 100

factoryops/ui-web/lib/api/reports.ts
  → getReportDownloadUrl() maps download_url → url
```

### System
```
/etc/hosts (Mac)
  → Added: 127.0.0.1  minio
```

---

## 6. PDF REPORT — CURRENT STATE (In Progress)

### Architecture
- **Library:** matplotlib (PdfPages) — draws everything directly on A4 figure
- **Key rule:** Always `pdf.savefig(fig, bbox_inches=None)` — NEVER `bbox_inches='tight'`
- **Positioning:** `_add_ax(fig, left, bottom, width, height)` with inch coordinates
- **Page size:** A4_W=8.27in, A4_H=11.69in, MARGIN=0.55in, CW=7.17in

### Sections in Order
1. Header — dark 3-row (brand bar → title → accent line → subtitle+period)
2. Executive Summary — 4 KPI cards (Energy / Peak / Hours / Cost)
3. Device Breakdown — table with device name, ID, kWh, peak, hours, cost
4. Daily Energy Consumption — bar chart (note shown if no data)
5. Cost Estimation — table with TOTAL row in blue
6. Key Insights — bullets with blue left border
7. Footer — timestamp + page number

### Currency
Uses `Rs.` not `₹` — the rupee Unicode symbol renders as broken square in some PDF viewers.

### OPEN ISSUE (as of Day 4)
Header dark background and KPI card boxes not rendering correctly in final PDF.
Current attempt: matplotlib `_filled_ax()` with `mpatches.Rectangle`.
Fix prompt in progress — being run in OpenCode with Minimax 2.5.

---

## 7. GUARD PROMPT — PASTE THIS AT START OF EVERY NEW AI SESSION

```
You are working on FactoryOPS — Industrial IoT platform.
Project root: /Users/vedanthshetty/Desktop/OPENCODE/factoryops/
Docker compose: factoryops/infrastructure/docker/docker-compose.yml

SERVICES:
  device-service:8000  data-service:8081  rule-engine:8002
  analytics:8003  reporting:8085  data-export:8080  ui-web:3000

CRITICAL — DO NOT UNDO THESE:
1. Mac /etc/hosts has "127.0.0.1 minio" — required for PDF downloads
2. device-service devices.py limit is le=1000 (not le=100)
3. reporting-service routes: /history and /wastage BEFORE /{report_id}
4. minio_client.py returns presigned URL as-is (no hostname replacement)
5. PDF builder uses bbox_inches=None (never bbox_inches='tight')
6. Currency is Rs. (not ₹)
7. daily_breakdown: kwh = power_w * interval_hours / 1000.0

CONSTRAINTS:
- No authentication (v1.0 by design)
- MySQL + InfluxDB hybrid storage
- Health scores: weights must sum to 100
- FastAPI async throughout — no blocking calls
- Response envelope: {"success": true, "data": {...}, "timestamp": "..."}
- Soft delete uses deleted_at field
- Default tariff: Rs. 8.5/kWh

REBUILD COMMANDS (use after any Python service change):
cd factoryops/infrastructure/docker
docker-compose stop <service> && docker-compose rm -f <service>
docker-compose build --no-cache <service> && docker-compose up -d <service>
sleep 25 && docker logs <container_name> --tail 10

UI rebuild (only when env vars change):
docker-compose stop ui-web && docker-compose rm -f ui-web
docker-compose build --no-cache ui-web && docker-compose up -d ui-web

DO NOT:
- Change device limit back to le=100
- Re-add hostname replacement in minio_client.py
- Use bbox_inches='tight' in PDF builder
- Put /{param} routes before specific /path routes in FastAPI
- Add blocking calls in async endpoints
- Change DB schema without alembic migration
```

---

## 8. ARCHITECTURE DECISIONS

| Decision | Reason |
|----------|--------|
| 6 microservices | Independent scaling, fault isolation per domain |
| MySQL + InfluxDB | MySQL for relational configs, InfluxDB for time-series |
| MQTT (EMQX) | Industry standard IoT, 1000+ connections |
| Redis cooldown | Sub-ms TTL for alert deduplication |
| MinIO | S3-compatible, no AWS dependency |
| FastAPI | Async-first, auto OpenAPI docs, Pydantic validation |
| No auth v1.0 | Open access internal system by design |
| Soft delete | Audit trail, no accidental data loss |
| Weights sum to 100 | Math requirement for health score |
| 90-day InfluxDB retention | Storage cost vs history balance |
| Async job queue | Long ops (PDF, ML) don't block API |
| WebSocket live telemetry | Sub-second dashboard updates |

---

## 9. DATABASE SCHEMA SUMMARY

### MySQL (5 databases)

**energy_device_db** → device-service
- devices: device_id(PK), device_name, device_type, location, legacy_status, deleted_at
- device_shifts, parameter_health_config, device_properties

**energy_rule_db** → rule-engine
- rules: rule_id(UUID), tenant_id, property, status, scope
- alerts: alert_id(UUID), rule_id(FK), device_id, status

**energy_analytics_db** → analytics-service
- analytics_jobs: job_id(UNIQUE), device_id, status, analysis_type

**energy_reporting_db** → reporting-service
- energy_reports: report_id(UNIQUE), status, report_type, result_json, s3_key
- tenant_tariffs: tenant_id, rate_per_unit, currency, is_active

**energy_export_db** → data-export-service
- export_checkpoints: device_id, status, format, start_time, end_time

### InfluxDB
- Bucket: `telemetry`, Measurement: `telemetry`
- Tags: device_id, schema_version
- Fields: power, voltage, temperature, current, + any numeric telemetry
- Retention: 90 days

---

## 10. INTER-SERVICE CONTRACTS

```
# Reporting → Device (get device names for PDF)
GET http://device-service:8000/api/v1/devices?limit=1000
Response: {"success": true, "data": [{"device_id": "...", "device_name": "...", ...}]}

# Data → Rule Engine (evaluate rules on telemetry)
POST http://rule-engine-service:8002/api/v1/rules/evaluate
Body: {"device_id": "...", "telemetry": {...}, "timestamp": "..."}

# Any service → MinIO (presigned download URL)
URL format: http://minio:9000/reports/...?X-Amz-Signature=...
Note: minio hostname resolves via /etc/hosts on Mac
```

---

*Last Updated: 2026-03-02 — Day 4*
*FactoryOPS v1.0.0*
