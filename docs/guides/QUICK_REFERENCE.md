# Scalable RAG - Quick Reference Guide

## 🚀 Getting Started (First Time)

### 1. Environment Setup
```bash
# Clone repository
git clone <repo-url>
cd Scalable RAG

# Create local environment files (use examples as template)
cp docker/.env.example .env
cp docker/.env.example docker/.env
cp docker/.env.example backend/.env

# Edit and add your real credentials
nano .env  # Add GROQ_API_KEY, passwords, etc.

# Keep these local - NEVER commit with real values!
# .gitignore prevents accidental commits
```

### 2. Start Services
```bash
# Navigate to docker directory
cd docker

# Start all services (backend, frontend, databases, monitoring)
docker-compose up -d

# Or start monitoring separately
docker-compose up -d prometheus grafana loki promtail redis-exporter
```

### 3. Access Everything
```
User Dashboard:      http://localhost:5173
Admin Dashboard:     http://localhost:5173/admin (password: admin123)
Backend API:         http://localhost:8000
API Docs:            http://localhost:8000/docs
Grafana Dashboards:  http://localhost:3000 (admin/admin)
Prometheus:          http://localhost:9090
Loki Logs:           http://localhost:3100
```

---

## 📊 Monitoring (What to Watch)

### Grafana Dashboards (http://localhost:3000)

**System Overview Dashboard Shows:**
```
1. HTTP Request Rate    → Should be steady if system is working
2. Active Workers       → Number of workers processing tasks
3. Request Latency      → p95/p99 latency (should be < 5000ms)
4. Task Completion      → How many tasks complete per minute
5. Cache Hit Rate       → Should be 45-60% if working well
6. Error Rate           → Should be near 0% in production
```

**What to Do When:**

| Observation | Meaning | Action |
|-------------|---------|--------|
| 📈 Request latency spikes | System overloaded | Check active workers, scale up |
| 📉 Cache hit rate drops | Cache invalidation | Check cache TTL settings |
| 📊 Error rate increases | Something broke | Check logs in Loki |
| ⚡ Workers inactive | No jobs queued | Check RabbitMQ in admin |
| 🔴 Service offline | Container crashed | `docker-compose logs <service>` |

### Backend Metrics (http://localhost:8000/metrics)

See raw metrics in Prometheus format:
```bash
curl http://localhost:8000/metrics | grep -E "http_requests|cache_hits|errors"
```

---

## 👨‍💼 Admin Dashboard (http://localhost:5173/admin)

### 6 Monitoring Tabs

**1. Overview**
- System statistics: queries, workers, tasks
- Service health: all systems status
- Device status: CPU, memory usage
- Quick health pulse

**2. Analytics**
- Query trends over time (line chart)
- Pipeline distribution (normal vs agentic)
- Response time breakdown
- Performance insights

**3. Queue** (RabbitMQ)
- Messages ready to process
- Active consumers
- Queue health
- Message rate

**4. Tasks**
- List all async tasks
- Filter by status (pending, completed, failed)
- Retry failed tasks
- View task details

**5. Cache**
- Cached queries browser
- Search through cache
- Delete individual entries
- Bulk clear cache

**6. Documents**
- Ingested documents
- Upload new documents
- View collection stats
- Manage metadata

---

## 🔍 Troubleshooting

### "Services won't start"
```bash
# Check what's running
docker ps

# View logs for failed service
docker-compose logs prometheus  # or any service name

# Validate configuration
docker-compose config --quiet

# Restart everything
docker-compose down
docker-compose up -d
```

### "Metrics not appearing in Prometheus"
```bash
# Check backend is running
curl http://localhost:8000/health

# Check metrics endpoint
curl http://localhost:8000/metrics | head -20

# Check Prometheus targets
# Visit http://localhost:9090/targets
# Should show "backend" as UP
```

### "Grafana dashboard is empty"
```bash
# Check datasources in Grafana UI
# Administration > Data Sources > Test all

# Re-import dashboard manually if needed
# Create > Import > Paste JSON from 
# docker/config/grafana/dashboards/niyanta-overview.json
```

### "Loki logs aren't showing"
```bash
# Check Promtail is running
docker-compose logs promtail

# Check Loki connection
# Grafana > Explore > Select Loki > Try query
# {job="docker"}
```

### "Admin dashboard not loading data"
```bash
# Check backend health
curl http://localhost:8000/admin/health-detailed

# Check Redis connection
curl http://localhost:8000/admin/stats | head -20

# Restart backend
docker-compose restart backend
```

---

## 🔐 Security Checklist

### Before Each commit
- [ ] ✅ No `.env` files with real credentials in git
- [ ] ✅ `.gitignore` has `.env` patterns
- [ ] ✅ Example files use placeholders only
- [ ] ✅ No passwords in code comments
- [ ] ✅ No API keys in documentation code samples

