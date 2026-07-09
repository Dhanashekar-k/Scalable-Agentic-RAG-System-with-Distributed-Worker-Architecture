# Scalable RAG - Deployment Checklist

## Pre-Deployment Verification

### ✅ Code & Configuration
- [ ] All code committed to git (except `.env` files)
- [ ] `.gitignore` includes `.env`, `*.key`, `secrets/`
- [ ] No hardcoded credentials in code or comments
- [ ] All `.env` files use placeholder values
- [ ] `requirements.txt` and `package.json` updated
- [ ] Tests passing (when CI/CD is set up)

### ✅ Environment Variables
- [ ] `.env.example` has all required variables
- [ ] All required API keys documented
- [ ] Database credentials documented
- [ ] Service endpoints documented
- [ ] Development values differ from production

### ✅ Docker Configuration
- [ ] `docker-compose.yml` validates: `docker-compose config --quiet`
- [ ] All services have health checks
- [ ] Volume mounts are correct
- [ ] Network configuration is correct
- [ ] Build arguments are set correctly

### ✅ Database Setup
- [ ] Neo4j initialized with schema
- [ ] ChromaDB collection created and populated
- [ ] Redis configured with appropriate TTLs
- [ ] Backup strategy defined
- [ ] Database credentials rotated from defaults

### ✅ Monitoring & Observability
- [ ] Prometheus targets configured
- [ ] Grafana dashboards imported
- [ ] Loki log retention set appropriately
- [ ] Alerting rules defined (if applicable)
- [ ] Monitoring storage sized for expected volume

### ✅ Security
- [ ] Secrets stored in environment variables (not code)
- [ ] All passwords changed from defaults
- [ ] SSL/TLS certificates configured (if needed)
- [ ] Network policies reviewed
- [ ] Access control lists defined
- [ ] API rate limiting configured

### ✅ Backend Services
- [ ] `/health` endpoint responding
- [ ] `/metrics` endpoint accessible
- [ ] API documentation generated correctly
- [ ] CORS configured appropriately
- [ ] Error logging configured
- [ ] Request logging enabled

### ✅ Frontend Services
- [ ] Build succeeds: `npm run build`
- [ ] No console errors in production build
- [ ] API endpoint configure correctly
- [ ] Environment variables set
- [ ] Assets minified and optimized
- [ ] Search engines excluded (robots.txt)

### ✅ Performance
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Caching TTLs set appropriately
- [ ] Worker count sufficient for load
- [ ] Memory limits appropriate
- [ ] Cache size limits configured

---

## Deployment Steps

### Phase 1: Pre-Flight Check
```bash
# 1. Verify all code is committed
git status
# Should show: "nothing to commit, working tree clean"
# Exception: .env files should be ignored

# 2. Verify .env files are in .gitignore
git check-ignore .env docker/.env backend/.env
# Should return paths (meaning they're ignored)

# 3. Validate docker-compose
cd docker
docker-compose config --quiet

# 4. Verify no secrets in committed files
git log --all -S 'gsk_' --oneline  # Should return nothing
git log --all -S 'password=' --oneline  # Should return nothing
```

### Phase 2: Create Production Environment
```bash
# 1. Copy environment template
cp docker/.env.example docker/.env.production

# 2. Configure production values
# Edit with real credentials:
# - GROQ_API_KEY=sk_[YOUR_KEY]
# - NEO4J_PASSWORD=[STRONG_PASSWORD]
# - RABBITMQ_PASSWORD=[STRONG_PASSWORD]
# - ADMIN_PASSWORD=[STRONG_PASSWORD]

# 3. Secure the file
chmod 600 docker/.env.production
# Never commit this file!
```

### Phase 3: Database Initialization
```bash
# 1. Start databases only
cd docker
docker-compose up -d neo4j chromadb redis

# 2. Wait for databases to be ready
sleep 10

# 3. Load initial data
docker-compose exec backend python ingest_data.py

# 4. Verify databases
docker-compose exec neo4j cypher-shell "MATCH (n) RETURN COUNT(*)"
docker-compose exec redis redis-cli DBSIZE
```

