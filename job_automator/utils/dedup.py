"""Job deduplication utilities."""

from __future__ import annotations

from job_automator.db.repository import job_exists_by_url
from job_automator.scrapers.base import JobListing


def deduplicate_listings(listings: list[JobListing]) -> list[JobListing]:
    """Remove duplicates from a list of scraped listings.

    Deduplicates by URL (exact match) and by (title, company) pair.
    Also checks against existing jobs in the database.
    """
    seen_urls: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    unique: list[JobListing] = []

    for listing in listings:
        # Skip if URL already in DB
        if listing.url and job_exists_by_url(listing.url):
            continue

        # Skip URL duplicates within batch
        if listing.url and listing.url in seen_urls:
            continue

        # Skip (title, company) duplicates within batch
        key = (listing.title.lower().strip(), listing.company.lower().strip())
        if key in seen_keys:
            continue

        if listing.url:
            seen_urls.add(listing.url)
        seen_keys.add(key)
        unique.append(listing)

    return unique
