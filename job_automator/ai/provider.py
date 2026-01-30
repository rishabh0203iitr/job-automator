"""Abstract AI provider and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from job_automator.config.constants import AIProvider
from job_automator.config.settings import get_settings


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "", temperature: Optional[float] = None) -> str:
        """Generate text from a prompt. Returns the generated text."""
        ...


def get_ai_provider() -> BaseAIProvider:
    """Factory function to create the configured AI provider."""
    settings = get_settings()
    provider_name = settings.ai.provider

    if provider_name == AIProvider.GEMINI.value:
        from job_automator.ai.gemini import GeminiProvider
        return GeminiProvider(
            api_key=settings.ai.get_api_key(),
            model=settings.ai.model or "gemini-2.0-flash",
            temperature=settings.ai.temperature,
        )
    elif provider_name == AIProvider.ANTHROPIC.value:
        from job_automator.ai.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=settings.ai.get_api_key(),
            model=settings.ai.model or "claude-sonnet-4-20250514",
            temperature=settings.ai.temperature,
        )
    elif provider_name == AIProvider.OPENAI.value:
        from job_automator.ai.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=settings.ai.get_api_key(),
            model=settings.ai.model or "gpt-4o-mini",
            temperature=settings.ai.temperature,
        )
    elif provider_name == AIProvider.OLLAMA.value:
        from job_automator.ai.ollama_provider import OllamaProvider
        return OllamaProvider(
            host=settings.ai.ollama_host,
            model=settings.ai.model or "llama3.1",
            temperature=settings.ai.temperature,
        )
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")
