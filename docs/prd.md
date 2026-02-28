# Product Requirements Document (PRD)

> **Project Name:** Energy Enterprise (FactoryOPS)  
> **Document Version:** 1.0  
> **Date:** February 2026  
> **Status:** Production Planning

---

## 1. Product Overview

### 1.1 Product Vision

**Energy Enterprise** is an Industrial IoT (IIoT) Intelligence Platform designed to provide real-time monitoring, health analytics, and predictive insights for industrial equipment. The platform enables plant managers and maintenance teams to:

- Monitor machine health and performance in real-time
- Receive instant alerts when equipment parameters exceed thresholds
- Analyze energy consumption patterns
- Predict potential equipment failures before they occur
- Generate compliance and performance reports

### 1.2 Product Summary

| Attribute | Value |
|-----------|-------|
| **Product Name** | Energy Enterprise (FactoryOPS) |
| **Product Type** | Industrial IoT Monitoring Platform |
| **Target Users** | Plant Managers, Maintenance Engineers, Operations Teams |
| **Target Industry** | Manufacturing, Industrial Production, Factories |
| **Deployment** | Cloud (AWS) / On-premise |
| **Devices Supported** | 1000+ concurrent connections |

### 1.3 Problem Statement

Industrial plants face challenges in:
1. **Reactive maintenance** - Waiting for equipment to fail before fixing
2. **Manual monitoring** - Walking around to check machine status
3. **Energy waste** - No visibility into consumption patterns
4. **Downtime** - Unexpected equipment failures causing production loss
5. **Compliance** - Difficulty generating required reports

### 1.4 Solution

The Energy Enterprise Platform provides:
- **Real-time visibility** into all equipment status
- **Proactive alerting** before failures occur
- **Energy analytics** to identify waste and optimize consumption
- **Predictive insights** using ML to forecast failures
- **Automated reporting** for compliance and management

---

## 2. User Personas

### 2.1 Plant Manager

**Name:** Rajesh Kumar  
**Role:** Plant Manager, Automotive Parts Factory

**Goals:**
- Keep production running smoothly
- Minimize downtime
- Optimize energy costs
- Meet production targets

**Pain Points:**
- Can't see all machines at once
- Don't know about problems until something breaks
- Manual reporting takes too much time
- Can't compare machine performance

**How Platform Helps:**
- Single dashboard showing all machines
- Instant alerts when issues arise
- Automated energy and performance reports
- Comparative analysis between machines

---

### 2.2 Maintenance Engineer

**Name:** Amit Sharma  
**Role:** Maintenance Engineer

**Goals:**
- Keep equipment running optimally
- Plan maintenance schedules
- Reduce emergency repairs
- Extend equipment life

**Pain Points:**
- Don't know which parameter is causing issues
- Hard to diagnose problems quickly
- No historical data to compare
- Health configurations are manual

**How Platform Helps:**
- Health score breakdown by parameter
- Real-time telemetry with historical trends
- Parameter health configuration with weights
- Shift-based uptime calculations

---

### 2.3 Operations Team

**Name:** Production Team  
**Role:** Shift Supervisors, Operators

**Goals:**
- Know when machines are running
- Report issues quickly
- Track shift performance

**Pain Points:**
- Don't know machine status in real-time
- Communication delays
- Manual shift logging

**How Platform Helps:**
- Live machine status on dashboard
- One-click alert creation
- Automatic shift tracking

---

## 3. User Stories & Features

### 3.1 Dashboard & Monitoring

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-001 | As a Plant Manager, I want to see all machines on a single screen so that I can quickly assess overall plant health | P0 | - Grid view of all devices<br>- Status indicators (Running/Stopped/Error)<br>- Last seen timestamp<br>- Auto-refresh every 10 seconds |
| US-002 | As an Operator, I want to see live telemetry data so that I can monitor machines in real-time | P0 | - WebSocket connection for live data<br>- 1-second auto-refresh<br>- Display all telemetry fields |
| US-003 | As a Manager, I want KPIs on the dashboard so that I can see overall performance at a glance | P1 | - Total machines count<br>- Average health score<br>- Total uptime percentage<br>- Active alerts count |

---

### 3.2 Machine Management

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-004 | As an Admin, I want to register new machines so that they can be monitored | P0 | - Create device with name, type, location<br>- Generate unique device ID<br>- Set initial status |
| US-005 | As a Manager, I want to view machine details so that I can see all information about a machine | P0 | - Device information display<br>- Current status<br>- Health score<br>- Configuration options |
| US-006 | As an Engineer, I want to configure shifts so that uptime can be accurately calculated | P0 | - Add/edit/delete shifts<br>- Set start time, end time<br>- Set maintenance break duration<br>- Select days of week |
| US-007 | As an Engineer, I want to configure parameter health so that health scores are accurate | P0 | - Add parameters (pressure, temp, voltage, etc.)<br>- Set normal range (min/max)<br>- Set max range (min/max)<br>- Set weight (must sum to 100%) |

---

### 3.3 Health & Uptime

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-008 | As an Engineer, I want to see health score for each machine so that I know equipment condition | P0 | - Display score 0-100%<br>- Color coded (Green/Yellow/Red)<br>- Breakdown by parameter<br>- Show status (Running/Standby) |
| US-009 | As an Engineer, I want to see uptime percentage so that I know machine availability | P0 | - Calculate based on shifts<br>- Account for maintenance breaks<br>- Display total planned vs effective time |
| US-010 | As an Engineer, I want to see parameter efficiency so that I know which parameter needs attention | P0 | - Show efficiency % per parameter<br>- Color coded status<br>- Link to health config |

