"""Status enums and constants."""

from enum import Enum


class ApplicationStatus(str, Enum):
    DISCOVERED = "discovered"
    SCORED = "scored"
    TAILORED = "tailored"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"


class EmailStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    REPLIED = "replied"
    BOUNCED = "bounced"


class JobSource(str, Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    CUSTOM = "custom"
    TWITTER = "twitter"
    LINKEDIN_POST = "linkedin_post"


class AIProvider(str, Enum):
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


APP_NAME = "job-automator"
DEFAULT_DB_NAME = "jobs.db"
DEFAULT_CONFIG_NAME = "config.yaml"
