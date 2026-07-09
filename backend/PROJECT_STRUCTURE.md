# Scalable RAG Backend - Project Structure

``` markdown

backend/
├── config/                 # Configuration files
│   └── settings.py        # Pydantic settings, environment variables
│
├── database/              # Database clients
│   ├── chroma_client.py   # ChromaDB vector store
│   ├── neo4j_client.py    # Neo4j graph database
│   └── redis_client.py    # Redis cache & storage
│
├── models/                # Data models
│   └── schemas.py         # Pydantic models for API and internal data
│
├── services/              # Business logic
│   ├── agentic_rag/       # Agentic RAG pipeline
│   │   ├── __init__.py
│   │   ├── langgraph_planner.py    # LangGraph-based query planning
│   │   ├── orchestrator.py         # Orchestrates agentic pipeline
│   │   └── worker.py               # RabbitMQ worker for async steps
│   ├── embedding_service.py        # Text embedding generation
│   ├── entity_matcher.py           # Semantic entity matching for Neo4j
│   ├── normal_rag.py               # Simple RAG pipeline
│   ├── router.py                   # Query complexity router
│   └── semantic_cache.py           # Redis-based semantic cache
│
├── utils/                 # Utilities
│   └── rabbitmq_client.py # RabbitMQ message queue client
│
├── docs/                  # Documentation
│   ├── ARCHITECTURE_EXPLAINED.py   # System architecture overview
│   ├── README.md                   # Main documentation
│   ├── ROBUSTNESS_ROADMAP.md       # Production readiness roadmap
│   ├── SETUP_GUIDE.md              # Setup instructions
│   └── SETUP_OPTIONS.md            # Infrastructure setup options
│
├── tests/                 # Test files
│   ├── test_all_services.py        # Comprehensive service tests
│   ├── test_robustness.py          # Robustness & load tests
│   ├── test_agentic_rag.py         # Agentic RAG async tests
│   ├── test_agentic_quick.py       # Quick agentic test
│   ├── test_database_usage.py      # DB usage verification
│   ├── test_fresh_queries.py       # Router decision tests
│   ├── test_hybrid_quick.py        # Hybrid mode tests
│   ├── test_matcher.py             # Entity matcher tests
│   ├── test_router_decision.py     # Router accuracy tests
│   ├── test_worker.py              # Worker functionality tests
│   ├── verify_services.py          # Service health checks
│   ├── verify_chromadb.py          # ChromaDB verification
│   ├── quick_test.py               # Basic API test
│   ├── check_hybrid_results.py     # Debug hybrid results
│   ├── check_neo4j_entities.py     # Neo4j entity inspector
│   ├── check_step_results.py       # Redis step result checker
│   ├── debug_entity_matching.py    # Entity matcher debugger
│   └── clear_cache.py              # Cache clearing utility
│
├── main.py                # FastAPI application (REST API server)
├── worker_main.py         # RabbitMQ worker process
├── ingest_data.py         # Data ingestion script
├── STATUS_REPORT.py       # System status reporter
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Full Docker setup
├── docker-compose.minimal.yml  # Minimal Docker (Redis + RabbitMQ)
├── setup_services.sh      # Service setup script
├── setup_hybrid.sh        # Hybrid infrastructure setup
└── check_services.sh      # Service health checker
```

## Running Tests

```bash
# All service tests
python tests/test_all_services.py

# Robustness tests (load, concurrency, error handling)
python tests/test_robustness.py

# Agentic RAG async pipeline
python tests/test_agentic_rag.py

# Hybrid mode (ChromaDB + Neo4j)
python tests/test_hybrid_quick.py

# Quick API test
python tests/quick_test.py

# Verify all services
python tests/verify_services.py
```

## Key Components

### Main API (`main.py`)

- FastAPI REST API server
- Endpoints: `/query`, `/agent/async`, `/agent/status/{id}`, `/health`, `/cache/stats`
- Synchronous and asynchronous query processing

### Worker (`worker_main.py`)

- Background worker for async agentic tasks
- Consumes steps from RabbitMQ
- Executes retrieval and reasoning steps
- Stores results in Redis

### Router (`services/router.py`)

- Analyzes query complexity
- Routes to Normal RAG or Agentic RAG
- Uses LLM-based scoring with heuristic fallback

### Normal RAG (`services/normal_rag.py`)

- Simple, fast RAG pipeline
- Vector search in ChromaDB
- Direct LLM answer generation
- ~1 second response time

### Agentic RAG (`services/agentic_rag/`)

- Complex multi-step pipeline
- LangGraph planning
- Hybrid retrieval (vector + graph)
- Multi-hop reasoning
- ~4-5 second response time

### Entity Matcher (`services/entity_matcher.py`)

- Semantic entity matching using embeddings
- Type-based inference for generic terms
- No hardcoded mappings
- Enables hybrid ChromaDB + Neo4j retrieval

## Documentation

See `docs/` folder for:

- **README.md**: Project overview

- **ARCHITECTURE_EXPLAINED.py**: Detailed architecture
- **ROBUSTNESS_ROADMAP.md**: Production readiness plan
- **SETUP_GUIDE.md**: Setup instructions
- **SETUP_OPTIONS.md**: Infrastructure options
