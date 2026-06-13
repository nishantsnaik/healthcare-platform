# Healthcare Clinical Communication Platform — Architecture Document

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Component Architecture](#2-component-architecture)
3. [Data Flow](#3-data-flow)
4. [Scaling Strategy](#4-scaling-strategy)
5. [Java/Spring Boot vs Python/FastAPI Mapping](#5-javaspring-boot-vs-pythonfastapi-mapping)
6. [HIPAA & Production Considerations](#6-hipaa--production-considerations)
7. [Interview Questions & Answers](#7-interview-questions--answers)

---

## 1. System Overview

The Healthcare Clinical Communication Platform receives clinical alerts from external monitoring systems and intelligently routes them to the correct caregiver in real time. Caregivers and physicians use the platform via mobile (iOS) and web interfaces to monitor patient alerts, acknowledge clinical events, and collaborate with care teams.

When an alert is received, the system identifies the currently assigned caregiver for that patient and delivers the alert immediately via WebSocket. If the caregiver does not acknowledge within defined time windows, the alert automatically escalates — first to a charge nurse, then to a physician, and finally to a hospital administrator as a failsafe. This ensures no critical clinical event goes unaddressed.

### Key Principles
- **Real-time delivery** — alerts reach caregivers in milliseconds via WebSocket
- **Guaranteed escalation** — Celery + Redis ensures escalation tasks survive server restarts
- **AI-powered triage** — GPT-4o generates clinical summaries and priority recommendations asynchronously
- **Event-driven** — Kafka decouples alert ingestion from downstream processing

---

## 2. Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                          │
│              (Engage, EHR, Lab Systems)                      │
└─────────────────────┬───────────────────────────────────────┘
                       │ POST /alerts
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Service                            │
│         REST endpoints, Pydantic validation,                 │
│         dependency injection, background tasks               │
└──────┬──────────┬──────────┬──────────┬────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│PostgreSQL│ │ Kafka  │ │ Redis  │ │  OpenAI      │
│          │ │        │ │        │ │  GPT-4o      │
│Persistent│ │Event   │ │Task    │ │              │
│storage   │ │stream  │ │queue   │ │LLM summary   │
│for all   │ │        │ │backend │ │+ priority    │
│entities  │ │        │ │        │ │              │
└──────────┘ └────────┘ └───┬────┘ └──────────────┘
                             │
                             ▼
                    ┌─────────────┐
                    │   Celery    │
                    │             │
                    │ Escalation  │
                    │ tasks at    │
                    │ 5/10/15 min │
                    └─────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │WebSocket Manager│
                    │                 │
                    │Real-time push   │
                    │to iOS + Web     │
                    └─────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| **FastAPI Service** | Entry point for all incoming clinical alerts. Exposes REST endpoints for alert creation, retrieval, and acknowledgment. |
| **PostgreSQL** | Persistent store for all alerts, assignments, caregivers, and escalation history. Single source of truth. |
| **Kafka** | Event streaming backbone. Publishes alert events so downstream consumers react independently without tight coupling. |
| **Redis** | Task queue backend for Celery. Persists scheduled escalation tasks across server restarts. |
| **Celery** | Distributed task executor. Picks up escalation tasks from Redis and executes them at correct time intervals. |
| **OpenAI GPT-4o** | Generates clinical summaries and priority recommendations for incoming alerts asynchronously. |
| **WebSocket Manager** | Maintains persistent connections to caregiver devices. Pushes real-time alert notifications to iOS and web clients. |

---

## 3. Data Flow

### Alert Lifecycle — Step by Step

```
Step 1:  External system (Engage) calls POST /alerts
         ↓
Step 2:  FastAPI validates request via Pydantic models
         Invalid → 422 Unprocessable Entity
         Valid   → continue
         ↓
Step 3:  Alert saved to PostgreSQL via repository layer
         escalation_level = "none"
         status = "new"
         ↓
Step 4:  Three Celery tasks scheduled in Redis:
         check_escalation(alert_id, countdown=300)   # T+5 min
         check_escalation(alert_id, countdown=600)   # T+10 min
         check_escalation(alert_id, countdown=900)   # T+15 min
         ↓
Step 5:  Alert event published to Kafka topic
         "healthcare.alerts.created"
         event = { alert_id, patient_id, created_at }
         ↓
Step 6:  LLM background task fires asynchronously:
         → Calls GPT-4o with alert context
         → Generates clinical summary + priority recommendation
         → Updates alert in PostgreSQL
         → Pushes updated alert to caregiver via WebSocket
         ↓
Step 7:  Caregiver receives alert on iOS/web in real time
         ↓
Step 8:  [T+5 min] If unacknowledged:
         Celery fires → escalation_level = "charge_nurse"
         Charge nurse notified
         ↓
Step 9:  [T+10 min] If still unacknowledged:
         Celery fires → escalation_level = "physician"
         Physician notified
         ↓
Step 10: [T+15 min] If still unacknowledged:
         Celery fires → escalation_level = "failsafe"
         Hospital administrator notified
```

### Why Kafka Decouples the System

The alert producer (FastAPI) doesn't care who consumes the event. Today it's the WebSocket manager. Tomorrow it could be:

```
→ SMS service
→ Pager system
→ EHR integration (Epic, Cerner)
→ Analytics pipeline
→ Compliance audit system
```

All without changing a single line in FastAPI. This is the core value of event-driven architecture.

---

## 4. Scaling Strategy

### 1 Hospital (~50 caregivers, ~200 alerts/day)

```
Infrastructure:
  1 FastAPI instance
  1 PostgreSQL instance + 1 read replica
  1 Kafka instance (KRaft, no Zookeeper)
  1 Redis instance
  2-3 Celery workers

Key decisions:
  ✓ Keep Kafka even at small scale
    → Cost of removing it later > cost of running it now
    → Architectural flexibility from day one
  ✓ Read replica for PostgreSQL
    → Separates read (dashboards) from write (alert creation)
  ✓ Single database schema
    → Simple, manageable at this scale
```

### 50 Hospitals (~2,500 caregivers, ~10,000 alerts/day)

```
Infrastructure:
  3 FastAPI instances behind load balancer
  PostgreSQL with schema-per-hospital isolation
  Kafka with partitions by hospital_id
  Redis for WebSocket pub/sub + Celery backend
  10-20 Celery workers

New challenges at this scale:

1. WebSocket cross-server delivery
   Problem:  Nurse on Server A, alert created on Server B
   Solution: Redis Pub/Sub
             Server B publishes to Redis channel
             Server A subscribes and delivers to nurse

2. Data isolation between hospitals
   Solution: Middleware validates X-Hospital-ID header
             Schema-per-hospital in PostgreSQL
             Every query scoped to hospital_id

3. Multi-tenancy
   Solution: Hospital isolation middleware on every request
             Prevents Hospital A from seeing Hospital B's data

Kafka organization:
  One topic: healthcare.alerts.created
  Partitioned by hospital_id
  → Each hospital's events processed independently
  → No noisy neighbor problem
```

### 500 Hospitals (~25,000 caregivers, ~100,000 alerts/day)

```
Infrastructure:
  10+ FastAPI instances (auto-scaled)
  PostgreSQL sharded (10 shards, 50 hospitals per shard)
  Confluent Cloud Kafka (managed, 500 topics)
  Redis Cluster (3 nodes)
  Celery with auto-scaling workers (min 5, max 50)
  Kubernetes orchestration

Scaling decisions:

1. Kafka → Confluent Cloud
   500 topics, one per hospital
   Managed service — no Kafka expertise needed
   BAA available for HIPAA compliance
   ~5-10ms additional latency — acceptable for clinical alerts

2. PostgreSQL → Horizontal Sharding
   500 schemas not manageable
   10 shards × 50 hospitals = balanced load
   Shard routing:
     shard = hospital_id % 10
     connect to shard_{n} database

3. Redis → Redis Cluster
   3 nodes, automatic slot assignment
   Hospitals 1-166   → Node 1
   Hospitals 167-333 → Node 2
   Hospitals 334-500 → Node 3
   No application code changes needed

4. Celery → Auto-scaling + Priority Queues
   Rush hour problem: ICU shift change = 1,000 alerts in 5 minutes
   Solution:
     celery worker --autoscale=50,5
     Separate queues:
       critical_alerts → processed first
       normal_alerts   → standard processing
   On Kubernetes: HPA scales Celery pods automatically

Complete 500-hospital stack:
  AWS ALB (load balancer)
    ↓
  10 FastAPI pods (ECS/EKS, auto-scaled)
    ↓
  Confluent Cloud Kafka
  500 topics, partitioned
    ↓
  PostgreSQL on RDS (10 shards)
  Multi-AZ, automated backups
    ↓
  Redis Cluster (ElastiCache, 3 nodes)
  pub/sub + task queue
    ↓
  Celery workers (5-50 pods, auto-scaled)
  priority queues
```

---

## 5. Java/Spring Boot vs Python/FastAPI Mapping

### Concept Mapping

| Concept | Spring Boot | FastAPI/Python |
|---|---|---|
| HTTP routing | `@RestController` + `@GetMapping` | `APIRouter` + `@router.get` |
| Dependency injection | `@Autowired` | `Depends()` |
| Request validation | Bean Validation `@Valid` | Pydantic models |
| Lightweight background tasks | `@Async` | `BackgroundTasks` |
| Persistent background tasks | `@Scheduled` + Quartz | Celery + Redis |
| Database ORM | Hibernate + Spring Data JPA | SQLAlchemy + asyncpg |
| Database migrations | Flyway / Liquibase | Alembic |
| Middleware / Filters | `OncePerRequestFilter` | `BaseHTTPMiddleware` |
| Configuration | `application.properties` + `@Value` | Pydantic `BaseSettings` + `.env` |
| Testing | JUnit + MockMvc | pytest + TestClient |
| Event streaming | Spring Kafka | aiokafka |
| API documentation | Springfox / Swagger UI | Built-in at `/docs` |
| Application context | Spring Application Context | FastAPI lifespan |

### Code Comparison — Alert Endpoint

```java
// Spring Boot
@RestController
@RequestMapping("/alerts")
public class AlertController {

    @Autowired
    private AlertService alertService;

    @PostMapping
    public ResponseEntity<Alert> createAlert(@Valid @RequestBody AlertRequest request) {
        Alert alert = alertService.create(request);
        return ResponseEntity.ok(alert);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Alert> getAlert(@PathVariable Long id) {
        return alertService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
```

```python
# FastAPI
router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("/", response_model=Alert)
async def create_alert(
    alert_data: AlertCreate,                    # Pydantic validates automatically
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)          # explicit dependency injection
):
    alert = await save_alert(db, alert_data.model_dump())
    background_tasks.add_task(generate_llm_summary, alert.id)
    return alert

@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    alert = await fetch_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
```

### Key Philosophical Differences

**1. Explicit vs Implicit Dependency Injection**

```java
// Spring Boot — implicit, magic at runtime
@Autowired
private AlertService service;  // Spring figures out how to create this
```

```python
# FastAPI — explicit, traceable
async def endpoint(service: AlertService = Depends(get_service)):
    # you can see exactly where service comes from
    # easy to swap in tests
```

Spring uses reflection and classpath scanning — powerful but opaque.
FastAPI uses explicit function calls — more verbose but easier to test and debug.

**2. Synchronous vs Asynchronous by Default**

```java
// Spring Boot — sync by default, async opt-in
@GetMapping("/alerts")
public List<Alert> getAlerts() { ... }  // blocks thread

@Async
@GetMapping("/alerts")
public CompletableFuture<List<Alert>> getAlertsAsync() { ... }  // async opt-in
```

```python
# FastAPI — async by default
@router.get("/alerts")
async def get_alerts():  # non-blocking, handles thousands of concurrent requests
    ...
```

**3. Type Safety**

```java
// Java — compile-time type safety
Alert alert = new Alert();
alert.setType(AlertType.SEPSIS);  // compiler catches type errors
```

```python
# Python — runtime type safety via Pydantic
class Alert(BaseModel):
    alert_type: AlertType  # Pydantic validates at runtime
```

**4. Performance Profile**

```
Spring Boot:  ~500ms cold start, high memory (~512MB baseline)
              thread-per-request model
              scales via thread pools

FastAPI:      ~50ms cold start, low memory (~50MB baseline)
              async event loop model
              scales via concurrency, not threads
```

---

## 6. HIPAA & Production Considerations

### The Three HIPAA Rules

**1. Privacy Rule — Minimum Necessary Access**

Patients control their health information. Technically requires:

```
✅ Implemented:
   - Caregiver roles defined (nurse, physician, care_coordinator)
   - Hospital isolation middleware — cross-hospital access prevented
   - AlertHistory tracks every status change with timestamp

❌ Not yet implemented:
   - PHI masking in logs (patient names, MRNs must be masked)
   - Role-based access control (nurses see only their patients)
   - Minimum necessary data in API responses
```

PHI masking in logs:
```python
# wrong — PHI in logs
logger.info(f"Alert created for patient John Smith, MRN MGH-100123")

# correct — masked
logger.info(f"Alert created for patient ***", extra={"patient_id": "***"})
```

**2. Security Rule — Technical Safeguards**

```
✅ Implemented:
   - Unique caregiver IDs with JID addressing
   - Availability status tracking

❌ Not yet implemented:
   - TLS/HTTPS (needs nginx reverse proxy)
   - JWT authentication on all endpoints
   - Role-based authorization
   - Encryption at rest (PostgreSQL + Redis)
   - Automatic session expiry
   - Unique user audit trails
```

Minimum security implementation for production:
```python
# JWT middleware
from fastapi_jwt_auth import AuthJWT

@router.post("/alerts")
async def create_alert(
    alert_data: AlertCreate,
    auth: AuthJWT = Depends()
):
    auth.jwt_required()  # validates JWT token
    current_user = auth.get_jwt_subject()
    ...
```

**3. Breach Notification Rule — Audit Trail**

```
✅ Implemented:
   - AlertHistory model tracks escalation transitions
   - created_at, updated_at on all entities

❌ Not yet implemented:
   - Access logging (who read which patient's data)
   - Anomaly detection
   - Breach detection pipeline
   - Data inventory (know exactly what PHI is stored where)
```

Production audit log pattern:
```python
async def get_alert(alert_id: int, current_user: User = Depends(get_current_user)):
    alert = await fetch_alert(db, alert_id)
    
    # audit every PHI access
    await log_access(
        user_id=current_user.id,
        resource="alert",
        resource_id=alert_id,
        action="read",
        timestamp=datetime.now()
    )
    return alert
```

### Business Associate Agreements (BAA) — Critical

Every cloud service that touches PHI requires a signed BAA:

| Service | HIPAA BAA Available | Notes |
|---|---|---|
| AWS RDS PostgreSQL | ✅ Yes | Standard AWS BAA |
| AWS ElastiCache Redis | ✅ Yes | Standard AWS BAA |
| Confluent Cloud Kafka | ✅ Yes | Enterprise plan |
| **OpenAI API** | ❌ **No** | **NOT HIPAA compliant** |
| Azure OpenAI | ✅ Yes | Use instead of OpenAI direct |
| Self-hosted Llama | ✅ N/A | PHI never leaves network |

**Current OpenAI integration is not HIPAA compliant.** Production options:

```python
# Option A — Azure OpenAI (BAA available)
from openai import AzureOpenAI
client = AzureOpenAI(
    azure_endpoint="https://your-resource.openai.azure.com",
    api_key=settings.azure_openai_key
)

# Option B — Self-hosted (PHI never leaves network)
from ollama import Client
client = Client(host="http://localhost:11434")
response = client.chat(model="llama3", messages=[...])
```

### Production Readiness Checklist

```
Infrastructure:
  ☐ HTTPS/TLS via nginx reverse proxy
  ☐ JWT authentication on all endpoints
  ☐ Role-based authorization
  ☐ PostgreSQL encryption at rest
  ☐ Redis AUTH password
  ☐ Secrets management (AWS Secrets Manager / HashiCorp Vault)

Observability:
  ☐ Structured logging (structlog)
  ☐ PHI masking in all logs
  ☐ Distributed tracing (OpenTelemetry)
  ☐ Metrics (Prometheus + Grafana)
  ☐ Alerting on escalation failures

Compliance:
  ☐ BAA with all cloud providers
  ☐ Replace OpenAI with Azure OpenAI or self-hosted
  ☐ Complete audit logging on all PHI access
  ☐ Data retention policy
  ☐ Penetration testing
  ☐ HIPAA risk assessment

Reliability:
  ☐ Database backups (automated, tested)
  ☐ Multi-AZ deployment
  ☐ Circuit breakers on external calls
  ☐ Retry logic with exponential backoff on LLM calls
  ☐ Dead letter queue for failed Celery tasks
```

---

## 7. Interview Questions & Answers

### FastAPI & Python

**Q: Why FastAPI over Flask or Django for this system?**

FastAPI is async-first, which matters for a system that makes concurrent LLM calls, database queries, and WebSocket connections. Flask is sync by default and Django adds ORM/template overhead we don't need. FastAPI also generates OpenAPI docs automatically and uses Pydantic for validation — both production requirements.

**Q: Explain async/await in the context of this system.**

When FastAPI receives 100 simultaneous alert requests, each making a 2-second LLM call, a sync server would need 100 threads (heavy memory). With async, one thread handles all 100 — it starts the LLM call, hits `await`, pauses that request, handles the next one, and resumes when the LLM responds. `await` means "I'm waiting for something slow — go do something else."

**Q: What's the difference between BackgroundTasks and Celery?**

```
BackgroundTasks → runs after response is sent, in the same process
                  lost if server restarts
                  good for: LLM summary generation

Celery          → runs in a separate process, persisted in Redis
                  survives server restarts
                  good for: escalation tasks that must fire in 5/10/15 min
```

**Q: Why use the Repository pattern?**

Decouples business logic from data access. The router doesn't know if data comes from PostgreSQL, SQLite, or an in-memory dict. In tests, we override `get_db` to use SQLite — no router code changes needed. This is the same reason Spring Boot uses `@Repository`.

### Distributed Systems

**Q: Why Kafka instead of direct database polling for escalation?**

Polling scans all unacknowledged alerts every N seconds — wasted work at scale. Kafka is event-driven: when an alert is created, an event fires immediately. Downstream consumers react without polling. Also, Kafka events survive consumer restarts — if the escalation service goes down, it replays missed events on restart.

**Q: How do WebSockets work across multiple servers?**

Single server: in-memory dict maps caregiver_id to WebSocket connection. Multi-server: nurse connects to Server A, alert fires on Server B — Server B publishes to Redis Pub/Sub channel, Server A subscribes and delivers to the nurse's connection. Redis is the message bus between servers.

**Q: What breaks first when scaling from 1 to 500 hospitals?**

Data isolation. A bug in any query could expose one hospital's patients to another. Solution: schema-per-hospital at 50 hospitals, horizontal sharding at 500 hospitals, plus middleware that validates hospital_id on every request.

### Healthcare Domain

**Q: What is the clinical significance of the escalation timeouts?**

5/10/15 minutes are configurable — clinical workflows vary by alert type. A sepsis alert may need 2-minute escalation. A fall risk alert may tolerate 10 minutes. The failsafe ensures no alert is ever truly missed — the administrator becomes the last line of defense.

**Q: Why is OpenAI not HIPAA compliant and what would you use instead?**

OpenAI's standard API doesn't offer a Business Associate Agreement (BAA), which is legally required for any service handling PHI. Azure OpenAI offers the same models with a BAA. For maximum privacy, a self-hosted model (Llama 3 via Ollama) keeps PHI entirely within the hospital network.