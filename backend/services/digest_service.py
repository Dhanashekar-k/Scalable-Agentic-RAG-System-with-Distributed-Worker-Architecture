"""
Digest generation service.
Automatically summarizes ingested content over a time window.
"""
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from groq import AsyncGroq

from models.ingestion_schemas import DigestResponse, DigestSection
from database.chroma_client import chroma_client
from database.redis_client import redis_client
from config.settings import settings


class DigestService:
    """Generate digests of ingested sources."""
    
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    async def generate_digest(self, ingestion_id: str, days_back: int = 7) -> DigestResponse:
        """
        Generate a digest of an ingested source.
        
        Args:
            ingestion_id: ID of the ingestion
            days_back: Number of days to include in digest
        """
        # Get ingestion metadata
        ingestion_data = await redis_client.get_json(f"ingestion:{ingestion_id}")
        if not ingestion_data:
            raise ValueError("Ingestion not found")
        
        source_name = ingestion_data.get('source_name', 'Unknown')
        
        # Query ChromaDB for all documents with this ingestion_id
        collection = chroma_client.client.get_or_create_collection(
            name=settings.INGESTED_COLLECTION_NAME
        )
        
        try:
            results = collection.get(
                where={"ingestion_id": ingestion_id},
                include=["documents", "metadatas"]
            )
        except Exception as e:
            print(f"Failed to query ChromaDB: {e}")
            results = {"documents": [], "metadatas": []}
        
        if not results or not results.get('documents'):
            raise ValueError("No documents found for this ingestion")
        
        # Filter by date if needed
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        documents = []
        for i, doc in enumerate(results['documents']):
            metadata = results['metadatas'][i] if results.get('metadatas') else {}
            
            # Check date
            created_at = metadata.get('created_at', '')
            if created_at:
                try:
                    doc_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if doc_date < cutoff_date:
                        continue
                except Exception:
                    pass
            
            documents.append({
                "content": doc,
                "metadata": metadata
            })
        
        # Group by source_type
        grouped = self._group_documents(documents)
        
        # Generate summaries for each group
        sections = []
        for group_name, docs in grouped.items():
            if docs:
                summary = await self._summarize_group(group_name, docs)
                sections.append(DigestSection(
                    type=group_name,
                    count=len(docs),
                    summary=summary
                ))
        
        # Calculate stats
        stats = self._calculate_stats(documents, grouped)
        
        # Determine period string
        if days_back == 7:
            period = "Last 7 days"
        elif days_back == 30:
            period = "Last 30 days"
        else:
            period = f"Last {days_back} days"
        
        return DigestResponse(
            source_name=source_name,
            period=period,
            sections=sections,
            stats=stats,
            generated_at=datetime.utcnow().isoformat()
        )
    
    def _group_documents(self, docs: List[Dict]) -> Dict[str, List[Dict]]:
        """Group documents by source_type."""
        grouped = defaultdict(list)
        
        for doc in docs:
            source_type = doc['metadata'].get('source_type', 'unknown')
            
            # Normalize type names for display
            type_map = {
                'github_issue': 'Issues',
                'github_pr': 'Pull Requests',
                'github_commit': 'Commits',
                'github_readme': 'Documentation',
                'github_changelog': 'Changelog',
                'webpage': 'Web Pages',
                'reddit_post': 'Reddit Posts',
                'reddit_comment': 'Reddit Comments',
                'youtube_transcript': 'Video Transcripts',
                'rss_entry': 'RSS Entries',
                'pdf': 'PDF Pages'
            }
            
            display_name = type_map.get(source_type, source_type.replace('_', ' ').title())
            grouped[display_name].append(doc)
        
        return dict(grouped)
    
    async def _summarize_group(self, group_name: str, docs: List[Dict]) -> str:
        """Generate a summary for a group of documents using Groq."""
        # Limit to first 20 documents to avoid token limits
        sample_docs = docs[:20]
        
        # Build context
        context_parts = []
        for i, doc in enumerate(sample_docs, 1):
            content = doc['content'][:300]  # Limit each doc to 300 chars
            title = doc['metadata'].get('title', '')
            if title:
                context_parts.append(f"[{i}] {title}: {content}")
            else:
                context_parts.append(f"[{i}] {content}")
        
        context = "\n".join(context_parts)
        
        # Generate summary
        prompt = f"""Summarize these {len(docs)} {group_name} in 2-3 sentences, highlighting main themes and key points.
Keep the summary under 100 words.

Content:
{context}

Summary:"""
        
        try:
            response = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Failed to generate summary: {e}")
            return f"Contains {len(docs)} items covering various topics."
    
    def _calculate_stats(self, documents: List[Dict], grouped: Dict[str, List[Dict]]) -> Dict:
        """Calculate statistics for the digest."""
        # Count authors
        authors = defaultdict(int)
        for doc in documents:
            author = doc['metadata'].get('author', '')
            if author and author not in ['[deleted]', 'unknown', 'Unknown']:
                authors[author] += 1
        
        # Top 5 authors
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Date range
        dates = []
        for doc in documents:
            created_at = doc['metadata'].get('created_at', '')
            if created_at:
                try:
                    date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    dates.append(date)
                except Exception:
                    pass
        
        date_range = ""
        if dates:
            min_date = min(dates).strftime('%Y-%m-%d')
            max_date = max(dates).strftime('%Y-%m-%d')
            date_range = f"{min_date} to {max_date}"
        
        return {
            "total_docs": len(documents),
            "date_range": date_range,
            "top_authors": [{"name": name, "count": count} for name, count in top_authors],
            "categories": {name: len(docs) for name, docs in grouped.items()}
        }


# Global digest service instance
digest_service = DigestService()
