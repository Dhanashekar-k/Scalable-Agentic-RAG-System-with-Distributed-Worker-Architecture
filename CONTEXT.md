# Niyanta: Agentic RAG System - Complete Project Context

## Project Overview

**Niyanta** is an enterprise-grade **Agentic Retrieval-Augmented Generation (RAG)** system designed for the financial domain. It combines autonomous query planning with distributed worker execution to provide intelligent, context-aware answers to complex financial questions.

### Key Characteristics
- **Domain**: Financial services, compliance, banking concepts
- **Architecture**: Distributed, scalable, event-driven
- **LLM Framework**: LangGraph for planning, Groq for synthesis
- **Message Queue**: RabbitMQ for distributed task execution
- **Caching**: Redis for semantic cache and results
- **Data Stores**: ChromaDB (vectors), Neo4j (graphs)
- **API**: FastAPI (async, single-threaded with event loop)

---

## System Architecture

### High-Level Flow

```
Client Request
    ↓
API (/query endpoint)
    ↓
[1] Semantic Cache Check (Redis)
    ├─ Hit: Return cached answer
    └─ Miss: Continue
    ↓
[2] Query Router Decision
    ├─ Simple query → Normal RAG
    └─ Complex query → Agentic RAG
    ↓
[3] LangGraph Planner (if Agentic)
    ├─ Classify query (LLM: Groq)
    ├─ Extract entities (LLM: Groq)
    ├─ Decide retrieval mode (Rules)
    ├─ Plan steps (up to 5)
    └─ Max 1 replan attempt (Rules)
    ↓
[4] Orchestrator Execution
    ├─ Publish steps to RabbitMQ
    ├─ Worker pool processes steps
    ├─ Wait for results in Redis
    ├─ Synthesize answer (LLM: Groq)
    ├─ Evaluate quality (Heuristics)
    └─ Optional replan if low quality
    ↓
[5] Cache Storage (Redis)
    └─ Store for future similar queries
    ↓
Return Answer + Confidence
```

### Components Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                       │
│              Single thread + asyncio event loop               │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                   Semantic Cache (Redis)                      │
│          Query similarity matching, 24-hour TTL              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                    Query Router                               │
│         Classification: Simple vs Complex vs Agentic         │
└──────────────────────────────────────────────────────────────┘
                    ↙                    ↖
        ┌─────────────────┐      ┌─────────────────┐
        │  Normal RAG     │      │  Agentic RAG    │
        │  (1 LLM call)   │      │  (2+ LLM calls) │
        └─────────────────┘      └─────────────────┘
                                       ↓
                        ┌──────────────────────────┐
                        │  LangGraph Planner (6    │
                        │  nodes, state machine)   │
                        └──────────────────────────┘
                                       ↓
                        ┌──────────────────────────┐
                        │    Orchestrator          │
                        │  (Plan execution + LLM)  │
                        └──────────────────────────┘
                                       ↓
              ┌────────────────────────┼────────────────────────┐
              ↓                        ↓                        ↓
    ┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │  RabbitMQ Queue  │    │  Redis Results   │    │  Groq LLM API   │
    │  (Task Delivery) │    │  (Caching)       │    │  (Synthesis)    │
    └──────────────────┘    └──────────────────┘    └─────────────────┘
              ↓
    ┌──────────────────────────────────────┐
    │    Worker Pool (N instances)         │
    │  Each processes ONE step at a time   │
    └──────────────────────────────────────┘
              ↓
      ┌───────┴───────┬─────────────┐
      ↓               ↓             ↓
   ChromaDB        Neo4j         Groq LLM
  (Vector DB)   (Graph DB)   (Reasoning)
```

---

## Core Components in Detail

### 1. LangGraph Planner (Planning Phase)

**Purpose**: Autonomous decision-making for query execution

**Structure**: 6-node state machine

```
Node 1: classify_query (LLM)
  Input: query + chat_history
  Output: query_classification (factual/reasoning/conversation)
  
Node 2: extract_entities (LLM)
  Input: query + classification
  Output: entities, time_range
  
Node 3: decide_retrieval (Rules)
  Input: classification + entities
  Output: retrieval_mode (semantic/graph/both)
  
