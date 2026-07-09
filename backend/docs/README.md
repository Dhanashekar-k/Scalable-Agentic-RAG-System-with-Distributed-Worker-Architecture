# Agentic RAG System

A **production-ready, scalable AI-backed backend** with dual RAG pipelines: **Normal RAG** (fast, simple queries) and **Agentic RAG** (multi-step reasoning for complex queries).

## 🎯 System Overview

```
Client Request
     ↓
Semantic Cache Check (Redis)
     ↓ (miss)
Query Router (decides pipeline)
     ↓
├─→ Normal RAG (simple)
│   ├─ Embed
│   ├─ Retrieve (ChromaDB)
│   └─ Generate (Groq)
│
└─→ Agentic RAG (complex)
    ├─ LangGraph Planning
    ├─ RabbitMQ Execution
    ├─ Workers (retrieve + reason)
    ├─ Neo4j Graph Reasoning
    └─ Evaluation + Optional Replan
```

## 🏗️ Architecture Highlights

### **Two AI Pipelines**
1. **Normal RAG**: Single retrieval + single LLM call (fast path)
2. **Agentic RAG**: Multi-step planning + reasoning (deep path)

### **Key Components**
- **LangGraph**: Agent planning brain (decision-only, no execution)
- **RabbitMQ**: Step execution queue (bounded, retriable)
- **Redis**: Semantic prompt cache + short-lived state
- **ChromaDB**: Vector similarity search (shared by both pipelines)
- **Neo4j**: Graph reasoning for entity relationships
- **FastAPI**: Async REST API

### **Design Principles**
- ✅ Semantic caching checks FIRST
- ✅ All loops are bounded (max steps, max replans)
- ✅ Clear separation: planning vs execution
- ✅ Async everywhere possible
- ✅ Retry logic with limits
- ✅ Pydantic models for all data

---

## 📁 Project Structure

```
.
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── main.py                    # FastAPI application
├── worker_main.py             # RabbitMQ worker startup
├── config/
│   └── settings.py            # Configuration management
├── models/
│   └── schemas.py             # Pydantic models
├── database/
│   ├── redis_client.py
│   ├── chroma_client.py
│   └── neo4j_client.py
├── services/
│   ├── embedding_service.py   # Sentence transformers
│   ├── semantic_cache.py      # Semantic prompt cache
│   ├── router.py              # Query routing logic
│   ├── normal_rag.py          # Simple RAG pipeline
│   └── agentic_rag/
│       ├── langgraph_planner.py  # Agent brain
│       ├── orchestrator.py       # Coordinates execution
│       └── worker.py             # RabbitMQ consumer
└── utils/
    └── rabbitmq_client.py
```

---

## 🚀 Quick Start

**📘 For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

### 1. Prerequisites
- Python 3.10+
- Homebrew (macOS) or system package manager
- Groq API key (free tier available)

### 2. Install Infrastructure Services

#### **🎯 Automated Setup (Recommended)**

```bash
# Navigate to project directory
cd /Users/samrudhp/Projects-git/Scalable RAG/backend

# Run setup script (installs & starts all services)
./setup_services.sh

# Verify services are running
./check_services.sh
```

#### **📋 Manual Setup**

#### **macOS (Homebrew)**

**Redis:**
```bash
# Install
brew install redis

# Start Redis
brew services start redis

# Verify it's running
redis-cli ping  # Should return "PONG"
```

**RabbitMQ:**
```bash
# Install
brew install rabbitmq

# Start RabbitMQ
brew services start rabbitmq

# Verify it's running (wait ~30 seconds after starting)
curl http://localhost:15672  # Management UI

# Default credentials: guest/guest
```

**Neo4j:**
```bash
# Install
brew install neo4j

# Start Neo4j
brew services start neo4j

# Wait ~30 seconds, then access browser UI
open http://localhost:7474

# Default credentials: neo4j/neo4j
# On first login, you'll be prompted to change password to: password
```

#### **Ubuntu/Debian**

**Redis:**
```bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis
redis-cli ping  # Should return "PONG"
```

**RabbitMQ:**
```bash
sudo apt install rabbitmq-server -y
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
```

**Neo4j:**
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j -y
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

### 3. Install Python Dependencies

```bash
# Navigate to project directory
cd /Users/samrudhp/Projects-git/Scalable RAG/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Groq API key
nano .env  # or code .env
```

**Update .env with:**
```env
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# Services (already configured for localhost)
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### 5. Verify Services Are Running

```bash
# Check Redis
redis-cli ping

# Check RabbitMQ
curl http://localhost:15672

# Check Neo4j
curl http://localhost:7474

