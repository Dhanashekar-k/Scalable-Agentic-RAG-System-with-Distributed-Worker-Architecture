"""
URL type detection for ingestion routing.
Detects GitHub repos, issues, PRs, Reddit, YouTube, RSS, and generic webpages.
"""
import re
from typing import Tuple, Optional


class URLDetector:
    """Detects the type of URL and routes to appropriate ingester."""
    
    # Regex patterns for URL detection
    GITHUB_REPO_PATTERN = r"github\.com/([^/]+)/([^/]+)/?$"
    GITHUB_ISSUE_PATTERN = r"github\.com/.+/issues/\d+"
    GITHUB_PR_PATTERN = r"github\.com/.+/pull/\d+"
    REDDIT_PATTERN = r"reddit\.com/r/"
    HACKERNEWS_PATTERN = r"news\.ycombinator\.com"
    YOUTUBE_PATTERN = r"(youtube\.com/watch|youtu\.be/)"
    
    def detect(self, url: str) -> str:
        """
        Detect URL type from the URL string.
        Returns one of: "github_repo", "github_issue", "github_pr",
                        "reddit", "hackernews", "youtube", "rss", "webpage", "unknown"
        """
        url_lower = url.lower()
        
        # GitHub patterns
        if re.search(self.GITHUB_ISSUE_PATTERN, url_lower):
            return "github_issue"
        if re.search(self.GITHUB_PR_PATTERN, url_lower):
            return "github_pr"
        if re.search(self.GITHUB_REPO_PATTERN, url_lower):
            return "github_repo"
        
        # Social/Community platforms
        if re.search(self.REDDIT_PATTERN, url_lower):
            return "reddit"
        if re.search(self.HACKERNEWS_PATTERN, url_lower):
            return "hackernews"
        
        # Video platforms
        if re.search(self.YOUTUBE_PATTERN, url_lower):
            return "youtube"
        
        # RSS/Atom feeds (check for common patterns)
        if any(pattern in url_lower for pattern in ['/feed', '/rss', '/atom', '.xml']):
            return "rss"
        
        # Default to webpage
        if url.startswith('http'):
            return "webpage"
        
        return "unknown"
    
    def extract_github_owner_repo(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract owner and repo name from GitHub URL.
        Returns (owner, repo) or (None, None) if not a valid GitHub URL.
        """
        match = re.search(self.GITHUB_REPO_PATTERN, url.lower())
        if match:
            return match.group(1), match.group(2)
        
        # Try to extract from issue/PR URLs
        match = re.search(r"github\.com/([^/]+)/([^/]+)/", url.lower())
        if match:
            return match.group(1), match.group(2)
        
        return None, None


# Global URL detector instance
url_detector = URLDetector()
