# Agentic RAG Architecture - How It Works

## Overview

This system implements a **true agentic RAG architecture** using a distributed worker pattern. Unlike traditional RAG systems that follow a fixed pipeline, this architecture uses an intelligent agent that can plan, execute tools, evaluate results, and replan if needed.

---

## Architecture Pattern

```mermaid
graph TB
    subgraph "Planning Layer (Brain)"
        LG[LangGraph Planner<br/>Thinks & Decides]
        EVAL[Evaluation Engine<br/>Validates Results]
    end
    
    subgraph "Orchestration Layer"
        ORCH[Orchestrator<br/>Coordinates Steps]
    end
    
    subgraph "Message Queue"
        RMQ[RabbitMQ<br/>Step Distribution]
    end
    
    subgraph "Execution Layer (Hands)"
        W1[Worker 1<br/>Executes Tools]
        W2[Worker 2<br/>Executes Tools]
        W3[Worker N<br/>Executes Tools]
    end
    
    subgraph "Storage Layer"
        REDIS[Redis<br/>Results & State]
    end
    
    subgraph "Tools"
        T1[Vector Search<br/>ChromaDB]
        T2[Graph Query<br/>Neo4j]
        T3[Entity Matching<br/>Semantic]
        T4[Reasoning<br/>LLM Analysis]
    end
    
    Query --> LG
    LG -->|Creates Plan| ORCH
    ORCH -->|Publishes Steps| RMQ
    RMQ --> W1
    RMQ --> W2
    RMQ --> W3
    
    W1 --> T1
    W1 --> T2
    W2 --> T3
    W2 --> T4
    W3 --> T1
    
    W1 -->|Stores Results| REDIS
    W2 -->|Stores Results| REDIS
    W3 -->|Stores Results| REDIS
    
    REDIS --> ORCH
    ORCH --> EVAL
    
    EVAL -->|Should Replan?| LG
    EVAL -->|Complete| Answer
    
    style LG fill:#9C27B0
    style ORCH fill:#FF9800
    style RMQ fill:#2196F3
    style W1 fill:#4CAF50
    style W2 fill:#4CAF50
    style W3 fill:#4CAF50
    style EVAL fill:#E91E63
```

---

## Complete Agentic Flow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant LangGraph
    participant RabbitMQ
    participant Worker
    participant Tools
    participant Redis
    participant Evaluator
    
    User->>Orchestrator: Complex Query
    
    Note over LangGraph: PLANNING PHASE
    Orchestrator->>LangGraph: Create Plan
    LangGraph->>LangGraph: Classify Query
    LangGraph->>LangGraph: Extract Entities
    LangGraph->>LangGraph: Decide Tools
    LangGraph-->>Orchestrator: Agent Plan
    
    Note over RabbitMQ: EXECUTION PHASE
    loop For Each Step in Plan
        Orchestrator->>RabbitMQ: Publish Step
        RabbitMQ->>Worker: Deliver Step
        
        alt Retrieval Step
            Worker->>Tools: Vector Search
            Worker->>Tools: Graph Search
            Tools-->>Worker: Documents
        else Reasoning Step
            Worker->>Tools: LLM Analysis
            Tools-->>Worker: Insights
        end
        
        Worker->>Redis: Store Result
        Orchestrator->>Redis: Poll for Result
        Redis-->>Orchestrator: Step Result
    end
    
    Note over Evaluator: EVALUATION PHASE
    Orchestrator->>Orchestrator: Collect All Results
    Orchestrator->>Orchestrator: Generate Answer
    Orchestrator->>Evaluator: Evaluate Quality
    
    alt Answer Satisfactory
        Evaluator-->>Orchestrator: Complete
        Orchestrator-->>User: Final Answer
    else Needs Replanning
        Evaluator-->>LangGraph: Replan Request
        LangGraph->>LangGraph: Create New Step
        Note over RabbitMQ: Execute Additional Step
        LangGraph-->>Orchestrator: Updated Plan
        Orchestrator->>RabbitMQ: Publish New Step
        RabbitMQ->>Worker: Execute
        Worker->>Redis: Store Result
        Orchestrator->>Orchestrator: Generate Final Answer
        Orchestrator-->>User: Final Answer
    end
