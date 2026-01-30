"""AI-powered job match scoring."""

from __future__ import annotations

import json

from job_automator.ai.prompts import SCORE_PROMPT, SCORE_SYSTEM
from job_automator.ai.provider import get_ai_provider
from job_automator.config.settings import get_settings
from job_automator.db.models import Job
from job_automator.db.repository import update_job_score
from job_automator.utils.display import print_error, print_info, print_success


def score_single_job(job: Job) -> tuple[int, str]:
    """Score a single job against the user's profile. Returns (score, reasons)."""
    settings = get_settings()
    provider = get_ai_provider()

    prompt = SCORE_PROMPT.format(
        name=settings.profile.name,
        title=settings.profile.title,
        years_experience=settings.profile.years_experience,
        skills=", ".join(settings.profile.skills),
        location=settings.profile.location,
        job_title=job.title,
        job_company=job.company,
        job_location=job.location or "Not specified",
        job_salary=job.salary or "Not specified",
        job_description=(job.description or "No description available")[:3000],
    )

    response = provider.generate(prompt, system=SCORE_SYSTEM, temperature=0.3)

    # Parse JSON response
    try:
        # Try to extract JSON from response
        text = response.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        score = max(0, min(100, int(data.get("score", 0))))
        reasons = data.get("reasons", "")
        return score, reasons
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback: try to find score in raw text
        return 50, f"Could not parse AI response: {response[:200]}"


def score_jobs(jobs: list[Job]) -> list[Job]:
    """Score multiple jobs and update the database."""
    print_info(f"Scoring {len(jobs)} jobs with AI...")

    scored = 0
    for job in jobs:
        if job.id is None:
            continue
        try:
            score, reasons = score_single_job(job)
            update_job_score(job.id, score, reasons)
            job.match_score = score
            job.match_reasons = reasons
            scored += 1
            print_info(f"  {job.title} @ {job.company}: {score}/100")
        except Exception as e:
            print_error(f"  Failed to score {job.title}: {e}")

    print_success(f"Scored {scored}/{len(jobs)} jobs")
    return jobs
