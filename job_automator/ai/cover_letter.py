"""AI-powered cover letter generation."""

from __future__ import annotations

from pathlib import Path

from job_automator.ai.prompts import COVER_LETTER_PROMPT, COVER_LETTER_SYSTEM
from job_automator.ai.provider import get_ai_provider
from job_automator.config.settings import get_settings
from job_automator.db.models import Job
from job_automator.utils.resume_parser import extract_text


def generate_cover_letter(job: Job, resume_path: str = "") -> str:
    """Generate a cover letter for a specific job application."""
    settings = get_settings()
    provider = get_ai_provider()

    resume_text = ""
    rpath = resume_path or settings.profile.resume_path
    if rpath:
        try:
            resume_text = extract_text(rpath)
        except Exception:
            resume_text = "Resume not available"

    prompt = COVER_LETTER_PROMPT.format(
        name=settings.profile.name,
        title=settings.profile.title,
        skills=", ".join(settings.profile.skills),
        years_experience=settings.profile.years_experience,
        resume_text=(resume_text or "Not provided")[:2000],
        job_title=job.title,
        job_company=job.company,
        job_description=(job.description or "No description")[:3000],
    )

    return provider.generate(prompt, system=COVER_LETTER_SYSTEM, temperature=0.7)


def save_cover_letter(content: str, job: Job, output_dir: str = "output") -> Path:
    """Save cover letter to a file."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    safe_company = "".join(c if c.isalnum() or c in "-_ " else "" for c in job.company).strip()
    filename = f"cover_letter_{safe_company}.txt"

    path = out / filename
    path.write_text(content)
    return path
