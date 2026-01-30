"""Tests for database CRUD operations and deduplication."""

import pytest

from job_automator.config.constants import ApplicationStatus, EmailStatus
from job_automator.db.models import Application, ColdEmail, Job, SocialPost
from job_automator.db.repository import (
    count_applications,
    count_applications_today,
    count_emails_sent_today,
    count_jobs,
    get_application,
    get_application_by_job,
    get_cold_email,
    get_job,
    insert_application,
    insert_cold_email,
    insert_job,
    insert_social_post,
    job_exists_by_url,
    list_applications,
    list_cold_emails,
    list_jobs,
    list_social_posts,
    social_post_exists,
    update_application_materials,
    update_application_status,
    update_cold_email_status,
    update_job_score,
)
from job_automator.scrapers.base import JobListing
from job_automator.utils.dedup import deduplicate_listings, normalize_url


# --- Jobs CRUD ---

class TestJobsCRUD:
    def test_insert_and_get(self):
        job = Job(title="Engineer", company="Acme", url="https://acme.com/jobs/1")
        job_id = insert_job(job)
        assert job_id > 0

        fetched = get_job(job_id)
        assert fetched is not None
        assert fetched.title == "Engineer"
        assert fetched.company == "Acme"

    def test_get_nonexistent(self):
        assert get_job(9999) is None

    def test_list_jobs_empty(self):
        assert list_jobs() == []

    def test_list_jobs_with_filters(self):
        insert_job(Job(title="A", company="X", source="linkedin", match_score=90))
        insert_job(Job(title="B", company="Y", source="indeed", match_score=40))
        insert_job(Job(title="C", company="X", source="linkedin", match_score=70))

        assert len(list_jobs()) == 3
        assert len(list_jobs(source="linkedin")) == 2
        assert len(list_jobs(min_score=60)) == 2
        assert len(list_jobs(company="X")) == 2
        assert len(list_jobs(source="linkedin", min_score=80)) == 1

    def test_list_jobs_ordering(self):
        insert_job(Job(title="Low", company="A", match_score=20))
        insert_job(Job(title="High", company="B", match_score=95))
        insert_job(Job(title="Mid", company="C", match_score=60))

        jobs = list_jobs()
        assert jobs[0].title == "High"
        assert jobs[1].title == "Mid"
        assert jobs[2].title == "Low"

    def test_update_score(self):
        job_id = insert_job(Job(title="Test", company="Co"))
        update_job_score(job_id, 85, "Great match")

        job = get_job(job_id)
        assert job.match_score == 85
        assert job.match_reasons == "Great match"

    def test_job_exists_by_url(self):
        insert_job(Job(title="X", company="Y", url="https://example.com/1"))
        assert job_exists_by_url("https://example.com/1") is True
        assert job_exists_by_url("https://example.com/2") is False

    def test_count_jobs(self):
        assert count_jobs() == 0
        insert_job(Job(title="A", company="X", source="linkedin"))
        insert_job(Job(title="B", company="Y", source="indeed"))
        assert count_jobs() == 2
        assert count_jobs(source="linkedin") == 1

    def test_list_jobs_limit_offset(self):
        for i in range(5):
            insert_job(Job(title=f"Job {i}", company="Co", match_score=i * 10))
        assert len(list_jobs(limit=2)) == 2
        assert len(list_jobs(limit=10, offset=3)) == 2


# --- Applications CRUD ---

class TestApplicationsCRUD:
    def _make_job(self) -> int:
        return insert_job(Job(title="Eng", company="Co"))

    def test_insert_and_get(self):
        job_id = self._make_job()
        app = Application(job_id=job_id, status=ApplicationStatus.DISCOVERED.value)
        app_id = insert_application(app)

        fetched = get_application(app_id)
        assert fetched is not None
        assert fetched.job_id == job_id
        assert fetched.status == "discovered"

    def test_get_by_job(self):
        job_id = self._make_job()
        insert_application(Application(job_id=job_id))
        assert get_application_by_job(job_id) is not None
        assert get_application_by_job(9999) is None

    def test_update_status(self):
        job_id = self._make_job()
        app_id = insert_application(Application(job_id=job_id))
        update_application_status(app_id, ApplicationStatus.APPLIED.value, "Submitted via portal")

        app = get_application(app_id)
        assert app.status == "applied"
        assert app.notes == "Submitted via portal"

    def test_update_materials(self):
        job_id = self._make_job()
        app_id = insert_application(Application(job_id=job_id))
        update_application_materials(app_id, resume_path="/tmp/resume.pdf", cover_letter="Dear...")

        app = get_application(app_id)
        assert app.resume_path == "/tmp/resume.pdf"
        assert app.cover_letter == "Dear..."

    def test_count_and_list(self):
        job_id = self._make_job()
        insert_application(Application(job_id=job_id, status="applied"))
        insert_application(Application(job_id=self._make_job(), status="discovered"))

        assert count_applications() == 2
        assert count_applications(status="applied") == 1
        assert len(list_applications(status="applied")) == 1


