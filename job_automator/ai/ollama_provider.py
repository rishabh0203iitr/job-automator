"""Ollama (local) AI provider."""

from __future__ import annotations

from typing import Optional

import httpx

from job_automator.ai.provider import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.1", temperature: float = 0.7):
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature

    def generate(self, prompt: str, system: str = "", temperature: Optional[float] = None) -> str:
        temp = temperature if temperature is not None else self.temperature

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        response = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": temp},
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]