### Phase 4: Start Backend Services
```bash
# 1. Build and start backend
docker-compose build backend
docker-compose up -d backend worker rabbitmq

# 2. Wait for services
sleep 10

# 3. Verify backend health
curl -s http://localhost:8000/health | jq .
# Should return: {"status": "healthy", "version": "..."}

# 4. Check metrics endpoint
curl -s http://localhost:8000/metrics | head -10
# Should show Prometheus metrics
```

### Phase 5: Start Monitoring Stack
```bash
# Start monitoring services
docker-compose up -d prometheus grafana loki promtail redis-exporter

# Wait for Grafana to be ready
sleep 15

# Verify Prometheus can scrape backend
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {labels: .labels, health: .health}'
# Should show backend as "up"
```

### Phase 6: Start Frontend
```bash
# 1. Build frontend
cd ../frontend
npm install
npm run build

# 2. Start frontend service
cd ../docker
docker-compose up -d frontend

# 3. Verify frontend is accessible
curl -s http://localhost:5173 | head -20
# Should show HTML content
```

### Phase 7: Verification
```bash
# 1. Check all containers are running
docker ps | grep -E "backend|frontend|prometheus|grafana|redis|neo4j|rabbitmq"

# 2. Verify all health endpoints
curl http://localhost:8000/health
curl http://localhost:5173/health
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
curl http://localhost:3100/ready

# 3. Test a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test question"}'

# 4. Check Grafana dashboard
# Visit http://localhost:3000 (admin/admin)
# Should see System Overview dashboard with data
```

---

## Post-Deployment Validation

### ✅ Functional Tests
- [ ] Create test query → Receives response
- [ ] Cache hit → Faster response
- [ ] Admin login → Dashboard loads
- [ ] Document ingest → Shows in admin panel
- [ ] Metrics visible → Grafana shows data
- [ ] Logs available → Loki has entries

### ✅ Performance Tests
```bash
# 1. Test response time
time curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "simple question"}'
# Should be < 2 seconds

# 2. Test concurrent queries
for i in {1..10}; do
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"query $i\"}" &
done
wait
# All should complete successfully

# 3. Monitor metrics during load
# Watch Grafana dashboard while running tests
```

### ✅ Monitoring Tests
- [ ] Prometheus scraping backend metrics
- [ ] Grafana dashboards display data
- [ ] Loki collecting logs from all services
- [ ] Alert rules (if any) are evaluating correctly
- [ ] No scrape errors in Prometheus targets

### ✅ Security Validation
- [ ] HTTPS enabled (if external access)
- [ ] Admin credentials work
- [ ] API requires authentication (if needed)
- [ ] No secrets in logs
- [ ] Rate limiting active
- [ ] CORS configured correctly

---

## Kubernetes Deployment (If Using K8s)

### Pre-Deployment
- [ ] kubectl configured and connected to cluster
- [ ] Docker images pushed to registry (`docker.io`, `ghcr.io`, etc.)
- [ ] ConfigMap values reviewed and updated
- [ ] Secrets created: `kubectl create secret generic ...`
- [ ] PersistentVolumes provisioned
- [ ] Namespaces created: `kubectl create namespace niyanta`

### Deploy to Kubernetes
```bash
# 1. Apply namespace and ConfigMap
kubectl apply -f k8s/01-namespace-configmap.yaml

# 2. Create secrets
kubectl create secret generic groq-secret \
  --from-literal=GROQ_API_KEY=$GROQ_API_KEY \
  -n niyanta

kubectl create secret generic db-secret \
  --from-literal=NEO4J_PASSWORD=$NEO4J_PASSWORD \
  --from-literal=RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD \
  -n niyanta

# 3. Deploy services
kubectl apply -f k8s/02-backend-deployment.yaml
kubectl apply -f k8s/03-frontend-deployment.yaml
# ... apply other manifests

# 4. Wait for rollout
kubectl rollout status deployment/backend -n niyanta
kubectl rollout status deployment/frontend -n niyanta

# 5. Verify pods are running
kubectl get pods -n niyanta
```

### Verify K8s Deployment
```bash
# Check pod status
kubectl get pods -n niyanta

# Check service endpoints
kubectl get svc -n niyanta

# Check logs
kubectl logs -n niyanta deployment/backend --tail=50

# Port forward to test locally
kubectl port-forward -n niyanta svc/backend 8000:8000
curl http://localhost:8000/health
```

