"""
LangGraph Planner - Agent Brain for Agentic RAG
Decides what to do, NOT how to execute it.
Emits steps one at a time for RabbitMQ workers.
"""
from typing import TypedDict, Annotated, Sequence
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import operator
import json

from models.schemas import (
    QueryClassification,
    RetrievalMode,
    AgentPlan
)
from config.settings import settings


# ============= State Definition =============

class AgentState(TypedDict):
    """State passed through LangGraph nodes."""
    request_id: str
    original_query: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    classification: str
    entities: list[str]
    retrieval_needed: bool
    retrieval_mode: str
    needs_graph_reasoning: bool
    steps_completed: int
    should_stop: bool
    replan_count: int
    intent_tags: list[str]       # NEW
    temporal_buckets: list[str]  # NEW


# ============= LangGraph Planner =============

class LangGraphPlanner:
    """
    Agent planning brain using LangGraph.
    Makes decisions but does NOT execute steps.
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=0.1,
            groq_api_key=settings.GROQ_API_KEY
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construct LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify_query", self._classify_query)
        workflow.add_node("extract_entities", self._extract_entities)
        workflow.add_node("decide_retrieval", self._decide_retrieval)
        workflow.add_node("plan_next_step", self._plan_next_step)
        workflow.add_node("check_stop_or_continue", self._check_stop_or_continue)
        workflow.add_node("decide_replan", self._decide_replan)
        
        # Define edges
        workflow.set_entry_point("classify_query")
        workflow.add_edge("classify_query", "extract_entities")
        workflow.add_edge("extract_entities", "decide_retrieval")
        
        # Conditional routing after retrieval decision
        workflow.add_conditional_edges(
            "decide_retrieval",
            self._route_after_retrieval,
            {
                "plan_step": "plan_next_step",
                "end": END
            }
        )
        
        workflow.add_edge("plan_next_step", "check_stop_or_continue")
        
        # Check if we should stop or replan
        workflow.add_conditional_edges(
            "check_stop_or_continue",
            self._route_stop_or_continue,
            {
                "continue": "plan_next_step",
                "replan": "decide_replan",
                "end": END
            }
        )
        
        workflow.add_edge("decide_replan", "plan_next_step")
        
        return workflow.compile()
    
    async def create_plan(self, query: str, request_id: str) -> AgentPlan:
        """
        Create execution plan for a complex query.
        Returns high-level plan with step descriptions.
        """
        initial_state: AgentState = {
            "request_id": request_id,
            "original_query": query,
            "messages": [HumanMessage(content=query)],
            "classification": "",
            "entities": [],
            "retrieval_needed": True,
            "retrieval_mode": RetrievalMode.VECTOR_ONLY.value,
            "needs_graph_reasoning": False,
            "steps_completed": 0,
            "should_stop": False,
            "replan_count": 0,
            "intent_tags": [],       # NEW
            "temporal_buckets": []   # NEW
        }
        
        # Run graph
        final_state = await self.graph.ainvoke(initial_state)
        
        # Convert to AgentPlan
        plan = AgentPlan(
            request_id=request_id,
            classification=QueryClassification(final_state["classification"]),
            entities=final_state["entities"],
            retrieval_needed=final_state["retrieval_needed"],
            retrieval_mode=RetrievalMode(final_state["retrieval_mode"]),
            needs_graph_reasoning=final_state["needs_graph_reasoning"],
            steps=self._extract_steps_from_state(final_state),
            intent_tags=final_state.get("intent_tags") or None,
            temporal_buckets=final_state.get("temporal_buckets") or None
        )
        
        return plan
    
    # ============= Node Implementations =============
    
    async def _classify_query(self, state: AgentState) -> dict:
        """Classify query complexity."""
        prompt = f"""Classify this query's complexity:
- SIMPLE: Single fact retrieval, no reasoning needed
- MODERATE: Multiple facts, basic connections
- COMPLEX: Multi-hop reasoning, contradictions, or deep analysis

Query: {state['original_query']}