Node 4: plan_next_step (Rules)
  Input: current step count
  Output: incremented counter + add step to plan
  
Node 5: check_stop_or_continue (Rules)
  Input: step_count + confidence + classification
  Output: should_continue boolean
  
Node 6: decide_replan (Rules)
  Input: replan_count + retrieval_mode
  Output: toggle mode or stop (max 1 replan)
```

**Output**: AgentPlan with classification, entities, retrieval_mode, steps list

**LLM Calls**: 2 per request (classification + extraction)

---

### 2. Orchestrator (Execution Coordination)

**Purpose**: Execute plan, manage workers, synthesize answer

**Flow**:
1. Get plan from LangGraph
2. Execute plan steps via RabbitMQ
3. Wait for worker results (polling Redis)
4. Synthesize answer with LLM
5. Evaluate answer quality
6. Optionally replan (max 1 additional step)

**LLM Calls**: 1 per request (answer synthesis) + 1 for reasoning step (optional)

**Key Decision: Polling vs Callbacks**
- Uses polling (500ms intervals) instead of callbacks
- Simple, works for 5-10s latency budget
- Callbacks would be overkill for current latency budget

---

### 3. Worker Pool (Distributed Execution)

**Purpose**: Execute individual steps in parallel, scale horizontally

**Architecture**:
- Stateless consumer processes
- RabbitMQ prefetch_count=1 (fair distribution)
- Process ONE step at a time
- Auto-retries (max 3 attempts)

**Step Types**:

**RETRIEVE Step**:
- Vector search (ChromaDB): Query embedding → find similar documents
- Graph search (Neo4j): Entity matching → traverse relationships (2 hops)
- Hybrid: Both in parallel
- Returns: Combined list of documents with metadata

**REASON Step**:
- LLM analysis (Groq): Analyze entity relationships
- Neo4j contradiction checking: Find conflicting information
- Returns: Reasoning analysis + contradictions

**Result Storage**: Redis with 10-minute TTL

---

### 4. Technologies Stack

| Component | Technology | Role |
|-----------|-----------|------|
| **API** | FastAPI | HTTP REST endpoints, async/await |
| **Planning** | LangGraph | State machine for query planning |
| **LLM** | Groq (Mixtral 8x7b) | Fast inference (~50ms), free tier |
| **Vector DB** | ChromaDB | 384-dim embeddings, semantic search |
| **Graph DB** | Neo4j (Bolt protocol) | Entity relationships, multi-hop queries |
| **Message Queue** | RabbitMQ (AMQP) | Distributed task delivery, persistence |
| **Cache/Results** | Redis | Semantic cache + step results |
| **Embeddings** | Sentence Transformers | Convert text to 384-dim vectors |
| **Concurrency** | asyncio | Single thread, event loop cooperation |
| **Processes** | Separate OS processes | Worker scalability, no GIL |

---

## Communication Protocols

| Protocol | Usage | From | To | Latency | Cost |
|----------|-------|------|-----|---------|------|
| **HTTP/REST** | API endpoints | Client | Backend API | <100ms | N/A |
| **AMQP** | Task distribution | Orchestrator | RabbitMQ | <1ms | Included |
| **Redis Protocol** | Caching & results | Workers/Orch | Redis | <10μs | Included |
| **Bolt** | Graph queries | Workers | Neo4j | 10-50ms | Included |
| **HTTPS** | External LLM | Orchestrator | Groq API | 50-200ms | $0.0001-0.001 |

---

## Data Flow Through System

### Request 1: "What is a savings account?"

```
[Semantic Cache] → HIT (simple factual query, cached)
[Return cached answer] → Client
Latency: ~10ms
LLM calls: 0
```

### Request 2: "Compare Tesla and Ford's EV strategies"

```
[Semantic Cache] → MISS
[Router] → COMPLEX (comparison, multi-entity)
[Planner] → 
  - classify: "reasoning"
  - extract_entities: ["Tesla", "Ford", "EV strategy"]
  - decide_retrieval: "both" (hybrid)
  - plan_steps: 2
