"""LinkedIn/Indeed scraper using python-jobspy."""

from __future__ import annotations

import json
from typing import Optional

from job_automator.scrapers.base import BaseScraper, JobListing


class JobSpyScraper(BaseScraper):
    """Scrapes LinkedIn and Indeed using the python-jobspy library."""

    source_name = "jobspy"

    def search(
        self,
        query: str,
        location: str = "",
        results_wanted: int = 25,
        sites: Optional[list[str]] = None,
        **kwargs,
    ) -> list[JobListing]:
        from jobspy import scrape_jobs

        site_list = sites or ["linkedin", "indeed"]

        try:
            df = scrape_jobs(
                site_name=site_list,
                search_term=query,
                location=location if location and location.lower() != "remote" else None,
                is_remote=location.lower() == "remote" if location else False,
                results_wanted=results_wanted,
                country_indeed="USA",
            )
        except Exception as e:
            raise RuntimeError(f"python-jobspy search failed: {e}") from e

        listings: list[JobListing] = []
        for _, row in df.iterrows():
            raw = {}
            for col in df.columns:
                val = row.get(col)
                if val is not None and str(val) != "nan":
                    raw[col] = str(val)

            listing = JobListing(
                title=str(row.get("title", "")) if str(row.get("title", "")) != "nan" else "",
                company=str(row.get("company", "")) if str(row.get("company", "")) != "nan" else "",
                location=str(row.get("location", "")) if str(row.get("location", "")) != "nan" else "",
                url=str(row.get("job_url", "")) if str(row.get("job_url", "")) != "nan" else "",
                description=str(row.get("description", "")) if str(row.get("description", "")) != "nan" else "",
                salary=_extract_salary(row),
                source=str(row.get("site", "unknown")),
                date_posted=str(row.get("date_posted", "")) if str(row.get("date_posted", "")) != "nan" else None,
                raw_data=raw,
            )
            if listing.title and listing.company:
                listings.append(listing)

        return listings


def _extract_salary(row) -> str:
    parts = []
    min_amt = row.get("min_amount")
    max_amt = row.get("max_amount")
    currency = row.get("currency", "USD")
    interval = row.get("interval", "")

    if min_amt and str(min_amt) != "nan":
        parts.append(str(min_amt))
    if max_amt and str(max_amt) != "nan":
        parts.append(str(max_amt))

    if not parts:
        return ""

    salary = f"{currency} " + " - ".join(parts)
    if interval and str(interval) != "nan":
        salary += f" ({interval})"
    return salary