---

### 3.4 Rules & Alerts

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-011 | As an Engineer, I want to create alert rules so that I get notified when parameters exceed limits | P0 | - Create rule with name<br>- Select property to monitor<br>- Choose condition (>, <, =, etc.)<br>- Set threshold value |
| US-012 | As an Engineer, I want to select which machines a rule applies to so that alerts are targeted | P0 | - Option for all devices<br>- Option to select specific devices<br>- Dynamic property loading based on selection |
| US-013 | As an Engineer, I want to receive notifications via email so that I get alerts even when not on the platform | P0 | - Configure email as notification channel<br>- Send email when rule triggers<br>- Include device, value, threshold in email |
| US-014 | As an Engineer, I want to receive SMS alerts so that I get critical alerts on my phone | P1 | - Configure SMS as notification channel<br>- Send SMS when rule triggers |
| US-015 | As an Engineer, I want to receive webhook notifications so that I can integrate with other systems | P1 | - Configure webhook URL<br>- POST JSON payload when rule triggers |
| US-016 | As an Operator, I want to see active alerts so that I know what needs attention | P0 | - List all open alerts<br>- Show severity, message, device<br>- Acknowledge/resolve buttons |
| US-017 | As an Engineer, I want to pause a rule temporarily so that I can stop alerts without deleting | P0 | - Pause/activate rule toggle<br>- Status indicator on rule list |

---

### 3.5 Telemetry

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-018 | As an Operator, I want to see live telemetry stream so that I can monitor current values | P0 | - Real-time WebSocket connection<br>- Display all telemetry fields<br>- Auto-refresh every second |
| US-019 | As an Engineer, I want to query historical telemetry so that I can analyze past performance | P0 | - Select device<br>- Select date range<br>- View historical data table |
| US-020 | As an Engineer, I want to see telemetry charts so that I can visualize trends | P0 | - Line charts for each parameter<br>- Selectable date range<br>- Multiple parameters on same chart |

---

### 3.6 Reports - Energy Consumption

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-021 | As a Manager, I want to generate energy consumption report so that I can analyze energy usage | P0 | - Select date range (1-90 days)<br>- Select devices (single or multiple)<br>- Choose group by (daily/weekly) |
| US-022 | As a Manager, I want to see total energy consumed so that I can track consumption | P0 | - Display total kWh<br>- Show average power<br>- Show peak power |
| US-023 | As a Manager, I want to see peak demand so that I can plan capacity | P0 | - Display peak demand kW<br>- Show timestamp of peak |
| US-024 | As a Manager, I want to see load factor so that I can assess efficiency | P0 | - Calculate load factor<br>- Show classification (Poor/Fair/Good/Excellent)<br>- Show recommendation |
| US-025 | As a Manager, I want to estimate energy cost so that I can budget | P0 | - Configure tariff rates<br>- Calculate total cost<br>- Display by device |
| US-026 | As a Manager, I want to download reports so that I can share with others | P0 | - Download as PDF<br>- Download as CSV |
| US-027 | As a Manager, I want AI-powered insights so that I can understand patterns | P1 | - Auto-generated insights<br>- Actionable recommendations |

---

### 3.7 Reports - Comparative Analysis

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-028 | As a Manager, I want to compare two machines so that I can identify better performer | P0 | - Select machine A and B<br>- Compare energy consumption<br>- Compare efficiency metrics |
| US-029 | As a Manager, I want to compare time periods so that I can see improvement | P0 | - Select machine<br>- Select period A and B<br>- Compare same machine over time |
| US-030 | As a Manager, I want to see side-by-side metrics so that comparison is clear | P0 | - Display metrics in columns<br>- Highlight better performer<br>- Show % difference |

---

### 3.8 Analytics (ML)

> **Note:** Analytics is a P0 feature for v1.0. The current implementation is inadequate - users need context-aware, reasoning-driven insights, not just raw results.

#### 3.8.1 Anomaly Detection

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-031 | As a Maintenance Engineer, I want the system to automatically detect unusual patterns in my machine data so I can investigate before failures occur | P0 | - Select machine from dropdown<br>- Select date range (last 7/30/90 days)<br>- Click "Run Analysis"<br>- System processes data in background<br>- Results show within 30 seconds |
| US-032 | As a Maintenance Engineer, I want to understand WHY an anomaly occurred so I can take corrective action | P0 | - Show timeline of anomalies<br>- For each anomaly: display what parameter triggered it<br>- Show context: "Temperature spiked to 85°C at 14:30 - 20% above normal range (20-60°C)"<br>- Suggest possible causes based on pattern |
| US-033 | As a Maintenance Engineer, I want historical anomaly trends so I can see if problems are worsening | P0 | - Show frequency chart: anomalies per day/week<br>- Show parameter breakdown: which parameters cause most anomalies<br>- Compare anomaly rate vs previous period |