[Orchestrator] →
  - Publish RETRIEVE step to RabbitMQ
  - Worker: Vector search (10 docs) + Graph search (5 relationships)
  - Publish REASON step to RabbitMQ
  - Worker: LLM analysis of relationships
  - Generate answer from combined context
  - Evaluate: confidence 0.85
  - No replan (high quality)
[Cache] → Store for future similar queries
[Return answer] → Client
Latency: ~5-10 seconds
LLM calls: 4 (2 planning + 1 synthesis + 1 reasoning)
```

---

## Key Architectural Decisions

### 1. Why LangGraph (Not LangChain Agents)?

```
LangGraph:
✓ Explicit state management (TypedDict)
✓ Visualizable DAG structure
✓ Testable planning nodes
✓ Fixed cost (2 LLM calls always)
✓ LangSmith integration

LangChain Agents:
✗ Hidden state in agent loop
✗ 5-10+ LLM calls variable
✗ Harder to test
✗ Less predictable
```

### 2. Why RabbitMQ (Not other queues)?

```
RabbitMQ:
✓ Durable queues (survives server restart)
✓ Persistent messages (survives broker crash)
✓ Fair dispatch (prefetch_count=1)
✓ ACK model (retries on failure)
✓ AMQP standard

Alternatives:
✗ Redis Streams: Not durable
✗ Kafka: Overkill, topic-based not task-based
✗ SQS: AWS-locked, higher latency
```

### 3. Why Polling (Not Callbacks)?

```
Polling:
✓ Simple, no special infrastructure
✓ Orchestrator is isolated
✓ No need for message routing back
✓ Works for 5-10s latency budget

Callbacks:
✗ Complex in distributed system
✗ Requires message routing to specific orchestrator
✗ Hard to handle failures
✗ Overkill for current latency needs
```

### 4. Why Rules-Based for Nodes 3-6 (Not LLM)?

```
LLM-based:
✗ 100-500ms per decision
✗ $0.001-0.01 cost per decision
✗ Non-deterministic
✗ Hard to audit

Rules-based:
✓ <1ms latency
✓ $0 cost
✓ 100% deterministic
✓ Easy to debug and modify

Hybrid approach:
- Nodes 1-2: LLM (understanding nuance)
- Nodes 3-6: Rules (speed + cost)
```

### 5. Why NO SQL Database?

```
Current data model:
✓ Polyglot persistence
  - Vectors → ChromaDB
  - Graphs → Neo4j
  - Semantic cache → Redis
  - Task results → Redis
✗ No relational data currently needed
✗ SQL would be overkill
✗ Specialized stores are faster

If relationships needed:
→ Add Neo4j relationships, not SQL
```

### 6. Why Async/Await + Processes (Not Threading)?

```
Threading:
✗ Python GIL prevents parallelism
✗ Deadlock risks with locks
✗ Race conditions in shared memory
✗ Very hard to debug

Async/Await:
✓ Single thread, event loop cooperation
✓ No locks or shared memory needed
✓ Clean, readable code
✓ Perfect for I/O-bound operations

Processes (for workers):
✓ True parallelism
✓ No shared memory
✓ Horizontal scalability
✓ Auto-restart on crash
```

---

## Request/Response Models

### QueryRequest

```python
{
  "query": "What is a savings account?",
  "use_cache": true,                    # Check semantic cache first
  "force_agentic": false               # Normal routing, not forced agentic
}
```

### QueryResponse

```python
{
  "request_id": "req_abc123",           # Server-generated UUID
  "answer": "A savings account is...",
  "confidence": 0.85,                   # 0.7-1.0 based on heuristics
  "pipeline": "agentic_rag",            # "cache" | "normal_rag" | "agentic_rag"
  "cache_hit": false,
  "sources": [],                        # Retrieved documents metadata
  "metadata": {
    "plan_classification": "reasoning",
    "entities": ["savings", "account"],
    "retrieval_mode": "both",
    "steps_executed": 2,
    "replanned": false
  },
  "processing_time_ms": 5230
}
```

---

## Current Gaps & Known Issues

### 1. **No Idempotency Keys from Client**

```
Issue:
- Every request generates new UUID (server-side)
- Client retries produce duplicate execution
- Financial transactions could double-charge

