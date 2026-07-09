"""
Admin Analytics Service
Provides analytics data and system statistics for admin dashboard.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database.redis_client import redis_client
from database.chroma_client import chroma_client
from database.neo4j_client import neo4j_client
from utils.rabbitmq_client import rabbitmq_client
import json


class AdminAnalytics:
    """Analytics service for admin dashboard."""
    
    STATS_KEY = "admin:stats"
    ROUTER_DECISIONS_KEY = "admin:router_decisions"
    QUERY_LOG_KEY = "admin:query_log"
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        # Get cache stats
        cache_stats = await redis_client.get_json("semantic_cache:stats") or {}
        
        # Get query count from cache stats
        total_queries = cache_stats.get("total_queries", 0)
        cache_hit_rate = cache_stats.get("hit_rate", 0.0)
        
        # Get average response time from recent queries
        avg_response_time = await self._get_avg_response_time()
        
        # Get active tasks count
        active_tasks = await self._get_active_tasks_count()
        
        # Get ChromaDB stats
        chromadb_docs = self._get_chromadb_doc_count()
        
        # Get Neo4j stats
        neo4j_nodes, neo4j_rels = await self._get_neo4j_counts()
        
        return {
            "total_queries": total_queries,
            "cache_hit_rate": cache_hit_rate,
            "avg_response_time_ms": avg_response_time,
            "active_tasks": active_tasks,
            "chromadb_docs": chromadb_docs,
            "neo4j_nodes": neo4j_nodes,
            "neo4j_relationships": neo4j_rels
        }
    
    async def _get_avg_response_time(self) -> float:
        """Calculate average response time from recent queries."""
        try:
            log_data = await redis_client.get_json(self.QUERY_LOG_KEY) or []
            if not log_data:
                return 0.0
            
            times = [q.get("response_time_ms", 0) for q in log_data[-100:]]
            return sum(times) / len(times) if times else 0.0
        except:
            return 0.0
    
    async def _get_active_tasks_count(self) -> int:
        """Get count of active/pending async tasks."""
        try:
            # Get all task keys
            pattern = "task:*:status"
            # For simplicity, we'll track this separately
            active_count = await redis_client.get_json("admin:active_tasks_count") or 0
            return active_count
        except:
            return 0
    
    def _get_chromadb_doc_count(self) -> int:
        """Get total document count in ChromaDB."""
        try:
            collection = chroma_client.get_collection()
            return collection.count()
        except:
            return 0
    
    async def _get_neo4j_counts(self) -> tuple:
        """Get Neo4j node and relationship counts."""
        try:
            query = """
            MATCH (n)
            RETURN count(n) as node_count
            """
            result = await neo4j_client.execute_query(query)
            node_count = result[0]["node_count"] if result else 0
            
            query = """
            MATCH ()-[r]->()
            RETURN count(r) as rel_count
            """
            result = await neo4j_client.execute_query(query)
            rel_count = result[0]["rel_count"] if result else 0
            
            return node_count, rel_count
        except:
            return 0, 0
    
    async def get_chromadb_stats(self) -> Dict[str, Any]:
        """Get detailed ChromaDB statistics."""
        try:
            collection = chroma_client.get_collection()
            total_docs = collection.count()
            
            return {
                "total_documents": total_docs,
                "collections": ["financial_services"],  # Our collection name
                "collection_sizes": {"financial_services": total_docs}
            }
        except Exception as e:
            return {
                "total_documents": 0,
                "collections": [],
                "collection_sizes": {}
            }
    
    async def get_neo4j_stats(self) -> Dict[str, Any]:
        """Get detailed Neo4j graph statistics."""
        try:
            # Get total nodes
            query = "MATCH (n) RETURN count(n) as total"
            result = await neo4j_client.execute_query(query)
            total_nodes = result[0]["total"] if result else 0
            
            # Get total relationships
            query = "MATCH ()-[r]->() RETURN count(r) as total"
            result = await neo4j_client.execute_query(query)
            total_rels = result[0]["total"] if result else 0
            
            # Get node labels distribution
            query = """
            MATCH (n)
            RETURN labels(n)[0] as label, count(*) as count
            ORDER BY count DESC
            """
            result = await neo4j_client.execute_query(query)
            node_labels = {r["label"]: r["count"] for r in result} if result else {}
            
            # Get relationship types distribution
            query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(*) as count
            ORDER BY count DESC
            """
            result = await neo4j_client.execute_query(query)
            rel_types = {r["type"]: r["count"] for r in result} if result else {}
            
            return {
                "total_nodes": total_nodes,
                "total_relationships": total_rels,
                "node_labels": node_labels,
                "relationship_types": rel_types
            }
        except Exception as e:
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "node_labels": {},
                "relationship_types": {}
            }
    
    async def get_router_stats(self) -> Dict[str, Any]:
        """Get router decision statistics."""
        try:
            decisions = await redis_client.get_json(self.ROUTER_DECISIONS_KEY) or []
            
            total = len(decisions)
            if total == 0:
                return {
                    "total_queries": 0,
                    "normal_rag_count": 0,
                    "agentic_rag_count": 0,
                    "normal_percentage": 0.0,
                    "agentic_percentage": 0.0,
                    "recent_decisions": []
                }
            
            normal_count = sum(1 for d in decisions if d.get("pipeline") == "normal_rag")
            agentic_count = total - normal_count
            
            return {
                "total_queries": total,
                "normal_rag_count": normal_count,
                "agentic_rag_count": agentic_count,
                "normal_percentage": (normal_count / total * 100) if total > 0 else 0,
                "agentic_percentage": (agentic_count / total * 100) if total > 0 else 0,
                "recent_decisions": decisions[-20:]  # Last 20
            }
        except:
            return {
                "total_queries": 0,
                "normal_rag_count": 0,
                "agentic_rag_count": 0,
                "normal_percentage": 0.0,
                "agentic_percentage": 0.0,
                "recent_decisions": []
            }
    
    async def log_router_decision(self, query: str, pipeline: str, classification: str):
        """Log a router decision for analytics."""
        try:
            decisions = await redis_client.get_json(self.ROUTER_DECISIONS_KEY) or []
            
            decision = {
                "query": query,
                "pipeline": pipeline,
                "classification": classification,
                "timestamp": datetime.now().isoformat()
            }
            
            decisions.append(decision)
            
            # Keep only last 1000 decisions
            if len(decisions) > 1000:
                decisions = decisions[-1000:]
            
            await redis_client.set_json(self.ROUTER_DECISIONS_KEY, decisions, ttl=86400 * 7)  # 7 days
        except:
            pass
    
    async def log_query(self, query: str, pipeline: str, response_time_ms: float, cache_hit: bool):
        """Log query for analytics."""
        try:
            log_data = await redis_client.get_json(self.QUERY_LOG_KEY) or []
            
            entry = {
                "query": query,
                "pipeline": pipeline,
                "response_time_ms": response_time_ms,
                "cache_hit": cache_hit,
                "timestamp": datetime.now().isoformat()
            }
            
            log_data.append(entry)
            
            # Keep only last 1000 queries
            if len(log_data) > 1000:
                log_data = log_data[-1000:]
            
            await redis_client.set_json(self.QUERY_LOG_KEY, log_data, ttl=86400 * 7)  # 7 days
        except:
            pass
    
    async def get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics data for charts."""
        try:
            log_data = await redis_client.get_json(self.QUERY_LOG_KEY) or []
            
            # Query volume by hour (last 24 hours)
            query_volume = self._calculate_query_volume(log_data)
            
            # Response times distribution
            response_times = [q.get("response_time_ms", 0) for q in log_data]
            
            # Database usage (from metadata if available)
            database_usage = self._calculate_database_usage(log_data)
            
            # Pipeline performance comparison
            pipeline_performance = self._calculate_pipeline_performance(log_data)
            
            return {
                "query_volume": query_volume,
                "response_times": response_times[-100:],  # Last 100
                "database_usage": database_usage,
                "pipeline_performance": pipeline_performance
            }
        except:
            return {
                "query_volume": [],
                "response_times": [],
                "database_usage": {"chromadb": 0, "neo4j": 0, "hybrid": 0},
                "pipeline_performance": {}
            }
    
    def _calculate_query_volume(self, log_data: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate hourly query volume for last 24 hours."""
        now = datetime.now()
        hourly_counts = {}
        
        for entry in log_data:
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if (now - timestamp).total_seconds() < 86400:  # Last 24 hours
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
            except:
                continue
        
        # Convert to list format for charts
        return [{"time": k, "count": v} for k, v in sorted(hourly_counts.items())]
    
    def _calculate_database_usage(self, log_data: List[Dict]) -> Dict[str, int]:
        """Calculate database usage statistics."""
        # This would need metadata from queries - simplified version
        return {
            "chromadb": len([q for q in log_data if q.get("pipeline") == "normal_rag"]),
            "neo4j": 0,  # Would need actual data
            "hybrid": len([q for q in log_data if q.get("pipeline") == "agentic_rag"])
        }
    
    def _calculate_pipeline_performance(self, log_data: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics per pipeline."""
        normal_times = [q["response_time_ms"] for q in log_data if q.get("pipeline") == "normal_rag" and "response_time_ms" in q]
        agentic_times = [q["response_time_ms"] for q in log_data if q.get("pipeline") == "agentic_rag" and "response_time_ms" in q]
        
        return {
            "normal_rag": {
                "avg_time": sum(normal_times) / len(normal_times) if normal_times else 0,
                "count": len(normal_times)
            },
            "agentic_rag": {
                "avg_time": sum(agentic_times) / len(agentic_times) if agentic_times else 0,
                "count": len(agentic_times)
            }
        }
    
    async def get_all_tasks(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all async tasks with optional status filter."""
        try:
            # Get task tracking data from Redis
            tasks_data = await redis_client.get_json("admin:all_tasks") or []
            
            if status_filter:
                tasks_data = [t for t in tasks_data if t.get("status") == status_filter]
            
            return tasks_data
        except:
            return []
    
    async def track_task(self, task_id: str, query: str, status: str, pipeline: Optional[str] = None, error: Optional[str] = None):
        """Track an async task for admin monitoring."""
        try:
            tasks_data = await redis_client.get_json("admin:all_tasks") or []
            
            # Find existing task or create new
            task_entry = None
            for task in tasks_data:
                if task["task_id"] == task_id:
                    task_entry = task
                    break
            
            if not task_entry:
                task_entry = {
                    "task_id": task_id,
                    "query": query,
                    "status": status,
                    "pipeline": pipeline,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None,
                    "error": None
                }
                tasks_data.append(task_entry)
            
            # Update task
            task_entry["status"] = status
            if pipeline:
                task_entry["pipeline"] = pipeline
            if error:
                task_entry["error"] = error
            if status in ["completed", "failed"]:
                task_entry["completed_at"] = datetime.now().isoformat()
            
            # Keep only last 500 tasks
            if len(tasks_data) > 500:
                tasks_data = tasks_data[-500:]
            
            await redis_client.set_json("admin:all_tasks", tasks_data, ttl=86400 * 7)
        except:
            pass


# Global instance
admin_analytics = AdminAnalytics()
