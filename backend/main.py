"""
FastAPI Main Application
Exposes REST API for RAG query processing.
"""
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi import BackgroundTasks, UploadFile, File
from datetime import datetime
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config.settings import settings
from utils.metrics import MetricsMiddleware
from models.schemas import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    CacheStatsResponse,
    CacheListResponse,
    CachedItem,
    CacheClearResponse,
    CacheDeleteResponse,
    # Admin schemas
    SystemStats,
    ServiceHealth,
    HealthDetailedResponse,
    ChromaDBStats,
    Neo4jStats,
    RabbitMQStatus,
    TaskInfo,
    TaskListResponse,
    RouterStatsResponse,
    AnalyticsData,
    IngestRequest,
    IngestResponse
)
from models.ingestion_schemas import (
    IngestURLRequest,
    IngestStatusResponse,
    DigestRequest,
    DigestResponse,
    IngestionListResponse
)
from models.workspace_schemas import (
    WorkspaceCreate,
    WorkspaceUpdate,
    Workspace,
    WorkspaceList,
    WorkspaceDetail,
    AddIngestionToWorkspace,
    WorkspaceStats
)
from database.redis_client import redis_client
from database.chroma_client import chroma_client
from database.neo4j_client import neo4j_client
from utils.rabbitmq_client import rabbitmq_client
from services.embedding_service import embedding_service
from services.semantic_cache import semantic_cache
from services.router import query_router
from services.normal_rag import normal_rag
from services.agentic_rag.orchestrator import agentic_orchestrator
from services.agentic_rag.langgraph_planner import langgraph_planner
from services.admin_analytics import admin_analytics
from services.ingestion.ingestion_pipeline import ingestion_pipeline
from services.digest_service import digest_service
from routers.graph_router import router as graph_router