# --- Cold Emails CRUD ---

class TestColdEmailsCRUD:
    def test_insert_and_get(self):
        email = ColdEmail(
            recipient_name="Jane", recipient_email="jane@co.com",
            company="Co", subject="Hi", body="Hello",
        )
        eid = insert_cold_email(email)
        fetched = get_cold_email(eid)
        assert fetched.recipient_name == "Jane"
        assert fetched.status == "draft"

    def test_update_status(self):
        eid = insert_cold_email(ColdEmail(recipient_email="a@b.com", company="X"))
        update_cold_email_status(eid, EmailStatus.SENT.value, sent_at="2025-01-01T00:00:00")

        email = get_cold_email(eid)
        assert email.status == "sent"
        assert email.sent_at == "2025-01-01T00:00:00"

    def test_list_with_filter(self):
        insert_cold_email(ColdEmail(status="draft", company="A"))
        insert_cold_email(ColdEmail(status="sent", company="B"))
        assert len(list_cold_emails()) == 2
        assert len(list_cold_emails(status="draft")) == 1


# --- Social Posts CRUD ---

class TestSocialPostsCRUD:
    def test_insert_and_exists(self):
        post = SocialPost(platform="twitter", post_url="https://twitter.com/1", author="bob")
        insert_social_post(post)
        assert social_post_exists("https://twitter.com/1") is True
        assert social_post_exists("https://twitter.com/2") is False

    def test_list(self):
        insert_social_post(SocialPost(platform="twitter", post_url="t/1"))
        insert_social_post(SocialPost(platform="linkedin_post", post_url="l/1"))
        assert len(list_social_posts()) == 2
        assert len(list_social_posts(platform="twitter")) == 1


# --- URL Normalization ---

class TestNormalizeUrl:
    def test_strips_tracking_params(self):
        url = "https://linkedin.com/jobs/123?utm_source=google&utm_medium=cpc&trk=abc"
        assert normalize_url(url) == "https://linkedin.com/jobs/123"

    def test_keeps_meaningful_params(self):
        url = "https://lever.co/jobs?team=engineering&location=remote"
        result = normalize_url(url)
        assert "team=engineering" in result
        assert "location=remote" in result

    def test_strips_fragment(self):
        url = "https://example.com/jobs/1#apply"
        assert normalize_url(url) == "https://example.com/jobs/1"

    def test_empty_url(self):
        assert normalize_url("") == ""

    def test_no_params(self):
        url = "https://example.com/jobs/1"
        assert normalize_url(url) == "https://example.com/jobs/1"

    def test_mixed_params(self):
        url = "https://example.com/job?id=42&utm_source=twitter&ref=abc"
        result = normalize_url(url)
        assert "id=42" in result
        assert "utm_source" not in result
        assert "ref=" not in result


# --- Deduplication ---

class TestDeduplicate:
    def test_removes_url_duplicates_in_batch(self):
        listings = [
            JobListing(title="A", company="X", url="https://example.com/1"),
            JobListing(title="B", company="Y", url="https://example.com/1"),
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1
        assert result[0].title == "A"

    def test_removes_title_company_duplicates(self):
        listings = [
            JobListing(title="Engineer", company="Acme", url="https://a.com"),
            JobListing(title="engineer", company="ACME", url="https://b.com"),
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1

    def test_removes_tracking_param_duplicates(self):
        listings = [
            JobListing(title="A", company="X", url="https://example.com/1"),
            JobListing(title="B", company="Y", url="https://example.com/1?utm_source=google&trk=abc"),
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1

    def test_keeps_genuinely_different_jobs(self):
        listings = [
            JobListing(title="Frontend", company="Acme", url="https://a.com/1"),
            JobListing(title="Backend", company="Acme", url="https://a.com/2"),
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 2

    def test_skips_jobs_already_in_db(self):
        insert_job(Job(title="Existing", company="Co", url="https://example.com/existing"))
        listings = [
            JobListing(title="Existing", company="Co", url="https://example.com/existing"),
            JobListing(title="New", company="Other", url="https://example.com/new"),
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 1
        assert result[0].title == "New"

    def test_empty_list(self):
        assert deduplicate_listings([]) == []

    def test_listings_without_urls(self):
        listings = [
            JobListing(title="A", company="X", url=""),
            JobListing(title="B", company="Y", url=""),
        ]
        result = deduplicate_listings(listings)
        assert len(result) == 2
