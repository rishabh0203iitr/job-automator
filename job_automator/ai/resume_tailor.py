"""AI-powered resume tailoring for specific job applications."""

from __future__ import annotations

from pathlib import Path

from job_automator.ai.prompts import TAILOR_PROMPT, TAILOR_SYSTEM
from job_automator.ai.provider import get_ai_provider
from job_automator.db.models import Job
from job_automator.utils.resume_parser import extract_text


def tailor_resume(job: Job, resume_path: str) -> str:
    """Generate a tailored resume for a specific job.

    Returns the tailored resume text content.
    """
    resume_text = extract_text(resume_path)
    provider = get_ai_provider()

    prompt = TAILOR_PROMPT.format(
        resume_text=resume_text,
        job_title=job.title,
        job_company=job.company,
        job_description=(job.description or "No description")[:3000],
    )

    return provider.generate(prompt, system=TAILOR_SYSTEM, temperature=0.5)


def save_tailored_resume(content: str, job: Job, output_dir: str = "output") -> Path:
    """Save tailored resume content to a file."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    safe_company = "".join(c if c.isalnum() or c in "-_ " else "" for c in job.company).strip()
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in job.title).strip()
    filename = f"resume_{safe_company}_{safe_title}.txt"

    path = out / filename
    path.write_text(content)
    return path
