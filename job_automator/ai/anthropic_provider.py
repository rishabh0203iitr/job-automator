"""Anthropic Claude AI provider."""

from __future__ import annotations

from typing import Optional

from job_automator.ai.provider import BaseAIProvider


class AnthropicProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", temperature: float = 0.7):
        if not api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY or configure in config.yaml")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, system: str = "", temperature: Optional[float] = None) -> str:
        temp = temperature if temperature is not None else self.temperature

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temp,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text