```

---

## Key Agentic Features

### 1. Separation of Concerns (Agent Design Pattern)

```mermaid
graph LR
    subgraph "Brain"
        P[Planning<br/>LangGraph]
    end
    
    subgraph "Coordinator"
        O[Orchestration<br/>Manages Flow]
    end
    
    subgraph "Hands"
        E[Execution<br/>Workers + Tools]
    end
    
    P -->|Plan| O
    O -->|Steps| E
    E -->|Results| O
    O -->|Feedback| P
    
    style P fill:#9C27B0
    style O fill:#FF9800
    style E fill:#4CAF50
```

**Why This Matters:**
- **Brain (LangGraph)** thinks and decides what to do
- **Coordinator (Orchestrator)** manages the workflow
- **Hands (Workers)** execute the actual tools
- Each component can be scaled independently

### 2. Tool Execution Framework

The worker implements multiple tools that the agent can use:

```python
# Tools Available to Agent
TOOL_CATALOG = {
    "vector_search": {
        "description": "Search document database",
        "execution": worker._execute_retrieval(mode="vector")
    },
    "graph_query": {
        "description": "Query knowledge graph",
        "execution": worker._execute_retrieval(mode="graph")
    },
    "entity_matching": {
        "description": "Find entities semantically",
        "execution": entity_matcher.find_matching_entities()
    },
    "reasoning": {
        "description": "Analyze with LLM",
        "execution": worker._execute_reasoning()
    }
}
```

### 3. Feedback Loop with Replanning

```mermaid
stateDiagram-v2
    [*] --> Planning
    Planning --> Execution
    Execution --> Evaluation
    
    Evaluation --> Complete: Quality Good
    Evaluation --> Replanning: Needs Improvement
    
    Replanning --> Execution: New Steps
    Complete --> [*]
    
    note right of Evaluation
        Checks:
        - Relevance
        - Completeness
        - Accuracy
    end note
    
    note right of Replanning
        Creates:
        - Additional steps
        - Alternative approach
        - Max 1 replan
    end note
```

**Evaluation Criteria:**
```python
class AnswerEvaluation:
    is_relevant: bool       # Answers the query?
    is_complete: bool       # All aspects covered?
    has_evidence: bool      # Based on retrieved docs?
    confidence_score: float # 0.0 to 1.0
    should_replan: bool     # Need more steps?
```

### 4. Distributed Execution

```mermaid
graph TB
    subgraph "Single Query Processing"
        Q[Complex Query]
    end
    
    subgraph "Step Distribution"
        S1[Step 1: Retrieve]
        S2[Step 2: Reason]
        S3[Step 3: Compare]
    end
    
    subgraph "Worker Pool"
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker 3]
    end
    
    Q --> S1
    Q --> S2
    Q --> S3
    
    S1 --> W1
    S2 --> W2
    S3 --> W3
    
    W1 --> R[Results]
    W2 --> R
    W3 --> R
    
    R --> A[Final Answer]
    
    style Q fill:#2196F3
    style S1 fill:#FF9800
    style S2 fill:#FF9800
    style S3 fill:#FF9800
    style W1 fill:#4CAF50
    style W2 fill:#4CAF50
    style W3 fill:#4CAF50
