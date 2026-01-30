"""YAML config loading with Pydantic validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from job_automator.config.constants import DEFAULT_CONFIG_NAME


class ProfileConfig(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    title: str = ""
    years_experience: int = 0
    skills: list[str] = Field(default_factory=list)
    resume_path: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""


class SearchConfig(BaseModel):
    default_query: str = "software engineer"
    default_location: str = "remote"
    sites: list[str] = Field(default_factory=lambda: ["linkedin", "indeed"])
    results_per_site: int = 25
    min_score: int = 60
    excluded_companies: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)


class AIConfig(BaseModel):
    provider: str = "gemini"
    model: str = ""
    api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    temperature: float = 0.7

    def get_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        env_keys = {
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        env_var = env_keys.get(self.provider, "")
        return os.environ.get(env_var, "")


class EmailConfig(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    daily_limit: int = 20
    delay_between_sends: int = 30
    signature: str = "Best regards,\n{name}"


class ApplyConfig(BaseModel):
    dry_run: bool = True
    screenshot_before_submit: bool = True
    auto_apply_threshold: int = 80
    max_daily_applications: int = 10


class DatabaseConfig(BaseModel):
    path: str = "jobs.db"


class Settings(BaseModel):
    profile: ProfileConfig = Field(default_factory=ProfileConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    apply: ApplyConfig = Field(default_factory=ApplyConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)


def get_config_path(config_dir: Optional[Path] = None) -> Path:
    if config_dir:
        return config_dir / DEFAULT_CONFIG_NAME
    return Path.cwd() / DEFAULT_CONFIG_NAME


def load_settings(config_path: Optional[Path] = None) -> Settings:
    path = config_path or get_config_path()
    if not path.exists():
        return Settings()
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return Settings(**data)


def save_settings(settings: Settings, config_path: Optional[Path] = None) -> Path:
    path = config_path or get_config_path()
    data = settings.model_dump()
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return path


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings(config_path: Optional[Path] = None) -> Settings:
    global _settings
    _settings = load_settings(config_path)
    return _settings
