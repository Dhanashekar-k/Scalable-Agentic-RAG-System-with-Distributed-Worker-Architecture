# Scalable RAG Monitoring & Observability Stack

**Status:** ✅ Production-Ready  
**Updated:** March 10, 2026  

---

## Overview

Comprehensive monitoring stack for Scalable RAG Agentic RAG system:
- **Prometheus**: Metrics collection & scraping
- **Grafana**: Visualization & dashboards
- **Loki**: Centralized log aggregation
- **Promtail**: Log shipping from containers
- **Redis Exporter**: Redis metrics export

---

## Quick Start

### 1. Start the Monitoring Stack

```bash
cd docker
docker-compose up -d prometheus grafana loki promtail redis-exporter
```

### 2. Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | (no auth) |
| **Loki** | http://localhost:3100 | (no auth) |
| **Backend Metrics** | http://localhost:8000/metrics | (prometheus format) |

### 3. First Dashboard

Grafana automatically loads:
- **Dashboard:** Scalable RAG Agentic RAG - System Overview
- **Folder:** Scalable RAG
- **Refresh:** Every 10 seconds

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Scalable RAG Services                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Backend  │  │ Workers  │  │  Redis   │  │RabbitMQ │    │
│  │  :8000   │  │ :8000    │  │ :6379    │  │ :5672   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘    │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │ Emit metrics & logs
                      │
┌─────────────────────┼────────────────────────────────────────┐
│            Observability Stack                               │
├─────────────────────┼────────────────────────────────────────┤
│                     │                                        │
│  ┌──────────────────┼──────────────────┐                   │
│  │                  ▼                  │                   │
│  │  ┌────────────────────────────┐    │                   │
│  │  │   Prometheus              │    │                   │
│  │  │ (Metrics Collection)      │    │                   │
│  │  │ :9090                     │    │                   │
│  │  └────────────┬───────────────┘    │                   │
│  │               │                    │                   │
│  │  ┌────────────┬─────────────────┐  │                   │
│  │  │            ▼                 │  │                   │
│  │  │  ┌──────────────────────┐    │  │                   │
│  │  │  │  Grafana            │    │  │                   │
│  │  │  │(Visualization)      │    │  │                   │
│  │  │  │ :3000               │    │  │                   │
│  │  │  └──────────────────────┘    │  │                   │
│  │  │            ▲                 │  │                   │
│  │  │            │                 │  │                   │
│  │  │  ┌─────────┴──────────────┐  │  │                   │
│  │  │  │                        │  │  │                   │
│  │  │  ▼                        ▼  ▼  │                   │
│  │  │ Loki              Prometheus   │                   │
│  │  │ (Logs)            (Metrics)    │                   │
│  │  │ :3100             :9090        │                   │
│  │  │                                │                   │
│  │  └────────────────────────────────┘                   │
│  │                                                        │
│  │  Promtail ◄─── Container Logs                        │
│  │  (Log Shipper)                                       │
│  │  :9080                                               │
│  │                                                        │
│  └────────────────────────────────────────────────────────┘
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Metrics Tracked

### Request Metrics
- `http_requests_total` - Total HTTP requests by method/endpoint/status
- `http_request_duration_seconds` - Request latency (p50, p95, p99)

### Worker Metrics
- `active_workers` - Current number of active workers
- `queued_tasks` - Tasks waiting in queue
- `completed_tasks_total` - Tasks completed (success/failed/timeout)
- `task_duration_seconds` - Task execution time

### RAG Metrics
- `rag_query_duration_seconds` - Query processing time by mode (normal/agentic/cached)
- `cache_hits_total` - Semantic cache hits
- `cache_misses_total` - Semantic cache misses

### Database Metrics
- `redis_operations_total` - Redis operations by type
- `vector_retrieval_duration_seconds` - Vector DB query duration

