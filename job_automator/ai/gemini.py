"""Google Gemini AI provider."""

from __future__ import annotations

from typing import Optional

from job_automator.ai.provider import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", temperature: float = 0.7):
        if not api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY or configure in config.yaml")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str, system: str = "", temperature: Optional[float] = None) -> str:
        from google.genai import types

        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        temp = temperature if temperature is not None else self.temperature

        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(temperature=temp),
        )
        return response.text
