"""Twitter/X job scraper via Nitter instances."""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from job_automator.db.models import SocialPost
from job_automator.db.repository import insert_social_post, social_post_exists
from job_automator.scrapers.base import BaseScraper, JobListing

# Public Nitter instances (may change over time)
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
]


class TwitterScraper(BaseScraper):
    """Scrape job posts from Twitter via Nitter instances."""

    source_name = "twitter"

    def __init__(self):
        self.client = httpx.Client(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"},
        )

    def search(
        self,
        query: str,
        location: str = "",
        results_wanted: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Search Twitter for job posts via Nitter."""
        search_query = f"{query} hiring OR remote OR apply"
        if location and location.lower() != "remote":
            search_query += f" {location}"

        listings: list[JobListing] = []
        encoded = quote_plus(search_query)

        for instance in NITTER_INSTANCES:
            if len(listings) >= results_wanted:
                break
            try:
                url = f"{instance}/search?f=tweets&q={encoded}"
                resp = self.client.get(url)
                if resp.status_code != 200:
                    continue

                new_listings = self._parse_results(resp.text, instance)
                listings.extend(new_listings)
            except Exception:
                continue

        # Save as social posts and convert to JobListings
        saved: list[JobListing] = []
        for listing in listings[:results_wanted]:
            if listing.url and not social_post_exists(listing.url):
                post = SocialPost(
                    platform="twitter",
                    post_url=listing.url,
                    author=listing.company,
                    content=listing.description,
                )
                insert_social_post(post)
            saved.append(listing)

        return saved

    def _parse_results(self, html: str, instance: str) -> list[JobListing]:
        soup = BeautifulSoup(html, "html.parser")
        listings = []

        for tweet in soup.select(".timeline-item"):
            try:
                username_el = tweet.select_one(".username")
                content_el = tweet.select_one(".tweet-content")
                link_el = tweet.select_one(".tweet-link")

                if not content_el:
                    continue

                username = username_el.get_text(strip=True) if username_el else ""
                content = content_el.get_text(strip=True)
                tweet_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    tweet_url = f"https://twitter.com{href}" if href.startswith("/") else href

                listing = JobListing(
                    title=content[:100],
                    company=username,
                    description=content,
                    url=tweet_url,
                    source="twitter",
                )
                listings.append(listing)
            except Exception:
                continue

        return listings