### System Metrics
- `backend_uptime_seconds` - Backend service uptime
- `worker_memory_bytes` - Worker memory usage
- `errors_total` - Error count by type/service

---

## Grafana Dashboards

### Built-in Dashboard: Scalable RAG System Overview

**Panels:**
1. **HTTP Request Rate** - Requests per second (5m moving average)
2. **Active Workers** - Current worker count (stat)
3. **Request Latency** - p95/p99 latency trends
4. **Task Completion Rate** - Tasks completed per second
5. **Cache Hit Rate** - Hit rate percentage
6. **Error Rate** - Error trends

**Time Range:** Last 1 hour (auto-refresh every 10s)

**Access:**
- Navigate to http://localhost:3000 → Dashboards → Scalable RAG
- Or direct: http://localhost:3000/d/niyanta-overview

### Create Custom Dashboards

1. **Login to Grafana**: http://localhost:3000 (admin/admin)
2. Click **+ → Dashboard**
3. Add panels:
   ```
   - Metric: Rate(metric_name[5m])
   - Datasource: Prometheus
   - Visualization: Graph/Stat/Table
   ```

**Example Queries:**
```promql
# Request rate by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# Error rate percentage
(rate(errors_total[5m]) / rate(http_requests_total[5m])) * 100

# Worker utilization
active_workers / 10  # Assuming 10 max workers

# Cache efficiency
cache_hits_total / (cache_hits_total + cache_misses_total)
```

---

## Prometheus

### Configuration

Located at: `docker/config/prometheus.yml`

**Default Scrape Targets:**
- Backend API: http://backend:8000/metrics (10s interval)
- Workers: http://worker:8000/metrics (10s interval)
- Redis Exporter: http://redis-exporter:9121 (10s interval)
- RabbitMQ: http://rabbitmq:15692/metrics (10s interval)
- Prometheus: http://localhost:9090 (15s interval)

### Access Prometheus

**UI:** http://localhost:9090

**Useful Endpoints:**
- Graph explorer: http://localhost:9090/graph
- Targets: http://localhost:9090/targets
- Rules: http://localhost:9090/rules
- Alerts: http://localhost:9090/alerts

**PromQL Query Examples:**
```promql
# HTTP request rate (per second)
rate(http_requests_total[5m])

# P95 request latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active worker count
active_workers

# Cache hit ratio
cache_hits_total / (cache_hits_total + cache_misses_total)
```

---

## Loki

### Configuration

Located at: `docker/config/loki-config.yml`

**Features:**
- Filesystem storage (can be upgraded to S3)
- 24-hour retention (configurable)
- Full-text log search

### Access Loki

**Via Grafana:**
1. Go to http://localhost:3000 → Explore
2. Select datasource: **Loki**
3. Enter LogQL query:
   ```
   {service="backend"}
   {service="worker"} | json | error="true"
   {job="docker"} | level="ERROR"
   ```

**Useful LogQL Queries:**
```
# All backend logs
{service="backend"}

# Worker errors only
{service="worker"} | level="ERROR"

# Specific container logs
{container_name="niyanta_backend"}

# Multi-service aggregation
{service=~"backend|worker"}
```

---

## Logs with Promtail

### Configuration

Located at: `docker/config/promtail-config.yml`

