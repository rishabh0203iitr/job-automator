"""Configuration commands: init, show, validate."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.panel import Panel
from rich.syntax import Syntax

from job_automator.config.settings import (
    Settings,
    get_config_path,
    load_settings,
    save_settings,
)
from job_automator.db.engine import init_db
from job_automator.utils.display import console, print_error, print_info, print_success

app = typer.Typer(help="Configuration management")


@app.command()
def init():
    """Interactive first-time setup. Creates config.yaml and initializes the database."""
    config_path = get_config_path()
    if config_path.exists():
        overwrite = typer.confirm(f"Config already exists at {config_path}. Overwrite?")
        if not overwrite:
            raise typer.Abort()

    console.print("\n[bold]Job Automator Setup[/bold]\n")

    name = typer.prompt("Your full name")
    email = typer.prompt("Your email")
    title = typer.prompt("Target job title", default="Software Engineer")
    location = typer.prompt("Preferred location", default="remote")
    skills_raw = typer.prompt("Key skills (comma-separated)", default="Python, JavaScript")
    skills = [s.strip() for s in skills_raw.split(",")]

    ai_provider = typer.prompt(
        "AI provider (gemini/anthropic/openai/ollama)", default="gemini"
    )
    api_key = typer.prompt(f"API key for {ai_provider} (or press enter to use env var)", default="")

    settings = Settings()
    settings.profile.name = name
    settings.profile.email = email
    settings.profile.title = title
    settings.profile.location = location
    settings.profile.skills = skills
    settings.search.default_query = title
    settings.search.default_location = location
    settings.ai.provider = ai_provider
    if api_key:
        settings.ai.api_key = api_key

    path = save_settings(settings)
    print_success(f"Config saved to {path}")

    db_path = init_db()
    print_success(f"Database initialized at {db_path}")

    print_info("Edit config.yaml to customize further settings (email, apply thresholds, etc.)")


@app.command()
def show():
    """Display current configuration."""
    config_path = get_config_path()
    if not config_path.exists():
        print_error("No config found. Run 'job config init' first.")
        raise typer.Exit(1)

    with open(config_path) as f:
        content = f.read()

    # Mask sensitive fields
    data = yaml.safe_load(content)
    if data.get("ai", {}).get("api_key"):
        data["ai"]["api_key"] = "***hidden***"
    if data.get("email", {}).get("sender_password"):
        data["email"]["sender_password"] = "***hidden***"

    masked = yaml.dump(data, default_flow_style=False, sort_keys=False)
    syntax = Syntax(masked, "yaml", theme="monokai")
    console.print(Panel(syntax, title=f"Config: {config_path}", border_style="blue"))


@app.command()
def validate():
    """Validate the current configuration."""
    config_path = get_config_path()
    if not config_path.exists():
        print_error("No config found. Run 'job config init' first.")
        raise typer.Exit(1)

    try:
        settings = load_settings(config_path)
    except Exception as e:
        print_error(f"Config validation failed: {e}")
        raise typer.Exit(1)

    issues: list[str] = []
    if not settings.profile.name:
        issues.append("profile.name is empty")
    if not settings.profile.email:
        issues.append("profile.email is empty")
    if not settings.ai.get_api_key() and settings.ai.provider != "ollama":
        issues.append(f"No API key found for {settings.ai.provider}")

    if issues:
        print_error("Config issues found:")
        for issue in issues:
            console.print(f"  [yellow]•[/yellow] {issue}")
    else:
        print_success("Configuration is valid")
