"""
RSS/Atom feed ingester.
Parses feeds and optionally fetches full article content.
"""
from typing import List
from datetime import datetime, timedelta
import feedparser

from models.ingestion_schemas import (
    IngestionDocument, IngestionResult, GraphData,
    GraphEntity, GraphRelationship
)
from services.ingestion.tagging_utils import compute_temporal_bucket, extract_key_terms


class RSSIngester:
    """Ingest RSS/Atom feeds."""
    
    async def ingest(self, url: str, days_back: int = 30) -> IngestionResult:
        """
        Ingest RSS/Atom feed entries.
        
        Args:
            url: Feed URL
            days_back: Only include entries from last N days
        """
        documents = []
        
        # Parse feed
        feed = feedparser.parse(url)
        
        if not feed.entries:
            raise ValueError("No entries found in feed")
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        feed_title = feed.feed.get('title', 'Unknown Feed')
        
        # Process entries
        for entry in feed.entries:
            # Check date
            published = self._parse_date(entry)
            if published and published < cutoff_date:
                continue
            
            # Extract content
            content_parts = [f"# {entry.get('title', 'Untitled')}"]
            
            # Get content (try different fields)
            content = (
                entry.get('content', [{}])[0].get('value', '') or
                entry.get('summary', '') or
                entry.get('description', '')
            )
            
            if content:
                content_parts.append(content)
            
            tags = [tag.get('term', '') for tag in entry.get('tags', [])]
            tags_str = ', '.join(tags) if tags else ''
            tags_lower = tags_str.lower()

            intent_parts = ["feed"]
            if any(w in tags_lower for w in ["tutorial", "guide", "how-to"]):
                intent_parts.append("explanation")
            if any(w in tags_lower for w in ["release", "changelog", "update", "version"]):
                intent_parts.append("changelog")
            if any(w in tags_lower for w in ["opinion", "review", "vs"]):
                intent_parts.append("opinion")

            rss_content = '\n\n'.join(content_parts)
            published_at_str = published.isoformat() if published else ''

            rss_meta = {
                "source_type": "rss_entry",
                "source_url": entry.get('link', url),
                "feed_title": feed_title,
                "published_at": published_at_str,
                "author": entry.get('author', ''),
                "tags": tags_str,
                "title": entry.get('title', 'Untitled'),
                "intent_tags": "|".join(intent_parts),
                "source_category": "feed",
                "content_quality": 0.6,
                "temporal_bucket": compute_temporal_bucket(published_at_str),
                "entities_mentioned": extract_key_terms(
                    rss_content, {"author": entry.get('author', ''), "tags": tags_str}
                )
            }

            documents.append(IngestionDocument(
                content=rss_content,
                metadata=rss_meta
            ))
        
        # Build graph data
        graph_data = GraphData(
            entities=[
                GraphEntity(name=feed_title, entity_type="rss_feed", properties={})
            ],
            relationships=[]
        )
        
        return IngestionResult(
            documents=documents,
            graph_data=graph_data,
            source_name=feed_title,
            source_type="rss"
        )
    
    def _parse_date(self, entry: dict) -> datetime:
        """Parse entry date from various fields."""
        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if field in entry and entry[field]:
                try:
                    time_struct = entry[field]
                    return datetime(*time_struct[:6])
                except Exception:
                    continue
        return None


# Global RSS ingester instance
rss_ingester = RSSIngester()
