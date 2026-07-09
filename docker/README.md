# Docker Setup for Scalable RAG - Updated March 10, 2026

## Overview

This directory contains Docker configuration for running Scalable RAG locally or testing before Kubernetes deployment.

**Current Status:**
- ✅ Docker Compose: Fully tested with 3-10 worker horizontal scaling
- ✅ Kubernetes: Fully deployed and tested (see `../k8s/` for production)
- ✅ Both configurations synchronized - same environment variables

## 📁 Directory Structure

```
docker/
├── README.md                    # This file (updated)
├── docker-compose.yml           # ✅ Main config - Backend, Workers, Redis, RabbitMQ
├── .env.example                 # Environment template
├── DOCKER_SETUP_SUMMARY.md      # Legacy setup documentation
├── DOCKER_QUICK_REFERENCE.txt   # Quick command reference
│
├── scripts/      # Optional deployment scripts
├── config/       # Optional configs
└── nginx/        # Optional reverse proxy
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create .env file from template
cp .env.example .env

# Edit .env and add your GROQ_API_KEY
# Get key from: https://console.groq.com
nano .env
```

### 2. Start Services

```bash
# Start backend + 3 workers + Redis + RabbitMQ
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Verify Backend

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","services":{"redis":true,"rabbitmq":true}}
```

## 📊 Services Running

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| **Backend** | 8000 | ✅ Running | FastAPI server + LangGraph orchestrator |
| **Workers** (3) | - | ✅ Running | RabbitMQ consumers, horizontally scalable |
| **Redis** | 6379 | ✅ Running | In-memory cache, step results |
| **RabbitMQ** | 5672 | ✅ Running | Task queue for worker distribution |
| **RabbitMQ UI** | 15672 | ✅ Running | Management interface (guest/guest) |

## 🔄 Horizontal Scaling

### Scale Workers Up

```bash
# Scale to 7 workers (from default 3)
docker-compose up -d --scale worker=7

# Verify
docker-compose ps | grep worker
# Output: 7 worker containers running
```

### Scale to Maximum (10 workers)

```bash
docker-compose up -d --scale worker=10
```

### Scale Back Down

```bash
docker-compose up -d --scale worker=3
```

## 📖 Configuration

### Environment Variables (in .env)

```bash
# Required
GROQ_API_KEY=gsk_your_key_here

# Optional (have defaults)
# RABBITMQ_USER=guest
# RABBITMQ_PASSWORD=guest
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=admin123
```

### Backend Settings

All settings in `docker-compose.yml` backend service:

```yaml
environment:
  APP_NAME: "Agentic RAG System"
  EMBEDDING_MODEL: "sentence-transformers/all-MiniLM-L6-v2"
  RETRIEVAL_TOP_K: "5"
  MAX_AGENT_STEPS: "5"
  CACHE_TTL_SECONDS: "3600"
```

### Worker Configuration

All workers share:
- Same Redis instance for state
- Same RabbitMQ queue for tasks
- Prefetch count = 1 (fair load distribution)
- Auto-assigned unique ID (pod hostname)

## 🧪 Testing

### Test Basic Connectivity

```bash
# Backend health
curl http://localhost:8000/health

# Redis connection
docker-compose exec redis redis-cli ping
# Response: PONG

# RabbitMQ connection
docker-compose exec rabbitmq rabbitmq-diagnostics ping
# Response: ok
```

### Test Worker Scaling

```bash
# Terminal 1: Monitor pods
watch 'docker-compose ps | grep worker'

# Terminal 2: Send test queries
for i in {1..10}; do
  curl -X POST http://localhost:8000/process_query \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"test $i\"}" \
  sleep 0.1
done

# Terminal 3: Scale up while queries are running
docker-compose up -d --scale worker=7

# Observe: New workers immediately start picking up tasks
```

## 📝 Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend    # Backend logs
docker-compose logs -f worker     # All worker logs
docker-compose logs -f redis      # Redis logs
docker-compose logs -f rabbitmq   # RabbitMQ logs

# Last 50 lines
docker-compose logs --tail 50 worker
```

### Check Service Status

```bash
# detailed status
docker-compose ps

# Specific service
docker-compose ps backend
```

### Stop Services

```bash
# Stop (preserve data)
docker-compose stop

# Stop specific service
docker-compose stop worker

# Stop and remove containers
docker-compose down

# Stop, remove, and delete volumes (careful!)
docker-compose down -v
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific
docker-compose restart backend
```

### Rebuild Images

```bash
# Rebuild backend image
docker-compose build backend

# Rebuild worker image
docker-compose build worker

# Rebuild all
docker-compose build
```

## 🔧 Troubleshooting

### Backend not responding?

```bash
# Check logs
docker-compose logs backend

# Verify connections
curl http://localhost:8000/health

# Restart
docker-compose restart backend
```

### Workers not starting?

```bash
# Check logs
docker-compose logs worker

# Check if Redis/RabbitMQ are healthy
docker-compose ps

# Restart workers
docker-compose down && docker-compose up -d
```

### Redis disk full?

```bash
# Monitor size
docker-compose exec redis redis-cli info memory

# Adjust in docker-compose.yml:
# command: redis-server --maxmemory 512mb ...
```

### Port already in use?

Edit `docker-compose.yml` and change port mapping:
```yaml
backend:
  ports:
    - "8001:8000"  # Changed from 8000 to 8001
