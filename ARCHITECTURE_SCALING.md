# Architecture Scaling Document

## Overview

This document outlines scaling strategies for the Healthcare Clinical Communication & Intelligent Alert Routing Platform to handle increased load, ensure high availability, and maintain performance as the system grows.

---

## Current Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   FastAPI   │──────│  PostgreSQL │──────│    Redis    │
│   (Async)   │      │  (Primary) │      │   (Cache)   │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Kafka     │──────│   Celery    │──────│  OpenAI     │
│  (Events)   │      │   Worker    │      │   (LLM)     │
└─────────────┘      └─────────────┘      └─────────────┘
```

---

## Scaling Strategies

### 1. Application Layer (FastAPI)

#### Horizontal Scaling
- **Multiple FastAPI instances** behind a load balancer
- **Stateless design** enables easy horizontal scaling
- **Session management** via Redis (not in-memory)

#### Load Balancer Options
- **Nginx** or **HAProxy** for L4/L7 load balancing
- **AWS ALB** or **Google Cloud Load Balancing** for cloud deployments
- **Kubernetes Ingress** for containerized deployments

#### Configuration
```yaml
# nginx.conf example
upstream fastapi_backend {
    least_conn;
    server fastapi-1:8000;
    server fastapi-2:8000;
    server fastapi-3:8000;
}
```

#### Scaling Considerations
- **CPU-bound**: LLM summarization, alert processing
- **I/O-bound**: Database queries, Kafka operations
- **Connection pooling**: Limit database connections per instance

---

### 2. Database Layer (PostgreSQL)

#### Read Replicas
```
┌─────────────┐
│   Primary   │ (Write)
└──────┬──────┘
       │
       ├───┬──────┬──────┐
       │   │      │      │
       ▼   ▼      ▼      ▼
  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
  │Rep 1│ │Rep 2│ │Rep 3│ │Rep 4│ (Read)
  └─────┘ └─────┘ └─────┘ └─────┘
```

#### Implementation
- **Primary** handles all writes
- **Replicas** handle read operations
- **Connection routing** based on operation type

#### SQLAlchemy Configuration
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine

# Primary (write)
primary_engine = create_async_engine(settings.database_url)

# Replicas (read)
replica_engines = [
    create_async_engine(settings.replica_url_1),
    create_async_engine(settings.replica_url_2),
]

# Round-robin replica selection
import itertools
replica_pool = itertools.cycle(replica_engines)
```

#### Database Scaling Techniques
- **Connection pooling**: PgBouncer for connection management
- **Partitioning**: Partition alerts by hospital/facility
- **Indexing**: Optimize queries with proper indexes
- **Vacuuming**: Regular maintenance to prevent bloat

#### Connection Pooling with PgBouncer
```yaml
# docker-compose.yml
pgbouncer:
  image: pgbouncer/pgbouncer
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 1000
```

---

### 3. Caching Layer (Redis)

#### Redis Cluster
```
┌─────────────┐
│  Redis      │
│  Cluster    │
├──────┬──────┤
│Node 1│Node 2│
│Slot 0│Slot 1│
├──────┼──────┤
│Node 3│Node 4│
│Slot 2│Slot 3│
└──────┴──────┘
```

#### Scaling Strategies
- **Redis Cluster** for horizontal scaling
- **Read replicas** for read-heavy workloads
- **Sharding** by key pattern (e.g., hospital_id)

#### Cache Patterns
- **Cache-aside**: Application manages cache
- **Write-through**: Cache updated on write
- **Write-behind**: Async cache updates

#### Configuration
```python
# app/core/cache.py
import redis
from redis.cluster import RedisCluster

redis_client = RedisCluster(
    host="redis-cluster",
    port=6379,
    decode_responses=True
)
```

---

### 4. Message Queue (Kafka)

#### Kafka Cluster Scaling
```
┌─────────────────────────────────┐
│         Kafka Cluster            │
├──────────┬──────────┬────────────┤
│ Broker 1 │ Broker 2 │  Broker 3  │
│ Part 0,1 │ Part 2,3 │  Part 4,5  │
└──────────┴──────────┴────────────┘
```

#### Scaling Strategies
- **Multiple brokers** for fault tolerance
- **Partitioning** for parallelism
- **Consumer groups** for horizontal scaling

#### Topic Configuration
```bash
# Create topic with partitions
kafka-topics --create \
  --topic healthcare.alerts.created \
  --partitions 6 \
  --replication-factor 3 \
  --bootstrap-server localhost:9092
```

#### Producer Scaling
- **Multiple producer instances**
- **Async sending** with batching
- **Compression** (snappy, gzip)

#### Consumer Scaling
```python
# Multiple consumer instances in same group
# Each instance gets subset of partitions
consumer_group = "alert_processors"
```

---

### 5. Task Queue (Celery)

#### Worker Scaling
```
┌─────────────────────────────────┐
│         Celery Workers          │
├──────────┬──────────┬────────────┤
│ Worker 1 │ Worker 2 │  Worker 3  │
│ Queue:   │ Queue:   │  Queue:    │
│ escalation│ escalation│ escalation│
└──────────┴──────────┴────────────┘
```

