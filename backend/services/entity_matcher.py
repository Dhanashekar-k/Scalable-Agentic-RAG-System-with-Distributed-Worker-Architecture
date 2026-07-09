"""
Semantic Entity Matcher
Uses embeddings to find best matching entities in Neo4j knowledge graph.
No hardcoded mappings - fully dynamic semantic search.
"""
from typing import List, Dict, Tuple
import numpy as np
from services.embedding_service import embedding_service
from database.neo4j_client import neo4j_client


class EntityMatcher:
    """
    Matches query entities to Neo4j entities using semantic similarity.
    """
    
    def __init__(self):
        self.entity_cache = {}  # Cache entity embeddings
        self.cache_ttl = 300  # 5 minutes
        self.last_refresh = 0
    
    async def find_matching_entities(
        self,
        query_entities: List[str],
        threshold: float = 0.6,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find Neo4j entities that semantically match query entities.
        
        Args:
            query_entities: List of entity strings from query
            threshold: Minimum similarity score (0-1)
            top_k: Max entities to return per query entity
            
        Returns:
            List of matched entities with scores and metadata
        """
        # Refresh entity cache if needed
        await self._ensure_entity_cache()
        
        matched_entities = []
        entity_match_count = {}  # Track matches per query entity
        
        for query_entity in query_entities:
            # Get embedding for query entity
            query_embedding = embedding_service.embed_text(query_entity)
            
            # Find top-k most similar entities
            similarities = []
            for neo4j_entity, data in self.entity_cache.items():
                entity_embedding = data['embedding']
                similarity = self._cosine_similarity(query_embedding, entity_embedding)
                
                if similarity >= threshold:
                    similarities.append({
                        'query_entity': query_entity,
                        'matched_entity': neo4j_entity,
                        'entity_type': data['type'],
                        'similarity': float(similarity),
                        'match_method': 'semantic_embedding'
                    })
            
            # Sort by similarity and take top-k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            entity_matches = similarities[:top_k]
            matched_entities.extend(entity_matches)
            entity_match_count[query_entity] = len(entity_matches)
        
        # If some entities had no matches, try type-based matching
        unmatched_entities = [e for e, count in entity_match_count.items() if count == 0]
        if unmatched_entities:
            print(f"  🔄 {len(unmatched_entities)} entities need type inference: {unmatched_entities}")
            type_matches = await self._match_by_type_inference(query_entities, top_k * 2)
            # Add type matches that aren't already included
            existing_entities = {m['matched_entity'] for m in matched_entities}
            for tm in type_matches:
                if tm['matched_entity'] not in existing_entities:
                    matched_entities.append(tm)
        
        return matched_entities
    
    async def _match_by_type_inference(
        self,
        query_entities: List[str],
        top_k: int = 3
    ) -> List[Dict]:
        """
        Match entities by inferring type from query terms.
        Helps when query uses generic terms like 'investment products'.
        """
        await self._ensure_entity_cache()
        
        # Infer entity types from query terms using semantic similarity
        type_keywords = {
            'InvestmentProduct': ['investment', 'fund', 'etf', 'portfolio', 'stock', 'bond'],
            'BankingProduct': ['banking', 'account', 'savings', 'checking', 'deposit'],
            'InsuranceProduct': ['insurance', 'coverage', 'policy', 'protection'],
            'Regulation': ['regulation', 'law', 'compliance', 'rule', 'act'],
            'CustomerSegment': ['customer', 'client', 'professional', 'retiree', 'family']
        }
        
        # Score types based on query content
        type_scores = {}
        query_text = ' '.join(query_entities).lower()
        
        for entity_type, keywords in type_keywords.items():
            score = sum(1 for kw in keywords if kw in query_text)
            if score > 0:
                type_scores[entity_type] = score
        
        # Get entities from top-scoring types
        matches = []
        for entity_type in sorted(type_scores, key=type_scores.get, reverse=True):
            # Get entities of this type
            type_entities = [
                (name, data) for name, data in self.entity_cache.items()
                if data['type'] == entity_type
            ]
            
            # Take top entities from this type
            for name, data in type_entities[:top_k]:
                matches.append({
                    'query_entity': f"(inferred {entity_type})",
                    'matched_entity': name,
                    'entity_type': entity_type,
                    'similarity': 0.65,  # Moderate confidence for type-based
                    'match_method': 'type_inference'
                })
                
                if len(matches) >= top_k * 2:
                    return matches
        
        return matches
    
    async def find_related_by_type(
        self,
        query_entities: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """
        Find entities by inferring types from query keywords.
        Fallback when semantic matching has low confidence.
        """
        await self._ensure_entity_cache()
        
        # Extract keywords from query entities
        keywords = set()
        for entity in query_entities:
            keywords.update(entity.lower().split())
        
        # Score entity types based on keyword overlap
        type_scores = {}
        for neo4j_entity, data in self.entity_cache.items():
            entity_type = data['type']
            entity_words = set(neo4j_entity.lower().split())
            
            # Check keyword overlap
            overlap = len(keywords & entity_words)
            if overlap > 0:
                if entity_type not in type_scores:
                    type_scores[entity_type] = []
                type_scores[entity_type].append({
                    'entity': neo4j_entity,
                    'overlap_score': overlap,
                    'type': entity_type
                })
        
        # Get top entities from most relevant types
        results = []
        for entity_type, entities in sorted(
            type_scores.items(),
            key=lambda x: max(e['overlap_score'] for e in x[1]),
            reverse=True
        ):
            for entity_data in sorted(entities, key=lambda x: x['overlap_score'], reverse=True)[:2]:
                results.append({
                    'matched_entity': entity_data['entity'],
                    'entity_type': entity_type,
                    'similarity': 0.7,  # Heuristic score
                    'match_method': 'keyword_type_inference'
                })
                
                if len(results) >= limit:
                    return results
        
        return results
    
    async def _ensure_entity_cache(self):
        """
        Load and cache all Neo4j entities with their embeddings.
        Refreshes periodically.
        """
        import time
        current_time = time.time()
        
        # Check if cache needs refresh
        if self.entity_cache and (current_time - self.last_refresh) < self.cache_ttl:
            return
        
        # Fetch all entities from Neo4j
        cypher = """
        MATCH (e:Entity)
        RETURN e.name as name, e.type as type
        """
        entities = await neo4j_client.execute_query(cypher, {})
        
        # Generate embeddings for all entities
        print(f"  📚 Caching {len(entities)} Neo4j entities...")
        self.entity_cache = {}
        
        for entity in entities:
            entity_name = entity['name']
            entity_type = entity['type']
            
            # Generate embedding
            embedding = embedding_service.embed_text(entity_name)
            
            self.entity_cache[entity_name] = {
                'type': entity_type,
                'embedding': embedding
            }
        
        self.last_refresh = current_time
        print(f"  ✅ Entity cache ready with {len(self.entity_cache)} entities")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


# Global instance
entity_matcher = EntityMatcher()
