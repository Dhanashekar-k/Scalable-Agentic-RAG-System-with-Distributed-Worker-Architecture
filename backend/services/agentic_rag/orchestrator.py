"""
Agentic RAG Orchestrator
Coordinates planning (LangGraph) and execution (RabbitMQ workers).
"""
import asyncio
import time
import uuid
from typing import Optional
from groq import AsyncGroq

from database.redis_client import redis_client
from database.chroma_client import chroma_client
from database.neo4j_client import neo4j_client
from services.embedding_service import embedding_service
from utils.rabbitmq_client import rabbitmq_client
from models.schemas import (
    AgentPlan,
    AgentStep,
    StepType,
    StepResult,
    AnswerEvaluation
)
from config.settings import settings
from .langgraph_planner import langgraph_planner


class AgenticOrchestrator:
    """
    Orchestrates Agentic RAG execution.
    Uses LangGraph for planning, RabbitMQ for step execution.
    """
    
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    async def process_query(self, query: str, request_id: str, ingestion_id: str = None) -> dict:
        """
        Execute complete Agentic RAG pipeline.
        Returns answer with metadata.
        """
        start_time = time.time()
        
        # Step 1: LangGraph Planning
        plan = await langgraph_planner.create_plan(query, request_id)
        
        # Step 2: Execute plan steps via RabbitMQ
        step_results = await self._execute_plan_steps(plan, query, ingestion_id)
        
        # Step 3: Generate answer from collected context
        answer = await self._generate_answer(query, step_results)
        
        # Step 4: Evaluate answer
        evaluation = await self._evaluate_answer(query, answer, plan)
        
        # Step 5: Optional replan (max 1)
        if evaluation.should_replan:
            # One additional step allowed
            refined_results = await self._execute_replan_step(plan, query, ingestion_id)
            step_results.extend(refined_results)
            answer = await self._generate_answer(query, step_results)
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "answer": answer,
            "confidence": evaluation.confidence_score,
            "metadata": {
                "plan_classification": plan.classification.value,
                "entities": plan.entities,
                "retrieval_mode": plan.retrieval_mode.value,
                "steps_executed": len(step_results),
                "replanned": evaluation.should_replan
            },
            "processing_time_ms": processing_time
        }
    
    async def _execute_plan_steps(
        self,
        plan: AgentPlan,
        query: str,
        ingestion_id: str = None
    ) -> list[StepResult]:
        """
        Execute plan by publishing steps to RabbitMQ.
        Wait for workers to complete them.
        """
        step_results = []
        
        # Step 1: Retrieval (always first)
        if plan.retrieval_needed:
            # Use resolution_chain step type when mode is resolution_chain
            step_type = (
                "resolution_chain"
                if plan.retrieval_mode.value == "resolution_chain"
                else StepType.RETRIEVE
            )
            retrieval_step = AgentStep(
                request_id=plan.request_id,
                step_id=f"{plan.request_id}_retrieve",
                step_type=step_type,
                payload={
                    "query": query,
                    "retrieval_mode": plan.retrieval_mode.value,
                    "entities": plan.entities,
                    "ingestion_id": ingestion_id,           # NEW
                    "intent_tags": plan.intent_tags,        # NEW
                    "temporal_buckets": plan.temporal_buckets,  # NEW
                    "min_content_quality": 0.3              # NEW
                }
            )
            
            await rabbitmq_client.publish_step(retrieval_step)
            result = await self._wait_for_step_result(retrieval_step.step_id)
            step_results.append(result)
        
        # Step 2: Graph reasoning (if needed)
        if plan.needs_graph_reasoning:
            reason_step = AgentStep(
                request_id=plan.request_id,
                step_id=f"{plan.request_id}_reason",
                step_type=StepType.REASON,
                payload={
                    "entities": plan.entities,
                    "previous_context": step_results[0].data if step_results else None
                }
            )
            
            await rabbitmq_client.publish_step(reason_step)
            result = await self._wait_for_step_result(reason_step.step_id)
            step_results.append(result)
        
        return step_results
    
    async def _wait_for_step_result(
        self,
        step_id: str,
        timeout: int = None
    ) -> StepResult:
        """
        Wait for worker to complete step and store result in Redis.
        Implements bounded waiting.
        """
        timeout = timeout or settings.AGENT_TIMEOUT_SECONDS
        result_key = f"step_result:{step_id}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            result_data = await redis_client.get_json(result_key)
            
            if result_data:
                return StepResult(**result_data)
            
            await asyncio.sleep(0.5)  # Poll every 500ms
        
        # Timeout - return partial result
        return StepResult(
            step_id=step_id,
            status="failure",
            data=None,
            error="Step execution timeout",
            execution_time_ms=(time.time() - start_time) * 1000
        )
    
    async def _generate_answer(
        self,
        query: str,
        step_results: list[StepResult]
    ) -> str:
        """Generate final answer from step results."""
        # Combine all context from steps
        context_parts = []
        
        for result in step_results:
            if result.status == "success" and result.data:
                if isinstance(result.data, dict):
                    if "documents" in result.data:
                        for doc in result.data["documents"]:
                            context_parts.append(doc["content"])
                    elif "relationships" in result.data:
                        context_parts.append(
                            f"Graph relationships: {result.data['relationships']}"
                        )
        
        context = "\n\n".join(context_parts)
        
        # Generate answer
        system_prompt = """You are an expert AI assistant. Answer the question based on the provided context.
Use information from both document retrieval and graph reasoning.
If information is insufficient, acknowledge it."""
        
        user_prompt = f"""Context:
{context}

Question: {query}

Provide a comprehensive answer:"""
        
        response = await self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    async def _evaluate_answer(
        self,
        query: str,
        answer: str,
        plan: AgentPlan
    ) -> AnswerEvaluation:
        """Evaluate answer quality and decide if replan needed."""
        # Simple evaluation logic
        # In production, use more sophisticated scoring
        
        # Check entity coverage
        entities_mentioned = sum(
            1 for entity in plan.entities
            if entity.lower() in answer.lower()
        )
        has_entity_coverage = (
            entities_mentioned >= len(plan.entities) * 0.6
            if plan.entities else True
        )
        
        # Basic relevance check
        is_relevant = len(answer) > 50 and "I don't know" not in answer
        
        # Completeness heuristic
        is_complete = len(answer) > 100
        
        # Calculate confidence
        confidence = 0.7
        if has_entity_coverage:
            confidence += 0.15
        if is_complete:
            confidence += 0.15
        
        # Decide if replan needed
        should_replan = (
            not has_entity_coverage or not is_relevant
        ) and plan.classification.value == "complex"
        
        return AnswerEvaluation(
            is_relevant=is_relevant,
            has_entity_coverage=has_entity_coverage,
            is_complete=is_complete,
            confidence_score=min(confidence, 1.0),
            should_replan=should_replan,
            evaluation_reasoning="Evaluated based on entity coverage and answer completeness"
        )
    
    async def _execute_replan_step(
        self,
        plan: AgentPlan,
        query: str,
        ingestion_id: str = None
    ) -> list[StepResult]:
        """Execute one additional retrieval step after replan."""
        replan_step = AgentStep(
            request_id=plan.request_id,
            step_id=f"{plan.request_id}_replan",
            step_type=StepType.RETRIEVE,
            payload={
                "query": query,
                "retrieval_mode": "hybrid_reranked",
                "entities": plan.entities,
                "ingestion_id": ingestion_id,
                "intent_tags": plan.intent_tags,
                "temporal_buckets": plan.temporal_buckets,
                "min_content_quality": 0.3
            }
        )
        
        await rabbitmq_client.publish_step(replan_step)
        result = await self._wait_for_step_result(replan_step.step_id)
        
        return [result]


# Global orchestrator instance
agentic_orchestrator = AgenticOrchestrator()
