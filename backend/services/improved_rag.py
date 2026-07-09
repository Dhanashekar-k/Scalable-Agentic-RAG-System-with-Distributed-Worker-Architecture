"""
Improved RAG Pipeline with Hybrid Search and Re-ranking.
Combines vector search, keyword search (BM25), and graph traversal.
Uses cross-encoder re-ranking for better relevance.
"""
import time
from typing import List, Optional
from groq import AsyncGroq

from services.hybrid_retriever import hybrid_retriever
from services.reranker import reranker
from config.settings import settings


class ImprovedRAG:
    """
    Enhanced RAG pipeline with:
    1. Hybrid retrieval (vector + keyword + graph)
    2. Cross-encoder re-ranking
    3. Better answer generation
    """
    
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    async def process_query(
        self,
        query: str,
        request_id: str,
        workspace_id: Optional[str] = None,
        source_filter: Optional[str] = None,
        use_reranking: bool = True
    ) -> dict:
        """
        Execute improved RAG pipeline with hybrid search and re-ranking.
        
        Args:
            query: User query
            request_id: Unique request ID
            workspace_id: Filter by workspace
            source_filter: Filter by ingestion_id
            use_reranking: Whether to use cross-encoder re-ranking
        
        Returns:
            Answer with metadata
        """
        start_time = time.time()
        
        # Step 1: Hybrid retrieval (vector + keyword + graph)
        retrieval_start = time.time()
        documents = await hybrid_retriever.retrieve(
            query=query,
            top_k=20,  # Get more for re-ranking
            workspace_id=workspace_id,
            source_filter=source_filter
        )
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        if not documents:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "confidence": 0.0,
                "sources": [],
                "metadata": {
                    "num_documents": 0,
                    "retrieval_mode": "hybrid",
                    "reranked": False,
                    "retrieval_time_ms": retrieval_time
                },
                "processing_time_ms": (time.time() - start_time) * 1000
            }
        
        # Step 2: Re-rank using cross-encoder
        rerank_start = time.time()
        if use_reranking:
            documents = reranker.rerank(
                query=query,
                documents=documents,
                top_k=settings.RETRIEVAL_TOP_K
            )
        else:
            documents = documents[:settings.RETRIEVAL_TOP_K]
        rerank_time = (time.time() - rerank_start) * 1000
        
        # Step 3: Generate answer
        generation_start = time.time()
        answer = await self._generate_answer(query, documents)
        generation_time = (time.time() - generation_start) * 1000
        
        # Calculate confidence based on re-rank scores
        confidence = self._calculate_confidence(documents)
        
        # Format sources
        sources = self._format_sources(documents)
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "metadata": {
                "num_documents": len(documents),
                "retrieval_mode": "hybrid",
                "reranked": use_reranking,
                "model": settings.GROQ_MODEL,
                "workspace_id": workspace_id,
                "source_filter": source_filter,
                "timing": {
                    "retrieval_ms": retrieval_time,
                    "reranking_ms": rerank_time if use_reranking else 0,
                    "generation_ms": generation_time,
                    "total_ms": processing_time
                }
            },
            "processing_time_ms": processing_time
        }
    
    async def _generate_answer(self, query: str, documents: List[dict]) -> str:
        """Generate answer using LLM with retrieved context."""
        # Build context from documents
        context_parts = []
        for i, doc in enumerate(documents[:5], 1):  # Use top 5 for context
            content = doc['content']
            # Truncate if too long
            if len(content) > 500:
                content = content[:500] + "..."
            
            source_info = ""
            if 'source_url' in doc.get('metadata', {}):
                source_info = f" (Source: {doc['metadata']['source_url']})"
            
            context_parts.append(f"[{i}] {content}{source_info}")
        
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context.

Context:
{context}

Question: {query}

Instructions:
1. Answer based primarily on the provided context
2. If the context doesn't contain enough information, say so
3. Cite sources using [1], [2], etc. when referencing specific information
4. Be concise but comprehensive
5. If multiple sources provide different information, acknowledge this

Answer:"""
        
        # Generate response
        try:
            response = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides accurate, well-cited answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM generation error: {e}")
            return "I encountered an error generating the answer. Please try again."
    
    def _calculate_confidence(self, documents: List[dict]) -> float:
        """Calculate confidence score based on document relevance."""
        if not documents:
            return 0.0
        
        # Use rerank scores if available, otherwise use retrieval scores
        scores = []
        for doc in documents:
            if 'rerank_score' in doc:
                scores.append(doc['rerank_score'])
            elif 'combined_score' in doc:
                scores.append(doc['combined_score'])
            elif 'score' in doc:
                scores.append(doc['score'])
        
        if not scores:
            return 0.5
        
        # Average of top 3 scores, normalized
        top_scores = sorted(scores, reverse=True)[:3]
        avg_score = sum(top_scores) / len(top_scores)
        
        # Normalize to 0-1 range
        # Rerank scores are typically -10 to 10, normalize to 0-1
        if 'rerank_score' in documents[0]:
            confidence = (avg_score + 10) / 20
        else:
            confidence = min(avg_score, 1.0)
        
        return max(0.0, min(1.0, confidence))
    
    def _format_sources(self, documents: List[dict]) -> List[dict]:
        """Format documents as sources for response."""
        sources = []
        for doc in documents:
            source = {
                "content": doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                "score": doc.get('rerank_score') or doc.get('combined_score') or doc.get('score', 0.0),
                "source_type": doc.get('source', 'unknown')
            }
            
            # Add metadata
            if 'metadata' in doc:
                source.update(doc['metadata'])
            
            sources.append(source)
        
        return sources


# Global improved RAG instance
improved_rag = ImprovedRAG()
