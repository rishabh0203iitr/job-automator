"""Profile commands: show, edit, import-resume."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel

from job_automator.config.settings import get_settings, load_settings, save_settings
from job_automator.utils.display import console, print_error, print_info, print_success
from job_automator.utils.resume_parser import extract_text

app = typer.Typer(help="Manage your profile")


@app.command("show")
def profile_show():
    """Display your current profile."""
    settings = get_settings()
    p = settings.profile

    lines = [
        f"[bold]Name:[/bold] {p.name or '—'}",
        f"[bold]Email:[/bold] {p.email or '—'}",
        f"[bold]Phone:[/bold] {p.phone or '—'}",
        f"[bold]Location:[/bold] {p.location or '—'}",
        f"[bold]Title:[/bold] {p.title or '—'}",
        f"[bold]Experience:[/bold] {p.years_experience} years",
        f"[bold]Skills:[/bold] {', '.join(p.skills) if p.skills else '—'}",
        f"[bold]Resume:[/bold] {p.resume_path or '—'}",
        f"[bold]LinkedIn:[/bold] {p.linkedin_url or '—'}",
        f"[bold]GitHub:[/bold] {p.github_url or '—'}",
        f"[bold]Portfolio:[/bold] {p.portfolio_url or '—'}",
    ]

    console.print(Panel("\n".join(lines), title="Profile", border_style="blue"))


@app.command("edit")
def profile_edit(
    name: str = typer.Option(None, "--name"),
    email: str = typer.Option(None, "--email"),
    title: str = typer.Option(None, "--title"),
    location: str = typer.Option(None, "--location"),
    skills: str = typer.Option(None, "--skills", help="Comma-separated skills"),
    experience: int = typer.Option(None, "--experience", "--exp"),
    resume: str = typer.Option(None, "--resume", help="Path to resume file"),
    linkedin: str = typer.Option(None, "--linkedin"),
    github: str = typer.Option(None, "--github"),
):
    """Update profile fields."""
    settings = load_settings()

    if name is not None:
        settings.profile.name = name
    if email is not None:
        settings.profile.email = email
    if title is not None:
        settings.profile.title = title
    if location is not None:
        settings.profile.location = location
    if skills is not None:
        settings.profile.skills = [s.strip() for s in skills.split(",")]
    if experience is not None:
        settings.profile.years_experience = experience
    if resume is not None:
        settings.profile.resume_path = resume
    if linkedin is not None:
        settings.profile.linkedin_url = linkedin
    if github is not None:
        settings.profile.github_url = github

    save_settings(settings)
    print_success("Profile updated")
    profile_show()


@app.command("import-resume")
def import_resume(
    file_path: str = typer.Argument(help="Path to resume file (PDF, DOCX, or TXT)"),
):
    """Parse and import resume text for AI operations."""
    path = Path(file_path)
    if not path.exists():
        print_error(f"File not found: {path}")
        raise typer.Exit(1)

    try:
        text = extract_text(path)
    except Exception as e:
        print_error(f"Failed to parse resume: {e}")
        raise typer.Exit(1)

    print_success(f"Parsed resume ({len(text)} characters)")
    console.print(Panel(text[:500] + ("..." if len(text) > 500 else ""), title="Resume Preview"))

    # Update config with resume path
    settings = load_settings()
    settings.profile.resume_path = str(path.resolve())
    save_settings(settings)
    print_info(f"Resume path saved: {path.resolve()}")
