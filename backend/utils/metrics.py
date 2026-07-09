"""
Prometheus metrics for Niyanta backend
Tracks API requests, worker tasks, and system performance
"""

from prometheus_client import Counter, Histogram, Gauge, Enum
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Task/Worker metrics
active_workers = Gauge(
    'active_workers',
    'Number of active workers'
)

queued_tasks = Gauge(
    'queued_tasks',
    'Number of tasks in queue'
)

completed_tasks_total = Counter(
    'completed_tasks_total',
    'Total completed tasks',
    ['worker_id', 'status']  # status: success, failed, timeout
)

task_duration_seconds = Histogram(
    'task_duration_seconds',
    'Task execution duration in seconds',
    ['task_type', 'worker_id'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# RAG metrics
rag_query_duration_seconds = Histogram(
    'rag_query_duration_seconds',
    'RAG query duration in seconds',
    ['mode'],  # mode: normal, agentic, cached
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses'
)

# Database metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']  # operation: get, set, delete, etc.
)

vector_retrieval_duration_seconds = Histogram(
    'vector_retrieval_duration_seconds',
    'Vector database retrieval duration',
    ['database'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

# System metrics
worker_memory_bytes = Gauge(
    'worker_memory_bytes',
    'Worker memory usage in bytes',
    ['worker_id']
)

backend_uptime_seconds = Gauge(
    'backend_uptime_seconds',
    'Backend uptime in seconds'
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'service']
)

# Middleware for request tracking
class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
        self.start_time = time.time()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        request_start_time = time.time()
        
        async def send_with_metrics(message):
            if message['type'] == 'http.response.start':
                status_code = message['status']
                path = scope.get('path', 'unknown')
                method = scope.get('method', 'UNKNOWN')
                
                # Record metrics
                duration = time.time() - request_start_time
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)
                
                http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status=status_code
                ).inc()
            
            await send(message)

        # Update uptime
        backend_uptime_seconds.set(time.time() - self.start_time)
        
        await self.app(scope, receive, send_with_metrics)


def setup_metrics():
    """
    Initialize metrics. Call this in your main.py:
    
    from prometheus_client import make_wsgi_app
    from fastapi.middleware.wsgi import WSGIMiddleware
    
    app.add_middleware(MetricsMiddleware)
    metrics_app = FastAPI()
    metrics_app.add_route('/metrics', make_wsgi_app())
    """
    pass
