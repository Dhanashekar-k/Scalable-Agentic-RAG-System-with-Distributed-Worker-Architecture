"""
Knowledge Graph Router
Provides endpoints for graph visualization — both financial domain
(:Entity nodes) and ingested sources (:IngestedEntity nodes).
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, List, Any

from database.neo4j_client import neo4j_client
from models.ingestion_schemas import GraphNode, GraphEdge, GraphResponse, GraphStatsResponse

router = APIRouter(prefix="/graph", tags=["graph"])


# ─────────────────────────────────────────────────────────────
# GET /graph/source/{ingestion_id}
# Returns all nodes + edges for a specific ingested source.
# ─────────────────────────────────────────────────────────────
@router.get("/source/{ingestion_id}", response_model=GraphResponse)
async def get_source_graph(ingestion_id: str):
    """
    Returns all IngestedEntity nodes and relationships for a specific ingestion.
    Used by IngestionPage mini-graph and KnowledgeGraphTab source selector.
    """
    cypher = """
    MATCH (n:IngestedEntity {ingestion_id: $ingestion_id})
    OPTIONAL MATCH (n)-[r]-(m:IngestedEntity {ingestion_id: $ingestion_id})
    RETURN n, r, m
    LIMIT 500
    """
    try:
        records = await neo4j_client.execute_query(cypher, {"ingestion_id": ingestion_id})
        return _build_graph_response(records, ingestion_id)
    except Exception as e:
        # Return empty graph rather than 500 if Neo4j has no data
        return GraphResponse(nodes=[], edges=[], stats={
            "node_count": 0, "edge_count": 0,
            "entity_type_distribution": {}, "relationship_type_distribution": {},
            "error": str(e)
        })


# ─────────────────────────────────────────────────────────────
# GET /graph/financial
# Returns the original financial knowledge graph (:Entity nodes).
# ─────────────────────────────────────────────────────────────
@router.get("/financial", response_model=GraphResponse)
async def get_financial_graph():
    """
    Returns the built-in financial domain knowledge graph (:Entity nodes).
    Falls back to all IngestedEntity nodes if no financial data exists.
    """
    # Try financial :Entity nodes first
    cypher_financial = """
    MATCH (n:Entity)
    OPTIONAL MATCH (n)-[r]-(m:Entity)
    RETURN n, r, m
    """
    try:
        records = await neo4j_client.execute_query(cypher_financial, {})
        if records:
            return _build_graph_response(records, ingestion_id="financial")
    except Exception:
        pass

    # Fallback: show all IngestedEntity nodes (overview of everything ingested)
    cypher_all = """
    MATCH (n:IngestedEntity)
    OPTIONAL MATCH (n)-[r]-(m:IngestedEntity)
    RETURN n, r, m
    LIMIT 500
    """
    try:
        records = await neo4j_client.execute_query(cypher_all, {})
        return _build_graph_response(records, ingestion_id="all")
    except Exception as e:
        return GraphResponse(nodes=[], edges=[], stats={
            "node_count": 0, "edge_count": 0,
            "entity_type_distribution": {}, "relationship_type_distribution": {},
            "error": str(e)
        })


# ─────────────────────────────────────────────────────────────
# GET /graph/entity/{entity_name}
# Returns a specific entity and its neighborhood up to `depth` hops.
# Called when user double-clicks a node to expand it.
# ─────────────────────────────────────────────────────────────
@router.get("/entity/{entity_name}", response_model=GraphResponse)
async def get_entity_neighborhood(
    entity_name: str,
    depth: int = Query(default=2, ge=1, le=4),
    ingestion_id: Optional[str] = Query(default=None)
):
    """
    Returns the neighborhood of a specific entity up to `depth` hops.
    Works for both :Entity (financial) and :IngestedEntity nodes.
    """
    try:
        if ingestion_id and ingestion_id != "financial":
            cypher = f"""
            MATCH path = (start:IngestedEntity {{name: $name, ingestion_id: $ing_id}})
                         -[*1..{depth}]-
                         (connected:IngestedEntity {{ingestion_id: $ing_id}})
            RETURN nodes(path) as nodes, relationships(path) as rels
            LIMIT 100
            """
            records = await neo4j_client.execute_query(
                cypher, {"name": entity_name, "ing_id": ingestion_id}
            )
        else:
            cypher = f"""
            MATCH path = (start:Entity {{name: $name}})
                         -[*1..{depth}]-
                         (connected:Entity)
            RETURN nodes(path) as nodes, relationships(path) as rels
            LIMIT 100
            """
            records = await neo4j_client.execute_query(cypher, {"name": entity_name})

        return _build_graph_response_from_paths(records)
    except Exception as e:
        return GraphResponse(nodes=[], edges=[], stats={
            "node_count": 0, "edge_count": 0,
            "entity_type_distribution": {}, "relationship_type_distribution": {},
            "error": str(e)
        })


# ─────────────────────────────────────────────────────────────
# GET /graph/path
# Finds shortest path between two entities.
# ─────────────────────────────────────────────────────────────
@router.get("/path", response_model=GraphResponse)
async def get_path_between_entities(
    from_entity: str = Query(...),
    to_entity: str = Query(...),
    ingestion_id: Optional[str] = Query(default=None)
):
    """
    Finds the shortest path between two entities in the graph.
    Used by the "Find Connection" feature in KnowledgeGraphTab.
    """
    try:
        if ingestion_id and ingestion_id != "financial":
            cypher = """
            MATCH path = shortestPath(
                (a:IngestedEntity {name: $from_name, ingestion_id: $ing_id})
                -[*]-
                (b:IngestedEntity {name: $to_name, ingestion_id: $ing_id})
            )
            RETURN nodes(path) as nodes, relationships(path) as rels
            """
            records = await neo4j_client.execute_query(
                cypher, {"from_name": from_entity, "to_name": to_entity, "ing_id": ingestion_id}
            )
        else:
            cypher = """
            MATCH path = shortestPath(
                (a:Entity {name: $from_name})-[*]-(b:Entity {name: $to_name})
            )
            RETURN nodes(path) as nodes, relationships(path) as rels
            """
            records = await neo4j_client.execute_query(
                cypher, {"from_name": from_entity, "to_name": to_entity}
            )

        return _build_graph_response_from_paths(records)
    except Exception as e:
        return GraphResponse(nodes=[], edges=[], stats={
            "node_count": 0, "edge_count": 0,
            "entity_type_distribution": {}, "relationship_type_distribution": {},
            "error": str(e)
        })


# ─────────────────────────────────────────────────────────────
# GET /graph/stats/{ingestion_id}
# Richer stats per source — used by stats sidebar in graph tab.
# ─────────────────────────────────────────────────────────────
@router.get("/stats/{ingestion_id}", response_model=GraphStatsResponse)
async def get_graph_stats_for_source(ingestion_id: str):
    """
    Returns detailed stats for a specific graph source.
    Works for "financial" (built-in) or any ingestion_id.
    """
    try:
        if ingestion_id == "financial":
            # Try :Entity nodes first, fall back to all IngestedEntity
            test = await neo4j_client.execute_query("MATCH (n:Entity) RETURN count(n) as cnt", {})
            has_financial = test and int(test[0].get("cnt", 0)) > 0

            if has_financial:
                node_records = await neo4j_client.execute_query(
                    "MATCH (n:Entity) RETURN n.type as type, count(*) as count", {}
                )
                rel_records = await neo4j_client.execute_query(
                    "MATCH ()-[r]-() WHERE startNode(r):Entity RETURN type(r) as rel, count(*) as cnt", {}
                )
                connected_records = await neo4j_client.execute_query(
                    """
                    MATCH (n:Entity)-[r]-()
                    WITH n, count(r) as connections
                    ORDER BY connections DESC LIMIT 5
                    RETURN n.name as name, connections
                    """, {}
                )
            else:
                # Fallback to all ingested
                node_records = await neo4j_client.execute_query(
                    "MATCH (n:IngestedEntity) RETURN n.entity_type as type, count(*) as count", {}
                )
                rel_records = await neo4j_client.execute_query(
                    "MATCH (n:IngestedEntity)-[r]-() RETURN type(r) as rel, count(*) as cnt", {}
                )
                connected_records = await neo4j_client.execute_query(
                    """
                    MATCH (n:IngestedEntity)-[r]-()
                    WITH n, count(r) as connections
                    ORDER BY connections DESC LIMIT 5
                    RETURN n.name as name, connections
                    """, {}
                )
        else:
            node_records = await neo4j_client.execute_query(
                """
                MATCH (n:IngestedEntity {ingestion_id: $ing_id})
                RETURN n.entity_type as type, count(*) as count
                """,
                {"ing_id": ingestion_id}
            )
            rel_records = await neo4j_client.execute_query(
                """
                MATCH (n:IngestedEntity {ingestion_id: $ing_id})-[r]-()
                RETURN type(r) as rel, count(*) as cnt
                """,
                {"ing_id": ingestion_id}
            )
            connected_records = await neo4j_client.execute_query(
                """
                MATCH (n:IngestedEntity {ingestion_id: $ing_id})-[r]-()
                WITH n, count(r) as connections
                ORDER BY connections DESC LIMIT 5
                RETURN n.name as name, connections
                """,
                {"ing_id": ingestion_id}
            )

        # Build distributions
        entity_dist: Dict[str, int] = {}
        for rec in node_records:
            t = rec.get("type") or "unknown"
            entity_dist[str(t)] = int(rec.get("count", 0))

        rel_dist: Dict[str, int] = {}
        total_rels = 0
        for rec in rel_records:
            r = rec.get("rel") or "unknown"
            cnt = int(rec.get("cnt", 0))
            rel_dist[str(r)] = cnt
            total_rels += cnt

        most_connected = []
        for rec in connected_records:
            most_connected.append({
                "name": rec.get("name", ""),
                "connections": int(rec.get("connections", 0))
            })

        total_nodes = sum(entity_dist.values())

        return GraphStatsResponse(
            node_count=total_nodes,
            edge_count=total_rels // 2,  # undirected count
            most_connected=most_connected,
            entity_type_distribution=entity_dist,
            relationship_type_distribution=rel_dist,
            ingestion_id=ingestion_id
        )

    except Exception as e:
        return GraphStatsResponse(
            node_count=0,
            edge_count=0,
            most_connected=[],
            entity_type_distribution={},
            relationship_type_distribution={},
            ingestion_id=ingestion_id
        )


# ─────────────────────────────────────────────────────────────
# Helper: build GraphResponse from MATCH (n)-[r]-(m) records
# ─────────────────────────────────────────────────────────────
def _build_graph_response(records: List[Any], ingestion_id: str = None) -> GraphResponse:
    """
    Converts raw Neo4j records (n, r, m format) into GraphResponse.
    Deduplicates nodes and edges, computes connection_count per node.
    """
    nodes_dict: Dict[str, GraphNode] = {}
    edges_dict: Dict[str, GraphEdge] = {}
    connection_counts: Dict[str, int] = {}

    for record in records:
        n = record.get("n")
        r = record.get("r")
        m = record.get("m")

        if n is None:
            continue

        # Process source node
        n_id = _node_id(n, ingestion_id)
        if n_id not in nodes_dict:
            nodes_dict[n_id] = _make_node(n, n_id)
            connection_counts[n_id] = 0

        # Process relationship + target node
        if r is not None and m is not None:
            m_id = _node_id(m, ingestion_id)
            if m_id not in nodes_dict:
                nodes_dict[m_id] = _make_node(m, m_id)
                connection_counts[m_id] = 0

            # Build edge (deduplicate by sorted pair + type)
            rel_type = r.type if hasattr(r, "type") else str(r.get("type", "RELATED"))
            edge_key = f"{min(n_id, m_id)}_{max(n_id, m_id)}_{rel_type}"
            if edge_key not in edges_dict:
                edges_dict[edge_key] = GraphEdge(
                    id=edge_key,
                    source=n_id,
                    target=m_id,
                    relationship=rel_type,
                    properties=dict(r) if hasattr(r, "items") else {}
                )
                connection_counts[n_id] = connection_counts.get(n_id, 0) + 1
                connection_counts[m_id] = connection_counts.get(m_id, 0) + 1

    # Apply connection counts
    for node_id, node in nodes_dict.items():
        node.connection_count = connection_counts.get(node_id, 0)

    # Limit to 200 nodes / 300 edges — keep highest-connected
    nodes_list = sorted(nodes_dict.values(), key=lambda n: n.connection_count, reverse=True)[:200]
    kept_ids = {n.id for n in nodes_list}
    edges_list = [e for e in edges_dict.values() if e.source in kept_ids and e.target in kept_ids][:300]

    # Stats
    entity_type_dist: Dict[str, int] = {}
    for node in nodes_list:
        entity_type_dist[node.entity_type] = entity_type_dist.get(node.entity_type, 0) + 1

    rel_type_dist: Dict[str, int] = {}
    for edge in edges_list:
        rel_type_dist[edge.relationship] = rel_type_dist.get(edge.relationship, 0) + 1

    return GraphResponse(
        nodes=nodes_list,
        edges=edges_list,
        stats={
            "node_count": len(nodes_list),
            "edge_count": len(edges_list),
            "entity_type_distribution": entity_type_dist,
            "relationship_type_distribution": rel_type_dist
        }
    )


def _build_graph_response_from_paths(records: List[Any]) -> GraphResponse:
    """
    Converts path query results (nodes(path), relationships(path) format)
    into GraphResponse.
    """
    nodes_dict: Dict[str, GraphNode] = {}
    edges_dict: Dict[str, GraphEdge] = {}
    connection_counts: Dict[str, int] = {}

    for record in records:
        path_nodes = record.get("nodes", [])
        path_rels = record.get("rels", [])

        for node in (path_nodes or []):
            if node is None:
                continue
            n_id = _node_id(node, None)
            if n_id not in nodes_dict:
                nodes_dict[n_id] = _make_node(node, n_id)
                connection_counts[n_id] = 0

        for rel in (path_rels or []):
            if rel is None:
                continue
            rel_type = rel.type if hasattr(rel, "type") else str(rel.get("type", "RELATED"))
            # Get start/end node ids from relationship
            try:
                src_id = str(rel.start_node.get("name", rel.start_node.id))
                tgt_id = str(rel.end_node.get("name", rel.end_node.id))
            except Exception:
                continue

            edge_key = f"{min(src_id, tgt_id)}_{max(src_id, tgt_id)}_{rel_type}"
            if edge_key not in edges_dict:
                edges_dict[edge_key] = GraphEdge(
                    id=edge_key,
                    source=src_id,
                    target=tgt_id,
                    relationship=rel_type,
                    properties={}
                )
                connection_counts[src_id] = connection_counts.get(src_id, 0) + 1
                connection_counts[tgt_id] = connection_counts.get(tgt_id, 0) + 1

    for node_id, node in nodes_dict.items():
        node.connection_count = connection_counts.get(node_id, 0)

    nodes_list = list(nodes_dict.values())
    edges_list = list(edges_dict.values())

    entity_type_dist: Dict[str, int] = {}
    for node in nodes_list:
        entity_type_dist[node.entity_type] = entity_type_dist.get(node.entity_type, 0) + 1

    rel_type_dist: Dict[str, int] = {}
    for edge in edges_list:
        rel_type_dist[edge.relationship] = rel_type_dist.get(edge.relationship, 0) + 1

    return GraphResponse(
        nodes=nodes_list,
        edges=edges_list,
        stats={
            "node_count": len(nodes_list),
            "edge_count": len(edges_list),
            "entity_type_distribution": entity_type_dist,
            "relationship_type_distribution": rel_type_dist
        }
    )


def _node_id(node: Any, ingestion_id: str = None) -> str:
    """Generate a stable unique ID for a node."""
    try:
        name = node.get("name") or node.get("id") or str(node.id)
    except Exception:
        name = str(node)
    if ingestion_id and ingestion_id != "financial":
        return f"{name}::{ingestion_id}"
    return str(name)


def _make_node(node: Any, node_id: str) -> GraphNode:
    """Convert a Neo4j node object into a GraphNode."""
    try:
        props = dict(node)
    except Exception:
        props = {}

    # Determine entity_type — check multiple possible property names
    entity_type = (
        props.get("entity_type") or
        props.get("type") or
        props.get("label") or
        # For financial :Entity nodes, infer from labels
        _infer_entity_type(props)
    )

    return GraphNode(
        id=node_id,
        label=props.get("name", node_id.split("::")[0]),
        entity_type=str(entity_type) if entity_type else "unknown",
        source_url=props.get("source_url"),
        source_id=props.get("source_id"),
        ingestion_id=props.get("ingestion_id"),
        properties=props,
        connection_count=0
    )


def _infer_entity_type(props: Dict) -> str:
    """Infer entity type from properties for financial :Entity nodes."""
    name = props.get("name", "").lower()
    # Financial domain heuristics
    financial_products = ["account", "fund", "bond", "stock", "etf", "loan", "card", "annuity", "ira", "401"]
    regulations = ["fdic", "sec", "finra", "cfpb", "occ", "fed", "regulation", "act", "rule"]
    institutions = ["bank", "reserve", "federal", "treasury", "exchange"]
    concepts = ["risk", "return", "liquidity", "diversification", "inflation", "yield", "portfolio"]
    segments = ["investor", "retiree", "customer", "client", "saver"]

    for kw in financial_products:
        if kw in name:
            return "Product"
    for kw in regulations:
        if kw in name:
            return "Regulation"
    for kw in institutions:
        if kw in name:
            return "Institution"
    for kw in concepts:
        if kw in name:
            return "Concept"
    for kw in segments:
        if kw in name:
            return "CustomerSegment"
    return "Entity"
