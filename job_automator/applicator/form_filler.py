"""Playwright-based form automation for job applications."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from job_automator.config.settings import get_settings
from job_automator.db.models import Job
from job_automator.utils.display import print_error, print_info, print_success, print_warning


def auto_apply(job: Job, resume_path: str, cover_letter: str = "") -> bool:
    """Attempt to auto-fill and submit a job application.

    Opens the job URL, attempts to find and fill the application form.
    Takes a screenshot before submission if configured.

    Returns True if application was submitted successfully.
    """
    from playwright.sync_api import sync_playwright

    if not job.url:
        print_error("No URL for this job")
        return False

    settings = get_settings()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            page.goto(job.url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            # Look for apply button
            apply_clicked = _click_apply_button(page)
            if not apply_clicked:
                print_warning("Could not find apply button. Opening page for manual review.")
                page.wait_for_timeout(5000)
                return False

            page.wait_for_timeout(2000)

            # Fill profile fields
            _fill_profile_fields(page, settings)

            # Upload resume
            _upload_resume(page, resume_path)

            # Fill cover letter if field exists
            if cover_letter:
                _fill_cover_letter(page, cover_letter)

            # Screenshot before submit
            if settings.apply.screenshot_before_submit:
                ss_path = Path("output") / f"screenshot_{job.id}.png"
                ss_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(ss_path), full_page=True)
                print_info(f"Screenshot saved: {ss_path}")

            if settings.apply.dry_run:
                print_warning("Dry run - not clicking submit")
                page.wait_for_timeout(5000)
                return False

            # Submit
            submitted = _click_submit(page)
            if submitted:
                page.wait_for_timeout(3000)
                print_success("Form submitted")
                return True
            else:
                print_warning("Could not find submit button")
                return False

        except Exception as e:
            print_error(f"Auto-apply error: {e}")
            return False
        finally:
            browser.close()


def _click_apply_button(page) -> bool:
    """Try to find and click an apply button."""
    selectors = [
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "button:has-text('Apply Now')",
        "a:has-text('Apply Now')",
        "[data-testid*='apply']",
        ".apply-button",
        "#apply-button",
    ]
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=2000):
                el.click()
                return True
        except Exception:
            continue
    return False


def _fill_profile_fields(page, settings):
    """Fill in common profile fields."""
    field_map = {
        "name": settings.profile.name,
        "full_name": settings.profile.name,
        "first_name": settings.profile.name.split()[0] if settings.profile.name else "",
        "last_name": settings.profile.name.split()[-1] if settings.profile.name and len(settings.profile.name.split()) > 1 else "",
        "email": settings.profile.email,
        "phone": settings.profile.phone,
        "linkedin": settings.profile.linkedin_url,
        "github": settings.profile.github_url,
        "portfolio": settings.profile.portfolio_url,
        "website": settings.profile.portfolio_url,
        "location": settings.profile.location,
        "city": settings.profile.location,
    }

    for field_hint, value in field_map.items():
        if not value:
            continue
        try:
            # Try by name/id attribute
            for attr in ["name", "id", "aria-label", "placeholder"]:
                selector = f"input[{attr}*='{field_hint}' i]"
                el = page.locator(selector).first
                if el.is_visible(timeout=500):
                    el.fill(value)
                    break
        except Exception:
            continue


def _upload_resume(page, resume_path: str):
    """Try to upload resume file."""
    try:
        file_input = page.locator("input[type='file']").first
        if file_input.count() > 0:
            file_input.set_input_files(resume_path)
            print_info("Resume uploaded")
    except Exception:
        print_warning("Could not upload resume automatically")


def _fill_cover_letter(page, cover_letter: str):
    """Try to fill cover letter textarea."""
    selectors = [
        "textarea[name*='cover' i]",
        "textarea[id*='cover' i]",
        "textarea[placeholder*='cover' i]",
        "textarea[name*='letter' i]",
        "textarea[aria-label*='cover' i]",
    ]
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=500):
                el.fill(cover_letter)
                print_info("Cover letter filled")
                return
        except Exception:
            continue


def _click_submit(page) -> bool:
    """Try to find and click the submit button."""
    selectors = [
        "button[type='submit']",
        "button:has-text('Submit')",
        "button:has-text('Submit Application')",
        "input[type='submit']",
        "button:has-text('Send')",
    ]
    for selector in selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=2000):
                el.click()
                return True
        except Exception:
            continue
    return False
