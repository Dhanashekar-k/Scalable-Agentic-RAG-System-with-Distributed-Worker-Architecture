"""
YouTube video transcript ingester.
Uses youtube-transcript-api (free, no API key required).
"""
import re
from typing import List
import httpx
from youtube_transcript_api import YouTubeTranscriptApi

from models.ingestion_schemas import (
    IngestionDocument, IngestionResult, GraphData,
    GraphEntity, GraphRelationship
)
from services.ingestion.tagging_utils import compute_temporal_bucket, extract_key_terms


class YouTubeIngester:
    """Ingest YouTube video transcripts."""
    
    async def ingest(self, url: str) -> IngestionResult:
        """
        Ingest a YouTube video transcript.
        
        Args:
            url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
        """
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        # Fetch video metadata using oEmbed API (free, no key)
        metadata = await self._fetch_metadata(url)
        
        # Fetch transcript
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            print(f"Failed to fetch transcript: {e}")
            transcript = []
        
        # Chunk transcript
        documents = self._chunk_transcript(transcript, video_id, url, metadata)
        
        # Build graph data
        channel = metadata.get('author_name', 'Unknown')
        graph_data = GraphData(
            entities=[
                GraphEntity(name=channel, entity_type="youtube_channel", properties={}),
                GraphEntity(name=video_id, entity_type="youtube_video", properties=metadata)
            ],
            relationships=[
                GraphRelationship(
                    from_entity=channel,
                    to_entity=video_id,
                    relationship_type="PUBLISHED",
                    properties={}
                )
            ]
        )
        
        return IngestionResult(
            documents=documents,
            graph_data=graph_data,
            source_name=metadata.get('title', video_id),
            source_type="youtube"
        )
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_metadata(self, url: str) -> dict:
        """Fetch video metadata using oEmbed API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://www.youtube.com/oembed?url={url}&format=json"
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Failed to fetch YouTube metadata: {e}")
        
        return {}
    
    def _chunk_transcript(
        self, transcript: List[dict], video_id: str, url: str, metadata: dict
    ) -> List[IngestionDocument]:
        """Chunk transcript into ~500 word segments."""
        documents = []
        
        if not transcript:
            return documents
        
        chunk_words = 500
        current_chunk = []
        current_word_count = 0
        chunk_start_time = transcript[0]['start']
        
        for entry in transcript:
            text = entry['text']
            words = text.split()
            word_count = len(words)
            
            current_chunk.append(text)
            current_word_count += word_count
            
            if current_word_count >= chunk_words:
                # Create document for this chunk
                chunk_text = ' '.join(current_chunk)
                chunk_end_time = entry['start'] + entry.get('duration', 0)

                video_title_lower = metadata.get('title', '').lower()
                tutorial_words_list = ["tutorial", "how to", "learn", "guide", "course", "step by step", "beginner"]
                opinion_words_list = ["review", "opinion", "vs", "compare", "better", "worse", "should you"]
                news_words_list = ["news", "update", "release", "announced", "new in"]

                if any(w in video_title_lower for w in tutorial_words_list):
                    yt_intent = "explanation|reference"
                    yt_quality = 0.85
                elif any(w in video_title_lower for w in opinion_words_list):
                    yt_intent = "opinion"
                    yt_quality = 0.75
                elif any(w in video_title_lower for w in news_words_list):
                    yt_intent = "changelog|feed"
                    yt_quality = 0.7
                else:
                    yt_intent = "explanation"
                    yt_quality = 0.7

                chunk_meta = {
                    "source_type": "youtube_transcript",
                    "source_url": url,
                    "video_title": metadata.get('title', ''),
                    "channel": metadata.get('author_name', ''),
                    "chunk_start_seconds": chunk_start_time,
                    "chunk_end_seconds": chunk_end_time,
                    "video_id": video_id,
                    "intent_tags": yt_intent,
                    "source_category": "media",
                    "content_quality": yt_quality,
                    "temporal_bucket": "unknown",
                    "entities_mentioned": extract_key_terms(chunk_text, chunk_meta if False else {})
                }
                # Re-compute entities_mentioned with the actual meta (avoid forward ref)
                chunk_meta["entities_mentioned"] = extract_key_terms(chunk_text, chunk_meta)

                documents.append(IngestionDocument(
                    content=chunk_text,
                    metadata=chunk_meta
                ))
                
                # Reset for next chunk
                current_chunk = []
                current_word_count = 0
                chunk_start_time = entry['start']
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)

            video_title_lower = metadata.get('title', '').lower()
            tutorial_words_list = ["tutorial", "how to", "learn", "guide", "course", "step by step", "beginner"]
            opinion_words_list = ["review", "opinion", "vs", "compare", "better", "worse", "should you"]
            news_words_list = ["news", "update", "release", "announced", "new in"]

            if any(w in video_title_lower for w in tutorial_words_list):
                yt_intent = "explanation|reference"
                yt_quality = 0.85
            elif any(w in video_title_lower for w in opinion_words_list):
                yt_intent = "opinion"
                yt_quality = 0.75
            elif any(w in video_title_lower for w in news_words_list):
                yt_intent = "changelog|feed"
                yt_quality = 0.7
            else:
                yt_intent = "explanation"
                yt_quality = 0.7

            last_meta = {
                "source_type": "youtube_transcript",
                "source_url": url,
                "video_title": metadata.get('title', ''),
                "channel": metadata.get('author_name', ''),
                "chunk_start_seconds": chunk_start_time,
                "chunk_end_seconds": transcript[-1]['start'] + transcript[-1].get('duration', 0),
                "video_id": video_id,
                "intent_tags": yt_intent,
                "source_category": "media",
                "content_quality": yt_quality,
                "temporal_bucket": "unknown",
                "entities_mentioned": ""
            }
            last_meta["entities_mentioned"] = extract_key_terms(chunk_text, last_meta)

            documents.append(IngestionDocument(
                content=chunk_text,
                metadata=last_meta
            ))
        
        return documents


# Global YouTube ingester instance
youtube_ingester = YouTubeIngester()
