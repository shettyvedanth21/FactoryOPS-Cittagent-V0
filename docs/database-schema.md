# Database Schema - Energy Enterprise Platform

> **Document Version:** 1.0  
> **Purpose:** Complete database schema for LLD phase  
> **Project:** Energy Enterprise (FactoryOPS) - Production v1.0

---

## Table of Contents
1. [Database Overview](#1-database-overview)
2. [Database 1: energy_device_db](#2-database-1-energy_device_db)
3. [Database 2: energy_rule_db](#3-database-2-energy_rule_db)
4. [Database 3: energy_analytics_db](#4-database-3-energy_analytics_db)
5. [Database 4: energy_reporting_db](#5-database-4-energy_reporting_db)
6. [Database 5: energy_export_db](#6-database-5-energy_export_db)
7. [InfluxDB Schema](#7-influxdb-schema)
8. [Entity Relationship Diagrams](#8-entity-relationship-diagrams)
9. [Index Strategy](#9-index-strategy)
10. [Data Retention Policies](#10-data-retention-policies)

---

## 1. Database Overview

### 1.1 Database Summary

| Database | Service | Purpose | Tables |
|----------|---------|---------|--------|
| `energy_device_db` | device-service | Device management, shifts, health config | 4 |
| `energy_rule_db` | rule-engine-service | Rules, alerts | 2 |
| `energy_analytics_db` | analytics-service | ML jobs | 1 |
| `energy_reporting_db` | reporting-service | Reports, schedules, tariffs | 3 |
| `energy_export_db` | data-export-service | Export checkpoints | 1 |
| **InfluxDB** | data-service | Telemetry time-series | 1 bucket |

**Total Tables:** 12

### 1.2 Technology Stack

- **MySQL:** 8.0+
- **InfluxDB:** 2.7+
- **Storage Engine:** InnoDB
- **Character Set:** utf8mb4

---

## 2. Database: energy_device_db

### 2.1 Table: devices

**Purpose:** Core device registry for all IoT devices

```sql
CREATE TABLE devices (
    device_id         VARCHAR(50)  PRIMARY KEY,
    tenant_id         VARCHAR(50)  NULL,
    device_name       VARCHAR(255) NOT NULL,
    device_type       VARCHAR(100) NOT NULL,
    manufacturer      VARCHAR(255) NULL,
    model             VARCHAR(255) NULL,
    location          VARCHAR(500) NULL,
    phase_type        VARCHAR(20)  NULL,           -- 'single' or 'three'
    legacy_status     VARCHAR(50)  DEFAULT 'active',
    last_seen_timestamp DATETIME(6) NULL,
    metadata_json     TEXT         NULL,
    created_at        DATETIME(6) NOT NULL,
    updated_at        DATETIME(6) NOT NULL,
    deleted_at        DATETIME(6) NULL,
    
    INDEX idx_tenant (tenant_id),
    INDEX idx_device_type (device_type),
    INDEX idx_last_seen (last_seen_timestamp),
    INDEX idx_legacy_status (legacy_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| device_id | VARCHAR(50) PK | Unique business key (e.g., "COMPRESSOR-001") |
| tenant_id | VARCHAR(50) | Multi-tenant identifier (nullable for v1.0) |
| device_name | VARCHAR(255) | Display name |
| device_type | VARCHAR(100) | Type: compressor, motor, pump, etc. |
| manufacturer | VARCHAR(255) | Manufacturer name |
| model | VARCHAR(255) | Model number |
| location | VARCHAR(500) | Physical location |
| phase_type | VARCHAR(20) | Electrical: single or three phase |
| legacy_status | VARCHAR(50) | Legacy: active/inactive/maintenance/error |
| last_seen_timestamp | DATETIME | Last telemetry received |
| metadata_json | TEXT | Extended metadata as JSON |
| created_at | DATETIME | Record creation time |
| updated_at | DATETIME | Last update time |
| deleted_at | DATETIME | Soft delete timestamp |

---

### 2.2 Table: device_shifts

**Purpose:** Shift configuration for uptime calculation

```sql
CREATE TABLE device_shifts (
    id                  INT         PRIMARY KEY AUTO_INCREMENT,
    device_id           VARCHAR(50) NOT NULL,
    tenant_id           VARCHAR(50) NULL,
    shift_name          VARCHAR(100) NOT NULL,
    shift_start         TIME        NOT NULL,
    shift_end           TIME        NOT NULL,
    maintenance_break_minutes INT   DEFAULT 0,
    day_of_week         INT         NULL,     -- 0=Monday, 6=Sunday, NULL=all days
    is_active           BOOLEAN     DEFAULT TRUE,
    created_at          DATETIME(6) NOT NULL,
    updated_at          DATETIME(6) NOT NULL,
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device_shifts_device (device_id),
    INDEX idx_device_shifts_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| id | INT PK | Auto-increment ID |
| device_id | VARCHAR(50) FK | Reference to device |
| tenant_id | VARCHAR(50) | Multi-tenant |
| shift_name | VARCHAR(100) | Shift identifier |
| shift_start | TIME | Shift start time (HH:MM) |
| shift_end | TIME | Shift end time (HH:MM) |
| maintenance_break_minutes | INT | Break duration in minutes |
| day_of_week | INT | 0-6 (Monday-Sunday), NULL=all days |
| is_active | BOOLEAN | Active flag |

---

### 2.3 Table: parameter_health_config

**Purpose:** Health parameter configuration for health score calculation

```sql
CREATE TABLE parameter_health_config (
    id                  INT         PRIMARY KEY AUTO_INCREMENT,
    device_id           VARCHAR(50) NOT NULL,
    tenant_id           VARCHAR(50) NULL,
    parameter_name      VARCHAR(100) NOT NULL,
    normal_min          FLOAT       NULL,
    normal_max          FLOAT       NULL,
    max_min             FLOAT       NULL,
    max_max             FLOAT       NULL,
    weight              FLOAT       NOT NULL DEFAULT 0.0,
    ignore_zero_value   BOOLEAN     DEFAULT FALSE,
    is_active           BOOLEAN     DEFAULT TRUE,
    created_at          DATETIME(6) NOT NULL,
    updated_at          DATETIME(6) NOT NULL,
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_health_config_device (device_id),
    INDEX idx_health_config_tenant (tenant_id),
    UNIQUE KEY uk_device_parameter (device_id, parameter_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| id | INT PK | Auto-increment ID |
| device_id | VARCHAR(50) FK | Reference to device |
| tenant_id | VARCHAR(50) | Multi-tenant |
| parameter_name | VARCHAR(100) | Parameter: power, voltage, temperature, etc. |
| normal_min | FLOAT | Normal range minimum |
| normal_max | FLOAT | Normal range maximum |
| max_min | FLOAT | Max range minimum |
| max_max | FLOAT | Max range maximum |
| weight | FLOAT | Weight (0-100), must sum to 100 for calculation |
| ignore_zero_value | BOOLEAN | Skip zero values in calculation |
| is_active | BOOLEAN | Active flag |

---

### 2.4 Table: device_properties

**Purpose:** Dynamic device properties discovered from telemetry

```sql
CREATE TABLE device_properties (
    id                  INT         PRIMARY KEY AUTO_INCREMENT,
    device_id           VARCHAR(50) NOT NULL,
    property_name       VARCHAR(100) NOT NULL,
    data_type          VARCHAR(20)  DEFAULT 'float',
    is_numeric         BOOLEAN     DEFAULT TRUE,
    discovered_at       DATETIME(6) NOT NULL,
    last_seen_at       DATETIME(6) NOT NULL,
    
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_device_properties_device (device_id),
    UNIQUE KEY uk_device_property (device_id, property_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 3. Database: energy_rule_db

### 3.1 Table: rules

**Purpose:** Alert rule definitions

```sql
CREATE TABLE rules (
    rule_id               VARCHAR(36)  PRIMARY KEY,
    tenant_id             VARCHAR(50)  NULL,
    rule_name             VARCHAR(255) NOT NULL,
    description           TEXT         NULL,
    scope                 VARCHAR(50)  DEFAULT 'selected_devices',
    property              VARCHAR(100) NOT NULL,
    condition             VARCHAR(20)  NOT NULL,
    threshold             FLOAT        NOT NULL,
    status                VARCHAR(50)  DEFAULT 'active',
    notification_channels JSON         NOT NULL,  -- ["email", "sms", "webhook"]
    cooldown_minutes      INT          DEFAULT 15,
    device_ids            JSON         NOT NULL,  -- List of device IDs
    last_triggered_at     DATETIME(6)  NULL,
    created_at            DATETIME(6)  NOT NULL,
    updated_at            DATETIME(6)  NOT NULL,
    deleted_at            DATETIME(6)  NULL,
    
    INDEX idx_rules_tenant (tenant_id),
    INDEX idx_rules_property (property),
    INDEX idx_rules_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Enums:**
```python
RuleScope: ALL_DEVICES = "all_devices", SELECTED_DEVICES = "selected_devices"
RuleStatus: ACTIVE = "active", PAUSED = "paused", ARCHIVED = "archived"
ConditionOperator: ">", "<", "=", "!=", ">=", "<="
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| rule_id | VARCHAR(36) PK | UUID |
| tenant_id | VARCHAR(50) | Multi-tenant |
| rule_name | VARCHAR(255) | Rule name |
| description | TEXT | Optional description |
| scope | VARCHAR(50) | all_devices or selected_devices |
| property | VARCHAR(100) | Telemetry property to monitor |
| condition | VARCHAR(20) | >, <, =, !=, >=, <= |
| threshold | FLOAT | Threshold value |
| status | VARCHAR(50) | active, paused, archived |
| notification_channels | JSON | List: ["email", "sms", "webhook", "whatsapp", "telegram"] |
| cooldown_minutes | INT | Minimum time between alerts |
| device_ids | JSON | List of device IDs (if scope = selected_devices) |
| last_triggered_at | DATETIME | Last time rule triggered |

---

### 3.2 Table: alerts

**Purpose:** Alert instances generated when rules trigger

```sql
CREATE TABLE alerts (
    alert_id          VARCHAR(36)  PRIMARY KEY,
    tenant_id         VARCHAR(50)  NULL,
    rule_id           VARCHAR(36)  NOT NULL,
    device_id         VARCHAR(50)  NOT NULL,
    severity          VARCHAR(50)  NOT NULL,  -- critical, warning, info
    message           TEXT        NOT NULL,
    actual_value      FLOAT        NULL,
    threshold_value   FLOAT        NULL,
    property_name     VARCHAR(100) NULL,
    status            VARCHAR(50)  DEFAULT 'open',  -- open, acknowledged, resolved
    acknowledged_by   VARCHAR(255) NULL,
    acknowledged_at   DATETIME(6)  NULL,
    resolved_at       DATETIME(6)  NULL,
    created_at        DATETIME(6)  NOT NULL,
    updated_at        DATETIME(6)  NOT NULL,
    
    FOREIGN KEY (rule_id) REFERENCES rules(rule_id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_alerts_rule (rule_id),
    INDEX idx_alerts_device (device_id),
    INDEX idx_alerts_status (status),
    INDEX idx_alerts_created (created_at),
    INDEX idx_alerts_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Enums:**
```python
AlertSeverity: CRITICAL = "critical", WARNING = "warning", INFO = "info"
AlertStatus: OPEN = "open", ACKNOWLEDGED = "acknowledged", RESOLVED = "resolved"
```

---

## 4. Database: energy_analytics_db

### 4.1 Table: analytics_jobs

**Purpose:** ML analytics job tracking

```sql
CREATE TABLE analytics_jobs (
    id                    VARCHAR(36)  PRIMARY KEY,
    job_id                VARCHAR(100) UNIQUE NOT NULL,
    device_id             VARCHAR(50)  NOT NULL,
    analysis_type         VARCHAR(50)  NOT NULL,  -- anomaly_detection, failure_prediction, forecasting
    model_name            VARCHAR(100) NOT NULL,
    date_range_start      DATETIME(6)  NOT NULL,
    date_range_end        DATETIME(6)  NOT NULL,
    parameters            JSON         NULL,
    status                VARCHAR(50)  NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed
    progress              FLOAT        NULL,
    message               TEXT         NULL,
    error_message         TEXT         NULL,
    results               JSON         NULL,
    accuracy_metrics     JSON         NULL,
    execution_time_seconds INT         NULL,
    created_at           DATETIME(6)  NOT NULL,
    started_at           DATETIME(6)  NULL,
    completed_at         DATETIME(6)  NULL,
    updated_at           DATETIME(6)  NOT NULL,
    
    INDEX idx_analytics_jobs_status (status),
    INDEX idx_analytics_jobs_created (created_at),
    INDEX idx_analytics_jobs_device (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 5. Database: energy_reporting_db

### 5.1 Table: energy_reports

**Purpose:** Report generation tracking

```sql
CREATE TABLE energy_reports (
    id                    INT          PRIMARY KEY AUTO_INCREMENT,
    report_id             VARCHAR(36)  UNIQUE NOT NULL,
    tenant_id            VARCHAR(50)  NOT NULL,
    report_type          VARCHAR(50)  NOT NULL,  -- consumption, comparison
    status               VARCHAR(50)  NOT NULL DEFAULT 'pending',
    params               JSON         NOT NULL,
    computation_mode     VARCHAR(50)  NULL,  -- direct_power, derived_single, derived_three
    phase_type_used     VARCHAR(20)  NULL,
    result_json          JSON         NULL,
    s3_key              VARCHAR(500) NULL,
    error_code           VARCHAR(100) NULL,
    error_message        TEXT         NULL,
    progress             INT          DEFAULT 0,
    created_at          DATETIME     NOT NULL,
    completed_at        DATETIME     NULL,
    
    INDEX ix_energy_reports_tenant_status (tenant_id, status),
    INDEX ix_energy_reports_tenant_type_created (tenant_id, report_type, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

### 5.2 Table: scheduled_reports

**Purpose:** Scheduled report configuration

```sql
CREATE TABLE scheduled_reports (
    id                  INT          PRIMARY KEY AUTO_INCREMENT,
    schedule_id         VARCHAR(36)  UNIQUE NOT NULL,
    tenant_id          VARCHAR(50)  NOT NULL,
    report_type        VARCHAR(50)  NOT NULL,  -- consumption, comparison
    frequency          VARCHAR(50)  NOT NULL,  -- daily, weekly, monthly
    params_template    JSON         NOT NULL,
    is_active         BOOLEAN      DEFAULT TRUE,
    last_run_at        DATETIME     NULL,
    next_run_at        DATETIME     NULL,
    last_status        VARCHAR(50)  NULL,
    retry_count        INT          DEFAULT 0,
    last_result_url    VARCHAR(2000) NULL,
    created_at        DATETIME      NOT NULL,
    updated_at        DATETIME      NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

### 5.3 Table: tenant_tariffs

**Purpose:** Energy tariff configuration for cost calculation

```sql
CREATE TABLE tenant_tariffs (
    id                  INT          PRIMARY KEY AUTO_INCREMENT,
    tenant_id          VARCHAR(50)  NOT NULL,
    tariff_name        VARCHAR(100) NOT NULL,
    rate_per_unit      DECIMAL(10, 4) NOT NULL,  -- ₹/kWh
    currency           VARCHAR(10)  DEFAULT 'INR',
    peak_rate          DECIMAL(10, 4) NULL,       -- Peak hour rate
    peak_start_time    TIME         NULL,          -- Peak start (HH:MM)
    peak_end_time      TIME         NULL,          -- Peak end (HH:MM)
    demand_charge      DECIMAL(10, 2) NULL,        -- ₹/kW
    power_factor_penalty DECIMAL(5,2) NULL,       -- % penalty
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        DATETIME      NOT NULL,
    updated_at        DATETIME      NOT NULL,
    
    INDEX idx_tenant_tariffs_tenant (tenant_id),
    UNIQUE KEY uk_tenant_tariff (tenant_id, tariff_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 5.5 Table: notification_configs (NEW)

**Purpose:** Store notification channel credentials and configurations

```sql
CREATE TABLE notification_configs (
    id                    INT          PRIMARY KEY AUTO_INCREMENT,
    tenant_id            VARCHAR(50)  NOT NULL,
    channel              VARCHAR(50)  NOT NULL,  -- email, sms, whatsapp, telegram, webhook
    config_name          VARCHAR(100) NOT NULL,
    is_active           BOOLEAN      DEFAULT TRUE,
    is_default          BOOLEAN      DEFAULT FALSE,
    
    -- Email (SMTP) Configuration
    smtp_host            VARCHAR(255) NULL,
    smtp_port            INT          NULL,
    smtp_username       VARCHAR(255) NULL,
    smtp_password       VARCHAR(255) NULL,        -- Encrypted
    smtp_from_email     VARCHAR(255) NULL,
    smtp_from_name      VARCHAR(255) NULL,
    use_tls             BOOLEAN      DEFAULT TRUE,
    
    -- SMS (AWS SNS / Twilio) Configuration
    sms_provider         VARCHAR(50)  NULL,       -- aws_sns, twilio
    sms_access_key       VARCHAR(255) NULL,        -- Encrypted
    sms_secret_key       VARCHAR(255) NULL,        -- Encrypted
    sms_region          VARCHAR(50)  NULL,
    sms_sender_id       VARCHAR(50)  NULL,
    
    -- WhatsApp (Twilio) Configuration
    whatsapp_account_sid VARCHAR(255) NULL,
    whatsapp_auth_token  VARCHAR(255) NULL,       -- Encrypted
    whatsapp_from_number VARCHAR(50)  NULL,
    
    -- Telegram Configuration
    telegram_bot_token   VARCHAR(255) NULL,       -- Encrypted
    telegram_chat_id    VARCHAR(50)  NULL,
    
    -- Webhook Configuration
    webhook_url         VARCHAR(500) NULL,
    webhook_method      VARCHAR(10)  DEFAULT 'POST',
    webhook_auth_header VARCHAR(255) NULL,
    webhook_auth_value  VARCHAR(255) NULL,       -- Encrypted
    
    -- Rate Limiting
    rate_limit_per_hour INT          DEFAULT 100,
    
    -- Metadata
    created_at          DATETIME      NOT NULL,
    updated_at          DATETIME      NOT NULL,
    
    INDEX idx_notification_configs_tenant (tenant_id),
    INDEX idx_notification_configs_channel (channel),
    UNIQUE KEY uk_tenant_channel_name (tenant_id, channel, config_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Notification Config Fields Explained

| Field | Channel | Description |
|-------|---------|-------------|
| **smtp_host** | Email | SMTP server (e.g., smtp.gmail.com) |
| **smtp_port** | Email | Port (e.g., 587) |
| **smtp_username** | Email | SMTP username |
| **smtp_password** | Email | SMTP password (encrypted) |
| **sms_provider** | SMS | aws_sns or twilio |
| **sms_access_key** | SMS | AWS Access Key (encrypted) |
| **sms_secret_key** | SMS | AWS Secret Key (encrypted) |
| **whatsapp_account_sid** | WhatsApp | Twilio Account SID |
| **whatsapp_auth_token** | WhatsApp | Twilio Auth Token (encrypted) |
| **telegram_bot_token** | Telegram | Bot API Token (encrypted) |
| **webhook_url** | Webhook | Target URL for HTTP POST |

### Security Considerations

1. **Encryption:** Sensitive fields (passwords, tokens) MUST be encrypted at rest
2. **Key Management:** Use AWS KMS or similar for key management
3. **Audit Logs:** Track who changed notification configs
4. **Validation:** Test credentials before saving

---

## 5.6 Table: notification_templates (NEW)

**Purpose:** Store customizable notification message templates

```sql
CREATE TABLE notification_templates (
    id                  INT          PRIMARY KEY AUTO_INCREMENT,
    tenant_id          VARCHAR(50)  NOT NULL,
    channel            VARCHAR(50)  NOT NULL,  -- email, sms, whatsapp, telegram
    template_name      VARCHAR(100) NOT NULL,
    subject            VARCHAR(255) NULL,       -- For email
    body_template      TEXT        NOT NULL,   -- Supports {{placeholders}}
    is_active         BOOLEAN      DEFAULT TRUE,
    created_at        DATETIME      NOT NULL,
    updated_at        DATETIME      NOT NULL,
    
    INDEX idx_notification_templates_tenant (tenant_id),
    UNIQUE KEY uk_tenant_channel_template (tenant_id, channel, template_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Template Placeholders:**
```
{{device_id}}
{{device_name}}
{{rule_name}}
{{property}}
{{condition}}
{{threshold}}
{{actual_value}}
{{timestamp}}
{{alert_id}}
{{alert_message}}
```

---

## 5.7 Table: notification_logs (NEW)

**Purpose:** Track all sent notifications for auditing

```sql
CREATE TABLE notification_logs (
    id                  INT          PRIMARY KEY AUTO_INCREMENT,
    tenant_id          VARCHAR(50)  NOT NULL,
    alert_id           VARCHAR(36)  NOT NULL,
    rule_id           VARCHAR(36)  NULL,
    channel           VARCHAR(50)  NOT NULL,  -- email, sms, whatsapp, telegram, webhook
    recipient         VARCHAR(500) NOT NULL,  -- email, phone, chat_id
    status            VARCHAR(50)  NOT NULL,  -- sent, failed, bounced
    error_message     TEXT         NULL,
    response_id       VARCHAR(255) NULL,       -- Provider's message ID
    sent_at          DATETIME      NOT NULL,
    
    INDEX idx_notification_logs_alert (alert_id),
    INDEX idx_notification_logs_status (status),
    INDEX idx_notification_logs_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 5.8 Table: notification_preferences (NEW)

**Purpose:** User-level notification preferences

```sql
CREATE TABLE notification_preferences (
    id                  INT          PRIMARY KEY AUTO_INCREMENT,
    tenant_id          VARCHAR(50)  NOT NULL,
    user_email         VARCHAR(255) NOT NULL,  -- Or user_id when auth is added
    
    -- Preferences
    email_enabled      BOOLEAN      DEFAULT TRUE,
    sms_enabled        BOOLEAN      DEFAULT TRUE,
    whatsapp_enabled   BOOLEAN      DEFAULT TRUE,
    telegram_enabled   BOOLEAN      DEFAULT TRUE,
    webhook_enabled    BOOLEAN      DEFAULT TRUE,
    
    -- Quiet Hours
    quiet_hours_enabled BOOLEAN     DEFAULT FALSE,
    quiet_hours_start  TIME         NULL,
    quiet_hours_end    TIME         NULL,
    
    -- Severity Filters
    critical_alerts    BOOLEAN      DEFAULT TRUE,
    warning_alerts    BOOLEAN      DEFAULT TRUE,
    info_alerts       BOOLEAN      DEFAULT FALSE,
    
    created_at        DATETIME      NOT NULL,
    updated_at        DATETIME      NOT NULL,
    
    INDEX idx_notification_prefs_tenant (tenant_id),
    UNIQUE KEY uk_tenant_email (tenant_id, user_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

### 6.1 Table: export_checkpoints

**Purpose:** Track data export progress for idempotent exports

```sql
CREATE TABLE export_checkpoints (
    id                  INT          PRIMARY KEY AUTO_INCREMENT,
    device_id          VARCHAR(50)  NOT NULL,
    export_type        VARCHAR(50)  NOT NULL,  -- full, incremental
    format             VARCHAR(20)  NOT NULL,  -- csv, parquet, json
    start_time         DATETIME     NOT NULL,
    end_time           DATETIME     NOT NULL,
    status             VARCHAR(50)  NOT NULL,  -- pending, in_progress, completed, failed
    records_exported   INT          DEFAULT 0,
    s3_key             VARCHAR(500) NULL,
    error_message      TEXT         NULL,
    created_at        DATETIME      NOT NULL,
    completed_at      DATETIME      NULL,
    
    INDEX idx_export_checkpoints_device (device_id),
    INDEX idx_export_checkpoints_status (status),
    INDEX idx_export_checkpoints_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 7. InfluxDB Schema

### 7.1 Bucket: telemetry

**Retention:** 90 days

**Measurement:** telemetry

**Tags (Indexed):**
| Tag | Type | Description |
|-----|------|-------------|
| device_id | string | Device identifier |
| schema_version | string | Schema version (v1, v2) |
| enrichment_status | string | success/failed |

**Fields (Dynamic):**
All numeric telemetry fields are stored as fields:
- power (W)
- voltage (V)
- current (A)
- temperature (°C)
- pressure (bar)
- humidity (%)
- vibration (mm/s)
- frequency (Hz)
- speed (RPM)
- torque (Nm)
- And any other dynamic fields...

**Example Data Point:**
```
telemetry,device_id=COMPRESSOR-001,schema_version=v1,enrichment_status=success power=5200,voltage=228,temperature=45,pressure=5.2,current=12.5 1704067200000000000
```

---

## 8. Entity Relationship Diagrams

### 8.1 Device Service

```
┌─────────────────────┐       ┌─────────────────────────┐
│      devices       │       │   device_shifts         │
├─────────────────────┤       ├─────────────────────────┤
│ PK device_id       │──1:N──│ FK device_id            │
│ device_name        │       │ PK id                   │
│ device_type       │       │ shift_name              │
│ location          │       │ shift_start             │
│ ...               │       │ shift_end               │
└─────────────────────┘       │ maintenance_break_min   │
         │                   │ day_of_week             │
         │                   │ is_active               │
         │                   └─────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│parameter_health_config │   │   device_properties     │
├─────────────────────────┤   ├─────────────────────────┤
│ PK id                  │   │ PK id                   │
│ FK device_id           │   │ FK device_id            │
│ parameter_name        │   │ property_name          │
│ normal_min/max        │   │ data_type              │
│ max_min/max           │   │ is_numeric             │
│ weight                 │   └─────────────────────────┘
│ is_active              │
└─────────────────────────┘
```

### 8.2 Rule Engine Service

```
┌─────────────────────┐       ┌─────────────────────┐
│       rules         │       │       alerts        │
├─────────────────────┤       ├─────────────────────┤
│ PK rule_id          │──1:N──│ FK rule_id          │
│ rule_name           │       │ PK alert_id         │
│ scope               │       │ FK device_id        │
│ property            │       │ severity            │
│ condition           │       │ status              │
│ threshold           │       │ message             │
│ status              │       │ actual_value        │
│ notification_channels│     │ threshold_value     │
│ device_ids          │       │ created_at          │
│ cooldown_minutes    │       └─────────────────────┘
└─────────────────────┘
```

### 8.3 Reporting Service

```
┌─────────────────────┐       ┌─────────────────────┐
│   energy_reports    │       │  scheduled_reports   │
├─────────────────────┤       ├─────────────────────┤
│ PK id               │       │ PK id               │
│ report_id           │       │ schedule_id         │
│ tenant_id           │       │ tenant_id           │
│ report_type          │       │ report_type         │
│ status               │       │ frequency           │
│ params               │       │ params_template     │
│ result_json          │       │ is_active           │
│ s3_key               │       │ last_run_at         │
└─────────────────────┘       │ next_run_at         │
                              └─────────────────────┘
                                      │
                                      │ 1:1 (optional)
                                      ▼
                              ┌─────────────────────┐
                              │   tenant_tariffs    │
                              ├─────────────────────┤
                              │ PK id               │
                              │ tenant_id           │
                              │ tariff_name         │
                              │ rate_per_unit       │
                              │ peak_rate           │
                              │ ...                 │
                              └─────────────────────┘
```

---

## 9. Index Strategy

### 9.1 Indexes for Performance

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| devices | idx_tenant | tenant_id | Multi-tenant queries |
| devices | idx_device_type | device_type | Filter by type |
| devices | idx_last_seen | last_seen_timestamp | Status calculation |
| device_shifts | idx_device | device_id | Get shifts for device |
| rules | idx_property | property | Find rules by property |
| rules | idx_status | status | Filter active/paused |
| alerts | idx_device | device_id | Get alerts for device |
| alerts | idx_status | status | Filter open alerts |
| alerts | idx_created | created_at | Date range queries |
| analytics_jobs | idx_status | status | Job queue queries |
| analytics_jobs | idx_device | device_id | Get jobs for device |
| energy_reports | idx_tenant_status | tenant_id, status | Report queries |
| export_checkpoints | idx_device | device_id | Export history |

---

## 10. Data Retention Policies

### 10.1 Retention by Table

| Data Type | Retention | Storage | Action |
|-----------|-----------|---------|--------|
| Telemetry (InfluxDB) | 90 days | InfluxDB | Auto-delete |
| Devices | Indefinite | MySQL | Keep |
| Device Shifts | Indefinite | MySQL | Keep |
| Health Configs | Indefinite | MySQL | Keep |
| Device Properties | 1 year | MySQL | Archive to S3, then delete |
| Rules | Indefinite | MySQL | Soft delete on user action |
| Alerts | 1 year | MySQL | Archive to S3, then delete |
| Analytics Jobs | 90 days | MySQL | Auto-delete |
| Reports | 90 days | MySQL + S3 | Keep S3, delete MySQL reference |
| Scheduled Reports | Indefinite | MySQL | Keep |
| Tariffs | Indefinite | MySQL | Keep |
| Export Checkpoints | 1 year | MySQL | Auto-delete |
| Notification Logs | 1 year | MySQL | Auto-delete |
| Notification Configs | Indefinite | MySQL | Keep (encrypted) |

### 10.2 Archive Strategy

1. **Alerts > 1 year:** Export to S3 as JSON, delete from MySQL
2. **Telemetry > 90 days:** Auto-deleted by InfluxDB retention policy
3. **Analytics Jobs > 90 days:** Auto-delete
4. **Reports > 90 days:** Delete MySQL record, keep S3 file with expiration

---

## 11. Migration Notes

### 11.1 Future Schema Changes

1. **Multi-tenancy (v2.0)**
   - Add tenant_id where NULL
   - Create tenant isolation policies
   - Add row-level security

---

## 12. Audit Logging Table (For v1.0 - Recommended)

### 12.1 Table: audit_logs

**Purpose:** Track all configuration changes for compliance and security

```sql
CREATE TABLE audit_logs (
    id                  BIGINT       PRIMARY KEY AUTO_INCREMENT,
    tenant_id          VARCHAR(50)  NULL,
    user_id            VARCHAR(50)  NULL,       -- Or 'system' for automated actions
    user_email         VARCHAR(255) NULL,
    action             VARCHAR(50)  NOT NULL,  -- CREATE, UPDATE, DELETE, LOGIN, EXPORT
    table_name         VARCHAR(100) NOT NULL,
    record_id          VARCHAR(255) NULL,
    old_value          JSON         NULL,
    new_value          JSON         NULL,
    ip_address         VARCHAR(45)  NULL,
    user_agent         VARCHAR(500) NULL,
    status             VARCHAR(20)  DEFAULT 'success',  -- success, failed
    error_message      TEXT         NULL,
    created_at         DATETIME(6)  NOT NULL,
    
    INDEX idx_audit_logs_tenant (tenant_id),
    INDEX idx_audit_logs_user (user_id),
    INDEX idx_audit_logs_table (table_name),
    INDEX idx_audit_logs_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Tracked Actions:**
| Table | Actions Tracked |
|-------|----------------|
| devices | CREATE, UPDATE, DELETE |
| rules | CREATE, UPDATE, DELETE, PAUSE, ACTIVATE |
| notification_configs | CREATE, UPDATE, DELETE, TEST |
| scheduled_reports | CREATE, UPDATE, DELETE |
| tenant_tariffs | CREATE, UPDATE, DELETE |

---

**Document prepared for LLD phase**

