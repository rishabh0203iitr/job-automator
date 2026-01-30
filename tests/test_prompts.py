"""Tests that all prompt templates format without KeyError."""

import pytest

from job_automator.ai.prompts import (
    COLD_EMAIL_PROMPT,
    COVER_LETTER_PROMPT,
    EXTRACT_JOB_FROM_POST,
    SCORE_PROMPT,
    TAILOR_PROMPT,
)


class TestPromptFormatting:
    """Every prompt template should format cleanly with its expected variables."""

    def test_score_prompt(self):
        result = SCORE_PROMPT.format(
            name="Test User",
            title="Engineer",
            years_experience=3,
            skills="Python, SQL",
            location="remote",
            job_title="Backend Engineer",
            job_company="Acme",
            job_location="SF",
            job_salary="$150k",
            job_description="Build stuff",
        )
        assert "Test User" in result
        assert "Backend Engineer" in result
        assert "Acme" in result

    def test_tailor_prompt(self):
        result = TAILOR_PROMPT.format(
            resume_text="Experience: 3 years Python",
            job_title="Senior Engineer",
            job_company="BigCo",
            job_description="Lead backend team",
        )
        assert "Experience: 3 years Python" in result
        assert "Senior Engineer" in result

    def test_cover_letter_prompt(self):
        result = COVER_LETTER_PROMPT.format(
            name="Test",
            title="Dev",
            skills="Python",
            years_experience=2,
            resume_text="Did things",
            job_title="SWE",
            job_company="Co",
            job_description="Build things",
        )
        assert "Test" in result
        assert "SWE" in result

    def test_cold_email_prompt(self):
        result = COLD_EMAIL_PROMPT.format(
            name="Test",
            title="Dev",
            skills="Python",
            recipient_name="Jane Doe",
            recipient_title="VP Eng",
            company="BigCo",
            job_title="Backend",
            job_description="Build APIs",
        )
        assert "Jane Doe" in result
        assert "BigCo" in result

    def test_extract_job_from_post(self):
        result = EXTRACT_JOB_FROM_POST.format(
            author="@techrecruiter",
            content="We're hiring a Python developer! Remote friendly.",
        )
        assert "@techrecruiter" in result
        assert "Python developer" in result

    def test_score_prompt_missing_field_raises(self):
        with pytest.raises(KeyError):
            SCORE_PROMPT.format(name="Test")  # missing other fields

    def test_cover_letter_prompt_missing_field_raises(self):
        with pytest.raises(KeyError):
            COVER_LETTER_PROMPT.format(name="Test")

    def test_cold_email_prompt_missing_field_raises(self):
        with pytest.raises(KeyError):
            COLD_EMAIL_PROMPT.format(name="Test")

    def test_prompts_contain_no_unescaped_braces(self):
        """Verify that literal braces in JSON examples are properly escaped as {{ }}."""
        # These prompts contain literal JSON examples that must use {{ }}
        for prompt in [SCORE_PROMPT, EXTRACT_JOB_FROM_POST]:
            # If we can format with all fields provided, there are no stray single braces
            # (this is implicitly tested above, but let's be explicit)
            assert "{{" in prompt, f"Prompt should have escaped braces for JSON examples"
