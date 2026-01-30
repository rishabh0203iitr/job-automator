"""LinkedIn Easy Apply automation."""

from __future__ import annotations

from job_automator.config.settings import get_settings
from job_automator.db.models import Job
from job_automator.utils.display import print_error, print_info, print_success, print_warning


def easy_apply(job: Job, resume_path: str) -> bool:
    """Attempt LinkedIn Easy Apply for a job.

    Requires the user to be logged into LinkedIn in the browser session.
    Uses Playwright with a persistent browser context for session reuse.

    Returns True if application was submitted.
    """
    from playwright.sync_api import sync_playwright

    if not job.url or "linkedin.com" not in job.url:
        print_error("Not a LinkedIn job URL")
        return False

    settings = get_settings()

    with sync_playwright() as p:
        # Use persistent context to reuse LinkedIn session
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(_get_browser_profile_dir()),
            headless=False,
        )
        page = context.new_page()

        try:
            page.goto(job.url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # Check if logged in
            if page.locator("button:has-text('Sign in')").is_visible(timeout=2000):
                print_warning("Not logged into LinkedIn. Please log in manually.")
                print_info("Waiting 60 seconds for manual login...")
                page.wait_for_timeout(60000)

            # Click Easy Apply
            easy_apply_btn = page.locator("button:has-text('Easy Apply')").first
            if not easy_apply_btn.is_visible(timeout=5000):
                print_warning("Easy Apply button not found. This job may require external application.")
                return False

            easy_apply_btn.click()
            page.wait_for_timeout(2000)

            # Navigate through Easy Apply modal steps
            max_steps = 10
            for step in range(max_steps):
                # Check for review/submit
                submit_btn = page.locator("button:has-text('Submit application')").first
                if submit_btn.is_visible(timeout=1000):
                    if settings.apply.dry_run:
                        print_warning("Dry run - not submitting")
                        _screenshot(page, job)
                        return False
                    submit_btn.click()
                    page.wait_for_timeout(2000)
                    print_success("Easy Apply submitted!")
                    return True

                # Upload resume if prompted
                file_input = page.locator("input[type='file']").first
                if file_input.count() > 0:
                    try:
                        file_input.set_input_files(resume_path)
                        print_info("Resume uploaded")
                    except Exception:
                        pass

                # Fill any required fields
                _fill_required_fields(page, settings)

                # Click Next/Continue
                next_btn = page.locator(
                    "button:has-text('Next'), button:has-text('Continue'), button:has-text('Review')"
                ).first
                if next_btn.is_visible(timeout=2000):
                    next_btn.click()
                    page.wait_for_timeout(1500)
                else:
                    break

            print_warning("Could not complete Easy Apply flow")
            _screenshot(page, job)
            return False

        except Exception as e:
            print_error(f"Easy Apply error: {e}")
            return False
        finally:
            context.close()


def _fill_required_fields(page, settings):
    """Fill required fields in Easy Apply modal."""
    # Phone number
    try:
        phone = page.locator("input[name*='phone' i], input[id*='phone' i]").first
        if phone.is_visible(timeout=500) and not phone.input_value():
            phone.fill(settings.profile.phone)
    except Exception:
        pass

    # City/Location
    try:
        city = page.locator("input[name*='city' i], input[id*='city' i]").first
        if city.is_visible(timeout=500) and not city.input_value():
            city.fill(settings.profile.location)
    except Exception:
        pass


def _screenshot(page, job: Job):
    """Take a screenshot of the current state."""
    from pathlib import Path
    ss_path = Path("output") / f"easy_apply_{job.id}.png"
    ss_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ss_path), full_page=True)
    print_info(f"Screenshot: {ss_path}")


def _get_browser_profile_dir():
    from pathlib import Path
    profile_dir = Path.home() / ".job-automator" / "browser-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir
