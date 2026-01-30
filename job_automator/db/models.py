"""Data models for the database."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from job_automator.config.constants import ApplicationStatus, EmailStatus


@dataclass
class Job:
    id: Optional[int] = None
    source: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    salary: str = ""
    match_score: Optional[int] = None
    match_reasons: str = ""
    date_posted: Optional[str] = None
    date_discovered: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_data: str = ""


@dataclass
class Application:
    id: Optional[int] = None
    job_id: int = 0
    status: str = ApplicationStatus.DISCOVERED.value
    resume_path: str = ""
    cover_letter: str = ""
    notes: str = ""
    applied_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ColdEmail:
    id: Optional[int] = None
    job_id: Optional[int] = None
    recipient_name: str = ""
    recipient_email: str = ""
    recipient_title: str = ""
    company: str = ""
    subject: str = ""
    body: str = ""
    status: str = EmailStatus.DRAFT.value
    sent_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SocialPost:
    id: Optional[int] = None
    platform: str = ""
    post_url: str = ""
    author: str = ""
    content: str = ""
    extracted_info: str = ""
    job_id: Optional[int] = None
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
