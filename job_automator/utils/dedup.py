"""Job deduplication utilities."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from job_automator.db.repository import job_exists_by_url
from job_automator.scrapers.base import JobListing

# Tracking parameters commonly appended by job boards and ad platforms
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "refId", "trk", "trackingId", "currentJobId", "eBP", "position",
    "pageNum", "fclid", "gclid", "fbclid", "mc_cid", "mc_eid",
    "si", "pp", "rcb", "tk", "fromSearchPage",
})


def normalize_url(url: str) -> str:
    """Strip tracking/session parameters from a URL for dedup comparison."""
    if not url:
        return url
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=False)
        cleaned = {k: v for k, v in params.items() if k.lower() not in _TRACKING_PARAMS}
        new_query = urlencode(cleaned, doseq=True) if cleaned else ""
        normalized = urlunparse(parsed._replace(query=new_query, fragment=""))
        return normalized.rstrip("?")
    except Exception:
        return url


def deduplicate_listings(listings: list[JobListing]) -> list[JobListing]:
    """Remove duplicates from a list of scraped listings.

    Deduplicates by normalized URL and by (title, company) pair.
    Also checks against existing jobs in the database.
    """
    seen_urls: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    unique: list[JobListing] = []

    for listing in listings:
        norm_url = normalize_url(listing.url)

        # Skip if URL already in DB (check both raw and normalized)
        if listing.url and (job_exists_by_url(listing.url) or job_exists_by_url(norm_url)):
            continue

        # Skip URL duplicates within batch
        if norm_url and norm_url in seen_urls:
            continue

        # Skip (title, company) duplicates within batch
        key = (listing.title.lower().strip(), listing.company.lower().strip())
        if key in seen_keys:
            continue

        if norm_url:
            seen_urls.add(norm_url)
        seen_keys.add(key)
        unique.append(listing)

    return unique
