"""
Agent Worker - Executes steps from RabbitMQ queue.
Consumes messages, executes them, stores results in Redis.
Does NOT plan or decide - only executes.
"""
import time
import asyncio
import os
import uuid
from typing import List
from datetime import datetime
from groq import AsyncGroq

from database.redis_client import redis_client
from database.chroma_client import chroma_client
from database.neo4j_client import neo4j_client
from services.embedding_service import embedding_service
from services.entity_matcher import entity_matcher
from services.hybrid_retriever import hybrid_retriever   # now used
from services.reranker import reranker                   # now used
from utils.rabbitmq_client import rabbitmq_client
from models.schemas import AgentStep, StepResult, StepType, Document
from config.settings import settings


class AgentWorker:
    """
    RabbitMQ consumer that executes agent steps.
    Runs independently, processes ONE step at a time.
    """
    
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.running = False
        # Worker identification for tracking and monitoring
        self.worker_id = os.getenv("WORKER_ID") or os.getenv("HOSTNAME") or f"worker-{uuid.uuid4().hex[:8]}"
        print(f"🆔 Worker ID: {self.worker_id}")
    
    async def start(self):
        """Start consuming steps from RabbitMQ."""
        self.running = True
        print("Agent Worker started, waiting for steps...")
        
        # Start consuming
        await rabbitmq_client.consume_steps(self._process_step)
        
        # Keep alive
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop worker gracefully."""
        self.running = False
    
    async def _process_step(self, step: AgentStep):
        """
        Process a single step from the queue.
        Execute it and store result in Redis.
        """
        start_time = time.time()
        started_at = datetime.utcnow()
        
        try:
            # Route to appropriate handler
            if step.step_type == StepType.RETRIEVE:
                result_data = await self._execute_retrieval(step)
                status = "success"
                error = None
            
            elif step.step_type == StepType.REASON:
                result_data = await self._execute_reasoning(step)
                status = "success"
                error = None

            elif step.step_type == "resolution_chain":  # NEW
                result_data = await self._execute_resolution_chain(step)
                status = "success"
                error = None
            
            else:
                result_data = None
                status = "failure"
                error = f"Unknown step type: {step.step_type}"
        
        except Exception as e:
            result_data = None
            status = "failure"
            error = str(e)
            print(f"Error processing step: {error}")
            
            # Retry logic
            if step.attempt < step.max_attempts:
                print(f"Retrying step {step.step_id} (attempt {step.attempt + 1}/{step.max_attempts})")
                # Re-publish with incremented attempt
                step_dict = step.model_dump()
                step_dict['attempt'] = step.attempt + 1
                retry_step = AgentStep(**step_dict)
                await rabbitmq_client.publish_step(retry_step)
                return  # Don't store result yet
        
        # Store result in Redis
        execution_time = (time.time() - start_time) * 1000
        completed_at = datetime.utcnow()
        
        result = StepResult(
            step_id=step.step_id,
            status=status,
            data=result_data,
            error=error,
            execution_time_ms=execution_time,
            worker_id=self.worker_id,
            started_at=started_at,
            completed_at=completed_at
        )
        
        result_key = f"step_result:{step.step_id}"
        await redis_client.set_json(
            result_key,
            result.model_dump(),
            ttl=600  # 10 minutes
        )
        
        print(f"Step {step.step_id} completed: {status}")
    
    async def _execute_retrieval(self, step: AgentStep) -> dict:
        """
        Intent-aware retrieval using semantic tags, hybrid search, and reranking.
        Uses hybrid_retriever.py and reranker.py (both exist, now called for the first time).
        """
        if "query" not in step.payload:
            raise ValueError(f"Missing 'query' in payload. Got: {list(step.payload.keys())}")

        query = step.payload["query"]
        retrieval_mode = step.payload.get("retrieval_mode", "hybrid_reranked")
        entities = step.payload.get("entities", [])
        ingestion_id = step.payload.get("ingestion_id", None)
        intent_tags = step.payload.get("intent_tags", None)
        temporal_buckets = step.payload.get("temporal_buckets", None)
        min_quality = step.payload.get("min_content_quality", 0.3)

        # Build ChromaDB where clause from semantic tags
        where_conditions = []

        if ingestion_id:
            where_conditions.append({"ingestion_id": {"$eq": ingestion_id}})

        if intent_tags:
            # intent_tags stored as pipe-separated string "decision|fix"
            # Use $or across all requested intent values
            intent_conditions = [{"intent_tags": {"$contains": tag}} for tag in intent_tags]
            if intent_conditions:
                where_conditions.append({"$or": intent_conditions})

        if temporal_buckets:
            bucket_conditions = [{"temporal_bucket": {"$eq": b}} for b in temporal_buckets]
            where_conditions.append({"$or": bucket_conditions})

        where = None
        if len(where_conditions) == 1:
            where = where_conditions[0]
        elif len(where_conditions) > 1:
            where = {"$and": where_conditions}

        # Step 1: Get query embedding
        query_embedding = embedding_service.embed_text(query)

        raw_documents = []

        # Step 2a: Original financial_services collection (no tag filter)
        try:
            results = chroma_client.query(
                query_embeddings=[query_embedding],
                n_results=10
            )
            for i, doc_id in enumerate(results['ids'][0]):
                raw_documents.append({
                    "doc_id": doc_id,
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'][0] else {},
                    "score": 1.0 - results['distances'][0][i],
                    "collection": "financial_services"
                })
        except Exception as e:
            print(f"Financial collection query failed: {e}")

        # Step 2b: Ingested collection — apply where filter
        try:
            ingested_collection = chroma_client.client.get_or_create_collection(
                name=settings.INGESTED_COLLECTION_NAME
            )
            ingested_results = ingested_collection.query(
                query_embeddings=[query_embedding],
                n_results=20,
                where=where
            )
            for i, doc_id in enumerate(ingested_results['ids'][0]):
                meta = ingested_results['metadatas'][0][i] if ingested_results['metadatas'][0] else {}
                if float(meta.get("content_quality", 1.0)) >= min_quality:
                    raw_documents.append({
                        "doc_id": doc_id,
                        "content": ingested_results['documents'][0][i],
                        "metadata": meta,
                        "score": 1.0 - ingested_results['distances'][0][i],
                        "collection": "niyanta_ingested"
                    })
        except Exception as e:
            print(f"Ingested collection query failed: {e}")

        # Step 3: BM25 keyword search via hybrid_retriever
        try:
            keyword_results = await hybrid_retriever._keyword_search(
                query=query,
                top_k=10,
                source_filter=ingestion_id
            )
            existing_ids = {d["doc_id"] for d in raw_documents}
            for doc in keyword_results:
                doc_id = doc.get("doc_id", doc["content"][:50])
                if doc_id not in existing_ids:
                    raw_documents.append(doc)
        except Exception as e:
            print(f"Keyword search failed, continuing: {e}")

        # Step 4: Graph retrieval if entities present
        graph_documents = []
        if retrieval_mode in ["graph", "hybrid", "hybrid_reranked", "source_aware"] and entities:
            matched_entities = await entity_matcher.find_matching_entities(
                query_entities=entities[:5],
                threshold=0.6,
                top_k=2
            )
            for match in matched_entities:
                entity_name = match['matched_entity']
                relationships = await neo4j_client.find_entity_relationships(
                    entity=entity_name,
                    max_depth=2
                )
                if relationships:
                    graph_content = f"Entity '{entity_name}':\n"
                    for rel in relationships[:5]:
                        graph_content += f"- {rel['target']} ({rel['target_type']}) via {rel['relationships']}\n"
                    graph_documents.append({
                        "doc_id": f"graph_{entity_name.replace(' ', '_')}",
                        "content": graph_content,
                        "metadata": {
                            "source": "neo4j",
                            "entity": entity_name,
                            "intent_tags": "reference",
                            "source_category": "code",
                            "content_quality": 0.8 + (match['similarity'] * 0.2)
                        },
                        "score": 0.8 + (match['similarity'] * 0.2)
                    })

        all_documents = raw_documents + graph_documents

        if not all_documents:
            return {"documents": [], "retrieval_mode": retrieval_mode, "num_results": 0}

        # Step 5: Rerank using cross-encoder
        try:
            reranked = reranker.rerank(
                query=query,
                documents=all_documents,
                top_k=7
            )
        except Exception as e:
            print(f"Reranking failed, using raw results: {e}")
            reranked = sorted(all_documents, key=lambda x: x.get("score", 0), reverse=True)[:7]

        return {
            "documents": reranked,
            "retrieval_mode": retrieval_mode,
            "num_results": len(reranked)
        }
    
    async def _execute_resolution_chain(self, step: AgentStep) -> dict:
        """
        Follows issue → PR → file chains in Neo4j.
        For 'how was X fixed/resolved/implemented' queries.
        """
        entities = step.payload.get("entities", [])
        ingestion_id = step.payload.get("ingestion_id", None)

        chains = []
        for entity_name in entities[:3]:
            cypher = """
            MATCH path = (start:IngestedEntity)
                         -[:RESOLVES|TAGGED|CREATED|CHANGES*1..3]-
                         (connected:IngestedEntity)
            WHERE (start.name CONTAINS $entity OR start.source_id CONTAINS $entity)
              AND ($ingestion_id IS NULL OR start.ingestion_id = $ingestion_id)
            RETURN
                [n in nodes(path) | n.name] as chain,
                [n in nodes(path) | n.source_url] as urls,
                [r in relationships(path) | type(r)] as rel_types,
                length(path) as depth
            ORDER BY depth ASC
            LIMIT 5
            """
            try:
                results = await neo4j_client.execute_query(cypher, {
                    "entity": entity_name,
                    "ingestion_id": ingestion_id
                })

                for record in results:
                    chain_nodes = record.get("chain", [])
                    rel_types = record.get("rel_types", [])
                    source_urls = [u for u in record.get("urls", []) if u]

                    chain_text = " → ".join([
                        f"{node} (via {rel})"
                        for node, rel in zip(chain_nodes, rel_types + [""])
                    ])
                    chains.append({
                        "doc_id": f"chain_{entity_name}_{len(chains)}",
                        "content": f"Resolution chain for '{entity_name}': {chain_text}",
                        "metadata": {
                            "source_type": "graph_chain",
                            "source_urls": "|".join(source_urls),
                            "intent_tags": "fix|decision",
                            "source_category": "code",
                            "content_quality": 0.9
                        },
                        "score": 0.9
                    })
            except Exception as e:
                print(f"Resolution chain query failed for '{entity_name}': {e}")

        return {
            "documents": chains,
            "retrieval_mode": "resolution_chain",
            "num_results": len(chains)
        }

    async def _execute_reasoning(self, step: AgentStep) -> dict:
        """
        Execute reasoning step using LLM.
        Analyzes relationships and draws conclusions.
        """
        entities = step.payload.get("entities", [])
        previous_context = step.payload.get("previous_context")
        
        # Build reasoning prompt
        prompt = f"""Analyze the relationships between these entities: {', '.join(entities)}

Previous context:
{previous_context if previous_context else 'None'}

Provide a reasoning analysis focusing on:
1. How these entities are connected
2. Any important relationships or patterns
3. Relevant conclusions

Keep your analysis concise and factual."""
        
        response = await self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an analytical AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        reasoning_output = response.choices[0].message.content
        
        # Check for contradictions in Neo4j
        contradictions = []
        if len(entities) >= 2:
            contradictions = await neo4j_client.find_contradictions(
                entities[0],
                entities[1]
            )
        
        return {
            "reasoning": reasoning_output,
            "entities_analyzed": entities,
            "contradictions_found": len(contradictions),
            "relationships": contradictions[:3] if contradictions else []
        }


# Global worker instance
agent_worker = AgentWorker()
