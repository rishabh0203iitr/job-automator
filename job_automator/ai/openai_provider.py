"""OpenAI AI provider."""

from __future__ import annotations

from typing import Optional

from job_automator.ai.provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.7):
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or configure in config.yaml")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, system: str = "", temperature: Optional[float] = None) -> str:
        temp = temperature if temperature is not None else self.temperature

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temp,
        )
        return response.choices[0].message.content
