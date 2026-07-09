"""
Pydantic models for request/response validation and internal data structures.
All data flowing through the system uses these typed models.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ============= API Models =============

class QueryRequest(BaseModel):
    """Client request for RAG query."""
    query: str = Field(..., min_length=1, description="User query text")
    use_cache: bool = Field(True, description="Whether to check semantic cache")
    force_agentic: bool = Field(False, description="Force Agentic RAG pipeline")
    user_id: Optional[str] = None
    username: Optional[str] = None
    workspace_id: Optional[str] = None  # Filter by workspace
    source_filter: Optional[str] = None  # ingestion_id to filter by


class QueryResponse(BaseModel):
    """Response to client query."""
    request_id: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    pipeline: str  # More flexible than Literal
    cache_hit: bool = False
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float


class HealthResponse(BaseModel):
    """System health status."""
    status: str
    timestamp: datetime
    services: Dict[str, bool]


class CacheStatsResponse(BaseModel):
    """Semantic cache statistics."""
    total_queries: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_similarity: float


class CachedItem(BaseModel):
    """Cached query item."""
    query: str
    answer_preview: str
    confidence: Optional[float] = None
    cached_at: Optional[str] = None


class CacheListResponse(BaseModel):
    """List of cached queries."""
    total: int
    items: List[CachedItem]


class CacheClearResponse(BaseModel):
    """Response for cache clear operation."""
    deleted_count: int
    message: str


class CacheDeleteResponse(BaseModel):
    """Response for deleting specific cache entry."""
    success: bool
    message: str


# ============= Admin Models =============

class SystemStats(BaseModel):
    """Overall system statistics."""
    total_queries: int
    cache_hit_rate: float
    avg_response_time_ms: float
    active_tasks: int
    chromadb_docs: int
    neo4j_nodes: int
    neo4j_relationships: int


class ServiceHealth(BaseModel):
    """Individual service health status."""
    name: str
    status: str
    healthy: bool
    details: Optional[Dict[str, Any]] = None


class HealthDetailedResponse(BaseModel):
    """Detailed health check response."""
    status: str
    timestamp: datetime
    services: List[ServiceHealth]
    uptime_seconds: float


class ChromaDBStats(BaseModel):
    """ChromaDB statistics."""
    total_documents: int
    collections: List[str]
    collection_sizes: Dict[str, int]


class Neo4jStats(BaseModel):
    """Neo4j graph statistics."""
    total_nodes: int
    total_relationships: int
    node_labels: Dict[str, int]
    relationship_types: Dict[str, int]


class RabbitMQStatus(BaseModel):
    """RabbitMQ queue status."""
    queue_name: str
    messages_ready: int
    messages_unacknowledged: int
    consumers: int
    total_messages: int


class TaskInfo(BaseModel):
    """Async task information."""
    task_id: str
    query: str
    status: str
    pipeline: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    """List of async tasks."""
    total: int
    tasks: List[TaskInfo]


class RouterStatsResponse(BaseModel):
    """Router decision statistics."""
    total_queries: int
    normal_rag_count: int
    agentic_rag_count: int
    normal_percentage: float
    agentic_percentage: float
    recent_decisions: List[Dict[str, Any]]


class AnalyticsData(BaseModel):
    """Analytics data for charts."""
    query_volume: List[Dict[str, Any]]
    response_times: List[float]
    database_usage: Dict[str, int]
    pipeline_performance: Dict[str, Dict[str, float]]


class IngestRequest(BaseModel):
    """Document ingestion request."""
    content: str
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Document ingestion response."""
    success: bool
    message: str
    doc_id: Optional[str] = None


# ============= Internal Models =============

class QueryClassification(str, Enum):
    """Query complexity classification."""
    SIMPLE = "simple"          # Single fact retrieval
    MODERATE = "moderate"      # Multi-fact, no reasoning
    COMPLEX = "complex"        # Requires reasoning/multi-hop


class RetrievalMode(str, Enum):
    """Vector search strategy."""
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"              # Vector + keyword
    GRAPH = "graph"                # Graph traversal in Neo4j
    SOURCE_AWARE = "source_aware"  # Filter by intent/category tags
    TEMPORAL = "temporal"          # Filter by temporal bucket
    RESOLUTION_CHAIN = "resolution_chain"  # Follow issue→PR→file chains
    HYBRID_RERANKED = "hybrid_reranked"    # Hybrid + cross-encoder rerank


class StepType(str, Enum):
    """Agent execution step types."""
    RETRIEVE = "retrieve"      # Fetch from vector/graph DB
    REASON = "reason"          # LLM reasoning step
    EVALUATE = "evaluate"      # Check answer quality


# ============= Agent Planning Models =============

class AgentPlan(BaseModel):
    """LangGraph planning output."""
    request_id: str
    classification: QueryClassification
    entities: List[str] = Field(default_factory=list)
    retrieval_needed: bool = True
    retrieval_mode: RetrievalMode = RetrievalMode.VECTOR_ONLY
    steps: List[str] = Field(default_factory=list)  # High-level step descriptions
    needs_graph_reasoning: bool = False
    intent_tags: Optional[List[str]] = None      # NEW — detected intent tags
    temporal_buckets: Optional[List[str]] = None  # NEW — temporal filter buckets


class AgentStep(BaseModel):
    """Single agent execution step (RabbitMQ message)."""
    request_id: str
    step_id: str
    step_type: StepType
    payload: Dict[str, Any]
    attempt: int = 1
    max_attempts: int = 2


class StepResult(BaseModel):
    """Result of executing an agent step (stored in Redis)."""
    step_id: str
    status: Literal["success", "failure", "partial"]
    data: Any
    error: Optional[str] = None
    execution_time_ms: float
    worker_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============= RAG Models =============

class Document(BaseModel):
    """Retrieved document from vector store."""
    doc_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = Field(ge=0.0, le=1.0)


class RetrievalResult(BaseModel):
    """Result of retrieval operation."""
    documents: List[Document]
    retrieval_mode: RetrievalMode
    query_embedding: Optional[List[float]] = None


class RAGContext(BaseModel):
    """Context passed through RAG pipeline."""
    request_id: str
    original_query: str
    retrieval_result: Optional[RetrievalResult] = None
    intermediate_answers: List[str] = Field(default_factory=list)
    reasoning_steps: List[str] = Field(default_factory=list)


# ============= Evaluation Models =============

class AnswerEvaluation(BaseModel):
    """Evaluation of generated answer quality."""
    is_relevant: bool
    has_entity_coverage: bool
    is_complete: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    should_replan: bool = False
    evaluation_reasoning: str


# ============= Cache Models =============

class CachedAnswer(BaseModel):
    """Cached response with metadata."""
    query: str
    query_embedding: List[float]
    answer: str
    confidence: float
    metadata: Dict[str, Any]
    cached_at: datetime
    ttl_seconds: int = 3600
    ttl_seconds: int
