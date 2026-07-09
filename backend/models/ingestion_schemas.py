"""
Pydantic models for ingestion system.
Handles URL ingestion, PDF uploads, and digest generation.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class IngestionDocument(BaseModel):
    """Single document extracted from an ingestion source."""
    content: str
    metadata: Dict[str, Any]
    # metadata always contains:
    # source_type, source_url, source_id, author, created_at, title (existing)
    # intent_tags: str          (NEW - pipe-separated, e.g. "decision|fix")
    # source_category: str      (NEW - "code"|"documentation"|"discussion"|"community"|"media"|"feed")
    # content_quality: float    (NEW - 0.0 to 1.0)
    # temporal_bucket: str      (NEW - "today"|"this_week"|"this_month"|"this_year"|"older"|"unknown")
    # entities_mentioned: str   (NEW - pipe-separated key terms for BM25)
    # ingestion_id: str         (added by pipeline._store_in_chromadb, not ingester)


class GraphEntity(BaseModel):
    """Entity node for Neo4j graph."""
    name: str
    entity_type: str  # "repo", "author", "label", "package", "issue", "pr"
    properties: Dict[str, Any]


class GraphRelationship(BaseModel):
    """Relationship edge for Neo4j graph."""
    from_entity: str
    to_entity: str
    relationship_type: str  # "RESOLVES", "TAGGED", "CREATED", "CHANGES", "MENTIONS"
    properties: Dict[str, Any] = {}


class GraphData(BaseModel):
    """Complete graph structure extracted from ingestion."""
    entities: List[GraphEntity]
    relationships: List[GraphRelationship]


class IngestionResult(BaseModel):
    """Result of ingestion operation."""
    documents: List[IngestionDocument]
    graph_data: GraphData
    source_name: str
    source_type: str


class IngestURLRequest(BaseModel):
    """Request to ingest a URL."""
    url: str
    recursive: bool = False  # for webpage crawling


class IngestStatusResponse(BaseModel):
    """Status of an ingestion operation."""
    ingestion_id: str
    status: str  # "running", "complete", "failed"
    source_url: str
    source_type: str
    source_name: str
    total_docs: int
    processed_docs: int
    entity_count: int
    created_at: str
    message: Optional[str] = None


class DigestRequest(BaseModel):
    """Request to generate a digest."""
    ingestion_id: str
    days_back: int = 7


class DigestSection(BaseModel):
    """Section of a digest (e.g., Issues, PRs, Commits)."""
    type: str
    count: int
    summary: str


class DigestResponse(BaseModel):
    """Generated digest of an ingested source."""
    source_name: str
    period: str
    sections: List[DigestSection]
    stats: Dict[str, Any]
    generated_at: str


class IngestionListResponse(BaseModel):
    """List of all ingestions."""
    ingestions: List[IngestStatusResponse]
    total: int


class RetrievalFilter(BaseModel):
    """Passed from planner to worker to filter ChromaDB search."""
    ingestion_id: Optional[str] = None           # filter to specific ingested source
    intent_tags: Optional[List[str]] = None      # filter by intent
    source_categories: Optional[List[str]] = None  # filter by category
    temporal_buckets: Optional[List[str]] = None   # filter by time
    min_content_quality: float = 0.3             # skip low-quality chunks


# ============= Knowledge Graph Visualization Models =============

class GraphNode(BaseModel):
    """A node in the knowledge graph visualization."""
    id: str                          # unique id for frontend (name + ingestion_id)
    label: str                       # display name
    entity_type: str                 # "repo"|"author"|"label"|"issue"|"pr"|"file"
                                     # OR financial: "Product"|"Regulation"|"Concept"|"CustomerSegment"|"Institution"
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    ingestion_id: Optional[str] = None
    properties: Dict[str, Any] = {}
    connection_count: int = 0        # number of edges — used for node sizing


class GraphEdge(BaseModel):
    """An edge in the knowledge graph visualization."""
    id: str                          # unique edge id
    source: str                      # node id (from)
    target: str                      # node id (to)
    relationship: str                # relationship type string
    properties: Dict[str, Any] = {}


class GraphResponse(BaseModel):
    """Full graph response for visualization."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, Any]            # node_count, edge_count, entity_type_distribution, relationship_type_distribution


class GraphStatsResponse(BaseModel):
    """Richer stats for a specific graph source."""
    node_count: int
    edge_count: int
    most_connected: List[Dict[str, Any]]   # [{name, connections}] top 5
    entity_type_distribution: Dict[str, int]
    relationship_type_distribution: Dict[str, int]
    ingestion_id: Optional[str] = None
    source_name: Optional[str] = None