#### 3.8.2 Failure Prediction

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-034 | As a Plant Manager, I want to know which machines are at risk of failure so I can plan maintenance | P0 | - Select machine<br>- System analyzes last 30 days of data<br>- Display risk score: LOW (0-30%), MEDIUM (31-60%), HIGH (61-100%)<br>- Show risk factors: "High temperature trend + voltage fluctuations" |
| US-035 | As a Plant Manager, I want to know HOW LIKELY failure is in the next 7/30 days so I can schedule maintenance | P0 | - Show probability percentage<br>- Show confidence level (based on data quality)<br>- Timeline view: risk over next 7/30 days<br>- "There is a 75% chance of failure in next 7 days if current trend continues" |
| US-036 | As a Maintenance Engineer, I want actionable recommendations so I can prevent failures | P0 | - For each risk factor, show recommended action<br>- Example: "Replace coolant filter" or "Check electrical connections"<br>- Priority ranking: what to fix first |

#### 3.8.3 Data Export for ML

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-037 | As a Data Analyst, I want to export raw telemetry data so I can build custom ML models | P0 | - Select one or more machines<br>- Select date range (max 90 days)<br>- Choose format: CSV<br>- Download starts immediately<br>- Show progress for large exports |

#### 3.8.4 Analytics Results Display

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-038 | As a user, I want results in plain language so I don't need ML expertise | P0 | - Avoid technical jargon<br>- Use visual indicators (green/yellow/red)<br>- Show confidence level as "High/Medium/Low" not percentages |
| US-039 | As a user, I want to see charts so I can visualize the insights | P0 | - Time-series line charts for trends<br>- Bar charts for comparisons<br>- Color-coded severity indicators |
| US-040 | As a user, I want to act on insights immediately so I don't lose time | P0 | - Each insight has action button<br>- Example: "Create Alert" or "Schedule Maintenance"<br>- Quick navigation to related pages |

---

### 3.9 Report Scheduling

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-035 | As a Manager, I want to schedule reports so that I get them automatically | P1 | - Create schedule (daily/weekly/monthly)<br>- Select report type<br>- Select devices<br>- Set delivery time |
| US-036 | As a Manager, I want to view scheduled reports so that I can manage them | P1 | - List all schedules<br>- Edit schedule<br>- Delete/deactivate schedule |

---

### 3.10 Dashboard Enhancements

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-041 | As a Plant Manager, I want to see KPI summary cards so I can assess overall plant health at a glance | P0 | - Total machines count<br>- Average health score<br>- Total uptime %<br>- Active alerts count<br>- Auto-refresh every 30 seconds |
| US-042 | As a User, I want to toggle dark/light mode so I can work comfortably in different lighting | P1 | - Toggle in settings<br>- Persist preference<br>- Smooth transition |
| US-043 | As a Manager, I want a customizable dashboard so I can see the KPIs that matter to me | P1 | - Drag-and-drop widgets<br>- Save dashboard layouts<br>- Multiple dashboard support |

---

### 3.10b Energy Wastage Dashboard (NEW)

> **This is a CRITICAL feature for v1.0** - Shows users exactly how much money they're wasting and what to fix.

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-041B | As a Plant Manager, I want to see total energy wastage in rupees so I know the financial impact | P0 | - Display total waste in ₹ for today/week/month<br>- Show trend vs previous period<br>- Works for ALL machine types |
| US-042B | As a Plant Manager, I want to see units wasted in kWh so I can track energy waste | P0 | - Display wasted kWh for today/week/month<br>- Show breakdown by source |
| US-043B | As a Plant Manager, I want to see idle running cost so I can identify machines running unnecessarily | P0 | - Detect idle: power > 0 OR power < 30% of rated power<br>- Calculate idle hours, kWh, and cost<br>- Show top idle machines |
| US-044B | As a Maintenance Engineer, I want to see pressure-related waste if pressure sensor exists | P1 | - Calculate waste if pressure > optimal<br>- 7% energy penalty per bar over optimal<br>- Only show if pressure data available |
| US-045B | As a Plant Manager, I want an efficiency score so I know how well my machines are performing | P0 | - Calculate: optimal_kwh / actual_kwh<br>- Display as percentage<br>- Color code: 0-60% 🔴 Poor, 60-80% 🟡 Moderate, 80-95% 🟢 Good, 95%+ 🟢 Excellent |
| US-046B | As a Plant Manager, I want a "What to Fix Today" list so I know immediate actions | P0 | - Rank issues by wastage amount<br>- Show top 5 fixes needed<br>- Include potential savings for each fix |
| US-047B | As a Plant Manager, I want waste source breakdown so I understand WHERE money is going | P0 | - Show breakdown: Idle Waste, Pressure Waste, Peak Hour Waste, etc.<br>- Display as bar chart with percentages<br>- Show ₹ amount for each source |

#### Energy Wastage Engine Specification

**Input:**
```json
{
  "power_series": [{"timestamp": "...", "power_w": 5000}, ...],
  "total_kwh": 1500,
  "runtime_hours": 24,
  "tariff_rate": 8.5,
  "device_metadata": {
    "device_id": "MACHINE-001",
    "device_type": "compressor",
    "rated_power": 15000
  },
  "pressure_series": [{"timestamp": "...", "pressure": 7.5}, ...] // optional
}
```

**Output:**
```json
{
  "wasted_kwh": 450,
  "wasted_rupees": 3825,
  "optimal_kwh": 1050,
  "actual_kwh": 1500,
  "efficiency_score": 70,
  "efficiency_grade": "Moderate",
  "idle_waste_kwh": 180,
  "idle_waste_rupees": 1530,
  "idle_hours": 4.5,
  "pressure_waste_kwh": 0, // if pressure sensor exists
  "breakdown": [
    {"source": "idle_running", "kwh": 180, "rupees": 1530, "percentage": 40},
    {"source": "peak_hours", "kwh": 150, "rupees": 1275, "percentage": 33},
    {"source": "inefficiency", "kwh": 120, "rupees": 1020, "percentage": 27}
  ],
  "recommendations": [
    {"action": "Check for idle running", "potential_savings": 1530, "priority": "high"},
    {"action": "Optimize peak hour usage", "potential_savings": 1275, "priority": "medium"}
  ]
}
```