```

**Benefits:**
- Parallel step execution (if independent)
- Fault tolerance (retry failed steps)
- Horizontal scaling (add more workers)
- Graceful degradation

---

## Why This is Truly Agentic

### Comparison: Traditional RAG vs Agentic RAG

| Feature | Traditional RAG | This Agentic System |
|---------|----------------|---------------------|
| **Planning** | Fixed pipeline | LLM-based dynamic planning |
| **Tool Use** | Hardcoded sequence | Selects tools based on query |
| **Feedback** | None | Evaluates and replans |
| **Execution** | Synchronous | Async distributed workers |
| **Adaptability** | Static | Adapts to complexity |
| **Error Handling** | Fails or returns error | Retries, replans, recovers |
| **Multi-Step** | Single retrieval | Multiple coordinated steps |

### Agent Decision-Making Process

```mermaid
flowchart TD
    START[Receive Query] --> CLASSIFY{Classify<br/>Complexity}
    
    CLASSIFY -->|Simple| SIMPLE[Single Vector<br/>Search]
    CLASSIFY -->|Moderate| HYBRID[Vector + Graph<br/>Search]
    CLASSIFY -->|Complex| MULTI[Multi-Step<br/>Reasoning]
    
    SIMPLE --> ANSWER[Generate Answer]
    HYBRID --> ANSWER
    
    MULTI --> EXTRACT[Extract Entities]
    EXTRACT --> TOOLS{Select Tools}
    
    TOOLS -->|Entities Found| GRAPH[Graph Traversal]
    TOOLS -->|Need Context| VECTOR[Vector Search]
    TOOLS -->|Need Analysis| REASON[LLM Reasoning]
    
    GRAPH --> COMBINE[Combine Results]
    VECTOR --> COMBINE
    REASON --> COMBINE
    
    COMBINE --> EVAL{Evaluate<br/>Quality}
    
    EVAL -->|Good| ANSWER
    EVAL -->|Poor| REPLAN[Create New Steps]
    
    REPLAN --> TOOLS
    
    ANSWER --> END[Return to User]
    
    style CLASSIFY fill:#9C27B0
    style EVAL fill:#E91E63
    style REPLAN fill:#FF9800
    style TOOLS fill:#2196F3
```

---

## Implementation Details

### 1. LangGraph State Machine

```python
# Agent state flows through nodes
class AgentState(TypedDict):
    request_id: str
    original_query: str
    classification: str          # simple/moderate/complex
    entities: list[str]          # extracted entities
    retrieval_mode: str          # vector/graph/hybrid
    steps_completed: int         # progress tracking
    should_stop: bool            # completion flag
    replan_count: int            # replanning attempts
```

**Graph Nodes:**
- `classify_query` - Determine complexity
- `extract_entities` - Find key concepts
- `decide_retrieval` - Choose tools
- `plan_next_step` - Create step
- `check_stop_or_continue` - Evaluate progress
- `decide_replan` - Replan if needed

### 2. Worker Tool Execution

```python
# Worker processes steps from queue
async def _process_step(self, step: AgentStep):
    if step.step_type == StepType.RETRIEVE:
        # Execute vector + graph search
        documents = await self._execute_retrieval(step)
    
    elif step.step_type == StepType.REASON:
        # Execute LLM reasoning
        analysis = await self._execute_reasoning(step)
    
    # Store result in Redis for orchestrator
    await redis_client.set_json(f"step_result:{step.id}", result)
```

**Tools Implemented:**
1. **Vector Search** - Semantic similarity in ChromaDB
2. **Graph Search** - Entity relationships in Neo4j
3. **Entity Matching** - Semantic entity resolution
4. **LLM Reasoning** - Complex analysis with Groq

### 3. Orchestrator Coordination

```python
# Orchestrator manages agent lifecycle
async def process_query(query: str):
    # 1. Planning
    plan = await langgraph_planner.create_plan(query)
    
    # 2. Execution
    results = await self._execute_plan_steps(plan)
    
    # 3. Answer Generation
    answer = await self._generate_answer(query, results)
    
    # 4. Evaluation
    evaluation = await self._evaluate_answer(query, answer)
    
    # 5. Replan if needed (max 1 time)
    if evaluation.should_replan:
        new_results = await self._execute_replan_step(plan)
        answer = await self._generate_answer(query, new_results)
    
    return answer
```

---

## Scalability & Fault Tolerance

### Horizontal Scaling

```mermaid
graph TB
    subgraph "High Load Scenario"
        Q1[Query 1]
        Q2[Query 2]
        Q3[Query 3]
        Q4[Query N]
    end
    
    subgraph "Load Balancer"
        LB[RabbitMQ Queue]
    end
    
    subgraph "Worker Pool (Auto-Scale)"
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker 3]
        W4[Worker 4]
        W5[Worker 5]
        W6[Worker N]
    end
    
    Q1 --> LB
    Q2 --> LB
    Q3 --> LB
    Q4 --> LB
    
    LB --> W1
    LB --> W2
    LB --> W3
    LB --> W4
    LB --> W5
    LB --> W6
    
    style LB fill:#2196F3
    style W1 fill:#4CAF50
    style W2 fill:#4CAF50
    style W3 fill:#4CAF50
    style W4 fill:#4CAF50
    style W5 fill:#4CAF50
    style W6 fill:#4CAF50
