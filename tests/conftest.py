"""Shared test fixtures."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from job_automator.config.settings import Settings
from job_automator.db import engine as db_engine


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path):
    """Give every test its own in-memory SQLite database."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(db_engine.SCHEMA)

    # Patch get_connection to return our in-memory DB
    db_engine._connection = conn
    yield conn
    conn.close()
    db_engine._connection = None


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path):
    """Give every test a fresh default Settings instance."""
    import job_automator.config.settings as settings_mod

    s = Settings()
    s.profile.name = "Test User"
    s.profile.email = "test@example.com"
    s.profile.title = "Software Engineer"
    s.profile.skills = ["Python", "SQL"]
    s.profile.years_experience = 3
    s.profile.location = "remote"
    s.database.path = str(tmp_path / "test.db")

    settings_mod._settings = s
    yield s
    settings_mod._settings = None