**Formulas:**

1. **Optimal Energy Calculation (Universal)**
   ```
   optimal_avg_kw = percentile(power_series, 25)  // Bottom 25% = most efficient
   optimal_kwh = optimal_avg_kw × runtime_hours
   ```

2. **Wastage Calculation**
   ```
   wasted_kwh = max(actual_kwh - optimal_kwh, 0)
   wasted_rupees = wasted_kwh × tariff_rate
   ```

3. **Efficiency Score**
   ```
   efficiency = (optimal_kwh / actual_kwh) × 100
   Clamp to 0-100%
   Grade: 0-60% Poor, 60-80% Moderate, 80-95% Good, 95%+ Excellent
   ```

4. **Idle Detection**
   ```
   If production_signal available:
     idle = power > 0.2 × rated_power AND production_signal == 0
   Else:
     idle = power < 0.3 × rated_power
   ```

5. **Pressure Waste (if available)**
   ```
   If pressure > optimal_pressure:
     extra_bar = pressure - optimal_pressure
     pressure_waste_kwh = total_kwh × 0.07 × extra_bar
   ```

#### UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚡ ENERGY WASTAGE DASHBOARD              [Today ▼] [Week] [Month] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │ 💸 WASTAGE  │ │ ⚡ UNITS     │ │ 📈 EFFICIENCY│ │ 🔧 SCORE  │ │
│  │  ₹45,230/mo │ │  5,320 kWh  │ │    71%      │ │  🟡 71    │ │
│  │  ↑ +₹12,400 │ │  this month │ │ 🟡 Moderate │ │  / 100    │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 🔍 WHAT TO FIX TODAY (Ranked by Potential Savings)             │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ 1. 🟠 Idle Running on Compressor-001     Save ₹1,530/mo      │ │
│  │ 2. 🔴 High Pressure on Compressor-003    Save ₹2,100/mo      │ │
│  │ 3. 🟡 Peak Hour Usage on Motor-002       Save ₹1,275/mo       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 💰 WASTE BREAKDOWN                                            │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │                                                                │ │
│  │ Idle Running     ████████████░░  32%  ₹14,400               │ │
│  │ Peak Hours      ██████████░░░░░  25%  ₹11,250               │ │
│  │ Over Pressure   ████████░░░░░░░  20%  ₹9,000                │ │
│  │ Inefficiency   ██████░░░░░░░░░  15%  ₹6,750                 │ │
│  │ Other          ████░░░░░░░░░░░░   8%  ₹3,600                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

#### Implementation Plan

1. **Backend: wastage_engine.py** (NEW)
   - Create in reporting-service
   - Accept power_series, total_kwh, runtime_hours, tariff
   - Return wastage metrics and breakdown

2. **Backend: New API Endpoint**
   ```
   GET /api/v1/reports/wastage?device_id=...&period=month
   ```

3. **Frontend: New Dashboard Page**
   - `/wastage` route
   - Summary cards
   - Waste breakdown chart
   - "What to Fix Today" list
   - Period selector (Today/Week/Month)

4. **Integration**
   - Reuse existing energy_engine.py
   - Call wastage_engine with power data
   - Display in dedicated dashboard

---

### 3.11 Notification Center

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-044 | As a User, I want a notification bell so I can see all my alerts in one place | P0 | - Bell icon in header<br>- Unread count badge<br>- Dropdown with recent alerts |
| US-045 | As a User, I want to mark notifications as read/unread so I can track what I've seen | P0 | - Click to mark read<br>- "Mark all as read" button |
| US-046 | As a User, I want notification history so I can review past alerts | P1 | - View last 30 days<br>- Filter by device/severity<br>- Search functionality |
| US-047 | As a User, I want to configure notification preferences so I choose how I'm notified | P1 | - Choose channels per alert type<br>- Set quiet hours<br>- Enable/disable by severity |

---

### 3.12 Device Management Enhancements

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-048 | As an Admin, I want to bulk import devices via CSV so I can add many machines quickly | P1 | - Upload CSV file<br>- Map columns to fields<br>- Preview before import<br>- Show success/error count |
| US-049 | As a Manager, I want to group devices so I can organize machines by area/line | P1 | - Create groups (e.g., "Assembly Line 1", "Compressors")<br>- Assign devices to groups<br>- Filter by group |
| US-050 | As an Admin, I want device templates so I can pre-configure health params for common machine types | P1 | - Create template (e.g., "Compressor Template")<br>- Template includes: shift config, health params with weights<br>- Apply template to new devices |
| US-051 | As an Admin, I want to duplicate device configuration so I can set up similar machines quickly | P1 | - Clone shifts from one device to another<br>- Clone health config from one device to another |

---

### 3.13 Advanced Reporting

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-052 | As a Manager, I want to create custom reports so I can define my own metrics | P1 | - Select metrics to include<br>- Choose grouping (device/day/week)<br>- Save report template |
| US-053 | As a Manager, I want report templates so I can quickly generate common reports | P1 | - Pre-built templates: Daily Summary, Weekly Analysis, Monthly Compliance<br>- One-click generation |
| US-054 | As a Manager, I want scheduled email delivery so reports are sent automatically | P1 | - Configure recipients<br>- Set schedule (daily/weekly/monthly)<br>- Attach PDF/CSV |

