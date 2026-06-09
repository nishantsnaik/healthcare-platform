# Healthcare Clinical Communication & Intelligent Alert Routing Platform

A production-style FastAPI application simulating clinical alert workflows used by hospitals and health systems. Features LLM-powered alert summarization, async processing, WebSocket notifications, and Kafka-based event streaming.

---

## Project Structure

```
healthcare-platform/
├── main.py                          # App entry point, lifespan, router registration
├── docker-compose.yml               # Kafka, Redis, PostgreSQL, Celery worker
├── Dockerfile                       # Celery worker container
├── requirements.txt
├── .env                             # API keys — never commit
├── .gitignore
└── app/
    ├── routers/
    │   └── alerts.py                # POST, GET, PATCH /alerts
    ├── services/
    │   └── llm_service.py           # OpenAI GPT-4o summarization
    ├── tasks/
    │   └── escalation.py            # Celery task for alert escalation
    ├── models/
    │   ├── alert.py                 # Alert, AlertCreate, AlertUpdate + enums
    │   ├── alert_db.py              # SQLAlchemy database model
    │   ├── patient.py               # Patient, PatientCreate + enums
    │   ├── caregiver.py             # Caregiver, CaregiverCreate + enums
    │   ├── assignment.py            # Assignment, AssignmentCreate
    │   └── message.py              # Message, MessageCreate + enums
    ├── repositories/
    │   ├── alerts.py                # Alert repository with database operations
    │   └── assignment.py            # Assignment repository
    └── core/
        ├── celery_app.py            # Celery app configuration
        ├── config.py                # Centralized settings with pydantic-settings
        ├── database.py              # Async (FastAPI) and sync (Celery) database sessions
        ├── kafka_producer.py        # aiokafka async producer
        └── websocket_manager.py     # ConnectionManager for real-time push
```

---

## Quick Start

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
# .env
OPENAI_API_KEY=your_openai_key_here
ESCALATION_NURSE_DELAY=30
ESCALATION_CHARGE_NURSE_DELAY=60
ESCALATION_PHYSICIAN_DELAY=90
DATABASE_URL=postgresql+asyncpg://healthcare:healthcare@localhost:5432/healthcare
```

### 4. Start infrastructure

```bash
docker-compose up -d
```

### 5. Create Kafka topic

```bash
docker exec kafka kafka-topics \
    --create \
    --topic healthcare.alerts.created \
    --bootstrap-server localhost:9092 \
    --partitions 1 \
    --replication-factor 1
```

### 6. Run the app

```bash
.venv/bin/uvicorn main:app --reload
```

### 7. Start Celery worker (in separate terminal)

```bash
.venv/bin/celery -A app.core.celery_app worker --loglevel=info
```

### 8. Open Swagger UI

```
http://localhost:8000/docs
```

---

## Docker Commands

### Start all containers

```bash
docker-compose up -d
```

### Stop all containers

```bash
docker-compose down
```

### Check running containers

```bash
docker ps
```

### View Kafka logs

```bash
docker logs kafka
```

### View Redis logs

```bash
docker logs healthcare-platform-redis-1
```

### Kafka — list topics

```bash
docker exec kafka kafka-topics \
    --list \
    --bootstrap-server localhost:9092
```

### Kafka — create topic

```bash
docker exec kafka kafka-topics \
    --create \
    --topic healthcare.alerts.created \
    --bootstrap-server localhost:9092 \
    --partitions 1 \
    --replication-factor 1
```

### Kafka — consume messages (debug)

```bash
docker exec kafka kafka-console-consumer \
    --topic healthcare.alerts.created \
    --bootstrap-server localhost:9092 \
    --from-beginning
```

### Kafka — describe topic

```bash
docker exec kafka kafka-topics \
    --describe \
    --topic healthcare.alerts.created \
    --bootstrap-server localhost:9092
```

### Redis — connect CLI

```bash
docker exec -it healthcare-platform-redis-1 redis-cli
```

### Redis — check all keys

```bash
docker exec healthcare-platform-redis-1 redis-cli keys "*"
```

### PostgreSQL — connect CLI

```bash
docker exec -it healthcare-platform-postgres-1 psql -U healthcare -d healthcare
```

### PostgreSQL — view tables

```bash
docker exec healthcare-platform-postgres-1 psql -U healthcare -d healthcare -c "\dt"
```

### Celery worker — view logs

```bash
docker logs healthcare-platform-celery_worker-1
```

---

## API Reference

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0",
  "timestamp": "2026-06-05T01:16:56.077840"
}
```

---

### Create Alert

```
POST /alerts/
```

Request body:
```json
{
  "patient_id": 1001,
  "alert_type": "sepsis alert",
  "priority": "critical",
  "status": "new",
  "bed": "4",
  "unit": "ICU"
}
```

Response:
```json
{
  "patient_id": 1001,
  "alert_type": "sepsis alert",
  "priority": "critical",
  "status": "new",
  "bed": "4",
  "unit": "ICU",
  "id": 1,
  "llm_summary": null,
  "llm_priority_suggestion": null,
  "acknowledged_at": null,
  "created_at": "2026-06-05T01:16:56.077840",
  "updated_at": null
}
```

Note: `llm_summary` starts as `null` and is populated asynchronously by GPT-4o in the background.

---

### Get Alert (with LLM summary)

```
GET /alerts/{alert_id}
```

