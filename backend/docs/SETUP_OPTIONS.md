# Setup Options Comparison

Choose the setup that best fits your needs.

---

## 📊 Quick Comparison

| Feature | All Native | **Hybrid** ⭐ | All Docker |
|---------|-----------|-----------|-----------|
| **Docker Required** | ❌ No | ✅ Yes | ✅ Yes |
| **System Clutter** | High | Low | None |
| **Easy Cleanup** | Hard | Easy | Very Easy |
| **Data Persistence** | ✅ Full | ✅ Neo4j only | ⚠️ Requires volumes |
| **Startup Speed** | Fast | Medium | Medium |
| **Best For** | No Docker | Most users | Clean slate |

---

## Option 1: All Native 💻

**Setup:**
```bash
./setup_services.sh
```

**What it does:**
- Installs Redis, RabbitMQ, Neo4j on your system
- Starts them as system services
- They run on boot

**When to use:**
- ✅ Don't have/want Docker
- ✅ Need maximum performance
- ✅ Want full control

**Management:**
```bash
# macOS
brew services start redis rabbitmq neo4j
brew services stop redis rabbitmq neo4j

# Linux
sudo systemctl start redis rabbitmq-server neo4j
sudo systemctl stop redis rabbitmq-server neo4j
```

---

## Option 2: Hybrid 🎯 **RECOMMENDED**

**Setup:**
```bash
./setup_hybrid.sh
```

**What it does:**
- Docker: Redis + RabbitMQ (temporary data)
- Native: Neo4j (persistent graph data)

**Why this is best:**
- ✅ Redis/RabbitMQ are cache/queue (ephemeral) → Perfect for containers
- ✅ Neo4j has valuable graph data → Keep accessible
- ✅ Easy to clean up Redis/RabbitMQ
- ✅ Direct access to Neo4j data

**Management:**
```bash
# Start/stop Docker services
docker-compose -f docker-compose.minimal.yml up -d
docker-compose -f docker-compose.minimal.yml down

# View logs
docker-compose -f docker-compose.minimal.yml logs -f

# Neo4j (native)
brew services start neo4j  # macOS
sudo systemctl start neo4j  # Linux
```

---

## Option 3: All Docker 🐳

**Setup:**
```bash
docker-compose up -d
```

**What it does:**
- Everything in containers
- Clean slate approach

**When to use:**
- ✅ Want clean system
- ✅ Temporary project
- ✅ Testing/demo

**Management:**
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Complete cleanup (removes data)
docker-compose down -v
```

---

## 🎯 My Recommendation

### For Development: **Hybrid Setup** ⭐

**Why?**

1. **Redis** - Just a cache, loses data anyway → Container perfect
2. **RabbitMQ** - Message queue, ephemeral → Container perfect  
3. **Neo4j** - Graph database with relationships → Keep native for easy access

**Quick Start:**
```bash
# One command setup
./setup_hybrid.sh

# That's it! Now just:
# 1. Set Neo4j password (http://localhost:7474)
# 2. Add Groq key to .env
# 3. Run: python main.py
```

---

## 🛠️ Switching Between Options

### From Native → Hybrid

```bash
# Stop native services
brew services stop redis rabbitmq  # macOS
sudo systemctl stop redis rabbitmq-server  # Linux

# Start Docker containers
docker-compose -f docker-compose.minimal.yml up -d
```

### From Hybrid → All Docker

```bash
# Stop Neo4j native
brew services stop neo4j  # macOS
sudo systemctl stop neo4j  # Linux

# Use full docker-compose
docker-compose up -d
```

### From Docker → Native

```bash
# Stop all containers
docker-compose down

# Run native setup
./setup_services.sh
```

---

## 📝 Port Reference

| Service | Port | Access |
|---------|------|--------|
| Redis | 6379 | `redis-cli` |
| RabbitMQ AMQP | 5672 | Application |
| RabbitMQ UI | 15672 | http://localhost:15672 |
| Neo4j HTTP | 7474 | http://localhost:7474 |
| Neo4j Bolt | 7687 | Application |
| FastAPI | 8000 | http://localhost:8000 |

All work the same regardless of native/Docker!

---

## 💡 Pro Tips

**Hybrid is best because:**
```bash
# Redis/RabbitMQ: Throw away containers anytime
docker-compose -f docker-compose.minimal.yml down
docker-compose -f docker-compose.minimal.yml up -d

# Neo4j: Access data directly
open http://localhost:7474
# Run queries, export data, backup easily

# System stays clean!
```

**Check what's running:**
```bash
# Docker services
docker ps

# Native services (macOS)
brew services list

# Native services (Linux)
systemctl status neo4j
```

---

## ✅ Final Recommendation

**Use the Hybrid Setup** unless you have a specific reason not to.

```bash
./setup_hybrid.sh
```

Simple, clean, and gives you the best of both worlds! 🎉