---

### 3.14 Data Management

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-055 | As an Admin, I want to configure data retention so old data is automatically managed | P1 | - Set retention period (e.g., 90 days for telemetry)<br>- Auto-archive before deletion<br>- Archive to S3 |
| US-056 | As an Admin, I want to backup/restore configuration so I can recover from disasters | P1 | - Export all configs to JSON<br>- Import from JSON<br>- Include devices, rules, schedules |
| US-057 | As an Admin, I want audit logs so I can track who changed what | P1 | - Log: user, action, timestamp, old/new values<br>- View in admin panel<br>- Filter by date/action |
| US-058 | As a User, I want to search across all data so I can find information quickly | P1 | - Global search bar<br>- Search devices, rules, reports<br>- Recent searches |

---

### 3.15 System Monitoring (Admin)

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|---------------------|
| US-059 | As an Admin, I want system health dashboard so I can monitor the platform | P1 | - CPU, Memory, Disk usage<br>- Service status (running/stopped)<br>- Database connections |
| US-060 | As an Admin, I want API usage analytics so I can see which endpoints are popular | P2 | - Request count per endpoint<br>- Response times<br>- Error rates |
| US-061 | As an Admin, I want error rate alerts so I know if something is wrong | P1 | - Configure error threshold<br>- Email/webhook notification |

---

## 4. Functional Requirements

### 4.1 Device Management

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-001 | Device CRUD | System shall allow Create, Read, Update, Delete operations for devices |
| FR-002 | Device Fields | Each device shall have: device_id, device_name, device_type, location, status |
| FR-003 | Auto Status | System shall automatically calculate device status based on last_seen timestamp |
| FR-004 | Device Properties | System shall support dynamic properties (no hardcoded fields) |

### 4.2 Shift Configuration

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-005 | Multiple Shifts | System shall support multiple shifts per device |
| FR-006 | Shift Fields | Each shift shall have: name, start_time, end_time, maintenance_break_minutes, day_of_week |
| FR-007 | Uptime Calculation | System shall calculate uptime as: ((planned_minutes - break_minutes) / planned_minutes) × 100 |

### 4.3 Health Configuration

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-008 | Parameter Config | System shall allow configuration of health parameters per device |
| FR-009 | Range Settings | Each parameter shall have: normal_min, normal_max, max_min, max_max |
| FR-010 | Weight Validation | System shall validate that weights sum to 100% |
| FR-011 | Health States | System shall only calculate health when machine_state is RUNNING |

### 4.4 Health Score Formula

```
SCORE CALCULATION:

Normal Range (value between normal_min and normal_max):
  ideal_center = (normal_min + normal_max) / 2
  half_range = (normal_max - normal_min) / 2
  raw_score = 100 - (|value - ideal_center| / half_range) × 30
  raw_score = clamp(raw_score, 70, 100)

Max Range (value between max_min and max_max):
  if value < normal_min:
    overshoot = normal_min - value
    tolerance = normal_min - max_min
    raw_score = 70 - (overshoot / tolerance) × 45
  else:
    overshoot = value - normal_max
    tolerance = max_max - normal_max
    raw_score = 70 - (overshoot / tolerance) × 45
  raw_score = clamp(raw_score, 25, 69)

Beyond Max:
  raw_score = max(0, 25 - overshoot × 10)

Final Health Score = Σ(raw_score × weight / 100) for all parameters
```

### 4.5 Telemetry

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-012 | MQTT Ingestion | System shall receive telemetry via MQTT protocol |
| FR-013 | Topic Pattern | Telemetry shall be on topic `telemetry/{device_id}` |
| FR-014 | Data Enrichment | System shall enrich telemetry with device metadata |
| FR-015 | InfluxDB Storage | System shall store telemetry in InfluxDB |
| FR-016 | Real-time Stream | System shall broadcast telemetry via WebSocket |
| FR-017 | Refresh Rate | Live telemetry shall refresh every 1 second |

### 4.6 Analytics (ML)

#### 4.6.1 Anomaly Detection

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-028 | Supported Algorithms | System shall support: Isolation Forest, Autoencoder |
| FR-028a | Isolation Forest | Detect anomalies using tree-based isolation |
| FR-028b | Autoencoder | Detect anomalies using neural network reconstruction error |
| FR-029 | Parameter Selection | User shall select which parameters to analyze |
| FR-030 | Anomaly Scoring | Each data point shall get an anomaly score (-1 to 1) |
| FR-031 | Context Generation | System shall generate human-readable context for each anomaly |
| FR-032 | Trend Analysis | System shall show anomaly frequency over time |
| FR-033 | Parameter Attribution | System shall identify which parameter caused the anomaly |

#### 4.6.2 Failure Prediction

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-034 | Supported Algorithms | System shall support: Random Forest, Gradient Boosting |
| FR-035 | Risk Score | System shall output failure risk as percentage (0-100%) |
| FR-036 | Confidence Level | System shall show confidence based on data quality |
| FR-037 | Time Forecast | System shall predict risk for next 7 and 30 days |
| FR-038 | Factor Attribution | System shall identify top contributing factors |
| FR-039 | Recommendations | System shall provide actionable maintenance recommendations |

