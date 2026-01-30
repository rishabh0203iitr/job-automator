"""Abstract base scraper and JobListing dataclass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobListing:
    """Intermediate representation of a scraped job before DB insertion."""
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    salary: str = ""
    source: str = ""
    date_posted: Optional[str] = None
    raw_data: dict = field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    source_name: str = ""

    @abstractmethod
    def search(
        self,
        query: str,
        location: str = "",
        results_wanted: int = 25,
        **kwargs,
    ) -> list[JobListing]:
        """Search for jobs and return a list of JobListing objects."""
        ...
