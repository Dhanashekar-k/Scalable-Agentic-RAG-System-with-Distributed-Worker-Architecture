"""
Embedding service using sentence-transformers.
Shared across all system components for consistency.
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from config.settings import settings


class EmbeddingService:
    """Singleton embedding service for consistent embeddings."""
    
    def __init__(self):
        self.model = None
    
    def load_model(self):
        """Load the sentence transformer model."""
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self.model:
            self.load_model()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently."""
        if not self.model:
            self.load_model()
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Global embedding service instance
embedding_service = EmbeddingService()
