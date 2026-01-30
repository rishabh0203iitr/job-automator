"""Tracking commands: list, update, stats."""

from __future__ import annotations

from typing import Optional

import typer

from job_automator.config.constants import ApplicationStatus
from job_automator.db.engine import init_db
from job_automator.db.repository import (
    count_applications,
    get_application,
    get_job,
    list_applications,
    update_application_status,
)
from job_automator.utils.display import (
    applications_table,
    console,
    job_detail_panel,
    print_error,
    print_info,
    print_success,
    STATUS_COLORS,
)

app = typer.Typer(help="Track applications")


@app.command("list")
def track_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-n"),
):
    """List applications with optional status filter."""
    init_db()
    apps = list_applications(status=status, limit=limit)
    if not apps:
        print_info("No applications found")
        raise typer.Exit(0)

    jobs_map = {}
    for app_record in apps:
        job = get_job(app_record.job_id)
        if job:
            jobs_map[app_record.job_id] = job

    console.print(applications_table(apps, jobs_map))


@app.command("update")
def track_update(
    app_id: int = typer.Argument(help="Application ID"),
    status: str = typer.Argument(help=f"New status: {', '.join(s.value for s in ApplicationStatus)}"),
    notes: str = typer.Option("", "--notes", "-n", help="Add notes"),
):
    """Update an application's status."""
    init_db()

    application = get_application(app_id)
    if not application:
        print_error(f"Application #{app_id} not found")
        raise typer.Exit(1)

    valid_statuses = [s.value for s in ApplicationStatus]
    if status not in valid_statuses:
        print_error(f"Invalid status. Choose from: {', '.join(valid_statuses)}")
        raise typer.Exit(1)

    update_application_status(app_id, status, notes)
    print_success(f"Application #{app_id} updated to '{status}'")

    job = get_job(application.job_id)
    if job:
        color = STATUS_COLORS.get(status, "dim")
        console.print(f"  {job.title} at {job.company} → [{color}]{status}[/{color}]")


@app.command("stats")
def track_stats():
    """Show application statistics."""
    init_db()

    total = count_applications()
    if total == 0:
        print_info("No applications tracked yet")
        raise typer.Exit(0)

    console.print(f"\n[bold]Application Statistics[/bold] (total: {total})\n")
    for status in ApplicationStatus:
        count = count_applications(status.value)
        color = STATUS_COLORS.get(status.value, "dim")
        bar = "█" * min(count, 40)
        pct = (count / total * 100) if total > 0 else 0
        console.print(f"  [{color}]{status.value:<14}[/{color}] {bar} {count} ({pct:.0f}%)")
