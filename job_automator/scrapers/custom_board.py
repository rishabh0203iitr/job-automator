"""Playwright-based scraper for custom career pages."""

from __future__ import annotations

import json
from typing import Optional

from job_automator.scrapers.base import BaseScraper, JobListing


class CustomBoardScraper(BaseScraper):
    """Scrape jobs from custom career pages using Playwright."""

    source_name = "custom"

    def search(
        self,
        query: str,
        location: str = "",
        results_wanted: int = 25,
        url: str = "",
        **kwargs,
    ) -> list[JobListing]:
        """Scrape job listings from a custom career page URL.

        Args:
            query: Search query to filter results
            location: Location filter
            results_wanted: Max results
            url: The career page URL to scrape
        """
        if not url:
            raise ValueError("Custom board scraper requires a URL")

        from playwright.sync_api import sync_playwright

        listings: list[JobListing] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)

                # Try common career page patterns
                listings = self._try_lever(page, url)
                if not listings:
                    listings = self._try_greenhouse(page, url)
                if not listings:
                    listings = self._try_generic(page, url)

            except Exception as e:
                raise RuntimeError(f"Failed to scrape {url}: {e}") from e
            finally:
                browser.close()

        # Filter by query
        if query:
            q = query.lower()
            listings = [
                l for l in listings
                if q in l.title.lower() or q in l.description.lower()
            ]

        return listings[:results_wanted]

    def _try_lever(self, page, base_url: str) -> list[JobListing]:
        """Parse Lever-style job boards."""
        postings = page.locator(".posting").all()
        if not postings:
            return []

        listings = []
        for posting in postings:
            try:
                title_el = posting.locator(".posting-title h5, .posting-name").first
                loc_el = posting.locator(".posting-categories .location, .workplaceTypes").first
                link_el = posting.locator("a.posting-btn-submit, a").first

                title = title_el.inner_text() if title_el.count() else ""
                location = loc_el.inner_text() if loc_el.count() else ""
                url = link_el.get_attribute("href") or "" if link_el.count() else ""

                if title:
                    listings.append(JobListing(
                        title=title.strip(),
                        location=location.strip(),
                        url=url,
                        source="custom",
                    ))
            except Exception:
                continue
        return listings

    def _try_greenhouse(self, page, base_url: str) -> list[JobListing]:
        """Parse Greenhouse-style job boards."""
        openings = page.locator(".opening").all()
        if not openings:
            return []

        listings = []
        for opening in openings:
            try:
                link_el = opening.locator("a").first
                loc_el = opening.locator(".location").first

                title = link_el.inner_text() if link_el.count() else ""
                url = link_el.get_attribute("href") or "" if link_el.count() else ""
                location = loc_el.inner_text() if loc_el.count() else ""

                if title:
                    listings.append(JobListing(
                        title=title.strip(),
                        location=location.strip(),
                        url=url,
                        source="custom",
                    ))
            except Exception:
                continue
        return listings

    def _try_generic(self, page, base_url: str) -> list[JobListing]:
        """Generic fallback: look for links that look like job postings."""
        links = page.locator("a").all()
        listings = []

        job_keywords = {"engineer", "developer", "manager", "designer", "analyst",
                        "scientist", "lead", "director", "coordinator", "specialist"}

        for link in links:
            try:
                text = link.inner_text().strip()
                href = link.get_attribute("href") or ""

                # Heuristic: link text contains job-related keywords
                if text and any(kw in text.lower() for kw in job_keywords):
                    if not href.startswith("http"):
                        href = base_url.rstrip("/") + "/" + href.lstrip("/")
                    listings.append(JobListing(
                        title=text,
                        url=href,
                        source="custom",
                    ))
            except Exception:
                continue

        return listings
