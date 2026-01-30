"""Rich display utilities for terminal output."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from job_automator.config.constants import ApplicationStatus
from job_automator.db.models import Application, ColdEmail, Job

console = Console()
error_console = Console(stderr=True)


def print_success(message: str):
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    error_console.print(f"[red]✗[/red] {message}")


def print_warning(message: str):
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str):
    console.print(f"[blue]→[/blue] {message}")


def get_spinner(text: str = "Working...") -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def score_color(score: Optional[int]) -> str:
    if score is None:
        return "dim"
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


STATUS_COLORS = {
    ApplicationStatus.DISCOVERED.value: "dim",
    ApplicationStatus.SCORED.value: "blue",
    ApplicationStatus.TAILORED.value: "cyan",
    ApplicationStatus.APPLIED.value: "yellow",
    ApplicationStatus.INTERVIEWING.value: "magenta",
    ApplicationStatus.OFFER.value: "green",
    ApplicationStatus.REJECTED.value: "red",
}


def jobs_table(jobs: list[Job], title: str = "Jobs") -> Table:
    table = Table(title=title, show_lines=False)
    table.add_column("ID", style="dim", width=5)
    table.add_column("Score", width=6)
    table.add_column("Title", min_width=20)
    table.add_column("Company", min_width=15)
    table.add_column("Location", min_width=10)
    table.add_column("Source", width=10)

    for job in jobs:
        color = score_color(job.match_score)
        score_str = f"[{color}]{job.match_score}[/{color}]" if job.match_score is not None else "-"
        table.add_row(
            str(job.id), score_str, job.title, job.company,
            job.location or "—", job.source,
        )
    return table


def job_detail_panel(job: Job) -> Panel:
    lines = [
        f"[bold]{job.title}[/bold] at [cyan]{job.company}[/cyan]",
        f"Location: {job.location or '—'}",
        f"Source: {job.source}",
        f"URL: {job.url or '—'}",
        f"Salary: {job.salary or '—'}",
        f"Score: [{score_color(job.match_score)}]{job.match_score or '—'}[/{score_color(job.match_score)}]",
    ]
    if job.match_reasons:
        lines.append(f"\n[bold]Match Reasons:[/bold]\n{job.match_reasons}")
    if job.description:
        desc = job.description[:500] + ("..." if len(job.description) > 500 else "")
        lines.append(f"\n[bold]Description:[/bold]\n{desc}")
    return Panel("\n".join(lines), title=f"Job #{job.id}", border_style="blue")


def applications_table(apps: list[Application], jobs_map: dict[int, Job]) -> Table:
    table = Table(title="Applications", show_lines=False)
    table.add_column("ID", style="dim", width=5)
    table.add_column("Status", width=14)
    table.add_column("Title", min_width=20)
    table.add_column("Company", min_width=15)
    table.add_column("Applied", width=12)

    for app in apps:
        job = jobs_map.get(app.job_id)
        color = STATUS_COLORS.get(app.status, "dim")
        table.add_row(
            str(app.id),
            f"[{color}]{app.status}[/{color}]",
            job.title if job else "—",
            job.company if job else "—",
            (app.applied_at or "—")[:10],
        )
    return table


def emails_table(emails: list[ColdEmail]) -> Table:
    table = Table(title="Cold Emails", show_lines=False)
    table.add_column("ID", style="dim", width=5)
    table.add_column("Status", width=10)
    table.add_column("Recipient", min_width=20)
    table.add_column("Company", min_width=15)
    table.add_column("Subject", min_width=20)

    for email in emails:
        table.add_row(
            str(email.id), email.status, email.recipient_name,
            email.company, email.subject[:40],
        )
    return table


def dashboard_stats(
    total_jobs: int,
    apps_by_status: dict[str, int],
    emails_sent: int,
    emails_drafted: int,
) -> Panel:
    lines = [
        f"[bold]Jobs Discovered:[/bold] {total_jobs}",
        "",
        "[bold]Application Pipeline:[/bold]",
    ]
    for status in ApplicationStatus:
        count = apps_by_status.get(status.value, 0)
        color = STATUS_COLORS.get(status.value, "dim")
        bar = "█" * min(count, 30)
        lines.append(f"  [{color}]{status.value:<14}[/{color}] {bar} {count}")

    lines.append("")
    lines.append(f"[bold]Emails:[/bold] {emails_sent} sent, {emails_drafted} drafted")

    return Panel("\n".join(lines), title="Dashboard", border_style="green")
