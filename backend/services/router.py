"""
Query Router - Decides which RAG pipeline to use.
Routes based on query complexity and user preferences.
"""
from groq import AsyncGroq
from models.schemas import QueryClassification
from config.settings import settings


class QueryRouter:
    """
    Routes queries to Normal RAG or Agentic RAG.
    Decision based on complexity analysis.
    """
    
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    async def route_query(
        self,
        query: str,
        force_agentic: bool = False
    ) -> str:
        """
        Decide which pipeline to use.
        Returns: 'normal_rag' or 'agentic_rag'
        """
        if force_agentic:
            return "agentic_rag"
        
        # Analyze query complexity
        complexity_score = await self._analyze_complexity(query)
        
        # Route based on threshold
        if complexity_score >= settings.COMPLEXITY_THRESHOLD:
            return "agentic_rag"
        else:
            return "normal_rag"
    
    async def _analyze_complexity(self, query: str) -> float:
        """
        Analyze query complexity using LLM.
        Returns score 0.0 to 1.0
        """
        prompt = f"""Analyze this query's complexity and return ONLY a number between 0.0 and 1.0.

Scoring guidelines:
0.0-0.3: Simple fact retrieval, single concept (e.g., "What is FDIC insurance?", "Define mortgage")
0.4-0.6: Multiple facts or basic comparisons (e.g., "What are interest rates?", "List savings accounts")
0.7-1.0: Complex multi-entity reasoning requiring multiple constraints, relationships, or cross-domain analysis (e.g., "Which products are regulated by X AND suitable for Y", "Compare A, B, C considering factors D and E")

Key complexity indicators:
- Multiple entities with AND/OR logic
- Multiple constraints or criteria
- Relationship analysis between entities
- Requires reasoning across categories
- Comparative analysis with multiple factors

Query: {query}

Return ONLY the number (e.g., 0.8):"""
        
        try:
            response = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            complexity_score = float(score_text)
            
            # Clamp to valid range
            return max(0.0, min(1.0, complexity_score))
        
        except Exception as e:
            # Fallback: use heuristics
            return self._heuristic_complexity(query)
    
    def _heuristic_complexity(self, query: str) -> float:
        """Fallback heuristic for complexity scoring."""
        query_lower = query.lower()
        
        # Complex indicators
        complex_words = [
            "analyze", "compare", "contrast", "relationship", "relationships",
            "contradiction", "evaluate", "synthesize", "multi-step",
            "suitable for", "regulated by", "considering", "across"
        ]
        
        # Simple indicators
        simple_words = ["what is", "who is", "define", "list"]
        
        complex_count = sum(1 for word in complex_words if word in query_lower)
        simple_count = sum(1 for word in simple_words if word in query_lower)
        
        # More factors
        has_multiple_entities = query.count(",") > 1 or query.count(" and ") > 1
        has_multi_criteria = ("which" in query_lower and " and " in query_lower)
        is_long = len(query.split()) > 15
        has_questions = query.count("?") > 1
        
        score = 0.5  # Base
        score += complex_count * 0.15
        score -= simple_count * 0.2
        score += 0.15 if has_multiple_entities else 0
        score += 0.2 if has_multi_criteria else 0  # Strong indicator
        score += 0.1 if is_long else 0
        score += 0.1 if has_questions else 0
        
        return max(0.0, min(1.0, score))


# Global router instance
query_router = QueryRouter()