#### 4.6.3 User Experience

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-040 | Plain Language | Results shall be presented in non-technical language |
| FR-041 | Visual Indicators | Use color coding: GREEN (safe), YELLOW (warning), RED (critical) |
| FR-042 | Confidence Display | Show confidence as "High/Medium/Low" with explanation |
| FR-043 | Action Buttons | Each insight shall have related action button |
| FR-044 | Progress Indication | Show analysis progress for long-running jobs |
| FR-045 | Result Caching | Cache results for 1 hour to avoid re-computation |

### 4.7 Data Export

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-046 | Format Support | System shall support CSV and JSON export |
| FR-047 | Date Range | Maximum export range shall be 90 days |
| FR-048 | Multi-Device | Support exporting data for multiple devices |
| FR-049 | Progress Tracking | Show progress for large exports (>10MB) |
| FR-050 | Download Link | Provide downloadable link valid for 24 hours |

### 4.6 Rules & Alerts

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-018 | Rule Scope | Rules shall support "all_devices" or "selected_devices" scope |
| FR-019 | Conditions | Rules shall support: >, <, =, !=, >=, <= |
| FR-020 | Cooldown | System shall respect cooldown period between alerts |
| FR-021 | Alert Status | Alerts shall have lifecycle: OPEN → ACKNOWLEDGED → RESOLVED |
| FR-022 | Notification Channels | System shall support: Email, SMS, Webhook |

### 4.7 Reports

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-023 | Date Range | Reports shall support 1-90 days range |
| FR-024 | Device Selection | Reports shall support single or multiple devices |
| FR-025 | Grouping | Reports shall support Daily and Weekly grouping |
| FR-026 | Load Factor | System shall calculate load factor with classification |
| FR-027 | Export Formats | Reports shall export as PDF and CSV |

### 4.8 Analytics

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-028 | Anomaly Detection | System shall detect anomalies using Isolation Forest |
| FR-029 | Failure Prediction | System shall predict failures using Random Forest |
| FR-030 | Async Processing | ML jobs shall run asynchronously |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | API Response Time | < 200ms (p95) |
| NFR-002 | Telemetry Throughput | 10,000 messages/second |
| NFR-003 | WebSocket Latency | < 100ms |
| NFR-004 | Report Generation | < 60 seconds |
| NFR-005 | ML Analysis | < 5 minutes |

### 5.2 Availability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-006 | System Uptime | 99.9% |
| NFR-007 | Recovery Time | < 15 minutes |
| NFR-008 | Data Loss | Zero (DLQ protection) |

### 5.3 Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-009 | Device Capacity | 1000+ concurrent devices |
| NFR-010 | Telemetry Rate | Support 1 message/second per device |
| NFR-011 | Concurrent Users | Support 50+ concurrent users |

### 5.4 Security

| ID | Requirement | Description |
|----|-------------|-------------|
| NFR-012 | Encryption in Transit | TLS 1.3 for all connections |
| NFR-013 | Encryption at Rest | AES-256 for database and S3 |
| NFR-014 | Network Isolation | VPC with private subnets |

---

## 6. User Interface Requirements

### 6.1 Navigation

- **Sidebar** with sections: Machines, Analytics, Reports, Rules, Settings
- **Breadcrumb** navigation for deep pages
- **Responsive** design for desktop, tablet, mobile

### 6.2 Machines Page

- Grid/card layout showing all devices
- Each card displays:
  - Device name
  - Device type
  - Location
  - Last seen (relative time)
  - Status badge (RUNNING/STANDBY/STOPPED/ERROR)
- Auto-refresh every 10 seconds

### 6.3 Machine Dashboard

**Tabs:**
1. **Overview** - KPIs, health score, uptime, parameters
2. **Telemetry** - Live data with 1-second refresh
3. **Charts** - Historical time-series charts
4. **Alerts** - Device-specific alerts
5. **Analytics** - ML analysis for this device
6. **Configuration** - Shift and parameter settings

### 6.4 Forms

- Shift Configuration:
  - Shift Name (text)
  - Start Time (time picker)
  - End Time (time picker)
  - Maintenance Break (number, minutes)
  - Day of Week (multi-select)

- Parameter Health Config:
  - Parameter Name (dropdown)
  - Normal Min/Max (number)
  - Max Min/Max (number)
  - Weight (number)
  - Ignore Zero (checkbox)

- Rule Creation:
  - Rule Name (text)
  - Scope (radio: All Devices / Selected Devices)
  - Device Selection (multi-select, if selected)
  - Property (dropdown, dynamic)
  - Condition (dropdown: >, <, =, !=, >=, <=)
  - Threshold (number)
  - Notification Channels (checkboxes: Email, SMS, Webhook)
  - Cooldown (number, minutes)

### 6.5 Reports UI

**Energy Consumption Report:**
- Date Range Selector (presets: Today, Yesterday, Last 7 Days, Last 30 Days, Last 90 Days, Custom)
- Device Multi-select
- Group By (Daily/Weekly)
- Generate Button
- Results: Cards for key metrics, chart for daily series, download buttons

**Comparative Analysis:**
- Comparison Type (Machine vs Machine / Period vs Period)
- Machine/Period selectors
- Results: Side-by-side comparison table

---

## 7. Technical Requirements

### 7.1 Data Retention

| Data Type | Retention Period | Storage |
|-----------|-----------------|---------|
| Telemetry | 90 days | InfluxDB |
| Devices | Indefinite | MySQL |
| Rules | Indefinite | MySQL |
| Alerts | 1 year | MySQL |
| Reports | 90 days | S3 |

