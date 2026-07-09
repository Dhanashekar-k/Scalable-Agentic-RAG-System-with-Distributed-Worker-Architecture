"""
Workspace management schemas.
Allows users to organize ingestions into workspaces/projects.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class WorkspaceCreate(BaseModel):
    """Request to create a new workspace."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WorkspaceUpdate(BaseModel):
    """Request to update workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class Workspace(BaseModel):
    """Workspace model."""
    workspace_id: str
    name: str
    description: Optional[str] = None
    ingestion_count: int = 0
    created_at: str
    updated_at: str


class WorkspaceList(BaseModel):
    """List of workspaces."""
    workspaces: List[Workspace]
    total: int


class WorkspaceDetail(BaseModel):
    """Detailed workspace with ingestions."""
    workspace_id: str
    name: str
    description: Optional[str] = None
    ingestion_count: int
    created_at: str
    updated_at: str
    ingestions: List[dict]  # List of ingestion summaries


class AddIngestionToWorkspace(BaseModel):
    """Request to add ingestion to workspace."""
    ingestion_id: str


class WorkspaceStats(BaseModel):
    """Workspace statistics."""
    workspace_id: str
    name: str
    total_ingestions: int
    total_documents: int
    total_entities: int
    source_types: dict  # Count by source type
    created_at: str