```

### High latency between workers and RabbitMQ?

Check network:
```bash
# Test connectivity
docker-compose exec worker ping rabbitmq

# Should see: rabbitmq is alive
```

## 📦 Optional Services (Commented Out)

### Using Neo4j (Graph Database)

Uncomment in `docker-compose.yml`:
```yaml
neo4j:
  image: neo4j:5.15-community
  ports:
    - "7687:7687"
  environment:
    NEO4J_AUTH: neo4j/YOUR_NEO4J_PASSWORD  # Use .env file value
```

Access at: http://localhost:7474

### Using ChromaDB (Vector Database)

Uncomment in `docker-compose.yml`:
```yaml
chromadb:
  image: chromadb/chroma:latest
  ports:
    - "8001:8000"
```

Access at: http://localhost:8001

## 🎯 Docker vs Kubernetes Comparison

| Feature | Docker Compose | Kubernetes |
|---------|---|---|
| **Scaling** | Manual (`--scale worker=N`) | Automatic HPA |
| **Local Dev** | ✅ Best choice | Complex |
| **Production** | ⚠️ Works but manual | ✅ Best choice |
| **Persistence** | Local volumes | StatefulSets |
| **Service Discovery** | Container names | DNS names |
| **Load Balancing** | Docker network | Kubernetes ingress |
| **Setup Time** | ~2 minutes | ~5 minutes |

## 🚀 Moving to Production (Kubernetes)

When ready for production deployment:

```bash
# Deploy to Kubernetes
kubectl apply -f ../k8s/

# Verify deployment
kubectl get pods -n niyanta

# Access backend
kubectl port-forward -n niyanta svc/backend 8000:8000
curl http://localhost:8000/health
```

See [../k8s/README.md](../k8s/README.md) for full Kubernetes guide.

## 📚 Documentation

- **[../k8s/README.md](../k8s/README.md)** - Kubernetes deployment guide
- **[../docs/README.md](../docs/README.md)** - Full architecture documentation

## ✅ What's Been Updated (March 10, 2026)

- ✅ Synchronized environment variables with Kubernetes ConfigMap
- ✅ Removed unnecessary Neo4j/ChromaDB dependencies (commented out)
- ✅ Simplified core services: Backend, Workers, Redis, RabbitMQ
- ✅ Added worker prefetch configuration for fair load balancing
- ✅ Updated documentation with tested commands
- ✅ Added .env.example template
- ✅ Added HPA equivalent documentation for Docker Compose scaling

## 📞 Support

For issues:
1. Check logs: `docker-compose logs <service>`
2. Verify service health: `docker-compose ps`
3. Test connectivity: `curl http://localhost:8000/health`
4. See troubleshooting section above

---

**Last Updated:** March 10, 2026  
**Tested With:** Docker Compose v3.8, Docker 28.5.1  
**Status:** ✅ Fully synchronized with Kubernetes deployment

```bash
# View logs
./docker/scripts/logs.sh

# Backup databases
./docker/scripts/backup.sh

# Check status
docker-compose -f docker/docker-compose.yml ps

# Restart services
docker-compose -f docker/docker-compose.yml restart
```

## 📝 Files Explained

### Core Files

- **docker-compose.yml** - Main production configuration
  - All services (backend, frontend, workers, databases)
  - Health checks and restart policies
  - Volume persistence
  - Network isolation

- **docker-compose.dev.yml** - Development overrides
  - Hot reload enabled
  - Debug mode
  - Volume mounts for live code

### Configuration

- **config/.env.example** - Environment variable template
  - Copy to `.env` in project root
  - Set GROQ_API_KEY and passwords

### Scripts

All scripts are in `scripts/` directory:

- **deploy.sh** - Automated deployment
  - Checks environment
  - Builds images
  - Starts all services
  - Verifies health

- **logs.sh** - Interactive log viewer
  - View logs from any service
  - Easy navigation

- **backup.sh** - Backup automation
  - Neo4j, Redis, ChromaDB, RabbitMQ
  - Compressed archives
  - Keeps last 7 backups

- **restore.sh** - Restore from backup
  - Safe restoration process
  - Confirmation prompts

### Nginx

- **nginx/nginx.conf** - Optional reverse proxy
  - Load balancing
  - Rate limiting
  - SSL ready
  - Security headers

## 🎯 Usage Examples

### Production Deployment

```bash
./docker/scripts/deploy.sh
```

### Development Mode

```bash
docker-compose -f docker/docker-compose.yml \
               -f docker/docker-compose.dev.yml up
```

### View Logs

```bash
./docker/scripts/logs.sh
```

### Scale Workers

```bash
docker-compose -f docker/docker-compose.yml up -d --scale worker-1=5
```

### Stop Everything

```bash
docker-compose -f docker/docker-compose.yml down
```

## 🔧 Customization

### Add More Workers

Edit `docker-compose.yml` and duplicate worker service:

```yaml
worker-4:
  # Copy worker-1 configuration
  environment:
    WORKER_ID: worker-4
```

### Change Ports

Edit `docker-compose.yml`:

```yaml
backend:
  ports:
    - "8080:8000"  # Change host port
```

### Add Monitoring

Add to `docker-compose.yml`:

```yaml
prometheus:
  image: prom/prometheus
  # ... configuration

grafana:
  image: grafana/grafana
  # ... configuration
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Project Main README](../README.md)
