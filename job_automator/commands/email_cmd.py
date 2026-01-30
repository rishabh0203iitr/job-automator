"""Email commands: generate, send, bulk, list."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import typer

from job_automator.config.constants import EmailStatus
from job_automator.db.engine import init_db
from job_automator.db.models import ColdEmail
from job_automator.db.repository import (
    get_cold_email,
    get_job,
    insert_cold_email,
    list_cold_emails,
    update_cold_email_status,
)
from job_automator.email.finder import company_to_domain, guess_email_patterns
from job_automator.email.sender import EmailSender
from job_automator.email.templates import generate_cold_email
from job_automator.utils.display import (
    console,
    emails_table,
    get_spinner,
    print_error,
    print_info,
    print_success,
    print_warning,
)

app = typer.Typer(help="Cold email management")


@app.command("generate")
def email_generate(
    job_id: int = typer.Argument(help="Job ID to generate email for"),
    recipient_name: str = typer.Option("", "--name", "-n", help="Recipient name"),
    recipient_email: str = typer.Option("", "--email", "-e", help="Recipient email"),
    recipient_title: str = typer.Option("Hiring Manager", "--title", "-t", help="Recipient title"),
):
    """Generate a cold email draft for a job."""
    init_db()

    job = get_job(job_id)
    if not job:
        print_error(f"Job #{job_id} not found")
        raise typer.Exit(1)

    if not recipient_name:
        recipient_name = typer.prompt("Recipient name")

    if not recipient_email:
        # Suggest email patterns
        domain = company_to_domain(job.company)
        patterns = guess_email_patterns(recipient_name, domain)
        if patterns:
            print_info(f"Suggested emails for {domain}:")
            for p in patterns[:3]:
                console.print(f"  {p}")
        recipient_email = typer.prompt("Recipient email")

    print_info("Generating cold email...")
    with get_spinner("Writing email...") as progress:
        task = progress.add_task("Generating...", total=None)
        try:
            subject, body = generate_cold_email(job, recipient_name, recipient_title)
        except Exception as e:
            print_error(f"Email generation failed: {e}")
            raise typer.Exit(1)

    email = ColdEmail(
        job_id=job_id,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        recipient_title=recipient_title,
        company=job.company,
        subject=subject,
        body=body,
        status=EmailStatus.DRAFT.value,
    )
    email_id = insert_cold_email(email)

    print_success(f"Email draft #{email_id} created")
    console.print(f"\n[bold]Subject:[/bold] {subject}")
    console.print(f"[bold]To:[/bold] {recipient_name} <{recipient_email}>")
    console.print(f"\n{body}")


@app.command("send")
def email_send(
    email_id: int = typer.Argument(help="Email draft ID to send"),
    confirm: bool = typer.Option(True, "--confirm/--no-confirm", help="Confirm before sending"),
):
    """Send a drafted cold email."""
    init_db()

    email = get_cold_email(email_id)
    if not email:
        print_error(f"Email #{email_id} not found")
        raise typer.Exit(1)

    if email.status != EmailStatus.DRAFT.value:
        print_warning(f"Email is already {email.status}")
        raise typer.Exit(0)

    console.print(f"[bold]To:[/bold] {email.recipient_name} <{email.recipient_email}>")
    console.print(f"[bold]Subject:[/bold] {email.subject}")
    console.print(f"\n{email.body}")

    if confirm:
        proceed = typer.confirm("\nSend this email?")
        if not proceed:
            raise typer.Abort()

    sender = EmailSender()
    can, reason = sender.can_send()
    if not can:
        print_error(reason)
        raise typer.Exit(1)

    try:
        sender.send(email.recipient_email, email.subject, email.body)
        now = datetime.now().isoformat()
        update_cold_email_status(email.id, EmailStatus.SENT.value, sent_at=now)
        print_success("Email sent!")
    except Exception as e:
        print_error(f"Send failed: {e}")
        raise typer.Exit(1)


@app.command("bulk")
def email_bulk(
    confirm: bool = typer.Option(True, "--confirm/--no-confirm"),
):
    """Send all pending email drafts."""
    init_db()

    drafts = list_cold_emails(status=EmailStatus.DRAFT.value)
    if not drafts:
        print_info("No pending drafts")
        raise typer.Exit(0)

    print_info(f"Found {len(drafts)} pending drafts")
    console.print(emails_table(drafts))

    if confirm:
        proceed = typer.confirm(f"\nSend all {len(drafts)} emails?")
        if not proceed:
            raise typer.Abort()

    sender = EmailSender()
    sent = 0
    for email in drafts:
        can, reason = sender.can_send()
        if not can:
            print_warning(f"Stopping: {reason}")
            break

        try:
            sender.send(email.recipient_email, email.subject, email.body)
            now = datetime.now().isoformat()
            update_cold_email_status(email.id, EmailStatus.SENT.value, sent_at=now)
            sent += 1
            print_success(f"Sent to {email.recipient_email}")
            if sent < len(drafts):
                sender.send_with_delay()
        except Exception as e:
            print_error(f"Failed to send to {email.recipient_email}: {e}")

    print_success(f"Sent {sent}/{len(drafts)} emails")


@app.command("list")
def email_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-n"),
):
    """List cold emails."""
    init_db()
    emails = list_cold_emails(status=status, limit=limit)
    if not emails:
        print_info("No emails found")
        raise typer.Exit(0)
    console.print(emails_table(emails))
