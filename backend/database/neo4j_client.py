"""
Neo4j client for graph-based reasoning and relationship queries.
Used ONLY when LangGraph decides graph reasoning is needed.
"""
from neo4j import AsyncGraphDatabase
from typing import List, Dict, Optional, Any
from config.settings import settings


class Neo4jClient:
    """Async Neo4j graph database client."""
    
    def __init__(self):
        self.driver = None
    
    async def connect(self):
        """Initialize Neo4j driver with optimized connection pool settings."""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            # Connection pool settings for high concurrency (50+ workers)
            max_connection_pool_size=100,
            connection_timeout=30,
            connection_acquisition_timeout=60
        )
    
    async def disconnect(self):
        """Close Neo4j driver."""
        if self.driver:
            await self.driver.close()
    
    async def execute_query(self, cypher: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a Cypher query within a transaction and return results.
        Ensures isolation and prevents race conditions.
        """
        parameters = parameters or {}
        async with self.driver.session() as session:
            # Execute within transaction for isolation
            async with await session.begin_transaction() as tx:
                try:
                    result = await tx.run(cypher, parameters)
                    records = await result.fetch(100)
                    await tx.commit()
                    return records
                except Exception as e:
                    await tx.rollback()
                    print(f"Neo4j transaction failed: {e}")
                    return []
    
    async def find_similar_entities(
        self,
        query_text: str,
        entity_type: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find entities similar to query text using fuzzy matching.
        Uses CONTAINS for partial matching and optional type filtering.
        """
        # Split query into keywords
        keywords = [w.lower().strip() for w in query_text.split() if len(w) > 3]
        
        if entity_type:
            # Type-specific search
            cypher = """
            MATCH (e:Entity)
            WHERE e.type = $entity_type
            AND ANY(keyword IN $keywords WHERE toLower(e.name) CONTAINS keyword)
            RETURN e.name as name, e.type as type
            LIMIT $limit
            """
            params = {"entity_type": entity_type, "keywords": keywords, "limit": limit}
        else:
            # Generic fuzzy search
            cypher = """
            MATCH (e:Entity)
            WHERE ANY(keyword IN $keywords WHERE toLower(e.name) CONTAINS keyword)
            RETURN e.name as name, e.type as type
            LIMIT $limit
            """
            params = {"keywords": keywords, "limit": limit}
        
        return await self.execute_query(cypher, params)
    
    async def find_entity_relationships(
        self,
        entity: str,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find relationships connected to an entity.
        Tries exact match first, then fuzzy matching.
        Used for multi-hop reasoning.
        """
        # Try exact match first
        cypher = f"""
        MATCH path = (start:Entity {{name: $entity}})-[*1..{max_depth}]-(connected)
        RETURN 
            start.name as source,
            [rel in relationships(path) | type(rel)] as relationships,
            connected.name as target,
            connected.type as target_type,
            length(path) as depth
        LIMIT 50
        """
        results = await self.execute_query(cypher, {"entity": entity})
        
        # If no exact match, try fuzzy matching
        if not results:
            similar_entities = await self.find_similar_entities(entity, limit=3)
            if similar_entities:
                # Use first matching entity
                matched_entity = similar_entities[0]['name']
                print(f"  📍 Fuzzy match: '{entity}' → '{matched_entity}'")
                results = await self.execute_query(
                    cypher.replace("$entity", "$matched_entity"),
                    {"matched_entity": matched_entity}
                )
        
        return results
    
    async def find_contradictions(
        self,
        entity1: str,
        entity2: str
    ) -> List[Dict]:
        """
        Check for contradictory relationships between entities.
        Used for reasoning validation.
        """
        cypher = """
        MATCH (e1:Entity {name: $entity1})-[r1]-(common)-[r2]-(e2:Entity {name: $entity2})
        WHERE type(r1) <> type(r2)
        RETURN 
            e1.name as entity1,
            type(r1) as rel1,
            common.name as common_entity,
            type(r2) as rel2,
            e2.name as entity2
        LIMIT 10
        """
        return await self.execute_query(
            cypher,
            {"entity1": entity1, "entity2": entity2}
        )
    
    async def add_entity(self, name: str, entity_type: str, properties: Dict = None):
        """Add or update an entity node."""
        properties = properties or {}
        properties_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        
        cypher = f"""
        MERGE (e:Entity {{name: $name}})
        SET e.type = $entity_type
        {f"SET e += {{{properties_str}}}" if properties else ""}
        RETURN e
        """
        params = {"name": name, "entity_type": entity_type, **properties}
        await self.execute_query(cypher, params)
    
    async def find_entities_by_type(
        self,
        entity_types: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all entities of specific types.
        Useful when entity names are too generic.
        """
        cypher = """
        MATCH (e:Entity)
        WHERE e.type IN $entity_types
        RETURN e.name as name, e.type as type
        LIMIT $limit
        """
        return await self.execute_query(
            cypher,
            {"entity_types": entity_types, "limit": limit}
        )
    
    async def add_relationship(
        self,
        source_name: str,
        target_name: str,
        relationship_type: str,
        properties: Dict = None
    ):
        """Create a relationship between entities."""
        properties = properties or {}
        cypher = f"""
        MATCH (e1:Entity {{name: $source_name}})
        MATCH (e2:Entity {{name: $target_name}})
        MERGE (e1)-[r:{relationship_type}]->(e2)
        SET r += $properties
        RETURN r
        """
        await self.execute_query(
            cypher,
            {"source_name": source_name, "target_name": target_name, "properties": properties}
        )
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the graph."""
        stats = {}
        
        # Get node count
        node_count_query = "MATCH (n:Entity) RETURN count(n) as count"
        node_result = await self.execute_query(node_count_query)
        stats['node_count'] = node_result[0]['count'] if node_result else 0
        
        # Get relationship count
        rel_count_query = "MATCH ()-[r]->() RETURN count(r) as count"
        rel_result = await self.execute_query(rel_count_query)
        stats['relationship_count'] = rel_result[0]['count'] if rel_result else 0
        
        # Get unique node types
        node_types_query = "MATCH (n:Entity) RETURN DISTINCT n.type as type"
        types_result = await self.execute_query(node_types_query)
        stats['node_labels'] = [r['type'] for r in types_result if r.get('type')]
        
        # Get unique relationship types
        rel_types_query = "MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type"
        rel_types_result = await self.execute_query(rel_types_query)
        stats['relationship_types'] = [r['rel_type'] for r in rel_types_result if r.get('rel_type')]
        
        return stats
    
    async def health_check(self) -> bool:
        """Check Neo4j connection health within a transaction."""
        try:
            async with self.driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run("RETURN 1 as health")
                    await result.single()
                    await tx.commit()
                    return True
        except Exception:
            return False
    
    # ============= Ingestion Methods =============
    
    async def create_ingested_entity(self, entity, ingestion_id: str):
        """
        Create or update an ingested entity node.
        MERGE (n:IngestedEntity {name: $name, ingestion_id: $ingestion_id})
        SET n.entity_type = $entity_type, n += $properties
        """
        cypher = """
        MERGE (n:IngestedEntity {name: $name, ingestion_id: $ingestion_id})
        SET n.entity_type = $entity_type
        SET n += $properties
        RETURN n
        """
        params = {
            "name": entity.name,
            "ingestion_id": ingestion_id,
            "entity_type": entity.entity_type,
            "properties": entity.properties
        }
        await self.execute_query(cypher, params)
    
    async def create_ingested_relationship(self, rel, ingestion_id: str):
        """
        Create relationship between ingested entities.
        MATCH (a:IngestedEntity {name: $from_name, ingestion_id: $ingestion_id})
        MATCH (b:IngestedEntity {name: $to_name, ingestion_id: $ingestion_id})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        """
        # Dynamic relationship type requires string formatting (safe here as we control the input)
        cypher = f"""
        MATCH (a:IngestedEntity {{name: $from_name, ingestion_id: $ingestion_id}})
        MATCH (b:IngestedEntity {{name: $to_name, ingestion_id: $ingestion_id}})
        MERGE (a)-[r:{rel.relationship_type}]->(b)
        SET r += $properties
        RETURN r
        """
        params = {
            "from_name": rel.from_entity,
            "to_name": rel.to_entity,
            "ingestion_id": ingestion_id,
            "properties": rel.properties
        }
        await self.execute_query(cypher, params)
    
    async def delete_ingested_entities(self, ingestion_id: str):
        """
        Delete all entities and relationships for an ingestion.
        MATCH (n:IngestedEntity {ingestion_id: $ingestion_id})
        DETACH DELETE n
        """
        cypher = """
        MATCH (n:IngestedEntity {ingestion_id: $ingestion_id})
        DETACH DELETE n
        """
        await self.execute_query(cypher, {"ingestion_id": ingestion_id})
    
    async def get_ingested_entities(self, ingestion_id: str) -> List[Dict]:
        """
        Get all entities for an ingestion.
        MATCH (n:IngestedEntity {ingestion_id: $ingestion_id})
        RETURN n
        """
        cypher = """
        MATCH (n:IngestedEntity {ingestion_id: $ingestion_id})
        RETURN n.name as name, n.entity_type as entity_type
        LIMIT 100
        """
        return await self.execute_query(cypher, {"ingestion_id": ingestion_id})


# Global Neo4j client instance
neo4j_client = Neo4jClient()
