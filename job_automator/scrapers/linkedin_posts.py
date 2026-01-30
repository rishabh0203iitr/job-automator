"""LinkedIn posts scraper via Google search for public previews."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from job_automator.db.models import SocialPost
from job_automator.db.repository import insert_social_post, social_post_exists
from job_automator.scrapers.base import BaseScraper, JobListing


class LinkedInPostsScraper(BaseScraper):
    """Find hiring-related LinkedIn posts via Google search."""

    source_name = "linkedin_post"

    def __init__(self):
        self.client = httpx.Client(
            timeout=15,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            },
        )

    def search(
        self,
        query: str,
        location: str = "",
        results_wanted: int = 20,
        **kwargs,
    ) -> list[JobListing]:
        """Search Google for LinkedIn posts about hiring."""
        search_query = f'site:linkedin.com/posts "{query}" ("hiring" OR "we\'re looking" OR "join our team")'
        if location and location.lower() != "remote":
            search_query += f" {location}"

        encoded = quote_plus(search_query)
        url = f"https://www.google.com/search?q={encoded}&num={min(results_wanted, 20)}"

        try:
            resp = self.client.get(url)
            if resp.status_code != 200:
                return []
        except Exception:
            return []

        listings = self._parse_google_results(resp.text)

        # Save as social posts
        saved: list[JobListing] = []
        for listing in listings[:results_wanted]:
            if listing.url and not social_post_exists(listing.url):
                post = SocialPost(
                    platform="linkedin_post",
                    post_url=listing.url,
                    author=listing.company,
                    content=listing.description,
                )
                insert_social_post(post)
            saved.append(listing)

        return saved

    def _parse_google_results(self, html: str) -> list[JobListing]:
        soup = BeautifulSoup(html, "html.parser")
        listings = []

        for result in soup.select("div.g"):
            try:
                link_el = result.select_one("a")
                title_el = result.select_one("h3")
                snippet_el = result.select_one("div.VwiC3b, span.aCOpRe")

                if not link_el:
                    continue

                url = link_el.get("href", "")
                if "linkedin.com/posts" not in url:
                    continue

                title = title_el.get_text(strip=True) if title_el else ""
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                # Extract author from title (usually "Author Name on LinkedIn: ...")
                author = ""
                if " on LinkedIn" in title:
                    author = title.split(" on LinkedIn")[0].strip()

                listing = JobListing(
                    title=title[:100],
                    company=author,
                    description=snippet,
                    url=url,
                    source="linkedin_post",
                )
                listings.append(listing)
            except Exception:
                continue

        return listings