# All should respond successfully
```

### 6. Run the System

**Terminal 1 - FastAPI Server:**
```bash
python main.py
# Should see: "✅ All services initialized"
# API running at: http://localhost:8000
```

**Terminal 2 - Agent Worker:**
```bash
python worker_main.py
# Should see: "Agent Worker started, waiting for steps..."
```

### 7. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Simple query (Normal RAG)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}'

# Complex query (Agentic RAG)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze the relationship between Python, Django, and Flask, comparing their use cases"}'

# Cache statistics
curl http://localhost:8000/cache/stats
```

---

## 🛠️ Troubleshooting

### **Service Connection Issues**

**Redis not connecting:**
```bash
# Check if running
brew services list | grep redis
# or
sudo systemctl status redis

# Test connection
redis-cli ping

# Restart if needed
brew services restart redis
# or
sudo systemctl restart redis
```

**RabbitMQ not connecting:**
```bash
# Check if running
brew services list | grep rabbitmq
# or
sudo systemctl status rabbitmq-server

# Enable management plugin
sudo rabbitmq-plugins enable rabbitmq_management

# Check management UI
open http://localhost:15672

# Restart if needed
brew services restart rabbitmq
```

**Neo4j not connecting:**
```bash
# Check if running
brew services list | grep neo4j
# or
sudo systemctl status neo4j

# Access browser UI
open http://localhost:7474

# Reset password if needed (first login)
# Default: neo4j/neo4j → Change to: neo4j/password

# Restart if needed
brew services restart neo4j
```

### **Python Environment Issues**

```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.10+
```

### **Port Conflicts**

If ports are already in use:

```bash
# Find what's using the port
lsof -i :6379  # Redis
lsof -i :5672  # RabbitMQ
lsof -i :7687  # Neo4j
lsof -i :8000  # FastAPI

# Kill the process if needed
kill -9 <PID>
```

---

## 🔧 Service Management

### **Start All Services:**
```bash
# macOS
brew services start redis
brew services start rabbitmq
brew services start neo4j

# Linux
sudo systemctl start redis
sudo systemctl start rabbitmq-server
sudo systemctl start neo4j
```

### **Stop All Services:**
```bash
# macOS
brew services stop redis
brew services stop rabbitmq
brew services stop neo4j

# Linux
sudo systemctl stop redis
sudo systemctl stop rabbitmq-server
sudo systemctl stop neo4j
```

### **Check Service Status:**
```bash
# macOS
brew services list

# Linux
sudo systemctl status redis
sudo systemctl status rabbitmq-server
sudo systemctl status neo4j
```
  -d '{"query": "What is Python?"}'

# Complex query (Agentic RAG)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze the relationship between Python, Django, and Flask, comparing their use cases"}'

# Check health
curl http://localhost:8000/health

# Cache statistics
curl http://localhost:8000/cache/stats
```

---

## 🔧 Configuration

Key settings in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key (required) | - |
| `GROQ_MODEL` | Groq model to use | llama-3.1-70b-versatile |
| `CACHE_SIMILARITY_THRESHOLD` | Cache hit threshold | 0.92 |
| `COMPLEXITY_THRESHOLD` | Router threshold for Agentic RAG | 0.6 |
| `MAX_AGENT_STEPS` | Max steps per agent execution | 5 |
| `MAX_REPLANS` | Max replanning attempts | 1 |
| `RETRIEVAL_TOP_K` | Documents to retrieve | 5 |

---

## 📊 API Endpoints

### `POST /query`
Main query endpoint.

**Request:**
```json
{
  "query": "Your question here",
  "use_cache": true,
  "force_agentic": false
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "answer": "Generated answer",
  "confidence": 0.85,
  "pipeline_used": "normal_rag",
  "metadata": {
    "num_documents": 5,
    "retrieval_mode": "vector_only"
  },
  "processing_time_ms": 450.2
}
```

### `GET /health`
System health check.

### `GET /cache/stats`
Semantic cache statistics.

---

## 🧠 How It Works

### Normal RAG Flow
1. Embed query using sentence-transformers
2. Retrieve top-k documents from ChromaDB
3. Generate answer with Groq (Llama 3.1)
4. Return immediately

**Use case**: Simple factual queries

### Agentic RAG Flow
1. **LangGraph Planning**:
   - Classify query complexity
   - Extract entities
   - Decide retrieval strategy (vector/hybrid/graph)
   - Plan execution steps

2. **RabbitMQ Execution**:
   - Orchestrator publishes steps to queue
   - Workers consume and execute:
     - Retrieve from ChromaDB/Neo4j
     - Reason using LLM
   - Store results in Redis

3. **Evaluation**:
   - Check answer relevance
   - Verify entity coverage
   - Assess completeness

4. **Optional Replan** (max 1):
   - If answer fails evaluation
   - Execute one refined step
   - Generate final answer

**Use case**: Complex queries requiring reasoning

### Semantic Cache
- Embeds incoming queries
- Finds similar cached queries (cosine similarity)
- Returns cached answer if similarity ≥ threshold
- Stores successful answers with TTL

---

## 🔬 Data Ingestion

To add documents to ChromaDB (example script):

```python
from database.chroma_client import chroma_client
from services.embedding_service import embedding_service