### 7.2 API Requirements

- RESTful API design
- JSON request/response format
- Versioned endpoints (`/api/v1/`)
- OpenAPI/Swagger documentation
- Rate limiting: 1000 req/min (GET), 100 req/min (POST)

### 7.3 Integration Points

| Integration | Protocol | Purpose |
|-------------|----------|---------|
| MQTT Broker | MQTT :1883 | Telemetry ingestion |
| Email | SMTP | Alert notifications |
| SMS | AWS SNS | SMS notifications |
| Webhook | HTTPS POST | External alerts |
| S3 | AWS S3 API | Report storage |

---

## 8. Edge Cases

| Scenario | Handling |
|----------|----------|
| No shifts configured | Display 0% uptime, show message |
| Weights don't sum to 100% | Show validation error, don't calculate health |
| Machine not sending telemetry | Show "Standby" status after 5 minutes |
| Zero value in parameter | Check "Ignore Zero" flag, skip if enabled |
| Rule with no matching devices | Show warning, allow save but won't trigger |
| Report with no data | Show "No data available" message |
| WebSocket disconnect | Auto-reconnect with exponential backoff |
| MQTT broker down | Queue messages locally, retry on reconnect |

---

## 9. Success Metrics

### 9.1 Product Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| Active Users | 50+ | Daily active users |
| Devices Onboarded | 1000+ | Total devices registered |
| Alerts Delivered | 99% | Successful notification delivery |
| Report Generation | 95% | Success rate |

### 9.2 Technical Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Uptime | 99.9% | CloudWatch |
| Response Time | < 200ms | APM logs |
| Data Freshness | < 2 seconds | Telemetry to dashboard |

---

## 10. Out of Scope & Future Versions

### v1.0 Now Includes (Enhanced)
The following have been ADDED to v1.0 scope based on requirements:
- ✅ In-App Notification Center
- ✅ Dashboard KPI Cards
- ✅ Dark/Light Mode
- ✅ Customizable Dashboard
- ✅ Bulk Device Import (CSV)
- ✅ Device Groups
- ✅ Device Templates
- ✅ Custom Report Builder
- ✅ Report Templates
- ✅ Scheduled Email Reports
- ✅ Data Retention Policies
- ✅ Backup/Restore Configuration
- ✅ Audit Logging
- ✅ Global Search
- ✅ System Health Dashboard

### v1.0 Still Out of Scope
The following are NOT included in v1.0:

- [ ] User authentication and login
- [ ] Role-based access control (RBAC)
- [ ] Multi-tenancy with isolation
- [ ] Mobile app (native)
- [ ] Invoice/billing

### v2.0 Future Features
The following are planned for version 2.0:

- [ ] OPC-UA integration (connect to PLCs)
- [ ] Modbus protocol support (connect to industrial equipment)
- [ ] Real-time video streaming
- [ ] Spare parts inventory management
- [ ] Work order management
- [ ] Advanced maintenance scheduling with calendar
- [ ] REST API for external partners
- [ ] Power BI / Tableau integration

---

## 11. Analytics UI - Detailed Requirements

### 11.1 User Experience Philosophy

The Analytics module shall follow these principles:

1. **Context Over Raw Data**: Always provide context - not just "temperature is high" but "temperature is 85°C which is 40% above normal range of 20-60°C"

2. **Reasoning Over Results**: Explain WHY the system thinks something is an anomaly or failure risk - show the reasoning chain

3. **Actionability**: Every insight should have a clear next step - create alert, schedule maintenance, investigate further

4. **Accessibility**: Non-technical users should understand without reading documentation