Respond with only: SIMPLE, MODERATE, or COMPLEX"""
        
        response = await self.llm.ainvoke([SystemMessage(content=prompt)])
        classification = response.content.strip().lower()
        
        return {"classification": classification}
    
    async def _extract_entities(self, state: AgentState) -> dict:
        """Extract key entities from query using LLM with robust parsing."""
        prompt = f"""Extract key entities, concepts, and topics from this financial query.
Include products, regulations, institutions, customer types, and financial concepts.

Query: {state['original_query']}

Return ONLY a JSON array. Examples:
["investment products", "retirement planning", "risk-averse customers"]
["FDIC", "banking regulations", "savings accounts"]

JSON:"""
        
        response = await self.llm.ainvoke([SystemMessage(content=prompt)])
        content = response.content.strip()
        
        # Try multiple parsing strategies
        entities = []
        
        # Strategy 1: Direct JSON parse
        try:
            entities = json.loads(content)
            if isinstance(entities, list) and entities:
                entities = [str(e).strip() for e in entities if e]
        except:
            pass
        
        # Strategy 2: Extract JSON from markdown code block
        if not entities:
            try:
                import re
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
                if json_match:
                    entities = json.loads(json_match.group(1))
            except:
                pass
        
        # Strategy 3: Extract array from text
        if not entities:
            try:
                import re
                array_match = re.search(r'\[([^\]]+)\]', content)
                if array_match:
                    # Parse manually
                    items = array_match.group(1).split(',')
                    entities = [item.strip().strip('"\'') for item in items if item.strip()]
            except:
                pass
        
        # Strategy 4: Use NLP noun phrase extraction as fallback
        if not entities:
            entities = await self._extract_noun_phrases(state['original_query'])
        
        # Clean and deduplicate
        entities = list(set([e.strip() for e in entities if e and len(e.strip()) > 2]))
        
        return {"entities": entities[:10]}  # Limit to 10 entities
    
    async def _extract_noun_phrases(self, query: str) -> list:
        """
        Extract noun phrases using statistical NLP (no hardcoding).
        Uses the LLM to identify key phrases.
        """
        prompt = f"""List the 5 most important noun phrases or key terms from this text.
Return one phrase per line, no numbering, no explanations.

Text: {query}