Response (after LLM background task completes):
```json
{
  "patient_id": 1001,
  "alert_type": "sepsis alert",
  "priority": "critical",
  "status": "new",
  "bed": "4",
  "unit": "ICU",
  "id": 1,
  "llm_summary": "New sepsis alert for patient in ICU bed 4, indicating a potential septic condition that needs immediate clinical evaluation.",
  "llm_priority_suggestion": "critical",
  "acknowledged_at": null,
  "created_at": "2026-06-05T01:16:56.077840",
  "updated_at": null
}
```

---

### Acknowledge Alert

```
PATCH /alerts/{alert_id}
```

Request body:
```json
{
  "status": "acknowledged"
}
```

Response:
```json
{
  "patient_id": 1001,
  "alert_type": "sepsis alert",
  "priority": "critical",
  "status": "acknowledged",
  "bed": "4",
  "unit": "ICU",
  "id": 1,
  "llm_summary": "New sepsis alert for patient in ICU bed 4...",
  "llm_priority_suggestion": "critical",
  "acknowledged_at": "2026-06-05T01:20:00.000000",
  "created_at": "2026-06-05T01:16:56.077840",
  "updated_at": null
}
```

---

## Sample Alert Types

| alert_type | Description |
|---|---|
| `sepsis alert` | Systemic infection risk — critical priority |
| `critical lab` | Abnormal lab result (e.g. potassium 2.4) |
| `fall risk` | Patient fall risk assessment triggered |
| `medication overdue` | Scheduled medication not administered |
| `abnormal vitals` | Vitals outside normal range |

---

## Alert Priority Levels

| priority | When to use |
|---|---|
| `critical` | Immediate intervention — risk to life |
| `high` | Prompt review needed — significant risk if delayed |
| `medium` | Clinical attention required — not urgent |
| `low` | Informational — routine follow-up |

---

## Alert Status Lifecycle

```
new → acknowledged → (resolved via PATCH)
new → charge_nurse → physician → failsafe (auto-escalated after configurable delays)
```

---

## Data Models

### Alert enums

```python
AlertType:     sepsis alert, critical lab, fall risk, medication overdue, abnormal vitals
AlertPriority: critical, high, medium, low
AlertStatus:   new, acknowledged, escalated
```

### Patient enums

```python
PatientStatus: admitted, discharged, deceased
```

### Caregiver enums

```python
Role:         nurse, physician, care_coordinator, respiratory_therapist
Availability: onboarding, available, busy, off_duty
```

### Message enums

```python
MessageType: secure message, broadcast, team notification
```

---

## Architecture Decisions

| Decision | Choice | Reason |
|---|---|---|
| Alert routing | By bed/unit, not caregiver name | Caregiver-independent — survives shift changes |
| MRN format | Facility-prefixed (`MGH-100123`) | Prevents ID collision across hospitals |
| LLM call | Background task, not blocking | POST returns in <100ms, LLM runs async |
| Escalation engine | Celery with Redis | Reliable task queue with retry and scheduling |
| Database sessions | Async (FastAPI) + Sync (Celery) | FastAPI requires async, Celery requires sync |
| `end_datetime` on assignment | Required at creation | Enforces timebound, shift-based assignments |
| `is_active` on assignment | Not stored — computed | Single source of truth from start/end datetime |
| Alert storage | Repository pattern | Decouples router from data layer |
| WebSocket key | `caregiver_id:device_id` | Supports multi-device per caregiver |
| Kafka vs polling | Kafka (KRaft) | Event-driven, survives server restarts |
| Configuration | pydantic-settings | Type-safe, environment-based configuration |

---

## Key Design Patterns Used

- **Repository pattern** — data access isolated from business logic
- **Base → Create → Response** — Pydantic model inheritance
- **Compound keys** — facility-prefixed MRN
- **Single source of truth** — computed fields never stored
- **Async background tasks** — LLM calls non-blocking
- **Event-driven architecture** — Kafka for escalation triggers
- **Location-based routing** — alerts route to bed/unit not person

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o summarization |
| `ESCALATION_NURSE_DELAY` | Delay in seconds before escalating to nurse (default: 30) |
| `ESCALATION_CHARGE_NURSE_DELAY` | Delay in seconds before escalating to charge nurse (default: 60) |
| `ESCALATION_PHYSICIAN_DELAY` | Delay in seconds before escalating to physician (default: 90) |
| `DATABASE_URL` | PostgreSQL connection URL |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap servers (default: localhost:9092) |
| `REDIS_URL` | Redis connection URL (default: redis://localhost:6379/0) |

---

## Ports

| Service | Port |
|---|---|
| FastAPI | 8000 |
| Kafka | 9092 |
| Redis | 6379 |
| PostgreSQL | 5432 |

---

## What's Built vs Remaining

### Done
- Pydantic models — all 5 entities
- Alert router — POST, GET, PATCH
- LLM summarization — GPT-4o async background task
- Repository pattern — alert_repository.py
- WebSocket manager — ConnectionManager
- Kafka producer — aiokafka async
- Docker infrastructure — Kafka KRaft + Redis + PostgreSQL
- Celery escalation engine — auto-escalation through charge_nurse → physician → failsafe
- Centralized configuration — pydantic-settings
- Async and sync database sessions — FastAPI (async) and Celery (sync)

### Remaining
- Care team directory endpoints
- Patient assignment endpoints
- Secure messaging endpoints
- Structured logging — structlog
- pytest test suite
- Architecture scaling document