### 11.2 Analytics Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Analytics                                                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  Anomaly    │ │  Failure    │ │  Data       │               │
│  │  Detection  │ │  Prediction │ │  Export     │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Machine: [Dropdown - Select Machine]                      │ │
│  │  Date Range: [Last 7 days ▼]  [Custom Range]              │ │
│  │  Parameters: [☐ Power ☐ Voltage ☐ Temperature ☐ ...]    │ │
│  │                                                             │ │
│  │                         [Run Analysis]                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  RESULTS (appears after analysis)                         │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Summary Card                                      │  │ │
│  │  │  🔴 3 Anomalies Found                              │  │ │
│  │  │  Most affected: Temperature (2), Voltage (1)       │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Anomaly Timeline (chart)                           │  │ │
│  │  │  ▁▂▃▅▇▅▃▂▁▂▃▅▇▅ (visual timeline)                │  │ │
│  │  │         ↑        ↑                                  │  │ │
│  │  │        anomaly anomaly                              │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                                                            │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Detailed Findings                                 │  │ │
│  │  │                                                      │  │ │
│  │  │  1. Temperature Spike - Critical                   │  │ │
│  │  │     📅 Feb 20, 2026 at 14:30                      │  │ │
│  │  │     🌡️ Temperature: 85°C (normal: 20-60°C)        │  │ │
│  │  │     💡 Context: 42% above upper normal limit     │  │ │
│  │  │     🔧 Possible cause: Coolant low / Sensor issue │  │ │
│  │  │     [Create Alert] [View Telemetry]               │  │ │
│  │  │                                                      │  │ │
│  │  │  2. Voltage Fluctuation - Warning                  │  │ │
│  │  │     📅 Feb 18-19, 2026                            │  │ │
│  │  │     ⚡ Voltage: 245-260V (normal: 210-240V)       │  │ │
│  │  │     💡 Context: 8 instances of overvoltage        │  │ │
│  │  │     🔧 Possible cause: Grid instability            │  │ │
│  │  │     [Create Alert] [View Telemetry]               │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 11.3 Failure Prediction Results Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Failure Prediction Results                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RISK ASSESSMENT                                        │   │
│  │                                                          │   │
│  │  ┌─────────────────┐ ┌─────────────────┐               │   │
│  │  │  7-Day Risk    │ │  30-Day Risk    │               │   │
│  │  │  ████████░░ 75%│ │  ██████████ 92%│               │   │
│  │  │  🔴 HIGH       │ │  🔴 VERY HIGH  │               │   │
│  │  │  Confidence: 78%│ │  Confidence: 82%│               │   │
│  │  └─────────────────┘ └─────────────────┘               │   │
│  │                                                          │   │
│  │  "Based on current trends, there is a 75% chance of     │   │
│  │   failure within the next 7 days if no action is taken" │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RISK FACTORS (ranked by impact)                       │   │
│  │                                                          │   │
│  │  1. 🔴 Temperature Trend (35% contribution)            │   │
│  │     → Temperature increased 15% over last 30 days     │   │
│  │     → Currently at 68°C, approaching danger zone       │   │
│  │                                                          │   │
│  │  2. 🟡 Voltage Fluctuations (25% contribution)         │   │
│  │     → 12 instances of voltage > 245V in last 7 days   │   │
│  │     → Could stress motor components                   │   │
│  │                                                          │   │
│  │  3. 🟢 Power Consumption (15% contribution)           │   │
│  │     → Normal patterns, no concerns                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  RECOMMENDED ACTIONS                                    │   │
│  │                                                          │   │
│  │  1. 🔧 Schedule maintenance within 3 days              │   │
│  │     → Replace coolant and check temperature sensor      │   │
│  │     → Estimated downtime: 2 hours                      │   │
│  │     [Schedule Maintenance]                             │   │
│  │                                                          │   │
│  │  2. ⚡ Check electrical supply                         │   │
│  │     → Investigate voltage fluctuations                 │   │  
│  │     → May require utility company coordination         │   │
│  │     [Create Alert Rule]                                │   │
│  │                                                          │   │
│  │  3. 📊 Increase monitoring frequency                   │   │
│  │     → Change telemetry from 1s to 500ms interval       │   │
│  │     [Update Device Config]                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 11.4 Analytics API Response Format

```json
{
  "job_id": "uuid",
  "status": "completed",
  "completed_at": "2026-02-26T10:30:00Z",
  "results": {
    "type": "anomaly_detection",
    "summary": {
      "total_anomalies": 3,
      "severity": {
        "critical": 1,
        "warning": 2,
        "info": 0
      },
      "most_affected_parameters": ["temperature", "voltage"]
    },
    "anomalies": [
      {
        "id": 1,
        "timestamp": "2026-02-20T14:30:00Z",
        "severity": "critical",
        "parameter": "temperature",
        "value": 85,
        "normal_range": {"min": 20, "max": 60},
        "context": "42% above upper normal limit",
        "possible_causes": ["Coolant low", "Sensor issue", "Overloading"],
        "recommendation": "Check coolant levels and temperature sensor calibration"
      }
    ],
    "timeline": [
      {"date": "2026-02-15", "count": 0},
      {"date": "2026-02-16", "count": 0},
      {"date": "2026-02-17", "count": 1}
    ]
  },
  "confidence": {
    "score": 85,
    "level": "high",
    "factors": ["Sufficient data points (10,500)", "Stable parameter ranges"]
  }
}
```

### 11.5 Error Handling

| Scenario | User Message | Action |
|----------|--------------|--------|
| Not enough data | "We need at least 7 days of data to analyze. You have 3 days. Continue collecting data and try again." | Disable run button, show data requirement |
| Analysis fails | "Something went wrong while analyzing. Our team has been notified. Please try again in 5 minutes." | Show retry button |
| No anomalies found | "Great news! No anomalies detected in the selected period. Your machine is operating within normal parameters." | Show positive message |
| All machines at low risk | "All machines are showing low failure risk. Continue monitoring as usual." | Show green status |

---

**End of Analytics Requirements**

---

## 11. Dependencies

### 11.1 Internal Dependencies

| Feature | Depends On |
|---------|-----------|
| Health Score | Shift Config, Parameter Config |
| Rules | Devices |
| Alerts | Rules |
| Reports | Telemetry (InfluxDB) |
| ML Analytics | Telemetry |

### 11.2 External Dependencies

| Service | Purpose |
|---------|---------|
| AWS SES | Email notifications |
| AWS SNS | SMS notifications |
| AWS InfluxDB | Time-series storage |
| EMQX | MQTT broker |

---

## 12. Glossary

| Term | Definition |
|------|------------|
| **Telemetry** | Real-time data sent by machines (voltage, temperature, pressure, etc.) |
| **Health Score** | Calculated value (0-100%) indicating machine health |
| **Uptime** | Percentage of time machine was available during shifts |
| **Rule** | Condition that triggers alert when threshold is crossed |
| **Alert** | Notification created when rule condition is met |
| **Load Factor** | Ratio of average load to peak load (efficiency metric) |
| **Anomaly** | Unusual pattern detected in telemetry data |
| **DLQ** | Dead Letter Queue for failed message processing |

---

**Document Approval**

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Manager | [Pending] | | |
| Technical Lead | [Pending] | | |
| Engineering Manager | [Pending] | | |

---

**End of Document**