# Initialize
chroma_client.connect()
embedding_service.load_model()

# Add documents
documents = ["Document 1 content", "Document 2 content"]
metadatas = [{"source": "doc1"}, {"source": "doc2"}]
ids = ["doc1", "doc2"]

chroma_client.add_documents(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)
```

For Neo4j graph data:

```python
from database.neo4j_client import neo4j_client

await neo4j_client.connect()

# Add entities
await neo4j_client.add_entity("Python", "programming_language")
await neo4j_client.add_entity("Django", "framework")

# Add relationships
await neo4j_client.add_relationship(
    "Django",
    "Python",
    "BUILT_WITH",
    {"year": 2005}
)
```

---

## 🎯 Interview Talking Points

### SDE Focus
- **Architecture**: Clean separation of concerns, async design
- **Scalability**: RabbitMQ for horizontal worker scaling
- **Reliability**: Bounded loops, retry logic, health checks
- **Caching**: Semantic cache reduces latency and costs
- **API Design**: RESTful, Pydantic validation, proper error handling

### AI Engineer Focus
- **Dual Pipelines**: Optimized for both speed and complexity
- **Agentic Design**: LangGraph for planning, workers for execution
- **Retrieval Strategy**: Vector + graph hybrid approach
- **Evaluation Loop**: Quality checks with replanning
- **Embedding Consistency**: Single model across all components

### System Design
- **Trade-offs**: Speed vs accuracy (Normal vs Agentic)
- **Bounded Complexity**: Max steps, timeouts, retry limits
- **State Management**: Redis for short-lived, Neo4j for long-term
- **Message Queue**: Decouples planning from execution

---

## 🐛 Troubleshooting

**ChromaDB not persisting?**
- Check `CHROMA_PERSIST_DIR` path exists
- Ensure write permissions

**RabbitMQ connection failed?**
- Verify `docker-compose ps` shows rabbitmq running
- Check ports 5672 (AMQP) and 15672 (management UI)

**Neo4j authentication error?**
- Default credentials: `neo4j/password`
- Change in `docker-compose.yml` and `.env`

**Worker not consuming?**
- Ensure worker_main.py is running
- Check RabbitMQ management UI: http://localhost:15672

**Cache not hitting?**
- Lower `CACHE_SIMILARITY_THRESHOLD`
- Check Redis connection
- Verify embeddings are consistent

---

## 📚 Tech Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API | FastAPI | Async REST endpoints |
| Models | Pydantic | Type-safe data validation |
| Planning | LangGraph | Agent decision graph |
| Queue | RabbitMQ | Step execution |
| Cache | Redis | Semantic cache + state |
| Vector DB | ChromaDB | Similarity search |
| Graph DB | Neo4j | Entity reasoning |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 |
| LLM | Groq | Llama 3.1 70B |

---

## 🎓 Key Concepts

**Why two pipelines?**
- Most queries are simple → fast path optimized
- Complex queries need reasoning → deep path available
- Router automatically decides based on complexity

**Why LangGraph?**
- Declarative agent planning
- State management built-in
- Conditional flows for decision-making

**Why RabbitMQ?**
- Decouples planning from execution
- Enables horizontal scaling of workers
- Provides message persistence and retries

**Why semantic cache?**
- Similar questions get similar answers
- Reduces LLM costs and latency
- Embedding similarity more robust than exact match

**Why Neo4j?**
- Multi-hop reasoning on relationships
- Contradiction detection
- Entity-centric knowledge graph

---

## 📈 Future Enhancements

- [ ] Add authentication and rate limiting
- [ ] Implement streaming responses
- [ ] Add observability (OpenTelemetry)
- [ ] Support multiple LLM providers
- [ ] Add data ingestion API
- [ ] Implement user feedback loop
- [ ] Add persistent conversation history
- [ ] Create admin dashboard

---

## 📄 License

This is a portfolio/resume project demonstrating production-ready AI system architecture.

---

## 🙏 Acknowledgments

Built to demonstrate:
- Clean backend architecture
- AI/ML engineering best practices
- Scalable system design
- Production-ready code quality

Perfect for showcasing in **SDE** and **AI Engineer** interviews.
