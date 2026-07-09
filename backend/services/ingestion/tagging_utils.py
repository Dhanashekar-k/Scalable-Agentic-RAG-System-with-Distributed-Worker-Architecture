"""
Shared tagging utilities for ingestion enrichment.
Kept in a separate module to avoid circular imports between
ingestion_pipeline.py and the individual ingesters.
"""
import re
from datetime import datetime


def compute_temporal_bucket(created_at_str: str) -> str:
    """
    Converts a datetime string into a fast-filterable bucket.
    Called at ingest time so the worker never does date math at query time.

    Returns: "today" | "this_week" | "this_month" | "this_year" | "older" | "unknown"
    """
    if not created_at_str:
        return "unknown"
    try:
        # Handle ISO strings with or without timezone suffix
        clean = created_at_str.replace("Z", "").split("+")[0].split(".")[0]
        created = datetime.fromisoformat(clean)
        delta = datetime.utcnow() - created
        if delta.days <= 1:
            return "today"
        elif delta.days <= 7:
            return "this_week"
        elif delta.days <= 30:
            return "this_month"
        elif delta.days <= 365:
            return "this_year"
        else:
            return "older"
    except Exception:
        return "unknown"


def extract_key_terms(content: str, metadata: dict) -> str:
    """
    Extracts exact-match terms from chunk content and metadata.
    These are stored as entities_mentioned in ChromaDB metadata.
    Used by BM25 in hybrid_retriever.py for exact-term matching.

    Returns pipe-separated string (ChromaDB metadata must be str/number).
    e.g. "issue#234|pr#891|@tj|body-parser|Express|Connect"
    """
    terms = set()

    # author from metadata
    if metadata.get("author"):
        terms.add(str(metadata["author"]))

    # source_id from metadata (e.g. "issue#234", "pr#891")
    if metadata.get("source_id"):
        terms.add(str(metadata["source_id"]))

    # labels from metadata (split by ", ")
    if metadata.get("labels"):
        for label in str(metadata["labels"]).split(", "):
            label = label.strip()
            if label:
                terms.add(label)

    # #numbers from content (issue/PR references like "#234")
    for match in re.findall(r'#(\d+)', content):
        terms.add(f"#{match}")

    # @mentions from content
    for match in re.findall(r'@([\w-]+)', content):
        terms.add(f"@{match}")

    # backtick terms from content (code terms like `body-parser`)
    for match in re.findall(r'`([^`]+)`', content):
        term = match.strip()
        if term:
            terms.add(term)

    # CamelCase words from content, max 10
    camel_words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', content)
    for word in camel_words[:10]:
        terms.add(word)

    # Deduplicate, max 20 terms, return as pipe-separated string
    return "|".join(list(terms)[:20])
