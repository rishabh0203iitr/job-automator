"""Cold email prompt templates and generation."""

from __future__ import annotations

from job_automator.ai.prompts import COLD_EMAIL_PROMPT, COLD_EMAIL_SYSTEM
from job_automator.ai.provider import get_ai_provider
from job_automator.config.settings import get_settings
from job_automator.db.models import Job


def generate_cold_email(
    job: Job,
    recipient_name: str,
    recipient_title: str = "Hiring Manager",
) -> tuple[str, str]:
    """Generate a cold email for a job opportunity.

    Returns (subject, body) tuple.
    """
    settings = get_settings()
    provider = get_ai_provider()

    prompt = COLD_EMAIL_PROMPT.format(
        name=settings.profile.name,
        title=settings.profile.title,
        skills=", ".join(settings.profile.skills[:5]),
        recipient_name=recipient_name,
        recipient_title=recipient_title,
        company=job.company,
        job_title=job.title,
        job_description=(job.description or "No description available")[:1500],
    )

    response = provider.generate(prompt, system=COLD_EMAIL_SYSTEM, temperature=0.7)

    # Parse subject and body from response
    subject = ""
    body = response.strip()

    if "SUBJECT:" in response:
        parts = response.split("---", 1)
        subject_line = parts[0].strip()
        if "SUBJECT:" in subject_line:
            subject = subject_line.split("SUBJECT:", 1)[1].strip()
        if len(parts) > 1:
            body = parts[1].strip()

    if not subject:
        subject = f"Re: {job.title} at {job.company}"

    # Append signature
    signature = settings.email.signature.format(name=settings.profile.name)
    body = f"{body}\n\n{signature}"

    return subject, body
