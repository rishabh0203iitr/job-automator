"""AI-powered job match scoring."""

from __future__ import annotations

import json
import re

import typer

from job_automator.ai.prompts import SCORE_PROMPT, SCORE_SYSTEM
from job_automator.ai.provider import get_ai_provider
from job_automator.config.settings import get_settings
from job_automator.db.models import Job
from job_automator.db.repository import update_job_score
from job_automator.utils.display import print_error, print_info, print_success, print_warning

# Rough per-job token estimates for cost confirmation
_AVG_TOKENS_PER_JOB = 1500
_COST_PER_1K_TOKENS = {
    "gemini": 0.0001,     # Gemini Flash
    "anthropic": 0.003,   # Claude Sonnet
    "openai": 0.00015,    # GPT-4o-mini
    "ollama": 0.0,        # local
}
_CONFIRM_THRESHOLD = 10  # ask for confirmation above this many jobs


def parse_score_response(response: str) -> tuple[int, str]:
    """Parse an AI scoring response into (score, reasons).

    Handles valid JSON, markdown-wrapped JSON, and malformed responses.
    Returns (score, reasons) or raises ValueError if unparseable.
    """
    text = response.strip()

    # Strip markdown code fences
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:]
            candidate = candidate.strip()
            if candidate.startswith("{"):
                text = candidate
                break

    # Try direct JSON parse
    try:
        data = json.loads(text)
        if "score" not in data:
            raise ValueError("Missing 'score' field in response")
        score = int(data["score"])
        reasons = str(data.get("reasons", ""))
        return max(0, min(100, score)), reasons
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: try to find JSON object in the text
    match = re.search(r'\{[^{}]*"score"\s*:\s*(\d+)[^{}]*\}', text)
    if match:
        try:
            data = json.loads(match.group(0))
            score = max(0, min(100, int(data["score"])))
            reasons = str(data.get("reasons", ""))
            return score, reasons
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    raise ValueError(f"Could not parse AI response: {text[:200]}")


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
    return parse_score_response(response)


def score_jobs(jobs: list[Job], skip_confirm: bool = False) -> list[Job]:
    """Score multiple jobs and update the database."""
    if not jobs:
        return jobs

    settings = get_settings()

    # Cost confirmation for large batches
    if len(jobs) >= _CONFIRM_THRESHOLD and not skip_confirm:
        provider_name = settings.ai.provider
        cost_per_1k = _COST_PER_1K_TOKENS.get(provider_name, 0.001)
        est_cost = (len(jobs) * _AVG_TOKENS_PER_JOB / 1000) * cost_per_1k
        print_warning(
            f"About to score {len(jobs)} jobs using {provider_name} "
            f"(estimated cost: ~${est_cost:.2f})"
        )
        if not typer.confirm("Proceed?"):
            print_info("Scoring cancelled")
            return jobs

    print_info(f"Scoring {len(jobs)} jobs with AI...")

    scored = 0
    failed = 0
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
        except ValueError as e:
            failed += 1
            job.match_reasons = str(e)
            print_warning(f"  {job.title} @ {job.company}: parse error (skipped)")
        except Exception as e:
            failed += 1
            print_error(f"  Failed to score {job.title}: {e}")

    print_success(f"Scored {scored}/{len(jobs)} jobs" + (f" ({failed} failed)" if failed else ""))
    return jobs
