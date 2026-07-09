"""
Workspace management service.
Handles workspace CRUD operations and ingestion organization.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from database.redis_client import redis_client


class WorkspaceService:
    """Service for managing workspaces."""
    
    def __init__(self):
        self.workspace_prefix = "workspace:"
        self.workspace_list_key = "workspaces:all"
    
    async def create_workspace(self, name: str, description: Optional[str] = None) -> dict:
        """Create a new workspace."""
        workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        workspace = {
            "workspace_id": workspace_id,
            "name": name,
            "description": description or "",
            "ingestion_ids": [],
            "created_at": now,
            "updated_at": now
        }
        
        # Store workspace
        await redis_client.set_json(
            f"{self.workspace_prefix}{workspace_id}",
            workspace,
            ttl=None  # No expiration for workspaces
        )
        
        # Add to workspace list
        await redis_client.lpush(self.workspace_list_key, workspace_id)
        
        return workspace
    
    async def get_workspace(self, workspace_id: str) -> Optional[dict]:
        """Get workspace by ID."""
        workspace = await redis_client.get_json(f"{self.workspace_prefix}{workspace_id}")
        return workspace
    
    async def list_workspaces(self) -> List[dict]:
        """List all workspaces."""
        workspace_ids = await redis_client.lrange(self.workspace_list_key, 0, -1)
        
        workspaces = []
        for ws_id in workspace_ids:
            workspace = await self.get_workspace(ws_id)
            if workspace:
                # Add ingestion count
                workspace['ingestion_count'] = len(workspace.get('ingestion_ids', []))
                workspaces.append(workspace)
        
        return workspaces
    
    async def update_workspace(
        self, 
        workspace_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[dict]:
        """Update workspace."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        if name is not None:
            workspace['name'] = name
        if description is not None:
            workspace['description'] = description
        
        workspace['updated_at'] = datetime.utcnow().isoformat()
        
        await redis_client.set_json(
            f"{self.workspace_prefix}{workspace_id}",
            workspace,
            ttl=None
        )
        
        return workspace
    
    async def delete_workspace(self, workspace_id: str) -> bool:
        """Delete workspace and optionally its ingestions."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        # Remove from workspace list
        await redis_client.lrem(self.workspace_list_key, workspace_id)
        
        # Delete workspace
        await redis_client.delete(f"{self.workspace_prefix}{workspace_id}")
        
        return True
    
    async def add_ingestion_to_workspace(
        self, 
        workspace_id: str, 
        ingestion_id: str
    ) -> bool:
        """Add an ingestion to a workspace."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        # Check if ingestion exists
        ingestion = await redis_client.get_json(f"ingestion:{ingestion_id}")
        if not ingestion:
            return False
        
        # Add to workspace if not already there
        if ingestion_id not in workspace.get('ingestion_ids', []):
            workspace.setdefault('ingestion_ids', []).append(ingestion_id)
            workspace['updated_at'] = datetime.utcnow().isoformat()
            
            await redis_client.set_json(
                f"{self.workspace_prefix}{workspace_id}",
                workspace,
                ttl=None
            )
            
            # Update ingestion with workspace_id
            ingestion['workspace_id'] = workspace_id
            await redis_client.set_json(
                f"ingestion:{ingestion_id}",
                ingestion,
                ttl=604800  # Keep original TTL
            )
        
        return True
    
    async def remove_ingestion_from_workspace(
        self, 
        workspace_id: str, 
        ingestion_id: str
    ) -> bool:
        """Remove an ingestion from a workspace."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        if ingestion_id in workspace.get('ingestion_ids', []):
            workspace['ingestion_ids'].remove(ingestion_id)
            workspace['updated_at'] = datetime.utcnow().isoformat()
            
            await redis_client.set_json(
                f"{self.workspace_prefix}{workspace_id}",
                workspace,
                ttl=None
            )
            
            # Remove workspace_id from ingestion
            ingestion = await redis_client.get_json(f"ingestion:{ingestion_id}")
            if ingestion and 'workspace_id' in ingestion:
                del ingestion['workspace_id']
                await redis_client.set_json(
                    f"ingestion:{ingestion_id}",
                    ingestion,
                    ttl=604800
                )
        
        return True
    
    async def get_workspace_ingestions(self, workspace_id: str) -> List[dict]:
        """Get all ingestions in a workspace."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return []
        
        ingestions = []
        for ing_id in workspace.get('ingestion_ids', []):
            ingestion = await redis_client.get_json(f"ingestion:{ing_id}")
            if ingestion:
                ingestions.append(ingestion)
        
        return ingestions
    
    async def get_workspace_stats(self, workspace_id: str) -> Optional[dict]:
        """Get workspace statistics."""
        workspace = await self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        ingestions = await self.get_workspace_ingestions(workspace_id)
        
        total_docs = sum(ing.get('total_docs', 0) for ing in ingestions)
        total_entities = sum(ing.get('entity_count', 0) for ing in ingestions)
        
        # Count by source type
        source_types = {}
        for ing in ingestions:
            source_type = ing.get('source_type', 'unknown')
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        return {
            "workspace_id": workspace_id,
            "name": workspace['name'],
            "total_ingestions": len(ingestions),
            "total_documents": total_docs,
            "total_entities": total_entities,
            "source_types": source_types,
            "created_at": workspace['created_at']
        }


# Global workspace service instance
workspace_service = WorkspaceService()
