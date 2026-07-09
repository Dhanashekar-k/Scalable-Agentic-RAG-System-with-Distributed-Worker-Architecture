"""
ChromaDB client for vector similarity search.
Shared by both Normal RAG and Agentic RAG pipelines.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from config.settings import settings


class ChromaDBClient:
    """ChromaDB vector store client."""
    
    def __init__(self):
        self.client: Optional[chromadb.Client] = None
        self.collection = None
    
    def connect(self):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """Add documents to vector store (for data ingestion)."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = None
    ) -> Dict:
        """
        Query vector store with embeddings.
        Returns documents, distances, and metadatas.
        """
        n_results = n_results or settings.RETRIEVAL_TOP_K
        
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )
        return results
    
    def get_collection(self):
        """Get the current collection."""
        return self.collection
    
    def health_check(self) -> bool:
        """Check ChromaDB health."""
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False


# Global ChromaDB client instance
chroma_client = ChromaDBClient()
