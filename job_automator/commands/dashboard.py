"""Dashboard command: rich overview of the pipeline."""

from __future__ import annotations

import typer
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from job_automator.config.constants import ApplicationStatus, EmailStatus
from job_automator.db.engine import init_db
from job_automator.db.repository import (
    count_applications,
    count_jobs,
    get_job,
    list_applications,
    list_cold_emails,
    list_jobs,
)
from job_automator.utils.display import (
    STATUS_COLORS,
    console,
    dashboard_stats,
    print_info,
    score_color,
)

app = typer.Typer(help="Dashboard overview", invoke_without_command=True)


@app.callback(invoke_without_command=True)
def show_dashboard():
    """Show a rich overview: pipeline, stats, recent activity."""
    init_db()

    total_jobs = count_jobs()
    apps_by_status = {}
    for status in ApplicationStatus:
        apps_by_status[status.value] = count_applications(status.value)

    emails = list_cold_emails(limit=100)
    emails_sent = sum(1 for e in emails if e.status == EmailStatus.SENT.value)
    emails_drafted = sum(1 for e in emails if e.status == EmailStatus.DRAFT.value)

    # Stats panel
    console.print(dashboard_stats(total_jobs, apps_by_status, emails_sent, emails_drafted))

    # Top scored jobs
    top_jobs = list_jobs(min_score=1, limit=10)
    if top_jobs:
        table = Table(title="Top Scored Jobs", show_lines=False)
        table.add_column("ID", style="dim", width=5)
        table.add_column("Score", width=6)
        table.add_column("Title", min_width=20)
        table.add_column("Company", min_width=15)

        for job in top_jobs:
            color = score_color(job.match_score)
            table.add_row(
                str(job.id),
                f"[{color}]{job.match_score}[/{color}]",
                job.title,
                job.company,
            )
        console.print(table)

    # Recent activity
    recent_apps = list_applications(limit=5)
    if recent_apps:
        table = Table(title="Recent Activity", show_lines=False)
        table.add_column("App ID", style="dim", width=7)
        table.add_column("Status", width=14)
        table.add_column("Job", min_width=25)
        table.add_column("Updated", width=12)

        for app_record in recent_apps:
            job = get_job(app_record.job_id)
            color = STATUS_COLORS.get(app_record.status, "dim")
            table.add_row(
                str(app_record.id),
                f"[{color}]{app_record.status}[/{color}]",
                f"{job.title} @ {job.company}" if job else "—",
                (app_record.updated_at or "—")[:10],
            )
        console.print(table)

    if total_jobs == 0:
        print_info("No data yet. Run 'job search run' to get started!")
