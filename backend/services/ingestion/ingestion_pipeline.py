"""
Main ingestion pipeline coordinator.
Routes to correct ingester, chunks documents, generates embeddings,
stores in ChromaDB and Neo4j, tracks progress in Redis.
"""
import asyncio
import uuid
from typing import List
from datetime import datetime

from models.ingestion_schemas import IngestionDocument, IngestionResult
from services.ingestion.url_detector import url_detector
from services.ingestion.github_ingester import github_ingester
from services.ingestion.web_ingester import web_ingester
from services.ingestion.reddit_ingester import reddit_ingester
from services.ingestion.youtube_ingester import youtube_ingester
from services.ingestion.rss_ingester import rss_ingester
from services.ingestion.pdf_ingester import pdf_ingester
from services.embedding_service import embedding_service
from database.chroma_client import chroma_client
from database.neo4j_client import neo4j_client
from database.redis_client import redis_client
from config.settings import settings


class IngestionPipeline:
    """Main coordinator for ingestion operations."""

    async def ingest_url(self, url: str, ingestion_id: str, recursive: bool = False):
        """
        Background task to ingest a URL.
        Detects type, calls appropriate ingester, stores results.
        """
        try:
            # Update status
            await self._update_status(ingestion_id, "running", "Detecting URL type...")
            
            # Detect URL type
            url_type = url_detector.detect(url)
            
            await self._update_status(
                ingestion_id, "running", f"Detected type: {url_type}. Fetching content..."
            )
            
            # Route to appropriate ingester
            result = None
            
            if url_type == "github_repo":
                owner, repo = url_detector.extract_github_owner_repo(url)
                if owner and repo:
                    result = await github_ingester.ingest(owner, repo)
            
            elif url_type in ["github_issue", "github_pr"]:
                # Extract owner/repo and fetch that repo
                owner, repo = url_detector.extract_github_owner_repo(url)
                if owner and repo:
                    result = await github_ingester.ingest(owner, repo)
            
            elif url_type == "webpage":
                result = await web_ingester.ingest(url, recursive=recursive)
            
            elif url_type == "reddit":
                result = await reddit_ingester.ingest(url)
            
            elif url_type == "youtube":
                result = await youtube_ingester.ingest(url)
            
            elif url_type == "rss":
                result = await rss_ingester.ingest(url)
            
            else:
                raise ValueError(f"Unsupported URL type: {url_type}")
            
            if not result or not result.documents:
                raise ValueError("No documents extracted from source")
            
            # Update status with document count
            await self._update_status(
                ingestion_id,
                "running",
                f"Extracted {len(result.documents)} documents. Chunking and embedding..."
            )
            
            # Chunk documents
            chunks = await self._chunk_documents(result.documents)
            
            # Store in ChromaDB
            await self._update_status(
                ingestion_id, "running", f"Storing {len(chunks)} chunks in vector database..."
            )
            doc_count = await self._store_in_chromadb(chunks, ingestion_id)
            
            # Store in Neo4j
            await self._update_status(
                ingestion_id, "running", "Building knowledge graph..."
            )
            entity_count = await self._store_in_neo4j(result.graph_data, ingestion_id)
            
            # Mark as complete
            await redis_client.set_json(f"ingestion:{ingestion_id}", {
                "ingestion_id": ingestion_id,
                "status": "complete",
                "source_url": url,
                "source_type": url_type,
                "source_name": result.source_name,
                "total_docs": doc_count,
                "processed_docs": doc_count,
                "entity_count": entity_count,
                "created_at": datetime.utcnow().isoformat(),
                "message": f"✅ Successfully ingested {doc_count} documents and {entity_count} entities"
            }, ttl=604800)  # 7 days
            
        except Exception as e:
            # Mark as failed
            await redis_client.set_json(f"ingestion:{ingestion_id}", {
                "ingestion_id": ingestion_id,
                "status": "failed",
                "source_url": url,
                "source_type": "unknown",
                "source_name": url,
                "total_docs": 0,
                "processed_docs": 0,
                "entity_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "message": f"❌ Failed: {str(e)}"
            }, ttl=604800)
    
    async def ingest_pdf(self, file_bytes: bytes, filename: str, ingestion_id: str):
        """Background task to ingest a PDF file."""
        try:
            await self._update_status(ingestion_id, "running", "Extracting text from PDF...")
            
            # Ingest PDF
            result = await pdf_ingester.ingest(file_bytes, filename)
            
            if not result or not result.documents:
                raise ValueError("No text extracted from PDF")
            
            await self._update_status(
                ingestion_id,
                "running",
                f"Extracted {len(result.documents)} pages. Embedding..."
            )
            
            # Chunk documents (PDFs are already chunked by page)
            chunks = result.documents
            
            # Store in ChromaDB
            doc_count = await self._store_in_chromadb(chunks, ingestion_id)
            
            # Store in Neo4j
            entity_count = await self._store_in_neo4j(result.graph_data, ingestion_id)
            
            # Mark as complete
            await redis_client.set_json(f"ingestion:{ingestion_id}", {
                "ingestion_id": ingestion_id,
                "status": "complete",
                "source_url": f"uploaded:{filename}",
                "source_type": "pdf",
                "source_name": result.source_name,
                "total_docs": doc_count,
                "processed_docs": doc_count,
                "entity_count": entity_count,
                "created_at": datetime.utcnow().isoformat(),
                "message": f"✅ Successfully ingested {doc_count} pages"
            }, ttl=604800)
            
        except Exception as e:
            await redis_client.set_json(f"ingestion:{ingestion_id}", {
                "ingestion_id": ingestion_id,
                "status": "failed",
                "source_url": f"uploaded:{filename}",
                "source_type": "pdf",
                "source_name": filename,
                "total_docs": 0,
                "processed_docs": 0,
                "entity_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "message": f"❌ Failed: {str(e)}"
            }, ttl=604800)
    
    async def delete_ingestion(self, ingestion_id: str):
        """Delete an ingestion from all databases."""
        # Delete from ChromaDB
        try:
            collection = chroma_client.client.get_or_create_collection(
                name=settings.INGESTED_COLLECTION_NAME
            )
            # Get all IDs for this ingestion
            results = collection.get(where={"ingestion_id": ingestion_id})
            if results and results['ids']:
                collection.delete(ids=results['ids'])
        except Exception as e:
            print(f"Failed to delete from ChromaDB: {e}")
        
        # Delete from Neo4j
        try:
            await neo4j_client.delete_ingested_entities(ingestion_id)
        except Exception as e:
            print(f"Failed to delete from Neo4j: {e}")
        
        # Delete from Redis
        await redis_client.delete(f"ingestion:{ingestion_id}")
        
        # Remove from index
        try:
            index = await redis_client.lrange("ingestion:index", 0, -1)
            if ingestion_id in index:
                # Redis doesn't have lrem in async, so we'll rebuild the list
                new_index = [id for id in index if id != ingestion_id]
                await redis_client.delete("ingestion:index")
                for id in new_index:
                    await redis_client.lpush("ingestion:index", id)
        except Exception as e:
            print(f"Failed to update index: {e}")
    
    async def _chunk_documents(self, documents: List[IngestionDocument]) -> List[IngestionDocument]:
        """Chunk documents into smaller pieces if needed."""
        chunks = []
        
        for doc in documents:
            words = doc.content.split()
            
            if len(words) <= settings.INGESTION_CHUNK_SIZE:
                chunks.append(doc)
            else:
                # Split into overlapping chunks
                chunk_size = settings.INGESTION_CHUNK_SIZE
                overlap = settings.INGESTION_CHUNK_OVERLAP
                
                for i in range(0, len(words), chunk_size - overlap):
                    chunk_words = words[i:i + chunk_size]
                    chunk_text = ' '.join(chunk_words)
                    
                    # Create new document with chunk metadata
                    chunk_doc = IngestionDocument(
                        content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_index": i // (chunk_size - overlap),
                            "is_chunked": True
                        }
                    )
                    chunks.append(chunk_doc)
        
        return chunks
    
    async def _store_in_chromadb(self, chunks: List[IngestionDocument], ingestion_id: str) -> int:
        """Store chunks in ChromaDB with embeddings."""
        if not chunks:
            return 0
        
        # Get or create ingested collection
        collection = chroma_client.client.get_or_create_collection(
            name=settings.INGESTED_COLLECTION_NAME
        )
        
        # Process in batches
        batch_size = 100
        total_stored = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Generate embeddings
            embeddings = []
            for doc in batch:
                embedding = embedding_service.embed_text(doc.content)
                embeddings.append(embedding)
            
            # Prepare data
            ids = [f"{ingestion_id}_{j}" for j in range(i, i + len(batch))]
            documents = [doc.content for doc in batch]
            metadatas = [
                {**doc.metadata, "ingestion_id": ingestion_id}
                for doc in batch
            ]
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            total_stored += len(batch)
            
            # Update progress
            await self._update_progress(ingestion_id, total_stored, len(chunks), "running")
        
        return total_stored
    
    async def _store_in_neo4j(self, graph_data, ingestion_id: str) -> int:
        """Store entities and relationships in Neo4j."""
        entity_count = 0
        
        # Create entities
        for entity in graph_data.entities:
            try:
                await neo4j_client.create_ingested_entity(entity, ingestion_id)
                entity_count += 1
            except Exception as e:
                print(f"Failed to create entity {entity.name}: {e}")
        
        # Create relationships
        for rel in graph_data.relationships:
            try:
                await neo4j_client.create_ingested_relationship(rel, ingestion_id)
            except Exception as e:
                print(f"Failed to create relationship: {e}")
        
        return entity_count
    
    async def _update_status(self, ingestion_id: str, status: str, message: str):
        """Update ingestion status in Redis."""
        data = await redis_client.get_json(f"ingestion:{ingestion_id}")
        if data:
            data["status"] = status
            data["message"] = message
            await redis_client.set_json(f"ingestion:{ingestion_id}", data, ttl=604800)
    
    async def _update_progress(
        self, ingestion_id: str, processed: int, total: int, status: str
    ):
        """Update ingestion progress."""
        data = await redis_client.get_json(f"ingestion:{ingestion_id}")
        if data:
            data["processed_docs"] = processed
            data["total_docs"] = total
            data["status"] = status
            await redis_client.set_json(f"ingestion:{ingestion_id}", data, ttl=604800)


# Global ingestion pipeline instance
ingestion_pipeline = IngestionPipeline()
