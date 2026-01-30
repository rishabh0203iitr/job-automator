"""Tests for email format validation."""

import pytest

from job_automator.email.sender import validate_email


class TestValidateEmail:
    def test_valid_emails(self):
        assert validate_email("user@example.com") is True
        assert validate_email("first.last@company.co.uk") is True
        assert validate_email("dev+tag@gmail.com") is True
        assert validate_email("user123@test.io") is True

    def test_invalid_emails(self):
        assert validate_email("") is False
        assert validate_email("notanemail") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user@.com") is False
        assert validate_email("user @example.com") is False
        assert validate_email("user@example") is False

    def test_whitespace_stripped(self):
        assert validate_email("  user@example.com  ") is True