# ============= Lifespan Management =============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Starting Agentic RAG System...")
    
    # Initialize database clients
    await redis_client.connect()
    chroma_client.connect()
    await neo4j_client.connect()
    await rabbitmq_client.connect()
    
    # Load embedding model
    embedding_service.load_model()
    
    print("✅ All services initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await redis_client.disconnect()
    await neo4j_client.disconnect()
    await rabbitmq_client.disconnect()
    print("✅ Cleanup complete")


# ============= FastAPI Application =============

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Add metrics middleware (BEFORE CORS for proper tracking)
app.add_middleware(MetricsMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(graph_router)


# ============= API Endpoints =============

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Main query endpoint with improved hybrid search and re-ranking.
    Flow: Cache Check → Router → (Improved RAG | Normal RAG | Agentic RAG) → Cache Store
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Step 1: Check semantic cache
        cached_answer = None
        if request.use_cache:
            cached_answer = await semantic_cache.get_similar_answer(request.query)
            
            if cached_answer:
                processing_time = (time.time() - start_time) * 1000
                
                # Log cached query for analytics
                pipeline = cached_answer.metadata.get("pipeline", "cache")
                await admin_analytics.log_query(
                    request.query, 
                    pipeline, 
                    processing_time, 
                    cache_hit=True
                )
                
                return QueryResponse(
                    request_id=request_id,
                    answer=cached_answer.answer,
                    confidence=cached_answer.confidence,
                    pipeline="cache",
                    cache_hit=True,
                    sources=[],
                    metadata={
                        "cached_at": cached_answer.cached_at.isoformat(),
                        **cached_answer.metadata
                    },
                    processing_time_ms=processing_time
                )
        
        # Step 2: Route query to appropriate pipeline
        classification = await query_router.route_query(
            request.query,
            force_agentic=request.force_agentic
        )
        
        # Log router decision for analytics
        pipeline = "agentic_rag" if classification != "normal_rag" else "improved_rag"
        await admin_analytics.log_router_decision(request.query, pipeline, str(classification))
        
        # Step 3: Execute pipeline
        # Use improved RAG by default for better accuracy
        from services.improved_rag import improved_rag
        
        if pipeline == "improved_rag":
            result = await improved_rag.process_query(
                query=request.query,
                request_id=request_id,
                workspace_id=getattr(request, 'workspace_id', None),
                source_filter=request.source_filter,
                use_reranking=True
            )
            pipeline_used = "improved_rag"
        elif pipeline == "agentic_rag":
            result = await agentic_orchestrator.process_query(
                query=request.query,
                request_id=request_id,
                ingestion_id=request.source_filter  # pass ingestion_id filter through
            )
            pipeline_used = "agentic_rag"
        else:
            # Fallback to normal RAG
            result = await normal_rag.process_query(request.query, request_id, request.source_filter)
            pipeline_used = "normal_rag"
        
        # Step 4: Store in cache
        if request.use_cache:
            await semantic_cache.store_answer(
                query=request.query,
                answer=result["answer"],
                confidence=result["confidence"],
                metadata={
                    "pipeline": pipeline_used,
                    **result["metadata"]
                }
            )
        
        # Step 5: Return response
        processing_time_ms = result.get("processing_time_ms", 0.0)
        
        # Log query for analytics
        await admin_analytics.log_query(
            request.query, 
            pipeline_used, 
            processing_time_ms, 
            cache_hit=False
        )
        
        return QueryResponse(
            request_id=request_id,
            answer=result.get("answer", ""),
            confidence=result.get("confidence", 0.0),
            pipeline=pipeline_used,
            cache_hit=False,
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
            processing_time_ms=processing_time_ms
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health status."""
    services = {
        "redis": await redis_client.health_check(),
        "chromadb": chroma_client.health_check(),
        "neo4j": await neo4j_client.health_check(),
        "rabbitmq": await rabbitmq_client.health_check()
    }
    
    all_healthy = all(services.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now(),
        services=services
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get semantic cache statistics."""
    stats = await semantic_cache.get_stats()
    
    return CacheStatsResponse(
        total_queries=stats["total_queries"],
        cache_hits=stats["cache_hits"],
        cache_misses=stats["cache_misses"],
        hit_rate=stats["hit_rate"],
        avg_similarity=stats["avg_similarity"]
    )


@app.get("/cache/keys", response_model=CacheListResponse)
async def list_cached_queries(limit: int = 100):
    """List all cached queries."""
    items = await semantic_cache.get_all_cached_queries(limit=limit)
    
    cached_items = [
        CachedItem(
            query=item['query'],
            answer_preview=item['answer_preview'],
            confidence=item.get('confidence'),
            cached_at=item.get('cached_at')
        )
        for item in items
    ]
    
    return CacheListResponse(
        total=len(cached_items),
        items=cached_items
    )


@app.get("/cache/search", response_model=CacheListResponse)
async def search_cached_queries(q: str, limit: int = 20):
    """Search cached queries by keyword."""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    items = await semantic_cache.search_cache(q, limit=limit)
    
    cached_items = [
        CachedItem(
            query=item['query'],
            answer_preview=item['answer_preview'],
            confidence=item.get('confidence'),
            cached_at=item.get('cached_at')
        )
        for item in items
    ]
    
    return CacheListResponse(
        total=len(cached_items),
        items=cached_items
    )


@app.post("/cache/clear", response_model=CacheClearResponse)
async def clear_cache():
    """Clear all cached queries."""
    deleted_count = await semantic_cache.clear_all()
    
    return CacheClearResponse(
        deleted_count=deleted_count,
        message=f"Successfully cleared {deleted_count} cached queries"
    )


@app.delete("/cache/query", response_model=CacheDeleteResponse)
async def delete_cached_query(query: str):
    """Delete a specific cached query."""
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    success = await semantic_cache.delete_query(query)
    
    if success:
        return CacheDeleteResponse(
            success=True,
            message="Cache entry deleted successfully"
        )
    else:
        return CacheDeleteResponse(
            success=False,
            message="Cache entry not found"
        )


@app.post("/agent/async")
async def submit_async_agent_task(request: QueryRequest):
    """
    Submit an async agent task for complex queries.
    Returns task_id immediately, processes in background via worker.
    """
    task_id = str(uuid.uuid4())
    
    try:
        # Plan the task using LangGraph
        plan = await langgraph_planner.create_plan(request.query, task_id)
        
        # Store initial status in Redis
        task_status = {
            "task_id": task_id,
            "status": "pending",
            "query": request.query,
            "plan": plan.model_dump() if plan else {},
            "created_at": datetime.now().isoformat()
        }
        
        await redis_client.set_json(
            f"task_status:{task_id}",
            task_status,
            ttl=3600  # 1 hour
        )
        
        # Publish steps to RabbitMQ for worker to process
        if plan and plan.steps:
            from models.schemas import AgentStep, StepType
            
            for step_desc in plan.steps:
                # Create proper step based on description
                step = AgentStep(
                    request_id=task_id,
                    step_id=f"{task_id}_{step_desc.lower().replace(' ', '_')}",
                    step_type=StepType.RETRIEVE if "retrieve" in step_desc.lower() else StepType.REASON,
                    payload={
                        "query": request.query,
                        "retrieval_mode": plan.retrieval_mode.value if plan.retrieval_mode else "vector_only",
                        "entities": plan.entities
                    }
                )
                
                await rabbitmq_client.publish_step(step)
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Task submitted successfully. Use /agent/status/{task_id} to check progress."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/status/{task_id}")
async def get_agent_task_status(task_id: str):
    """
    Get status and result of an async agent task.
    """
    try:
        # Get task status from Redis
        task_status = await redis_client.get_json(f"task_status:{task_id}")
        
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Check if steps are completed
        plan = task_status.get("plan", {})
        steps = plan.get("steps", [])
        
        completed_steps = 0
        step_results = []
        
        for step_desc in steps:
            step_id = f"{task_id}_{step_desc.lower().replace(' ', '_')}"
            result = await redis_client.get_json(f"step_result:{step_id}")
            
            if result:
                step_results.append(result)
                if result.get("status") == "success":
                    completed_steps += 1
        
        # Update status based on completion
        if completed_steps == len(steps) and len(steps) > 0:
            # Check if we already generated the final answer
            if task_status.get("status") != "completed":
                # All steps completed - generate final synthesized answer
                query = task_status.get("query")
                
                # Collect all retrieved documents
                all_documents = []
                for result in step_results:
                    if result.get("status") == "success":
                        data = result.get("data", {})
                        if "documents" in data:
                            all_documents.extend(data["documents"])
                
                # Build context from documents
                context_parts = []
                for i, doc in enumerate(all_documents[:10], 1):  # Limit to top 10
                    content = doc.get("content", "")
                    if len(content) > 300:
                        content = content[:300] + "..."
                    context_parts.append(f"[{i}] {content}")
                
                context = "\n\n".join(context_parts)
                
                # Generate synthesized answer using Groq
                from groq import AsyncGroq
                groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                
                prompt = f"""Based on the following retrieved information, answer this question comprehensively:

Question: {query}

Retrieved Information:
{context}

Provide a clear, concise answer that directly addresses the question. Cite relevant information from the sources."""

                response = await groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful financial assistant. Provide accurate, well-structured answers based on the given information."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                final_answer = response.choices[0].message.content
                
                # Separate and format sources
                vector_docs = [d for d in all_documents if 'fin' in d.get('doc_id', '').lower()]
                graph_docs = [d for d in all_documents if 'graph_' in d.get('doc_id', '').lower()]
                
                # Include both types in sources
                sources = []
                for doc in (graph_docs[:3] + vector_docs[:3])[:5]:  # Mix both, max 5
                    sources.append(
                        f"{doc.get('doc_id', 'unknown')}: {doc.get('content', '')[:100]}... (score: {doc.get('score', 0):.2f})"
                    )
                
                task_status["status"] = "completed"
                task_status["result"] = {
                    "answer": final_answer,
                    "confidence": 0.85,
                    "sources": sources,
                    "num_documents": len(all_documents),
                    "vector_count": len(vector_docs),
                    "graph_count": len(graph_docs),
                    "pipeline": "agentic_rag"
                }
            
            task_status["steps_completed"] = completed_steps
            task_status["total_steps"] = len(steps)
            
            # Update in Redis
            await redis_client.set_json(
                f"task_status:{task_id}",
                task_status,
                ttl=3600
            )
        elif any(r.get("status") == "failure" for r in step_results):
            task_status["status"] = "failed"
            task_status["error"] = "One or more steps failed"
            task_status["steps_completed"] = completed_steps
            task_status["total_steps"] = len(steps)
        elif completed_steps > 0:
            task_status["status"] = "processing"
            task_status["steps_completed"] = completed_steps
            task_status["total_steps"] = len(steps)
        
        return task_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= Admin Endpoints =============

@app.get("/admin/stats", response_model=SystemStats)
async def get_admin_stats():
    """Get overall system statistics for admin dashboard."""
    stats = await admin_analytics.get_system_stats()
    return SystemStats(**stats)


@app.get("/admin/health-detailed", response_model=HealthDetailedResponse)
async def get_detailed_health():
    """Get detailed health check with all services."""
    services = []
    
    # Check Redis
    try:
        await redis_client.client.ping()
        services.append(ServiceHealth(name="Redis", status="healthy", healthy=True))
    except Exception as e:
        services.append(ServiceHealth(name="Redis", status="unhealthy", healthy=False, details={"error": str(e)}))
    
    # Check Neo4j
    try:
        await neo4j_client.execute_query("RETURN 1")
        services.append(ServiceHealth(name="Neo4j", status="healthy", healthy=True))
    except Exception as e:
        services.append(ServiceHealth(name="Neo4j", status="unhealthy", healthy=False, details={"error": str(e)}))
    
    # Check ChromaDB
    try:
        chroma_client.get_collection()
        services.append(ServiceHealth(name="ChromaDB", status="healthy", healthy=True))
    except Exception as e:
        services.append(ServiceHealth(name="ChromaDB", status="unhealthy", healthy=False, details={"error": str(e)}))
    
    # Check RabbitMQ
    try:
        if rabbitmq_client.connection and not rabbitmq_client.connection.is_closed:
            services.append(ServiceHealth(name="RabbitMQ", status="healthy", healthy=True))
        else:
            services.append(ServiceHealth(name="RabbitMQ", status="unhealthy", healthy=False))
    except Exception as e:
        services.append(ServiceHealth(name="RabbitMQ", status="unhealthy", healthy=False, details={"error": str(e)}))
    
    all_healthy = all(s.healthy for s in services)
    
    return HealthDetailedResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now(),
        services=services,
        uptime_seconds=time.time()  # Simplified uptime
    )


@app.post("/admin/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """Ingest a document into ChromaDB."""
    try:
        collection = chroma_client.get_collection()
        
        # Generate embedding
        embedding = embedding_service.embed_text(request.content)
        
        # Generate doc ID
        doc_id = str(uuid.uuid4())
        
        # Add to ChromaDB
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[request.content],
            metadatas=[request.metadata or {}]
        )
        
        return IngestResponse(
            success=True,
            message="Document ingested successfully",
            doc_id=doc_id
        )
    except Exception as e:
        return IngestResponse(
            success=False,
            message=f"Failed to ingest document: {str(e)}",
            doc_id=None
        )


@app.get("/admin/chromadb/stats", response_model=ChromaDBStats)
async def get_chromadb_stats():
    """Get ChromaDB statistics."""
    stats = await admin_analytics.get_chromadb_stats()
    return ChromaDBStats(**stats)


@app.get("/admin/neo4j/stats", response_model=Neo4jStats)
async def get_neo4j_stats():
    """Get Neo4j graph statistics."""
    stats = await admin_analytics.get_neo4j_stats()
    return Neo4jStats(**stats)


@app.get("/admin/rabbitmq/status", response_model=RabbitMQStatus)
async def get_rabbitmq_status():
    """Get RabbitMQ queue status."""
    try:
        # For pika's async, we'll return basic status
        # Full queue stats would need RabbitMQ Management API
        queue_name = settings.RABBITMQ_QUEUE
        
        # Check if connected
        if not rabbitmq_client.connection or rabbitmq_client.connection.is_closed:
            raise HTTPException(status_code=503, detail="RabbitMQ not connected")
        
        # Return basic status (would need management API for detailed stats)
        return RabbitMQStatus(
            queue_name=queue_name,
            messages_ready=0,  # Placeholder - needs management API
            messages_unacknowledged=0,
            consumers=0,
            total_messages=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


@app.get("/admin/tasks", response_model=TaskListResponse)
async def get_all_tasks(status: str = None):
    """Get all async tasks with optional status filter."""
    tasks_data = await admin_analytics.get_all_tasks(status_filter=status)
    
    tasks = [
        TaskInfo(
            task_id=t["task_id"],
            query=t["query"],
            status=t["status"],
            pipeline=t.get("pipeline"),
            created_at=t["created_at"],
            completed_at=t.get("completed_at"),
            error=t.get("error")
        )
        for t in tasks_data
    ]
    
    return TaskListResponse(total=len(tasks), tasks=tasks)


@app.post("/admin/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """Retry a failed async task."""
    try:
        # Get task status from Redis
        task_key = f"task:{task_id}:status"
        task_status = await redis_client.get_json(task_key)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task_status.get("status") != "failed":
            raise HTTPException(status_code=400, detail="Can only retry failed tasks")
        
        # Get original query
        query = task_status.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Original query not found")
        
        # Create new plan
        plan = await langgraph_planner.create_plan(query, task_id)
        
        # Reset status
        task_status["status"] = "processing"
        task_status["error"] = None
        await redis_client.set_json(task_key, task_status, ttl=3600)
        
        # Publish steps to RabbitMQ
        for step in plan.get("steps", []):
            await rabbitmq_client.publish_message(step)
        
        return {"success": True, "message": "Task retry initiated", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/router-stats", response_model=RouterStatsResponse)
async def get_router_stats():
    """Get router decision statistics."""
    stats = await admin_analytics.get_router_stats()
    return RouterStatsResponse(**stats)


@app.get("/admin/analytics", response_model=AnalyticsData)
async def get_analytics():
    """Get analytics data for charts and graphs."""
    data = await admin_analytics.get_analytics_data()
    return AnalyticsData(**data)


# ============= Ingestion Endpoints =============

@app.post("/ingest/url", response_model=dict)
async def ingest_url(request: IngestURLRequest, background_tasks: BackgroundTasks):
    """
    Start ingestion of a URL (GitHub repo, webpage, Reddit, YouTube, RSS).
    Returns immediately with ingestion_id. Poll /ingest/status/{id} for progress.
    """
    ingestion_id = f"ing_{uuid.uuid4().hex[:12]}"
    
    # Store initial status in Redis
    await redis_client.set_json(f"ingestion:{ingestion_id}", {
        "ingestion_id": ingestion_id,
        "status": "running",
        "source_url": request.url,
        "source_type": "detecting",
        "source_name": request.url,
        "total_docs": 0,
        "processed_docs": 0,
        "entity_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "message": "Starting ingestion..."
    })
    
    # Add ingestion_id to index
    await redis_client.lpush("ingestion:index", ingestion_id)
    
    # Run ingestion in background
    background_tasks.add_task(
        ingestion_pipeline.ingest_url, request.url, ingestion_id, request.recursive
    )
    
    return {"ingestion_id": ingestion_id, "message": "Ingestion started"}


@app.post("/ingest/pdf", response_model=dict)
async def ingest_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and ingest a PDF file."""
    ingestion_id = f"ing_{uuid.uuid4().hex[:12]}"
    file_bytes = await file.read()
    
    await redis_client.set_json(f"ingestion:{ingestion_id}", {
        "ingestion_id": ingestion_id,
        "status": "running",
        "source_url": f"uploaded:{file.filename}",
        "source_type": "pdf",
        "source_name": file.filename,
        "total_docs": 0,
        "processed_docs": 0,
        "entity_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "message": "Processing PDF..."
    })
    
    await redis_client.lpush("ingestion:index", ingestion_id)
    
    background_tasks.add_task(
        ingestion_pipeline.ingest_pdf, file_bytes, file.filename, ingestion_id
    )
    
    return {"ingestion_id": ingestion_id, "message": "PDF ingestion started"}


@app.get("/ingest/status/{ingestion_id}", response_model=IngestStatusResponse)
async def get_ingestion_status(ingestion_id: str):
    """Poll ingestion progress."""
    data = await redis_client.get_json(f"ingestion:{ingestion_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return IngestStatusResponse(**data)


@app.get("/ingest/list", response_model=IngestionListResponse)
async def list_ingestions():
    """List all ingested sources."""
    ids = await redis_client.lrange("ingestion:index", 0, 49)  # last 50
    ingestions = []
    for ing_id in ids:
        data = await redis_client.get_json(f"ingestion:{ing_id}")
        if data:
            ingestions.append(IngestStatusResponse(**data))
    return IngestionListResponse(ingestions=ingestions, total=len(ingestions))


@app.delete("/ingest/{ingestion_id}")
async def delete_ingestion(ingestion_id: str):
    """Delete an ingested source from ChromaDB, Neo4j, and Redis."""
    await ingestion_pipeline.delete_ingestion(ingestion_id)
    return {"message": "Ingestion deleted"}


@app.post("/digest", response_model=DigestResponse)
async def generate_digest(request: DigestRequest):
    """Generate a digest of an ingested source."""
    result = await digest_service.generate_digest(request.ingestion_id, request.days_back)
    return result


# ============= Workspace Endpoints =============

@app.post("/workspaces", response_model=dict)
async def create_workspace(request: WorkspaceCreate):
    """Create a new workspace to organize ingestions."""
    from services.workspace_service import workspace_service
    workspace = await workspace_service.create_workspace(request.name, request.description)
    return workspace


@app.get("/workspaces", response_model=WorkspaceList)
async def list_workspaces():
    """List all workspaces."""
    from services.workspace_service import workspace_service
    workspaces = await workspace_service.list_workspaces()
    return WorkspaceList(workspaces=workspaces, total=len(workspaces))


@app.get("/workspaces/{workspace_id}", response_model=WorkspaceDetail)
async def get_workspace(workspace_id: str):
    """Get workspace details with ingestions."""
    from services.workspace_service import workspace_service
    workspace = await workspace_service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    ingestions = await workspace_service.get_workspace_ingestions(workspace_id)
    
    return WorkspaceDetail(
        workspace_id=workspace['workspace_id'],
        name=workspace['name'],
        description=workspace.get('description'),
        ingestion_count=len(ingestions),
        created_at=workspace['created_at'],
        updated_at=workspace['updated_at'],
        ingestions=ingestions
    )


@app.put("/workspaces/{workspace_id}", response_model=dict)
async def update_workspace(workspace_id: str, request: WorkspaceUpdate):
    """Update workspace name or description."""
    from services.workspace_service import workspace_service
    workspace = await workspace_service.update_workspace(
        workspace_id, 
        request.name, 
        request.description
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@app.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str):
    """Delete a workspace."""
    from services.workspace_service import workspace_service
    success = await workspace_service.delete_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"message": "Workspace deleted"}


@app.post("/workspaces/{workspace_id}/ingestions")
async def add_ingestion_to_workspace(workspace_id: str, request: AddIngestionToWorkspace):
    """Add an ingestion to a workspace."""
    from services.workspace_service import workspace_service
    success = await workspace_service.add_ingestion_to_workspace(
        workspace_id, 
        request.ingestion_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Workspace or ingestion not found")
    return {"message": "Ingestion added to workspace"}


@app.delete("/workspaces/{workspace_id}/ingestions/{ingestion_id}")
async def remove_ingestion_from_workspace(workspace_id: str, ingestion_id: str):
    """Remove an ingestion from a workspace."""
    from services.workspace_service import workspace_service
    success = await workspace_service.remove_ingestion_from_workspace(
        workspace_id, 
        ingestion_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"message": "Ingestion removed from workspace"}


@app.get("/workspaces/{workspace_id}/stats", response_model=WorkspaceStats)
async def get_workspace_stats(workspace_id: str):
    """Get workspace statistics."""
    from services.workspace_service import workspace_service
    stats = await workspace_service.get_workspace_stats(workspace_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceStats(**stats)


@app.get("/knowledge-graph")
async def get_knowledge_graph(ingestion_id: str = None):
    """
    Get knowledge graph data for visualization.
    Returns nodes (entities) and edges (relationships) from Neo4j.
    
    Args:
        ingestion_id: Optional filter by specific ingestion
    
    Returns:
        {
            "nodes": [{"id": "entity_name", "label": "entity_type", "properties": {...}}],
            "edges": [{"source": "from", "target": "to", "label": "relationship_type"}],
            "stats": {"total_nodes": N, "total_edges": M}
        }
    """
    try:
        # Build Cypher query
        if ingestion_id:
            # Filter by ingestion_id if provided
            cypher = """
            MATCH (n)
            WHERE n.ingestion_id = $ingestion_id
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE m.ingestion_id = $ingestion_id
            RETURN n, r, m
            LIMIT 500
            """
            params = {"ingestion_id": ingestion_id}
        else:
            # Get all nodes and relationships
            cypher = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 500
            """
            params = {}
        
        # Execute query
        results = await neo4j_client.execute_query(cypher, params)
        
        # Process results into nodes and edges
        nodes_dict = {}
        edges = []
        
        for record in results:
            # Process source node
            if record.get('n'):
                node = record['n']
                node_id = node.get('name') or str(node.id)
                if node_id not in nodes_dict:
                    nodes_dict[node_id] = {
                        "id": node_id,
                        "label": node.get('entity_type', 'unknown'),
                        "properties": dict(node)
                    }
            
            # Process relationship and target node
            if record.get('r') and record.get('m'):
                rel = record['r']
                target = record['m']
                target_id = target.get('name') or str(target.id)
                
                # Add target node
                if target_id not in nodes_dict:
                    nodes_dict[target_id] = {
                        "id": target_id,
                        "label": target.get('entity_type', 'unknown'),
                        "properties": dict(target)
                    }
                
                # Add edge
                edges.append({
                    "source": node_id,
                    "target": target_id,
                    "label": rel.type,
                    "properties": dict(rel)
                })
        
        nodes = list(nodes_dict.values())
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "filtered_by": ingestion_id if ingestion_id else "all"
            }
        }
    
    except Exception as e:
        # If Neo4j is not available or query fails, return empty graph
        return {
            "nodes": [],
            "edges": [],
            "stats": {
                "total_nodes": 0,
                "total_edges": 0,
                "error": str(e)
            }
        }


@app.get("/")
def root():
    """Root endpoint - API documentation."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "query": {
                "path": "/query",
                "method": "POST",
                "description": "Main RAG query endpoint (Normal or Agentic)"
            },
            "async_agent": {
                "path": "/agent/async",
                "method": "POST",
                "description": "Submit async Agentic RAG task"
            },
            "agent_status": {
                "path": "/agent/status/{task_id}",
                "method": "GET",
                "description": "Check async task status and get results"
            },
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "System health check"
            },
            "cache": {
                "stats": "GET /cache/stats",
                "list": "GET /cache/keys?limit=100",
                "search": "GET /cache/search?q=keyword",
                "clear": "POST /cache/clear",
                "delete": "DELETE /cache/query?query=..."
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