### Local Development
- [ ] ✅ Create local `.env` files (ignored by git)
- [ ] ✅ Use different passwords locally vs production
- [ ] ✅ Never share `.env` files
- [ ] ✅ Use strong passwords in production

### Production Deployment
- [ ] ✅ Use Kubernetes Secrets: `kubectl create secret generic ...`
- [ ] ✅ Use environment variable injection in CI/CD
- [ ] ✅ Store config in secure configuration management
- [ ] ✅ Never hardcode secrets anywhere

---

## 📈 Performance Tuning

### If Latency is High
```bash
# 1. Check cache hit rate (should be 45-60%)
# View in Grafana > Cache Hit Rate panel

# 2. Check worker count
# Admin > Overview > Active Workers

# 3. Scale workers if needed
docker-compose up -d --scale worker=3  # Run 3 worker instances

# 4. Check database queries
# Use Neo4j Browser: http://localhost:7474
```

### If Cache Hit Rate is Low
```bash
# 1. Check if TTL is too short
# Default: 24 hours in backend/.env

# 2. Check if queries are same (semantically)
# Few cache hits = many different queries (normal)

# 3. Check Redis connection
docker-compose logs redis
```

### If Services Crash Often
```bash
# 1. Check CPU/Memory limits
docker stats

# 2. Increase Docker resources
# Desktop Docker > Preferences > Resources

# 3. Check logs for errors
docker-compose logs --tail=100 backend | tail -20
```

---

## 🔄 Common Operations

### Update Code and Redeploy
```bash
# 1. Make code changes
# 2. Rebuild backend image
docker-compose build backend

# 3. Restart service
docker-compose up -d backend

# 4. Check it's running
curl http://localhost:8000/health
```

### Clear Cache
```bash
# Option 1: Via Admin Dashboard
# Cache Tab > Clear All

# Option 2: Via API
curl -X POST http://localhost:8000/cache/clear

# Option 3: Direct Redis
docker exec -it docker-redis-1 redis-cli FLUSHALL
```

### View Recent Errors
```bash
# Check application logs in Loki
# Grafana > Explore > Loki > {app="backend"}

# Or via Docker
docker-compose logs --tail=50 backend | grep ERROR

# Or check specific service
docker-compose logs --tail=50 prometheus
```

### Backup Data
```bash
# Backup all volumes
docker-compose exec redis redis-cli BGSAVE
docker-compose exec neo4j /var/lib/neo4j/bin/neo4j-admin dump --database=neo4j --to=/data/backup.dump

# Or backup volumes manually
docker inspect docker_prometheus-data_1  # Get volume path
# Location shown under "Mountpoint"
```

---

## 📚 Documentation References

**Quick Guides:**
- [Monitoring Setup](./docker/MONITORING.md) - Full monitoring guide
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) - What was built
- [Agentic Architecture](./docs/AGENTIC_ARCHITECTURE.md) - System design

**Deployment:**
- [Kubernetes Guide](./docs/DEPLOYMENT.md) - K8s manifests and setup
- [Docker Readme](./docker/README.md) - Docker-specific info

**Development:**
- [Backend](./docs/BACKEND.md) - API and backend architecture
- [Frontend](./docs/FRONTEND.md) - React components

---

## 💡 Tips & Tricks

### Quick Health Check
```bash
# Single command to verify all services
docker-compose exec -T backend curl -s http://localhost:8000/health && \
docker-compose exec -T redis redis-cli ping && \
docker-compose logs --tail=1 prometheus | grep "Server ready"
```

### Monitor in Terminal
```bash
# Watch real-time metrics
watch -n 5 'curl -s http://localhost:8000/metrics | grep "^http_requests"'

# Watch Docker stats
docker stats --no-stream

# Watch logs
docker-compose logs -f --tail=10 backend
```

### Query Prometheus from CLI
```bash
# Get all metric names
curl -s 'http://localhost:9090/api/v1/label/__name__/values' | jq .

# Get metric values
curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total' | jq .

# Get range data
curl -s 'http://localhost:9090/api/v1/query_range?query=cache_hit_rate&start=1678000000&end=1678086400&step=3600' | jq .
```

### Query Loki from CLI
```bash
# Get all logs
curl -s 'http://localhost:3100/loki/api/v1/query_range?query={job="docker"}&start=<unix-time>&end=<unix-time>' | jq .

# Filter by service
curl -s 'http://localhost:3100/loki/api/v1/query_range?query={service="backend"}' | jq .
```

---

## 🎯 Next Steps

**When You're Ready:**

1. **Set up CI/CD** → GitHub Actions for automated testing
2. **Deploy to Kubernetes** → Use manifests in `k8s/`
3. **Add Alerting** → AlertManager integration with Prometheus
4. **Custom Dashboards** → Create dashboards for your metrics
5. **Scaling** → Horizontal pod autoscaling, worker scaling

**See Also:** `IMPLEMENTATION_SUMMARY.md` for complete feature list

---

**Last Updated:** March 10, 2026  
**System Status:** ✅ Production-Ready
