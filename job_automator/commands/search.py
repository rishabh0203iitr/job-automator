"""Search commands: run, twitter, linkedin-posts."""

from __future__ import annotations

import json
from typing import Optional

import typer

from job_automator.config.settings import get_settings
from job_automator.db.engine import init_db
from job_automator.db.models import Job
from job_automator.db.repository import insert_job
from job_automator.scrapers.base import JobListing
from job_automator.scrapers.jobspy_scraper import JobSpyScraper
from job_automator.utils.dedup import deduplicate_listings
from job_automator.utils.display import (
    console,
    get_spinner,
    jobs_table,
    print_error,
    print_info,
    print_success,
    print_warning,
)

app = typer.Typer(help="Search for jobs")


def _listing_to_job(listing: JobListing) -> Job:
    return Job(
        source=listing.source,
        title=listing.title,
        company=listing.company,
        location=listing.location,
        url=listing.url,
        description=listing.description,
        salary=listing.salary,
        date_posted=listing.date_posted,
        raw_data=json.dumps(listing.raw_data) if listing.raw_data else "",
    )


@app.command("run")
def search_run(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Location filter"),
    sites: Optional[str] = typer.Option(None, "--sites", "-s", help="Comma-separated sites: linkedin,indeed"),
    results: int = typer.Option(25, "--results", "-n", help="Results per site"),
    score: bool = typer.Option(False, "--score", help="Score jobs with AI after search"),
):
    """Search LinkedIn/Indeed for jobs via python-jobspy."""
    settings = get_settings()
    init_db()

    search_query = query or settings.search.default_query
    search_location = location or settings.search.default_location
    site_list = sites.split(",") if sites else settings.search.sites

    print_info(f"Searching for '{search_query}' in '{search_location}' on {', '.join(site_list)}")

    scraper = JobSpyScraper()

    with get_spinner("Searching...") as progress:
        task = progress.add_task("Searching job boards...", total=None)
        try:
            listings = scraper.search(
                query=search_query,
                location=search_location,
                results_wanted=results,
                sites=site_list,
            )
        except Exception as e:
            print_error(f"Search failed: {e}")
            raise typer.Exit(1)

    print_info(f"Found {len(listings)} raw results")

    unique = deduplicate_listings(listings)
    skipped = len(listings) - len(unique)
    if skipped:
        print_info(f"Skipped {skipped} duplicates")

    saved_jobs: list[Job] = []
    for listing in unique:
        job = _listing_to_job(listing)
        job_id = insert_job(job)
        job.id = job_id
        saved_jobs.append(job)

    print_success(f"Saved {len(saved_jobs)} new jobs")

    if score and saved_jobs:
        _score_jobs(saved_jobs)

    if saved_jobs:
        console.print(jobs_table(saved_jobs[:20], title=f"New Jobs ({len(saved_jobs)} total)"))


def _score_jobs(jobs: list[Job]):
    """Score jobs using AI. Imported lazily to avoid circular deps."""
    try:
        from job_automator.ai.job_scorer import score_jobs
        score_jobs(jobs)
    except ImportError:
        print_warning("AI scoring not available. Install AI provider dependencies.")
    except Exception as e:
        print_error(f"Scoring failed: {e}")


@app.command("twitter")
def search_twitter(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    max_results: int = typer.Option(20, "--max", "-n", help="Max results"),
):
    """Search Twitter/X for job posts via Nitter."""
    init_db()
    try:
        from job_automator.scrapers.twitter_scraper import TwitterScraper
        scraper = TwitterScraper()
        settings = get_settings()
        search_query = query or f"{settings.search.default_query} hiring"

        with get_spinner("Searching Twitter...") as progress:
            task = progress.add_task("Searching...", total=None)
            posts = scraper.search(search_query, results_wanted=max_results)

        print_success(f"Found {len(posts)} posts")
        for p in posts[:10]:
            console.print(f"  [cyan]{p.author}[/cyan]: {p.title[:80]}")
    except ImportError:
        print_error("Twitter scraper not available yet.")
    except Exception as e:
        print_error(f"Twitter search failed: {e}")


@app.command("linkedin-posts")
def search_linkedin_posts(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    max_results: int = typer.Option(20, "--max", "-n", help="Max results"),
):
    """Search LinkedIn posts for hiring announcements."""
    init_db()
    try:
        from job_automator.scrapers.linkedin_posts import LinkedInPostsScraper
        scraper = LinkedInPostsScraper()
        settings = get_settings()
        search_query = query or f"{settings.search.default_query} hiring"

        with get_spinner("Searching LinkedIn posts...") as progress:
            task = progress.add_task("Searching...", total=None)
            posts = scraper.search(search_query, results_wanted=max_results)

        print_success(f"Found {len(posts)} posts")
        for p in posts[:10]:
            console.print(f"  [cyan]{p.author}[/cyan]: {p.title[:80]}")
    except ImportError:
        print_error("LinkedIn posts scraper not available yet.")
    except Exception as e:
        print_error(f"LinkedIn posts search failed: {e}")
