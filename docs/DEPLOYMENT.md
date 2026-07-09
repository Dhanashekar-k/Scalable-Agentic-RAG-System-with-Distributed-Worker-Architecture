# Scalable RAG Deployment Guide

Complete guide for deploying Scalable RAG in production using Docker.

---

## 🎯 Quick Start

### Prerequisites
- Docker 20.10+ and Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space
- Groq API key ([get one here](https://console.groq.com))

### One-Command Deployment

```bash
# 1. Clone repository
git clone <your-repo-url>
cd Scalable RAG

# 2. Configure environment
cp docker/config/.env.example .env
# Edit .env with your configuration

# 3. Deploy
./docker/scripts/deploy.sh
```

That's it! Your application will be running at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

---

## 📋 Detailed Setup

### 1. Environment Configuration

Create `.env` file from template:
```bash
cp docker/config/.env.example .env
```

**Required Variables:**
```env
GROQ_API_KEY=your_actual_api_key
ADMIN_PASSWORD=secure_password_here
NEO4J_PASSWORD=secure_password_here
RABBITMQ_PASS=secure_password_here
```

### 2. Build and Start Services

**Production Mode:**
```bash
./docker/scripts/deploy.sh
```

**Development Mode (with hot reload):**
```bash
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up
```

**Manual Start:**
```bash
# Build images
docker-compose -f docker/docker-compose.yml build

# Start services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### 3. Verify Deployment

Check service health:
```bash
docker-compose -f docker/docker-compose.yml ps
```

All services should show "healthy" status.

Test backend:
```bash
curl http://localhost:8000/health
```

---

## 🏗️ Architecture Overview

### Services

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | React UI with Nginx |
| Backend | 8000 | FastAPI REST API |
| Worker-1,2,3 | - | Distributed task workers |
| Redis | 6379 | Cache & state storage |
| RabbitMQ | 5672, 15672 | Message queue |
| Neo4j | 7474, 7687 | Graph database |
| ChromaDB | 8001 | Vector database |

### Network Architecture

```
Internet → Frontend (port 3000)
              ↓
          Backend (port 8000)
              ↓
        ┌─────┴─────┬──────────┬─────────┐
        ↓           ↓          ↓         ↓
    Worker-1    Worker-2   Worker-3   Redis
        ↓           ↓          ↓         ↓
    [Vector DB] [Graph DB] [Queue]   [Cache]
```

### Data Persistence

All data is stored in Docker volumes:
- `redis-data`: Cache and temporary state
- `rabbitmq-data`: Message queue data
- `neo4j-data`: Graph database
- `chromadb-data`: Vector embeddings

---

## 🔧 Management Commands

### View Logs
```bash
# Interactive log viewer
./docker/scripts/logs.sh

# Or directly
docker-compose -f docker/docker-compose.yml logs -f backend
docker-compose -f docker/docker-compose.yml logs -f worker-1 worker-2 worker-3
```

### Backup Data
```bash
# Create backup
./docker/scripts/backup.sh

# Backups stored in ./backups/
ls -lh backups/
```

### Restore Data
```bash
# Restore from backup
./docker/scripts/restore.sh
```

### Scale Workers
```bash
# Scale to 5 workers
docker-compose -f docker/docker-compose.yml up -d --scale worker-1=5

# Or in docker/docker-compose.yml:
# Add more worker services (worker-4, worker-5, etc.)
```

### Restart Services
```bash
# Restart all
docker-compose -f docker/docker-compose.yml restart

# Restart specific service
docker-compose -f docker/docker-compose.yml restart backend

# Rebuild and restart
docker-compose -f docker/docker-compose.yml up -d --build backend
```

### Stop Services
```bash
# Stop (keep data)
docker-compose -f docker/docker-compose.yml stop

# Stop and remove containers (keep data)
docker-compose -f docker/docker-compose.yml down

# Stop and remove everything (including data)
docker-compose -f docker/docker-compose.yml down -v
```

---

## 🚀 Production Deployment

### Cloud Platforms

#### AWS (EC2 / ECS)

**EC2 Deployment:**
1. Launch Ubuntu 22.04 instance (t3.medium or larger)
2. Install Docker:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   ```
3. Clone and deploy:
   ```bash
   git clone <repo>
   cd Scalable RAG
   cp .env.example .env
   # Edit .env
   ./deploy.sh
   ```
4. Configure security group: Open ports 80, 443, 3000, 8000

**ECS Deployment:**
- Use provided docker-compose.yml
- Convert to ECS task definition
- Use AWS Secrets Manager for sensitive data

#### Google Cloud (GCE / Cloud Run)

**GCE Deployment:**
```bash
# Create VM
gcloud compute instances create niyanta-instance \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-medium \
  --boot-disk-size=50GB

# SSH and deploy
gcloud compute ssh niyanta-instance
# Follow EC2 steps above
```

#### DigitalOcean Droplet

1. Create Droplet (Ubuntu 22.04, 4GB RAM)
2. SSH into droplet
3. Install Docker and deploy (same as EC2)

#### Heroku / Railway / Render

These platforms support Docker Compose directly:
1. Connect GitHub repository
2. Platform auto-detects docker-compose.yml
3. Set environment variables in dashboard
4. Deploy

### SSL/HTTPS Setup

**Option 1: Using Nginx Reverse Proxy**

1. Install Certbot:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. Get certificate:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

3. Update nginx/nginx.conf with SSL config

**Option 2: Using Cloudflare**
- Point domain to your server
- Enable Cloudflare proxy (orange cloud)
- SSL automatically handled

### Performance Tuning

**For High Traffic:**

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      WORKERS: 4  # Increase Uvicorn workers
  
  # Add more worker instances
  worker-4:
    # ... (copy worker-1 config)
  worker-5:
    # ...
```

**Resource Limits:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

---

## 🔒 Security Best Practices

### 1. Change Default Passwords
```env
ADMIN_PASSWORD=use_strong_password
NEO4J_PASSWORD=use_strong_password
RABBITMQ_PASS=use_strong_password
```

### 2. Use Docker Secrets (Production)
```yaml
secrets:
  groq_api_key:
    external: true
services:
  backend:
    secrets:
      - groq_api_key
```

### 3. Enable Firewall
```bash
# UFW (Ubuntu)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 4. Regular Updates
```bash
# Update base images
docker-compose pull
docker-compose up -d --build
```

### 5. Monitoring
Consider adding:
- Prometheus + Grafana for metrics
- Sentry for error tracking
- CloudWatch / Stackdriver for logs

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend

# Restart problematic service
docker-compose restart backend
```

### Out of Memory

```bash
# Check resource usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase

# Or reduce workers
docker-compose down
# Edit docker-compose.yml to use 2 workers instead of 3
docker-compose up -d
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Neo4j Connection Issues

```bash
# Check Neo4j logs
docker-compose logs neo4j

# Restart Neo4j
docker-compose restart neo4j

# Reset Neo4j data (WARNING: deletes data)
docker-compose down
docker volume rm niyanta_neo4j-data
docker-compose up -d
```

### Worker Not Processing Tasks

```bash
# Check RabbitMQ
docker-compose logs rabbitmq

# Check worker logs
docker-compose logs worker-1

# Restart workers
docker-compose restart worker-1 worker-2 worker-3
```

---

## 📊 Monitoring

### Access Dashboards

**RabbitMQ Management:**
- URL: http://localhost:15672
- Login: guest / guest
- View queues, messages, connections

**Neo4j Browser:**
- URL: http://localhost:7474
- Login: neo4j / [your NEO4J_PASSWORD]
- Query graph data

**API Documentation:**
- URL: http://localhost:8000/docs
- Interactive API testing

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# All services
docker-compose ps
```

### Log Aggregation

```bash
# Follow all logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Since timestamp
docker-compose logs --since 2024-01-01T00:00:00 backend
```

---

## 🔄 Updates and Maintenance

### Updating Application Code

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

### Database Migrations

```bash
# Backup first
./backup.sh

# Run migrations (if needed)
docker-compose exec backend python -m alembic upgrade head

# Verify
docker-compose logs backend
```

### Cleaning Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (CAREFUL!)
docker volume prune

# Remove all stopped containers
docker container prune
```

---

## 📈 Scaling Guide

### Horizontal Scaling

**Add More Workers:**
```yaml
# docker-compose.yml
worker-4:
  build:
    context: ./backend
    dockerfile: Dockerfile.worker
  # ... (same config as worker-1)
```

**Load Balance Backend:**
```yaml
backend:
  deploy:
    replicas: 3  # Multiple backend instances
```

### Vertical Scaling

**Increase Resources:**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### Database Scaling

**Redis Cluster:**
- Switch to Redis Cluster for distributed caching
- Update connection strings

**Neo4j Cluster:**
- Use Neo4j Enterprise for clustering
- Configure causal cluster

---

## 🎓 Next Steps

1. **Configure Custom Domain**: Point your domain to server
2. **Enable SSL**: Use Certbot or Cloudflare
3. **Set Up Monitoring**: Add Prometheus + Grafana
4. **Configure Backups**: Schedule automated backups
5. **Add CI/CD**: GitHub Actions for automated deployment
6. **Scale Workers**: Add more workers for high load
7. **Optimize Performance**: Tune database settings

---

## 📞 Support

For issues or questions:
- Check logs: `./logs.sh`
- Review troubleshooting section
- Check GitHub issues
- Contact support team

---

## 📝 License

See LICENSE file for details.
