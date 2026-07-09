"""
Web page scraper and crawler.
Supports single page scraping and recursive crawling for documentation sites.
"""
import asyncio
from typing import List, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from models.ingestion_schemas import (
    IngestionDocument, IngestionResult, GraphData,
    GraphEntity, GraphRelationship
)
from services.ingestion.tagging_utils import compute_temporal_bucket, extract_key_terms


class WebIngester:
    """Scrape webpages and optionally crawl documentation sites."""
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
    
    async def ingest(self, url: str, recursive: bool = False) -> IngestionResult:
        """
        Ingest a webpage or recursively crawl a site.
        
        Args:
            url: Starting URL
            recursive: If True, crawl same-domain links (max depth 2, max 20 pages)
        """
        self.visited_urls = set()
        documents = []
        
        if recursive:
            documents = await self._crawl_recursive(url, max_depth=2, max_pages=20)
        else:
            doc = await self._scrape_single_page(url)
            if doc:
                documents.append(doc)
        
        # Extract minimal graph data (domain as entity)
        domain = urlparse(url).netloc
        graph_data = GraphData(
            entities=[GraphEntity(name=domain, entity_type="website", properties={})],
            relationships=[]
        )
        
        return IngestionResult(
            documents=documents,
            graph_data=graph_data,
            source_name=domain,
            source_type="webpage"
        )
    
    async def _scrape_single_page(self, url: str) -> IngestionDocument:
        """Scrape a single webpage."""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Niyanta/1.0)"
                })
                
                if response.status_code != 200:
                    return None
                
                html = response.text
                return self._extract_text(html, url)
        
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            return None
    
    async def _crawl_recursive(
        self, start_url: str, max_depth: int = 2, max_pages: int = 20
    ) -> List[IngestionDocument]:
        """Recursively crawl a website."""
        documents = []
        to_visit = [(start_url, 0)]  # (url, depth)
        base_domain = urlparse(start_url).netloc
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            while to_visit and len(documents) < max_pages:
                url, depth = to_visit.pop(0)
                
                if url in self.visited_urls or depth > max_depth:
                    continue
                
                self.visited_urls.add(url)
                
                try:
                    response = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; Niyanta/1.0)"
                    })
                    
                    if response.status_code != 200:
                        continue
                    
                    html = response.text
                    
                    # Extract document
                    doc = self._extract_text(html, url)
                    if doc:
                        documents.append(doc)
                    
                    # Extract links for next depth
                    if depth < max_depth:
                        links = self._get_links(html, url)
                        for link in links:
                            link_domain = urlparse(link).netloc
                            if link_domain == base_domain and link not in self.visited_urls:
                                to_visit.append((link, depth + 1))
                    
                    await asyncio.sleep(0.5)  # Be polite
                
                except Exception as e:
                    print(f"Failed to crawl {url}: {e}")
                    continue
        
        return documents
    
    def _extract_text(self, html: str, url: str) -> IngestionDocument:
        """Extract main content from HTML."""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                element.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else urlparse(url).path
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''
            
            # Extract main content
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean up text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            content = '\n'.join(lines)
            
            # Skip if too short
            if len(content) < 100:
                return None
            
            return IngestionDocument(
                content=content[:10000],  # Limit to 10k chars
                metadata={
                    "source_type": "webpage",
                    "source_url": url,
                    "title": title_text,
                    "domain": urlparse(url).netloc,
                    "description": description,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "intent_tags": self._detect_web_intent(url),
                    "source_category": self._detect_web_category(url),
                    "content_quality": min(1.0, len(content.split()) / 300),
                    "temporal_bucket": "unknown",
                    "entities_mentioned": extract_key_terms(
                        content[:10000], {"source_url": url}
                    )
                }
            )
        
        except Exception as e:
            print(f"Failed to extract text from {url}: {e}")
            return None
    
    def _detect_web_intent(self, url: str) -> str:
        """Detect intent tags from URL patterns."""
        url_lower = url.lower()
        if any(p in url_lower for p in ["/docs/", "/documentation/", "readthedocs", "/wiki/", "/guide/"]):
            return "explanation|reference"
        elif any(p in url_lower for p in ["/blog/", "/post/", "/article/", "/news/"]):
            return "opinion|explanation"
        elif any(p in url_lower for p in ["/api/", "/reference/", "/spec/"]):
            return "reference"
        elif any(p in url_lower for p in ["/faq/", "/troubleshoot/", "/error/"]):
            return "problem|explanation"
        else:
            return "explanation"

    def _detect_web_category(self, url: str) -> str:
        """Detect source category from URL patterns."""
        url_lower = url.lower()
        if any(p in url_lower for p in ["/blog/", "/post/", "/article/", "/news/"]):
            return "feed"
        return "documentation"

    def _get_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML."""
        try:
            soup = BeautifulSoup(html, 'lxml')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # Skip anchors, javascript, mailto, etc.
                if href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                
                # Remove fragments
                absolute_url = absolute_url.split('#')[0]
                
                links.append(absolute_url)
            
            return list(set(links))  # Deduplicate
        
        except Exception:
            return []


# Global web ingester instance
web_ingester = WebIngester()
