"""
PDF document ingester using PyMuPDF (fitz).
Extracts text per page and chunks large pages.
"""
from typing import List
import fitz  # PyMuPDF

from models.ingestion_schemas import (
    IngestionDocument, IngestionResult, GraphData,
    GraphEntity, GraphRelationship
)
from services.ingestion.tagging_utils import compute_temporal_bucket, extract_key_terms


class PDFIngester:
    """Ingest PDF documents."""
    
    async def ingest(self, file_bytes: bytes, filename: str) -> IngestionResult:
        """
        Ingest a PDF file.
        
        Args:
            file_bytes: PDF file content as bytes
            filename: Original filename
        """
        documents = []
        
        # Open PDF from bytes
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Extract metadata
        metadata_dict = pdf_document.metadata
        pdf_title = metadata_dict.get('title', filename)
        pdf_author = metadata_dict.get('author', 'Unknown')
        total_pages = pdf_document.page_count
        
        # Extract text from each page
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            text = page.get_text()
            
            if not text.strip():
                continue
            
            # Check if page is too long (> 1000 words)
            words = text.split()
            if len(words) > 1000:
                # Split into sub-chunks
                chunks = self._split_text(text, chunk_size=500)
                for i, chunk in enumerate(chunks):
                    page_number = page_num + 1
                    if page_number <= 2:
                        pdf_intent = "explanation"
                    elif page_number >= total_pages - 1:
                        pdf_intent = "reference"
                    else:
                        pdf_intent = "reference|explanation"

                    pdf_meta = {
                        "source_type": "pdf",
                        "source_url": f"uploaded:{filename}",
                        "page_number": page_number,
                        "sub_chunk": i + 1,
                        "total_pages": total_pages,
                        "pdf_title": pdf_title,
                        "pdf_author": pdf_author,
                        "filename": filename,
                        "intent_tags": pdf_intent,
                        "source_category": "documentation",
                        "content_quality": min(1.0, len(chunk.split()) / 300),
                        "temporal_bucket": "unknown",
                        "entities_mentioned": extract_key_terms(
                            chunk, {"author": pdf_author}
                        )
                    }
                    documents.append(IngestionDocument(content=chunk, metadata=pdf_meta))
            else:
                page_number = page_num + 1
                if page_number <= 2:
                    pdf_intent = "explanation"
                elif page_number >= total_pages - 1:
                    pdf_intent = "reference"
                else:
                    pdf_intent = "reference|explanation"

                pdf_meta = {
                    "source_type": "pdf",
                    "source_url": f"uploaded:{filename}",
                    "page_number": page_number,
                    "total_pages": total_pages,
                    "pdf_title": pdf_title,
                    "pdf_author": pdf_author,
                    "filename": filename,
                    "intent_tags": pdf_intent,
                    "source_category": "documentation",
                    "content_quality": min(1.0, len(text.split()) / 300),
                    "temporal_bucket": "unknown",
                    "entities_mentioned": extract_key_terms(
                        text, {"author": pdf_author}
                    )
                }
                documents.append(IngestionDocument(content=text, metadata=pdf_meta))
        
        pdf_document.close()
        
        # Build graph data
        graph_data = GraphData(
            entities=[
                GraphEntity(name=pdf_title, entity_type="pdf_document", properties={
                    "author": pdf_author,
                    "pages": total_pages
                })
            ],
            relationships=[]
        )
        
        return IngestionResult(
            documents=documents,
            graph_data=graph_data,
            source_name=pdf_title,
            source_type="pdf"
        )
    
    def _split_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks by word count, preserving sentence boundaries."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_count = 0
        
        for word in words:
            current_chunk.append(word)
            current_count += 1
            
            # Check if we should end chunk (at sentence boundary if possible)
            if current_count >= chunk_size:
                # Look for sentence ending
                if word.endswith(('.', '!', '?')):
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_count = 0
                elif current_count >= chunk_size + 50:  # Force split if too long
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_count = 0
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


# Global PDF ingester instance
pdf_ingester = PDFIngester()
