# Kubernetes Deployment Guide for Scalable RAG

## Quick Start

### 1. Apply All Manifests
```bash
kubectl apply -f k8s/
```

### 2. Check Status
```bash
# Watch all pods starting
kubectl get pods -n niyanta -w

# Check services
kubectl get svc -n niyanta

# Check deployments
kubectl get deploy -n niyanta
```

### 3. Wait for Everything to be Ready
```bash
# Wait for backend
kubectl rollout status deployment/backend -n niyanta

# Wait for workers (3 initial replicas)
kubectl rollout status deployment/worker -n niyanta

# Verify all pods running
kubectl get pods -n niyanta
```

### 4. Access Backend API

#### Option A: Port Forward (local testing)
```bash
kubectl port-forward -n niyanta svc/backend 8000:8000
# Access: http://localhost:8000
# Health check: curl http://localhost:8000/health
```

#### Option B: LoadBalancer (if supported)
```bash
# Get external IP
kubectl get svc -n niyanta backend

# Access via external IP
curl http://<EXTERNAL-IP>:8000/health
```

## Kubernetes Manifest Files

| File | Purpose |
|------|---------|
| 01-namespace-configmap.yaml | Namespace + environment config |
| 02-redis-statefulset.yaml | Redis (in-memory cache) |
| 03-rabbitmq-statefulset.yaml | RabbitMQ (message queue) |
| 04-neo4j-statefulset.yaml | Neo4j (graph database) |
| 05-chromadb-deployment.yaml | ChromaDB (vector store) |
| 06-backend-deployment.yaml | Backend API + Orchestrator |
| 07-worker-deployment.yaml | Scalable workers (3-10 replicas) |
| 08-ingress.yaml | External routing |
| 09-hpa.yaml | Auto-scaling rules |

## Auto-Scaling Behavior

**Worker pods automatically scale based on:**
- **CPU**: Scale up if >70% utilization, scale down if <70%
- **Memory**: Scale up if >80% utilization, scale down if <80%

**Scaling Ranges:**
- Minimum: 3 workers
- Maximum: 10 workers

**Speed:**
- Scale up: 30 second stabilization, max 2 pods per 15 sec
- Scale down: 60 second stabilization, max 50% reduction per 15 sec

## Testing Horizontal Scaling

### 1. Monitor Worker Count
```bash
# Watch HPA status (opens new terminal)
kubectl get hpa -n niyanta -w
```

### 2. Check Current Replicas
```bash
kubectl get deploy worker -n niyanta
```

### 3. Send Heavy Load (trigger scaling)
```bash
# From another terminal, send multiple requests to backend
for i in {1..50}; do
  curl -X POST http://localhost:8000/process \
    -H "Content-Type: application/json" \
    -d '{"query": "Test query '$i'"}' &
done
```

### 4. Observe Auto-Scaling
```bash
# After a few seconds, HPA will trigger scale-up
kubectl get pods -n niyanta | grep worker
# Should see: worker-xxxxx (3 → 5 → 7 → 9 → 10 pods)
```

### 5. Stop Load and Observe Scale-Down
```bash
# Wait 60+ seconds after load stops
# HPA will scale down
kubectl get hpa -n niyanta
# Adjust MinReplicas back to 3
```

## Troubleshooting

### Pods Not Starting?
```bash
# Check pod status
kubectl describe pod <pod-name> -n niyanta

# Check pod logs
kubectl logs <pod-name> -n niyanta

# Check all events
kubectl get events -n niyanta
```

### Backend Can't Connect to Databases?
```bash
# Verify all services are up
kubectl get svc -n niyanta

# Test Redis connection from backend pod
kubectl exec -it deployment/backend -n niyanta -- redis-cli -h redis ping

# Test RabbitMQ connection
kubectl exec -it deployment/backend -n niyanta -- python -c "import pika; pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))"
```

### HPA Not Scaling?
```bash
# Check metrics-server is installed
kubectl get deploy metrics-server -n kube-system

# Check HPA status
kubectl describe hpa worker-autoscaler -n niyanta

# View HPA events
kubectl get events -n niyanta | grep HPA
```

## Cleanup

### Remove Everything
```bash
kubectl delete namespace niyanta
```

### Keep Namespace, Remove Services
```bash
kubectl delete -f k8s/ -n niyanta
```

## Logging & Monitoring

### View Backend Logs
```bash
kubectl logs deployment/backend -n niyanta -f
```

### View Worker Logs
```bash
kubectl logs deployment/worker -n niyanta -f

# Specific worker
kubectl logs worker-<hash> -n niyanta -f
```

### View Worker IDs (WORKER_ID env var)
```bash
# Should see each pod get unique ID from metadata.name
kubectl exec -it worker-<hash> -n niyanta -- env | grep WORKER_ID
```

## Architecture Overview

```
┌─────────────┐
│   Frontend  │ (localhost:5174, npm run dev)
└──────┬──────┘
       │ HTTP
       ↓
┌─────────────────────────────────────────┐
│  Ingress / LoadBalancer Service         │
│  (External endpoint to backend:8000)    │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│  Backend Pod (1 replica)                │
│  - FastAPI Server (port 8000)           │
│  - LangGraph Orchestrator                │
│  - Step coordination via Redis          │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ↓                ↓
┌──────────────┐  ┌──────────────────────┐
│     RabbitMQ │  │  Redis (ConfigMap)   │
│ (Task Queue) │  │ (Step Results)       │
└────────┬─────┘  └──────────┬───────────┘
         │                   │
         ↓                   ↓
    ┌─────────────────────────────────────────┐
    │ Worker Pods (3-10 replicas, auto-scaled)│
    │ - worker-abc123                         │
    │ - worker-def456                         │
    │ - worker-ghi789                         │
    │ - ... (auto-scales based on CPU > 70%)  │
    └─────┬───────┬───────┬──────────────────┘
          │       │       │
          ↓       ↓       ↓
       ┌──────────────────────────┐
       │ Shared Databases         │
       │ - Neo4j (graph DB)       │
       │ - ChromaDB (vectors)     │
       └──────────────────────────┘
```

## Performance Notes

- **Backend**: 1 replica (orchestrator is stateless bottleneck)
- **Workers**: 3-10 replicas (scale with demand)
- **RabbitMQ**: 1 replica (handles ~1000s of messages/sec)
- **Redis**: 1 replica (handles ~10000s of ops/sec)
- **Databases**: 1 replica each (scale vertically if needed)

## Next Steps

1. **Deploy to Kubernetes**: `kubectl apply -f k8s/`
2. **Verify all pods healthy**: `kubectl get pods -n niyanta`
3. **Port-forward backend**: `kubectl port-forward svc/backend 8000:8000`
4. **Test health endpoint**: `curl http://localhost:8000/health`
5. **Start frontend**: `cd frontend && npm run dev`
6. **Send queries and observe auto-scaling**: `kubectl get hpa -n niyanta -w`
