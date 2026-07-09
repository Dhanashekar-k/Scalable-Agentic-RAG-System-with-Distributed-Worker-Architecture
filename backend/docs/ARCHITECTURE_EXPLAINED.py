"""
DIFFERENCE BETWEEN main.py and worker_main.py
================================================

┌─────────────────────────────────────────────────────────────────────┐
│                         MAIN.PY                                     │
│                    (FastAPI Server)                                 │
└─────────────────────────────────────────────────────────────────────┘

PURPOSE:
  HTTP API server that receives user queries and returns answers

WHAT IT DOES:
  1. Listens on port 8000 for HTTP requests
  2. Provides REST API endpoints:
     - POST /query → Answer user questions
     - GET /health → Check service status
     - POST /agent/async → Submit async agent task
     - GET /agent/status/{id} → Check task status
  
  3. Handles SYNCHRONOUS queries:
     - Check semantic cache
     - Route to Normal RAG or Agentic RAG
     - Return immediate response
  
  4. For Agentic RAG:
     - Uses LangGraph planner to create execution plan
     - Publishes steps to RabbitMQ queue
     - Returns task_id immediately (async)
     - Doesn't wait for completion

PROCESS FLOW (Normal RAG):
  User → HTTP Request → main.py → Cache Check → Router → Normal RAG
                                                            ↓
  User ← HTTP Response ← Generate Answer ← Retrieve Docs ←─┘

PROCESS FLOW (Agentic RAG):
  User → HTTP Request → main.py → LangGraph Plan → Publish to Queue
                                                            ↓
  User ← HTTP Response (task_id) ───────────────────────────┘
  
  (Steps are processed by worker_main.py separately)

WHEN TO USE:
  - Query answering via API
  - Web frontend integration
  - Direct user interaction
  - Real-time responses (Normal RAG)


┌─────────────────────────────────────────────────────────────────────┐
│                      WORKER_MAIN.PY                                 │
│                   (RabbitMQ Consumer)                               │
└─────────────────────────────────────────────────────────────────────┘

PURPOSE:
  Background worker that executes agent steps from the queue

WHAT IT DOES:
  1. Connects to RabbitMQ and listens for messages
  2. Processes agent steps ONE AT A TIME:
     - RETRIEVE steps → Query ChromaDB/Neo4j
     - REASON steps → Use LLM for analysis
     - EVALUATE steps → Check answer quality
  
  3. Stores results in Redis
  4. Runs independently from main.py
  5. Can be scaled (run multiple workers)

PROCESS FLOW:
  RabbitMQ Queue → worker_main.py → Execute Step → Store Result in Redis
       ↑                                  ↓
       └──────────── Retry if failed ─────┘

  Step Types:
  - RETRIEVE: Get documents from ChromaDB or graph from Neo4j
  - REASON: Use LLM to analyze relationships
  - EVALUATE: Check if answer is good enough

WHEN TO USE:
  - Processing complex multi-step queries
  - Graph reasoning with Neo4j
  - Long-running agent tasks
  - When you want async processing


┌─────────────────────────────────────────────────────────────────────┐
│                    KEY DIFFERENCES                                  │
└─────────────────────────────────────────────────────────────────────┘

╔═══════════════════╤═══════════════════╤═══════════════════════════╗
║     ASPECT        │     MAIN.PY       │     WORKER_MAIN.PY        ║
╟───────────────────┼───────────────────┼───────────────────────────╢
║ Type              │ HTTP Server       │ Background Worker         ║
║ Protocol          │ HTTP/REST         │ RabbitMQ (AMQP)          ║
║ Port              │ 8000              │ No port (consumer)        ║
║ Listens To        │ HTTP requests     │ RabbitMQ queue messages   ║
║ Returns           │ HTTP response     │ Stores in Redis           ║
║ Speed             │ Fast (sync)       │ Slower (async)            ║
║ Use Case          │ Normal RAG        │ Agentic RAG (complex)     ║
║ Scalability       │ 1 instance        │ Multiple workers possible ║
║ Required          │ YES (always)      │ NO (only for agentic)     ║
║ Depends On        │ Nothing           │ Needs main.py to publish  ║
║ User Interaction  │ Direct (API)      │ Indirect (background)     ║
╚═══════════════════╧═══════════════════╧═══════════════════════════╝


┌─────────────────────────────────────────────────────────────────────┐
│                   TYPICAL SETUP SCENARIOS                           │
└─────────────────────────────────────────────────────────────────────┘

SCENARIO 1: Simple Setup (Normal RAG only)
  Terminal 1: python main.py
  
  ✅ Can answer queries
  ✅ Uses semantic cache
  ✅ Vector search
  ❌ No complex graph reasoning

SCENARIO 2: Full Setup (Normal + Agentic RAG)
  Terminal 1: python main.py
  Terminal 2: python worker_main.py
  
  ✅ Can answer queries
  ✅ Uses semantic cache
  ✅ Vector search
  ✅ Complex graph reasoning with Neo4j
  ✅ Multi-step agent tasks


┌─────────────────────────────────────────────────────────────────────┐
│                     COMMUNICATION FLOW                              │
└─────────────────────────────────────────────────────────────────────┘

For Normal RAG Query:
  User → main.py → Direct processing → Response
  (worker_main.py NOT involved)

For Agentic RAG Query:
  1. User → main.py → LangGraph creates plan
  2. main.py → Publishes steps to RabbitMQ
  3. main.py → Returns task_id to user
  4. worker_main.py → Picks up step from queue
  5. worker_main.py → Executes step (retrieve/reason)
  6. worker_main.py → Stores result in Redis
  7. main.py → User checks status via /agent/status/{task_id}
  8. main.py → Reads result from Redis
  9. main.py → Returns final answer to user


┌─────────────────────────────────────────────────────────────────────┐
│                       ARCHITECTURE                                  │
└─────────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │    USER     │
                    └──────┬──────┘
                           │ HTTP
                    ┌──────▼──────┐
                    │   MAIN.PY   │ ◄─── FastAPI Server
                    │  (port 8000)│
                    └──┬────────┬─┘
                       │        │
         Normal RAG ───┘        └─── Agentic RAG
              │                           │
    ┌─────────▼────────┐         ┌───────▼────────┐
    │ Direct Processing│         │  Publish Steps │
    │ Return Answer    │         │  to RabbitMQ   │
    └──────────────────┘         └───────┬────────┘
                                         │
                                 ┌───────▼────────┐
                                 │  RABBITMQ      │
                                 │  Queue         │
                                 └───────┬────────┘
                                         │
                                 ┌───────▼────────┐
                                 │ WORKER_MAIN.PY │ ◄─── Background
                                 │  Processes     │      Worker
                                 │  Steps         │
                                 └───────┬────────┘
                                         │
                                 ┌───────▼────────┐
                                 │  REDIS         │
                                 │  Store Result  │
                                 └────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                        SUMMARY                                      │
└─────────────────────────────────────────────────────────────────────┘

main.py:
  • HTTP server for user queries
  • Always required
  • Handles Normal RAG directly
  • Publishes Agentic RAG tasks to queue

worker_main.py:
  • Background worker for async tasks
  • Optional (only for Agentic RAG)
  • Consumes messages from RabbitMQ
  • Executes complex multi-step reasoning
  • Can run multiple instances for scaling

Think of it like:
  main.py = Restaurant front desk (takes orders)
  worker_main.py = Kitchen staff (prepares complex dishes)
  
Simple orders (Normal RAG) = Front desk handles directly
Complex orders (Agentic RAG) = Send to kitchen workers

"""

print(__doc__)