Key phrases:"""
        
        try:
            response = await self.llm.ainvoke([SystemMessage(content=prompt)])
            phrases = response.content.strip().split('\n')
            # Clean up phrases
            phrases = [
                p.strip().lstrip('0123456789.-) ').strip('"\'') 
                for p in phrases 
                if p.strip()
            ]
            return phrases[:5]
        except:
            # Last resort: split query into meaningful chunks
            words = query.lower().split()
            # Return bigrams and trigrams that might be entities
            chunks = []
            for i in range(len(words)):
                if i + 1 < len(words):
                    chunks.append(f"{words[i]} {words[i+1]}")
                if i + 2 < len(words):
                    chunks.append(f"{words[i]} {words[i+1]} {words[i+2]}")
            return chunks[:5] if chunks else [query]
    
    async def _decide_retrieval(self, state: AgentState) -> dict:
        """Detect query intent and choose retrieval strategy."""
        query_lower = state["original_query"].lower()
        entities = state["entities"]

        decision_keywords = ["why", "decided", "chose", "reason", "because",
                              "approach", "alternative", "trade-off"]
        fix_keywords = ["fixed", "resolved", "solved", "how was", "patch",
                        "closed", "merged"]
        temporal_keywords = ["recent", "latest", "last week", "this week",
                              "changed", "new", "update", "today"]
        explanation_keywords = ["what is", "explain", "how does", "understand",
                                 "what are", "describe"]
        problem_keywords = ["bug", "issue", "error", "broken", "fail",
                             "problem", "wrong"]
        opinion_keywords = ["think", "opinion", "recommend", "better",
                             "prefer", "community", "people say"]

        if any(k in query_lower for k in fix_keywords):
            retrieval_mode = RetrievalMode.RESOLUTION_CHAIN.value
            intent_tags = ["fix", "problem", "decision"]
            temporal_buckets = []

        elif any(k in query_lower for k in decision_keywords):
            retrieval_mode = RetrievalMode.SOURCE_AWARE.value
            intent_tags = ["decision", "discussion", "proposal"]
            temporal_buckets = []

        elif any(k in query_lower for k in temporal_keywords):
            retrieval_mode = RetrievalMode.TEMPORAL.value
            intent_tags = []
            temporal_buckets = ["today", "this_week", "this_month"]

        elif any(k in query_lower for k in problem_keywords):
            retrieval_mode = RetrievalMode.SOURCE_AWARE.value
            intent_tags = ["problem", "question", "fix"]
            temporal_buckets = []

        elif any(k in query_lower for k in explanation_keywords):
            retrieval_mode = RetrievalMode.SOURCE_AWARE.value
            intent_tags = ["explanation", "reference"]
            temporal_buckets = []

        elif any(k in query_lower for k in opinion_keywords):
            retrieval_mode = RetrievalMode.SOURCE_AWARE.value
            intent_tags = ["opinion", "discussion", "community"]
            temporal_buckets = []

        else:
            retrieval_mode = RetrievalMode.HYBRID_RERANKED.value
            intent_tags = []
            temporal_buckets = []

        needs_graph = (
            retrieval_mode in [RetrievalMode.RESOLUTION_CHAIN.value, RetrievalMode.SOURCE_AWARE.value]
            and len(entities) > 1
        )

        return {
            "retrieval_needed": True,
            "retrieval_mode": retrieval_mode,
            "needs_graph_reasoning": needs_graph,
            "intent_tags": intent_tags,
            "temporal_buckets": temporal_buckets
        }
    
    async def _plan_next_step(self, state: AgentState) -> dict:
        """Plan the next execution step."""
        steps_completed = state["steps_completed"]
        
        # Bounded: max steps
        if steps_completed >= settings.MAX_AGENT_STEPS:
            return {"should_stop": True}
        
        return {
            "steps_completed": steps_completed + 1,
            "should_stop": False
        }
    
    async def _check_stop_or_continue(self, state: AgentState) -> dict:
        """Evaluate if we should stop, continue, or replan."""
        # Simple logic: stop after planned steps
        should_stop = state["steps_completed"] >= 2
        return {"should_stop": should_stop}
    
    async def _decide_replan(self, state: AgentState) -> dict:
        """Decide if replanning is needed (max 1 replan)."""
        replan_count = state["replan_count"]
        
        if replan_count >= settings.MAX_REPLANS:
            return {"should_stop": True}
        
        return {
            "replan_count": replan_count + 1,
            "steps_completed": 0  # Reset for new plan
        }
    
    # ============= Routing Functions =============
    
    def _route_after_retrieval(self, state: AgentState) -> str:
        """Route after retrieval decision."""
        return "plan_step" if state["retrieval_needed"] else "end"
    
    def _route_stop_or_continue(self, state: AgentState) -> str:
        """Route based on stop decision."""
        if state["should_stop"]:
            return "end"
        
        # Check if we should replan (placeholder logic)
        if state["steps_completed"] >= 3 and state["replan_count"] < settings.MAX_REPLANS:
            return "replan"
        
        return "continue" if not state["should_stop"] else "end"
    
    def _extract_steps_from_state(self, state: AgentState) -> list[str]:
        """Extract high-level step descriptions from final state."""
        steps = []

        if state["retrieval_needed"]:
            intent_info = f" intent={state.get('intent_tags')}" if state.get("intent_tags") else ""
            steps.append(f"Retrieve ({state['retrieval_mode']}){intent_info}")

        if state["needs_graph_reasoning"]:
            steps.append(f"Graph reasoning on: {state['entities']}")

        steps.append("Synthesize answer")

        return steps


# Global LangGraph planner instance
langgraph_planner = LangGraphPlanner()
