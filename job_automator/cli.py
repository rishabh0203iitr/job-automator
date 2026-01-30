"""Root Typer CLI application."""

import typer

from job_automator.commands import (
    apply,
    config_cmd,
    dashboard,
    email_cmd,
    profile,
    search,
    track,
)

app = typer.Typer(
    name="job",
    help="AI-powered job search and application automator",
    no_args_is_help=True,
)

app.add_typer(config_cmd.app, name="config")
app.add_typer(search.app, name="search")
app.add_typer(apply.app, name="apply")
app.add_typer(track.app, name="track")
app.add_typer(email_cmd.app, name="email")
app.add_typer(profile.app, name="profile")
app.add_typer(dashboard.app, name="dashboard")
