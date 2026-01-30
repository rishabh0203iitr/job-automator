"""Hiring manager email discovery."""

from __future__ import annotations

import re


def guess_email_patterns(name: str, domain: str) -> list[str]:
    """Generate common email patterns from a name and company domain.

    Returns a list of likely email addresses, ordered by probability.
    """
    parts = name.lower().strip().split()
    if len(parts) < 2:
        first = parts[0] if parts else "unknown"
        last = ""
    else:
        first = parts[0]
        last = parts[-1]

    domain = domain.lower().strip()
    if not domain:
        return []

    patterns = []
    if first and last:
        patterns = [
            f"{first}.{last}@{domain}",
            f"{first}{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"{first}@{domain}",
            f"{first}_{last}@{domain}",
            f"{first[0]}.{last}@{domain}",
            f"{last}.{first}@{domain}",
        ]
    elif first:
        patterns = [f"{first}@{domain}"]

    return patterns


def extract_domain_from_url(url: str) -> str:
    """Extract the company domain from a job URL or company website."""
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if not match:
        return ""

    domain = match.group(1)

    # Skip job board domains
    job_boards = {"linkedin.com", "indeed.com", "glassdoor.com", "lever.co",
                  "greenhouse.io", "workday.com", "smartrecruiters.com"}
    if any(domain.endswith(board) for board in job_boards):
        return ""

    return domain


def company_to_domain(company: str) -> str:
    """Guess a company's domain from its name."""
    cleaned = re.sub(r"[^\w\s]", "", company.lower()).strip()
    cleaned = re.sub(r"\s+", "", cleaned)
    return f"{cleaned}.com"
