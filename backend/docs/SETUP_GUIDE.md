# 🚀 Complete Setup Guide - No Docker Required

## Quick Summary

**What you need:**
1. ✅ Redis (cache)
2. ✅ RabbitMQ (message queue)
3. ✅ Neo4j (graph database)
4. ✅ Groq API key (free)
5. ✅ Python 3.10+

---

## Option 1: Automated Setup (Easiest) ⚡

```bash
cd /Users/samrudhp/Projects-git/Scalable RAG/backend
./setup_services.sh
```

This script will:
- Install Redis, RabbitMQ, Neo4j
- Start all services
- Verify they're running

**Then skip to Step 3 below.**

---

## Option 2: Manual Setup (Step-by-Step) 📝

### Step 1: Install Services

#### macOS (Homebrew)

```bash
# Install services
brew install redis rabbitmq neo4j

# Start services
brew services start redis
brew services start rabbitmq
brew services start neo4j

# Verify
brew services list
```

#### Ubuntu/Debian

```bash
# Redis
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis

# RabbitMQ
sudo apt install rabbitmq-server -y
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management

# Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j -y
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

### Step 2: Verify Services

```bash
# Test Redis
redis-cli ping  # Should return "PONG"

# Test RabbitMQ
curl http://localhost:15672  # Management UI (guest/guest)

# Test Neo4j
open http://localhost:7474  # Browser UI (neo4j/neo4j → change to neo4j/password)
```

---

## Step 3: Get Groq API Key (Free) 🔑

1. Visit: https://console.groq.com/
2. Sign up (Google/GitHub/Email)
3. Go to: https://console.groq.com/keys
4. Click "Create API Key"
5. Copy the key (starts with `gsk_`)

**Free Tier:** 14,000 requests/day

---

## Step 4: Python Setup

```bash
cd /Users/samrudhp/Projects-git/Scalable RAG/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env
nano .env  # or code .env or vim .env
```

**Add your Groq key:**
```env
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# These should already be correct:
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

---

## Step 6: Set Neo4j Password

**First time only:**

1. Visit: http://localhost:7474
2. Login with: `neo4j` / `neo4j`
3. You'll be prompted to change password
4. Set new password to: `password`

---

## Step 7: Run the System 🎉

**Terminal 1 - FastAPI Server:**
```bash
cd /Users/samrudhp/Projects-git/Scalable RAG/backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Worker Process:**
```bash
cd /Users/samrudhp/Projects-git/Scalable RAG/backend
source venv/bin/activate
python worker_main.py
```

**Expected Output:**
```
Terminal 1:
🚀 Starting Agentic RAG System...
✅ All services initialized

Terminal 2:
Agent Worker started, waiting for steps...
```

---

## Step 8: Test It! 🧪

```bash
# Health check
curl http://localhost:8000/health

# Simple query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'

# Complex query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare supervised and unsupervised learning"}'
```

---

## 🛠️ Common Issues & Solutions

### "Connection refused" errors

**Check if services are running:**
```bash
# macOS
brew services list

# Linux
sudo systemctl status redis
sudo systemctl status rabbitmq-server
sudo systemctl status neo4j
```

**Restart services:**
```bash
# macOS
brew services restart redis
brew services restart rabbitmq
brew services restart neo4j

# Linux
sudo systemctl restart redis
sudo systemctl restart rabbitmq-server
sudo systemctl restart neo4j
```

### "Port already in use"

```bash
# Find what's using the port
lsof -i :6379  # Redis
lsof -i :5672  # RabbitMQ
lsof -i :7687  # Neo4j

# Kill if needed
kill -9 <PID>
```

### Neo4j authentication failed

```bash
# Reset Neo4j password
neo4j-admin set-initial-password password

# Restart Neo4j
brew services restart neo4j
# or
sudo systemctl restart neo4j
```

### Python package errors

```bash
# Make sure venv is activated
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Service Management

### Start All Services

```bash
# macOS
brew services start redis rabbitmq neo4j

# Linux
sudo systemctl start redis rabbitmq-server neo4j
```

### Stop All Services

```bash
# macOS
brew services stop redis rabbitmq neo4j

# Linux
sudo systemctl stop redis rabbitmq-server neo4j
```

### Check Status

```bash
# macOS
brew services list

# Linux
systemctl status redis rabbitmq-server neo4j
```

---

## 🎯 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **RabbitMQ Management** | http://localhost:15672 | guest/guest |
| **Neo4j Browser** | http://localhost:7474 | neo4j/password |
| **Redis CLI** | `redis-cli` | - |

---

## 💡 Pro Tips

1. **Auto-start on boot (macOS):**
   ```bash
   brew services start redis  # Already persists
   ```

2. **Monitor RabbitMQ queues:**
   - Visit: http://localhost:15672
   - Login: guest/guest
   - Go to "Queues" tab

3. **Redis data inspection:**
   ```bash
   redis-cli
   > KEYS *
   > GET semantic_cache:1234567
   ```

4. **Neo4j query console:**
   - Visit: http://localhost:7474
   - Run: `MATCH (n) RETURN n LIMIT 10`

---

## ✅ You're All Set!

The system is now running locally without Docker. All data persists across restarts.

**Need help?** Check the main [README.md](README.md) for API documentation and architecture details.