Should have:
- Optional idempotency_key in request
- Cache results by key (24-hour TTL)
- Return cached result on duplicate
```

### 2. **No Webhooks**

```
Current:
- Synchronous request-response only
- Client holds connection for 5-10 seconds

Should have for:
- Long-running queries (>30s)
- Batch processing
- Real-time progress updates
```

### 3. **No Strong Internal Idempotency**

```
Current:
- step_id is deterministic
- Results cached in Redis
- No lock mechanism during processing

Risk:
- If cache expires during processing
- Two workers could execute same step
- Race condition not prevented

Should add:
- SETNX lock during processing
- Explicit "processing" state flag
```

### 4. **Simple Evaluation Heuristics**

```
Current:
- Entity coverage >= 60%?
- Answer > 50 chars?
- Completeness > 100 chars?

Could improve with:
- LLM-based evaluation (costs extra)
- ML model trained on human feedback
- Semantic similarity scoring
```

---

## Scaling Considerations

### Horizontal Scaling

```
API Servers:
├─ Run multiple instances behind load balancer
├─ Each has own asyncio event loop
├─ No shared state between instances
└─ Scale: 1 to 1000+ requests/second

RabbitMQ:
├─ Single broker (or cluster)
├─ Message persistence
├─ Fair distribution via prefetch_count=1
└─ Bottleneck: usually not message queue

Worker Pool:
├─ Run 1 to 1000 worker instances
├─ Each independent, stateless
├─ Auto-scales based on queue depth
└─ Can add/remove dynamically

Redis:
├─ Single instance (or cluster)
├─ Results expire after 10 minutes
├─ Semantic cache data expires after 24 hours
└─ Bottleneck: memory for large caches

Neo4j:
├─ Single instance (or cluster)
├─ Graph traversal is 1-2 seconds
└─ Bottleneck: complex relationship queries

ChromaDB:
├─ Standalone or embedded
├─ Vector similarity search ~300ms
└─ Bottleneck: large document collections (>1M docs)
```

### Throughput Estimates

```
Single instance:
├─ Orchestrator: ~1 request per 5-10 seconds
├─ 1 worker: ~1 step per 1-2 seconds
└─ Throughput: ~3600-7200 queries/day

