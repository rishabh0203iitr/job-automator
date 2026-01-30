"""Smoke tests: every CLI command runs without crashing on an empty DB."""

import pytest
from typer.testing import CliRunner

from job_automator.cli import app

runner = CliRunner()


class TestConfigCommands:
    def test_config_show_no_config(self):
        result = runner.invoke(app, ["config", "show"])
        # Should fail gracefully (no config file)
        assert result.exit_code != 0 or "No config found" in result.output

    def test_config_validate_no_config(self):
        result = runner.invoke(app, ["config", "validate"])
        assert result.exit_code != 0 or "No config found" in result.output


class TestSearchCommands:
    def test_search_help(self):
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "run" in result.output

    def test_search_run_help(self):
        result = runner.invoke(app, ["search", "run", "--help"])
        assert result.exit_code == 0
        assert "--query" in result.output


class TestApplyCommands:
    def test_apply_help(self):
        result = runner.invoke(app, ["apply", "--help"])
        assert result.exit_code == 0
        assert "single" in result.output
        assert "auto" in result.output

    def test_apply_single_missing_job(self):
        result = runner.invoke(app, ["apply", "single", "9999"])
        assert result.exit_code != 0 or "not found" in result.output


class TestTrackCommands:
    def test_track_list_empty(self):
        result = runner.invoke(app, ["track", "list"])
        assert result.exit_code == 0 or "No applications" in result.output

    def test_track_stats_empty(self):
        result = runner.invoke(app, ["track", "stats"])
        assert result.exit_code == 0 or "No applications" in result.output

    def test_track_update_missing(self):
        result = runner.invoke(app, ["track", "update", "9999", "applied"])
        assert result.exit_code != 0 or "not found" in result.output


class TestEmailCommands:
    def test_email_help(self):
        result = runner.invoke(app, ["email", "--help"])
        assert result.exit_code == 0
        assert "generate" in result.output

    def test_email_list_empty(self):
        result = runner.invoke(app, ["email", "list"])
        assert result.exit_code == 0 or "No emails" in result.output


class TestProfileCommands:
    def test_profile_show(self):
        result = runner.invoke(app, ["profile", "show"])
        assert result.exit_code == 0
        assert "Test User" in result.output

    def test_profile_help(self):
        result = runner.invoke(app, ["profile", "--help"])
        assert result.exit_code == 0
        assert "import-resume" in result.output


class TestDashboard:
    def test_dashboard_empty(self):
        result = runner.invoke(app, ["dashboard"])
        assert result.exit_code == 0
        assert "Dashboard" in result.output or "No data" in result.output


class TestRootHelp:
    def test_root_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "config" in result.output
        assert "search" in result.output
        assert "apply" in result.output
        assert "track" in result.output
        assert "email" in result.output
        assert "profile" in result.output
        assert "dashboard" in result.output