```

**Scaling Strategy:**
- Add more worker processes during peak load
- Workers pull from shared RabbitMQ queue
- No coordination needed between workers
- Each worker is stateless

### Fault Tolerance

```mermaid
stateDiagram-v2
    [*] --> StepPublished
    StepPublished --> WorkerReceives
    
    WorkerReceives --> Executing
    Executing --> Success: Completed
    Executing --> Failed: Error
    
    Failed --> Retry1: Attempt 1/3
    Retry1 --> Executing
    Retry1 --> Retry2: Failed Again
    
    Retry2 --> Executing
    Retry2 --> Retry3: Failed Again
    
    Retry3 --> Executing
    Retry3 --> DeadLetter: Max Retries
    
    Success --> ResultStored
    ResultStored --> [*]
    
    DeadLetter --> ManualReview
    ManualReview --> [*]
```

**Error Handling:**
- Automatic retry (max 3 attempts)
- Exponential backoff between retries
- Dead letter queue for failed steps
- Graceful degradation (partial results)

---

## Production Features

### 1. Observability

**Tracking Points:**
- LangGraph decisions logged
- Each step execution tracked
- Results stored with metadata
- End-to-end tracing with request_id

**Metrics Collected:**
```python
{
    "request_id": "abc-123",
    "classification": "complex",
    "entities_extracted": 3,
    "tools_used": ["vector_search", "graph_query", "reasoning"],
    "steps_executed": 3,
    "replanned": True,
    "total_time_ms": 3200,
    "worker_time_ms": 2100,
    "planning_time_ms": 400
}
```

### 2. Resource Management

**Timeouts:**
- Planning: 5 seconds max
- Step execution: 30 seconds max
- Total query: 120 seconds max

**Bounded Execution:**
- Max 5 steps per query
- Max 1 replan attempt
- Max 3 retries per step

### 3. State Persistence

**Redis Storage:**
```
step_result:{step_id} → StepResult (TTL: 10 min)
task_status:{request_id} → TaskStatus (TTL: 1 hour)
agent_plan:{request_id} → AgentPlan (TTL: 1 hour)
```

---

## Comparison to Other Agentic Patterns

### LangChain ReAct Agent

**Standard Pattern:**
```
Question → Thought → Action → Observation → Thought → ... → Answer
```

**This System:**
```
Query → Plan → Distribute Steps → Execute in Parallel → Evaluate → Answer
```

**Advantage:** Parallel execution, better for complex queries

### AutoGPT Pattern

**AutoGPT:**
- Sequential execution
- Many LLM calls
- Can loop indefinitely

**This System:**
- Bounded execution (max steps)
- Efficient LLM usage
- Distributed processing

---

## Future Enhancements

**To make it even more agentic:**

1. **Dynamic Tool Discovery**
   - Agent discovers available tools
   - Tools register themselves
   - Runtime tool composition

2. **Multi-Round Conversation**
   - Memory across queries
   - Context accumulation
   - Clarification questions

3. **Meta-Reasoning**
   - Agent reflects on strategy
   - Learns from failures
   - Optimizes tool selection

4. **Advanced Evaluation**
   - Multi-dimensional scoring
   - Contradiction detection
   - Source citation validation

---

## Conclusion

This system implements a **production-grade agentic RAG architecture** with:

✅ Intelligent planning (LangGraph)
✅ Distributed execution (RabbitMQ workers)
✅ Tool abstraction (worker implements tools)
✅ Feedback loops (evaluation + replanning)
✅ Fault tolerance (retries, graceful degradation)
✅ Horizontal scaling (add more workers)
✅ Observability (comprehensive tracking)

**It's truly agentic because:**
- Agent decides what to do (not hardcoded)
- Executes tools dynamically
- Evaluates its own output
- Can replan and improve
- Adapts to query complexity

This architecture pattern is suitable for production use cases requiring complex, multi-step reasoning with high reliability and scalability.
