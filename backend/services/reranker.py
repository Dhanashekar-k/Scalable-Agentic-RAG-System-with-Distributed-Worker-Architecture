"""
Re-ranking service using cross-encoder for better relevance scoring.
Cross-encoders are more accurate than bi-encoders for relevance scoring.
"""
from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder


class Reranker:
    """
    Re-rank search results using a cross-encoder model.
    Cross-encoders jointly encode query and document for better accuracy.
    """
    
    def __init__(self):
        self.model = None
        self.model_name = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
    
    def load_model(self):
        """Load the cross-encoder model."""
        if self.model is None:
            print(f"Loading re-ranker model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            print("✅ Re-ranker model loaded")
    
    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """
        Re-rank documents using cross-encoder.
        
        Args:
            query: Search query
            documents: List of documents with content and metadata
            top_k: Number of top results to return
        
        Returns:
            Re-ranked documents with relevance scores
        """
        if not documents:
            return []
        
        # Ensure model is loaded
        if self.model is None:
            self.load_model()
        
        # Prepare query-document pairs
        pairs = []
        for doc in documents:
            content = doc.get('content', '')
            # Truncate long documents for efficiency
            if len(content) > 512:
                content = content[:512]
            pairs.append([query, content])
        
        # Get relevance scores
        try:
            scores = self.model.predict(pairs)
            
            # Combine documents with scores
            scored_docs = []
            for doc, score in zip(documents, scores):
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = float(score)
                scored_docs.append(doc_copy)
            
            # Sort by rerank score
            scored_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            return scored_docs[:top_k]
        
        except Exception as e:
            print(f"Re-ranking error: {e}")
            # Return original documents if re-ranking fails
            return documents[:top_k]
    
    def rerank_with_threshold(
        self,
        query: str,
        documents: List[Dict],
        threshold: float = 0.0,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Re-rank and filter by relevance threshold.
        
        Args:
            query: Search query
            documents: List of documents
            threshold: Minimum relevance score
            top_k: Maximum number of results
        
        Returns:
            Filtered and re-ranked documents
        """
        reranked = self.rerank(query, documents, top_k=len(documents))
        
        # Filter by threshold
        filtered = [doc for doc in reranked if doc['rerank_score'] >= threshold]
        
        return filtered[:top_k]


# Global reranker instance
reranker = Reranker()