**What's Being Shipped:**
- Docker container logs (all containers via docker.sock)
- System logs from /var/log/* (optional)

**Log Labels:**
- `container`: Container name
- `service`: Service name (from docker labels)
- `stream`: Log stream (stdout/stderr)
- `job`: Job identifier (docker)

### Viewing Logs

**In Grafana:**
1. Explore → Datasource: Loki
2. Label filters:
   ```
   {service="backend"} | grep "error"
   {container_name="niyanta_worker_1"} | json
   ```

**In Terminal (via Docker):**
```bash
docker logs niyanta_backend -f
docker-compose logs -f worker
```

---

## Performance Tuning

### Prometheus

**Storage Optimization:**
```yaml
# In docker-compose.yml
prometheus:
  command:
    - '--storage.tsdb.retention.time=30d'  # Retention period
    - '--storage.tsdb.max-block-duration=2h'  # Block size
```

**Memory Usage:**
- Default: ~200MB for 1-week retention
- Scales with: metric count × time range × scrape frequency

### Loki

**Log Retention:**
```yaml
# In loki-config.yml
retention_deletes_enabled: false  # Set to true for cleanup
retention_period: 30d  # Keep 30 days of logs
```

**Storage Breakdown:**
- Each service × log lines per second × retention period
- Typical: 5-10 MB/day per service

### Grafana

**Dashboard Performance:**
- Reduce refresh rate: 10s → 30s for large dashboards
- Use query caching
- Limit time range in queries

---

## Alerting (Future Enhancement)

### Setup AlertManager

```yaml
# Add to prometheus.yml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/rules/*.yml'
```

### Example Alert Rules

```yaml
groups:
  - name: niyanta
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05  # > 5%
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: WorkerDown
        expr: active_workers < 1
        for: 1m
        annotations:
          summary: "All workers offline"
```

---

## Troubleshooting

### Prometheus Not Scraping Metrics

```bash
# Check targets status
curl http://localhost:9090/api/v1/targets

# Verify backend /metrics endpoint
curl http://localhost:8000/metrics | head -20
```

### Loki Not Receiving Logs

```bash
# Check Promtail status
docker logs niyanta_promtail

# Verify docker.sock is mounted
docker-compose exec promtail ls -la /var/run/docker.sock

# Test Loki connectivity
curl http://loki:3100/ready
```

### Grafana Cannot Find Datasources

```bash
# Check Grafana logs
docker logs niyanta_grafana

# Verify provisioning file
docker-compose exec grafana ls -la /etc/grafana/provisioning/datasources/
```

### High Memory Usage

```bash
# Check Prometheus storage
du -sh /path/to/docker/prometheus-data/

# Reduce retention
docker-compose down
rm -rf docker/prometheus-data/  # Clean old data
docker-compose up -d prometheus
```

---

## Commands Reference

```bash
# Start monitoring stack
cd docker
docker-compose up -d prometheus grafana loki promtail redis-exporter

# Start full stack (including app)
docker-compose up -d

# View monitoring logs
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f loki

# Check metrics endpoint
curl http://localhost:8000/metrics

# Scale workers and watch metrics
docker-compose up -d --scale worker=7

# Clean monitoring data
docker volume rm docker_prometheus-data docker_grafana-data docker_loki-data

# Restart monitoring services
docker-compose restart prometheus grafana loki promtail
```

---

## Next Steps

### Phase 2: Alerting
- AlertManager for alert routing
- Slack/email notifications
- Alert templates & routing rules

### Phase 3: Tracing
- Jaeger distributed tracing
- Trace instrumentation in backend
- Service dependency visualization

### Phase 4: Advanced Dashboards
- Worker breakdown by task type
- Query pipeline efficiency
- Cache effectiveness analysis
- Cost tracking per request

---

## Files Reference

| File | Purpose |
|------|---------|
| `config/prometheus.yml` | Prometheus configuration & scrape targets |
| `config/loki-config.yml` | Loki storage & ingestion config |
| `config/promtail-config.yml` | Promtail log scraping config |
| `config/grafana/datasources.yml` | Grafana data source definitions |
| `config/grafana/dashboards.yml` | Grafana dashboard provider |
| `config/grafana/dashboards/niyanta-overview.json` | System overview dashboard |
| `backend/utils/metrics.py` | Prometheus metrics definitions |
| `backend/main.py` | /metrics endpoint integration |

---

**Questions?**
- Prometheus Docs: https://prometheus.io/docs
- Grafana Docs: https://grafana.com/docs
- Loki Docs: https://grafana.com/docs/loki