#### Scaling Strategies
- **Multiple worker processes** per machine
- **Multiple worker machines** for horizontal scaling
- **Queue separation** by task type

#### Worker Configuration
```python
# app/core/celery_app.py
celery_app.conf.update(
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
)
```

#### Queue Priorities
```python
# Separate queues for different priorities
celery_app.conf.task_queues = [
    Queue('critical', routing_key='critical'),
    Queue('high', routing_key='high'),
    Queue('default', routing_key='default'),
]
```

#### Autoscaling
```bash
# Celery autoscaling
celery -A app.core.celery_app worker \
  --autoscale=10,2 \
  --maxtasksperchild=1000
```

---

### 6. LLM Service (OpenAI)

#### Rate Limiting
- **Implement exponential backoff**
- **Queue requests** during rate limit periods
- **Cache LLM responses** for similar alerts

#### Cost Optimization
- **Batch processing** where possible
- **Model selection** based on complexity
- **Response caching** to reduce API calls

#### Fallback Strategy
```python
# app/services/llm_service.py
async def generate_llm_summary_with_fallback(alert_id: int):
    try:
        return await generate_llm_summary(alert_id)
    except OpenAIError:
        # Fallback to rule-based summarization
        return await generate_rule_based_summary(alert_id)
```

---

## Monitoring & Observability

### Metrics to Track
- **Request latency** (p50, p95, p99)
- **Error rates** (4xx, 5xx)
- **Database query times**
- **Queue depths** (Celery, Kafka)
- **Cache hit ratios**
- **Worker utilization**

### Tools
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **ELK Stack** for logging
- **Jaeger** for distributed tracing

### Alerting
- **High error rates** (> 5%)
- **Slow response times** (> 2s p95)
- **Queue buildup** (> 1000 tasks)
- **Database connection exhaustion**

---

## Disaster Recovery

### Backup Strategy
- **Database backups**: Daily full + hourly WAL
- **Redis snapshots**: Every 5 minutes
- **Kafka log retention**: 7 days

### High Availability
- **Multi-region deployment**
- **Database failover** (primary → replica)
- **Load balancer health checks**
- **Automatic instance replacement**

### Recovery Procedures
1. **Promote replica** to primary
2. **Restore from backup** if needed
3. **Update DNS/load balancer**
4. **Verify service health**
5. **Monitor for issues**

---

## Security at Scale

### Authentication
- **JWT tokens** with short expiration
- **Token refresh** mechanism
- **OAuth 2.0 / OpenID Connect**

### Authorization
- **Role-based access control** (RBAC)
- **Attribute-based access control** (ABAC)
- **Hospital/facility isolation**

### Data Protection
- **Encryption at rest** (database, storage)
- **Encryption in transit** (TLS 1.3)
- **PII masking** in logs
- **HIPAA compliance**

---

## Performance Optimization

### Database Optimization
- **Query optimization** with EXPLAIN ANALYZE
- **Index strategy** for common queries
- **Connection pooling** with PgBouncer
- **Read replicas** for read-heavy workloads

### Application Optimization
- **Async I/O** throughout the stack
- **Connection reuse** with keep-alive
- **Response compression** (gzip)
- **Static asset CDN**

### Caching Strategy
- **API response caching** (short TTL)
- **Database query caching** (Redis)
- **Computed field caching**
- **Session caching**

---

## Deployment Strategies

### Blue-Green Deployment
```
Current: Blue  ──────>  Switch  ──────>  New: Green
  Traffic                     Traffic
```

### Canary Deployment
```
10% traffic → New version
Monitor metrics
50% traffic → New version
Monitor metrics
100% traffic → New version
```

### Rolling Deployment
```
Instance 1: Update → Health check
Instance 2: Update → Health check
Instance 3: Update → Health check
...
```

---

## Cost Optimization

### Resource Optimization
- **Right-sizing** instances
- **Auto-scaling** based on load
- **Spot instances** for non-critical workloads
- **Reserved instances** for baseline load

### Data Transfer
- **CDN** for static assets
- **Compression** for API responses
- **Batch processing** for bulk operations

### Storage Optimization
- **Lifecycle policies** for old data
- **Compression** for logs
- **Tiered storage** (hot/warm/cold)

---

## Scaling Roadmap

### Phase 1: Foundation (Current)
- Single instance deployment
- Basic monitoring
- Manual scaling

### Phase 2: High Availability
- Multiple FastAPI instances
- Database read replicas
- Redis clustering
- Load balancer

### Phase 3: Horizontal Scaling
- Auto-scaling groups
- Kafka cluster
- Celery worker pool
- Advanced monitoring

### Phase 4: Multi-Region
- Multi-region deployment
- Cross-region replication
- Global load balancing
- Disaster recovery automation

---

## References

- [PostgreSQL Scaling Guide](https://wiki.postgresql.org/wiki/Scaling)
- [Redis Cluster Tutorial](https://redis.io/docs/manual/scaling/)
- [Kafka Scaling Best Practices](https://kafka.apache.org/documentation/#design)
- [Celery Scaling Guide](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
