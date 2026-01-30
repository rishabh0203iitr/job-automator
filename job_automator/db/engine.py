"""SQLite database setup and migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from job_automator.config.settings import get_settings

_connection: Optional[sqlite3.Connection] = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    salary TEXT NOT NULL DEFAULT '',
    match_score INTEGER,
    match_reasons TEXT NOT NULL DEFAULT '',
    date_posted TEXT,
    date_discovered TEXT NOT NULL,
    raw_data TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'discovered',
    resume_path TEXT NOT NULL DEFAULT '',
    cover_letter TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    applied_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS cold_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    recipient_name TEXT NOT NULL DEFAULT '',
    recipient_email TEXT NOT NULL DEFAULT '',
    recipient_title TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    sent_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS social_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL DEFAULT '',
    post_url TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    extracted_info TEXT NOT NULL DEFAULT '',
    job_id INTEGER,
    discovered_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(match_score);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_cold_emails_status ON cold_emails(status);
"""


def get_db_path() -> Path:
    settings = get_settings()
    return Path(settings.database.path)


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    global _connection
    if _connection is not None:
        return _connection

    path = db_path or get_db_path()
    _connection = sqlite3.connect(str(path))
    _connection.row_factory = sqlite3.Row
    _connection.execute("PRAGMA journal_mode=WAL")
    _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def init_db(db_path: Optional[Path] = None) -> Path:
    path = db_path or get_db_path()
    conn = get_connection(path)
    conn.executescript(SCHEMA)
    conn.commit()
    return path


def close_db():
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