---

## Rollback Procedures

### Docker Compose Rollback
```bash
# 1. Keep previous version tag
# Before deploying: docker tag backend:current backend:previous

# 2. If deployment fails, revert
docker-compose down
docker-compose up -d --no-build  # Use previous image

# 3. Verify services
docker-compose logs -f backend
curl http://localhost:8000/health
```

### Kubernetes Rollback
```bash
# 1. View rollout history
kubectl rollout history deployment/backend -n niyanta

# 2. Rollback to previous version
kubectl rollout undo deployment/backend -n niyanta

# 3. Wait for rollback
kubectl rollout status deployment/backend -n niyanta

# 4. Verify new version (actually previous)
kubectl get pods -n niyanta
```

---

## Monitoring Post-Deployment

### Create Dashboards (First Time)
```
1. Open Grafana: http://localhost:3000 (or k8s LB IP:3000)
2. Credentials: admin/admin
3. Add Prometheus datasource: http://prometheus:9090
4. Add Loki datasource: http://loki:3100
5. Import dashboard: Use niyanta-overview.json from docker/config/grafana/dashboards/
```

### Set Up Alerts (Optional)
```bash
# 1. Create alerting rules (Prometheus)
# Edit docker/config/prometheus.yml

# 2. Configure AlertManager
# Create alertmanager.yml with notification channels

# 3. Test alert
# Trigger condition and verify notification received
```

### Performance Baseline
```bash
# 1. Record current metrics
# Export from Grafana for comparison

# 2. Document expected ranges
# Response time: 500-1500ms (normal), 1500-5000ms (agentic)
# Cache hit rate: 45-60%
# Error rate: < 0.5%

# 3. Set up alerts for deviations
# High latency, low cache hit rate, high error rate
```

---

## Ongoing Maintenance

### Daily Checks
- [ ] All services running and healthy
- [ ] No error spikes in logs
- [ ] Cache hit rate stable
- [ ] Response times normal
- [ ] No stuck tasks in RabbitMQ

### Weekly Checks
- [ ] Database size growth normal
- [ ] Backup completed successfully
- [ ] Log retention under control
- [ ] Metrics storage size stable
- [ ] Update dependencies (if applicable)

### Monthly Checks
- [ ] Security patch updates available
- [ ] Password rotation (if policy requires)
- [ ] Capacity planning review
- [ ] Cost analysis (cloud deployments)
- [ ] Documentation updates needed

### Quarterly Checks
- [ ] Full backup verification (restore test)
- [ ] Disaster recovery plan review
- [ ] Load test for scaling requirements
- [ ] Security audit
- [ ] Architecture review

---

## Emergency Procedures

### Service Down
```bash
# 1. Check status
docker ps | grep <service>

# 2. Check logs
docker-compose logs --tail=50 <service>

# 3. Restart service
docker-compose restart <service>

# 4. If still failing, rebuild
docker-compose build --no-cache <service>
docker-compose up -d <service>
```

### Data Corruption
```bash
# 1. Stop application
docker-compose down

# 2. Restore from backup
# Restore volumes from backup storage

# 3. Verify restore
docker-compose up -d
curl http://localhost:8000/health
```

### Performance Degradation
```bash
# 1. Check metrics in Grafana
# High latency? High memory? High CPU?

# 2. Scale workers if needed
docker-compose up -d --scale worker=5

# 3. Check databases
docker-compose logs neo4j | tail -20
docker-compose logs redis | tail -20

# 4. Clear cache if needed
curl -X POST http://localhost:8000/cache/clear
```

---

## Sign-Off Checklist

**Before going live:**
- [ ] All systems verified and tested
- [ ] Backups configured and tested
- [ ] Monitoring and alerts active
- [ ] Documentation updated
- [ ] Rollback procedures verified
- [ ] Team training completed
- [ ] Emergency contacts documented
- [ ] Go/No-go decision made

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Verified By:** _______________  
**Notes:** _______________________________________________

---

**Last Updated:** March 10, 2026  
**Status:** Ready for Production Deployment
