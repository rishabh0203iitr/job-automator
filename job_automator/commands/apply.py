"""Apply commands: single, auto, batch."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import typer

from job_automator.ai.cover_letter import generate_cover_letter, save_cover_letter
from job_automator.ai.resume_tailor import save_tailored_resume, tailor_resume
from job_automator.config.constants import ApplicationStatus
from job_automator.config.settings import get_settings
from job_automator.db.engine import init_db
from job_automator.db.models import Application
from job_automator.db.repository import (
    count_applications_today,
    get_application_by_job,
    get_job,
    insert_application,
    list_jobs,
    update_application_materials,
    update_application_status,
)
from job_automator.utils.display import (
    console,
    get_spinner,
    job_detail_panel,
    print_error,
    print_info,
    print_success,
    print_warning,
)

app = typer.Typer(help="Apply to jobs")


@app.command("single")
def apply_single(
    job_id: int = typer.Argument(help="Job ID to apply to"),
    dry_run: bool = typer.Option(True, "--dry-run/--submit", help="Generate materials without submitting"),
    no_cover_letter: bool = typer.Option(False, "--no-cover-letter", help="Skip cover letter generation"),
):
    """Apply to a single job: tailor resume, generate cover letter, optionally submit."""
    init_db()
    settings = get_settings()

    job = get_job(job_id)
    if not job:
        print_error(f"Job #{job_id} not found")
        raise typer.Exit(1)

    console.print(job_detail_panel(job))

    resume_path = settings.profile.resume_path
    if not resume_path:
        print_error("No resume configured. Run 'job profile import-resume <file>'")
        raise typer.Exit(1)

    # Get or create application record
    application = get_application_by_job(job_id)
    if not application:
        application = Application(job_id=job_id, status=ApplicationStatus.DISCOVERED.value)
        application.id = insert_application(application)

    # Tailor resume
    print_info("Tailoring resume...")
    with get_spinner("Tailoring resume...") as progress:
        task = progress.add_task("Tailoring...", total=None)
        try:
            tailored = tailor_resume(job, resume_path)
            saved_resume = save_tailored_resume(tailored, job)
            print_success(f"Tailored resume saved: {saved_resume}")
        except Exception as e:
            print_error(f"Resume tailoring failed: {e}")
            raise typer.Exit(1)

    # Generate cover letter
    cover_letter_text = ""
    if not no_cover_letter:
        print_info("Generating cover letter...")
        with get_spinner("Generating cover letter...") as progress:
            task = progress.add_task("Writing...", total=None)
            try:
                cover_letter_text = generate_cover_letter(job, resume_path)
                saved_cl = save_cover_letter(cover_letter_text, job)
                print_success(f"Cover letter saved: {saved_cl}")
            except Exception as e:
                print_error(f"Cover letter generation failed: {e}")

    # Update application
    update_application_materials(
        application.id,
        resume_path=str(saved_resume),
        cover_letter=cover_letter_text,
    )
    update_application_status(application.id, ApplicationStatus.TAILORED.value)

    if dry_run:
        print_warning("Dry run mode - materials generated but not submitted")
        print_info("Use --submit flag to attempt auto-submission")
        console.print("\n[bold]Tailored Resume Preview:[/bold]")
        console.print(tailored[:500] + "...")
        if cover_letter_text:
            console.print("\n[bold]Cover Letter Preview:[/bold]")
            console.print(cover_letter_text[:500] + "...")
    else:
        # Attempt auto-apply
        try:
            from job_automator.applicator.form_filler import auto_apply
            success = auto_apply(job, str(saved_resume), cover_letter_text)
            if success:
                update_application_status(application.id, ApplicationStatus.APPLIED.value)
                print_success("Application submitted!")
            else:
                print_warning("Auto-apply could not complete. Apply manually.")
                print_info(f"Job URL: {job.url}")
        except ImportError:
            print_warning("Auto-apply not available. Apply manually.")
            print_info(f"Job URL: {job.url}")


@app.command("auto")
def apply_auto(
    limit: int = typer.Option(5, "--limit", "-n", help="Max jobs to apply to"),
    dry_run: bool = typer.Option(True, "--dry-run/--submit", help="Generate materials without submitting"),
):
    """Auto-apply to top-scored jobs above threshold."""
    init_db()
    settings = get_settings()
    threshold = settings.apply.auto_apply_threshold

    today_count = count_applications_today()
    remaining = settings.apply.max_daily_applications - today_count
    if remaining <= 0:
        print_warning(f"Daily application limit reached ({settings.apply.max_daily_applications})")
        raise typer.Exit(0)

    actual_limit = min(limit, remaining)
    jobs = list_jobs(min_score=threshold, limit=actual_limit)

    if not jobs:
        print_info(f"No jobs found with score >= {threshold}")
        raise typer.Exit(0)

    print_info(f"Found {len(jobs)} jobs above threshold ({threshold})")

    for job in jobs:
        existing = get_application_by_job(job.id)
        if existing and existing.status not in (
            ApplicationStatus.DISCOVERED.value,
            ApplicationStatus.SCORED.value,
        ):
            continue

        console.print(f"\n[bold]{job.title}[/bold] at [cyan]{job.company}[/cyan] (score: {job.match_score})")

        try:
            apply_single(job.id, dry_run=dry_run, no_cover_letter=False)
        except (typer.Exit, SystemExit):
            continue
        except Exception as e:
            print_error(f"Failed: {e}")
            continue


@app.command("batch")
def apply_batch(
    min_score: int = typer.Option(60, "--min-score", help="Minimum match score"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max jobs"),
    dry_run: bool = typer.Option(True, "--dry-run/--submit"),
):
    """Apply to all jobs above a minimum score threshold."""
    apply_auto(limit=limit, dry_run=dry_run)