Scaled (10x):
├─ 10 API instances (load balanced)
├─ 10 workers (parallel processing)
└─ Throughput: ~36000-72000 queries/day
```

---

## LLM Usage Summary

### Total LLM Calls Per Request

| Scenario | Calls | Cost | Latency |
|----------|-------|------|---------|
| Cache hit | 0 | $0 | ~10ms |
| Normal RAG | 1 | <$0.0001 | 100-200ms |
| Agentic RAG (no reason) | 3 | <$0.0001 | 150-300ms |
| Agentic RAG (with reason) | 4 | <$0.0001 | 150-350ms |

### Models Used

- **Planning** (Classify + Extract): Groq Mixtral 8x7b
- **Synthesis** (Answer generation): Groq Mixtral 8x7b
- **Reasoning** (Optional): Groq Mixtral 8x7b

**Why Groq?**
- ~50ms latency per call
- ~$0.00001 per 1K tokens
- Free tier available

---

## Deployment Architecture

### Docker Compose Stack

```
Services:
├─ backend (FastAPI, asyncio)
├─ redis (Caching + results)
├─ chroma (Vector database)
├─ neo4j (Graph database)
├─ rabbitmq (Message queue)
├─ worker_1 (RabbitMQ consumer #1)
├─ worker_2 (RabbitMQ consumer #2)
└─ worker_N (RabbitMQ consumer #N)

Volumes:
├─ redis_data
├─ chroma_data
├─ neo4j_data
└─ neo4j_logs
```

### Port Mapping

```
API:        8000 (FastAPI)
Redis:      6379 (Protocol)
RabbitMQ:   5672 (AMQP)
RabbitMQ UI: 15672 (HTTP)
Neo4j:      7687 (Bolt)
Neo4j UI:   7474 (HTTP)
```

---

## Interview Preparation Topics

### 1. **System Architecture**
- How does agentic RAG differ from normal RAG?
- Why separate planning from execution?
- How do you handle distributed execution?

### 2. **RabbitMQ Deep Dive**
- Message persistence and reliability
- Fair distribution (prefetch_count=1)
- ACK model for retries
- Why not alternatives like Kafka, SQS?

### 3. **Redis Architecture**
- Semantic cache mechanics (45-60% hit rate)
- Dual usage: cache + step results
- Same instance, different namespaces
- TTL-based auto-cleanup

### 4. **LangGraph Planner**
- 6-node state machine design
- Hybrid LLM/rules approach
- Max 1 replan logic
- How it differs from LangChain agents

### 5. **Orchestrator Deep Dive**
- Step execution flow
- Result polling mechanism
- Answer synthesis and evaluation
- Replan decision logic

### 6. **Worker Execution**
- Parallel vector + graph retrieval
- Entity matching (semantic + keyword fallback)
- Retry logic with exponential backoff
- Error handling and graceful degradation

### 7. **Concurrency Model**
- Why async/await + processes?
- Python GIL explanation
- Event loop mechanics
- Horizontal scalability

### 8. **OS Concepts Used**
- Processes vs threads
- Network sockets and ports
- File descriptors
- Event-driven I/O (epoll/kqueue)
- Signals and graceful shutdown

---

## Project Statistics

### Code Structure

```
backend/
├─ main.py (416 lines, API endpoints)
├─ config/ (settings.py, configuration)
├─ database/ (redis_client, chroma_client, neo4j_client)
├─ models/ (schemas.py, Pydantic models)
├─ services/
│  ├─ embedding_service.py (text→vectors)
│  ├─ semantic_cache.py (query similarity)
│  ├─ router.py (classification logic)
│  ├─ normal_rag.py (simple pipeline)
│  └─ agentic_rag/
│     ├─ orchestrator.py (execution coordination)
│     ├─ langgraph_planner.py (planning)
│     └─ worker.py (step execution)
└─ utils/ (rabbitmq_client.py, etc.)
```

### Latency Breakdown

```
Per request (complex query):
├─ Cache check: 10ms
├─ Router decision: 20ms
├─ Planner (2 LLM calls): 200-300ms
├─ Orchestrator publish + wait: 5000-8000ms
│  ├─ Vector search: 300ms
│  ├─ Graph traversal: 800ms
│  ├─ LLM reasoning: 50ms
│  └─ Result polling: overhead
├─ Answer synthesis LLM: 50ms
├─ Evaluation: 5ms
└─ Total: 5.3-8.4 seconds
```

### Cost Breakdown

```
Per 1000 requests:
├─ LLM (Groq): $0.05-0.10
├─ Infrastructure: depends on deployment
├─ Vector DB: depends on doc count
├─ Graph DB: depends on relationship count
├─ Message Queue: included
├─ Cache: included
└─ Total: <$0.50 + infrastructure
```

---

## Key Takeaways for LLM Context

1. **Distributed Architecture**: Orchestrator + Worker pool for horizontal scaling
2. **Hybrid Intelligence**: LLM for understanding (classification), rules for decisions
3. **Event-Driven**: Async/await in API, separate processes for workers
4. **Polyglot Persistence**: ChromaDB + Neo4j + Redis (specialized stores)
5. **Message Queue Based**: RabbitMQ for reliable task distribution
6. **Constrained by Design**: Limited tools for financial domain reliability
7. **Production-Ready Pattern**: Polling, graceful degradation, retry logic
8. **Financial Focus**: Designed for accuracy, auditability, compliance

---

## Future Roadmap

### Short Term
- [ ] Add idempotency keys from client
- [ ] Implement distributed locks for strong idempotency
- [ ] Add webhook support for long-running queries

### Medium Term
- [ ] Implement webhook callbacks for async queries
- [ ] Add LLM-based evaluation (improve answer quality scoring)
- [ ] Learning loop: track which retrieval modes work best per classification

### Long Term
- [ ] Multi-modal support (images, tables)
- [ ] Tool extensibility framework (add custom retrieval tools)
- [ ] Advanced evaluation with human feedback loop
- [ ] Real-time streaming of planning/execution progress

