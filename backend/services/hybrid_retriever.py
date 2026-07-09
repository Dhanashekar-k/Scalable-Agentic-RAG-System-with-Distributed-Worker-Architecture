"""
Hybrid retrieval combining vector search, keyword search (BM25), and graph traversal.
Uses Reciprocal Rank Fusion (RRF) to combine results.
"""
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from collections import defaultdict
import numpy as np

from database.chroma_client import chroma_client
from database.neo4j_client import neo4j_client
from services.embedding_service import embedding_service
from config.settings import settings


class HybridRetriever:
    """
    Hybrid retrieval system combining multiple search methods.
    """
    
    def __init__(self):
        self.bm25_index = None
        self.bm25_documents = []
        self.bm25_metadata = []
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        workspace_id: Optional[str] = None,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Hybrid retrieval combining vector, keyword, and graph search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            workspace_id: Filter by workspace
            source_filter: Filter by ingestion_id
        
        Returns:
            List of documents with scores
        """
        # 1. Vector search (ChromaDB)
        vector_results = await self._vector_search(
            query, 
            top_k=top_k * 2,  # Get more for fusion
            workspace_id=workspace_id,
            source_filter=source_filter
        )
        
        # 2. Keyword search (BM25)
        keyword_results = await self._keyword_search(
            query,
            top_k=top_k * 2,
            workspace_id=workspace_id,
            source_filter=source_filter
        )
        
        # 3. Graph-based retrieval (Neo4j)
        graph_results = await self._graph_search(
            query,
            top_k=top_k,
            workspace_id=workspace_id
        )
        
        # 4. Combine using Reciprocal Rank Fusion
        combined_results = self._reciprocal_rank_fusion(
            [vector_results, keyword_results, graph_results],
            k=60  # RRF constant
        )
        
        # Return top_k results
        return combined_results[:top_k]
    
    async def _vector_search(
        self,
        query: str,
        top_k: int,
        workspace_id: Optional[str] = None,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """Vector similarity search using ChromaDB."""
        try:
            # Get collection
            collection = chroma_client.client.get_or_create_collection(
                name=settings.INGESTED_COLLECTION_NAME
            )
            
            # Build where filter
            where_filter = {}
            if workspace_id:
                where_filter["workspace_id"] = workspace_id
            if source_filter:
                where_filter["ingestion_id"] = source_filter
            
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None
            )
            
            # Format results
            documents = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'source': 'vector'
                    })
            
            return documents
        
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        workspace_id: Optional[str] = None,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """Keyword search using BM25."""
        try:
            # Get all documents from ChromaDB for BM25 indexing
            collection = chroma_client.client.get_or_create_collection(
                name=settings.INGESTED_COLLECTION_NAME
            )
            
            # Build where filter
            where_filter = {}
            if workspace_id:
                where_filter["workspace_id"] = workspace_id
            if source_filter:
                where_filter["ingestion_id"] = source_filter
            
            # Get documents
            results = collection.get(
                where=where_filter if where_filter else None,
                limit=1000  # Limit for performance
            )
            
            if not results or not results['documents']:
                return []
            
            # Tokenize documents for BM25
            tokenized_docs = [doc.lower().split() for doc in results['documents']]
            
            # Create BM25 index
            bm25 = BM25Okapi(tokenized_docs)
            
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = bm25.get_scores(tokenized_query)
            
            # Get top_k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Format results
            documents = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include if score > 0
                    documents.append({
                        'content': results['documents'][idx],
                        'metadata': results['metadatas'][idx] if results['metadatas'] else {},
                        'score': float(scores[idx]),
                        'source': 'keyword'
                    })
            
            return documents
        
        except Exception as e:
            print(f"Keyword search error: {e}")
            return []
    
    async def _graph_search(
        self,
        query: str,
        top_k: int,
        workspace_id: Optional[str] = None
    ) -> List[Dict]:
        """Graph-based retrieval using Neo4j."""
        try:
            # Extract potential entities from query
            query_terms = query.lower().split()
            
            # Search for related entities in graph
            cypher = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS $term
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, collect(DISTINCT m.name) as related_entities
            LIMIT $limit
            """
            
            all_entities = []
            for term in query_terms:
                if len(term) > 3:  # Skip short words
                    results = await neo4j_client.execute_query(
                        cypher,
                        {"term": term, "limit": 5}
                    )
                    all_entities.extend(results)
            
            # Format as documents
            documents = []
            for record in all_entities[:top_k]:
                if record.get('n'):
                    node = record['n']
                    related = record.get('related_entities', [])
                    
                    content = f"Entity: {node.get('name', 'Unknown')}"
                    if related:
                        content += f"\nRelated to: {', '.join(related[:5])}"
                    
                    documents.append({
                        'content': content,
                        'metadata': {
                            'entity_name': node.get('name'),
                            'entity_type': node.get('entity_type'),
                            'source': 'graph'
                        },
                        'score': 0.5,  # Fixed score for graph results
                        'source': 'graph'
                    })
            
            return documents
        
        except Exception as e:
            print(f"Graph search error: {e}")
            return []
    
    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Dict]],
        k: int = 60
    ) -> List[Dict]:
        """
        Combine multiple ranked lists using Reciprocal Rank Fusion.
        
        RRF formula: score(d) = sum(1 / (k + rank(d)))
        
        Args:
            result_lists: List of ranked result lists
            k: RRF constant (default 60)
        
        Returns:
            Combined and re-ranked results
        """
        # Track scores for each unique document
        doc_scores = defaultdict(float)
        doc_data = {}
        
        # Process each result list
        for results in result_lists:
            for rank, doc in enumerate(results, start=1):
                # Use content as unique identifier
                doc_id = doc['content'][:100]  # First 100 chars as ID
                
                # Add RRF score
                doc_scores[doc_id] += 1.0 / (k + rank)
                
                # Store document data (keep first occurrence)
                if doc_id not in doc_data:
                    doc_data[doc_id] = doc
        
        # Sort by combined score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return documents with combined scores
        combined_results = []
        for doc_id, score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc['combined_score'] = score
            combined_results.append(doc)
        
        return combined_results


# Global hybrid retriever instance
hybrid_retriever = HybridRetriever()
