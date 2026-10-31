"""Gemma 4 (open weights) through the Gemini API, with ordered fallbacks and live streaming."""
from __future__ import annotations

import logging
from collections.abc import Iterator

from .config import Settings

log = logging.getLogger("proof2motion.llm")

NO_KEY_MESSAGE = "The server has no GEMINI_API_KEY. Add it to backend/.env and restart."


class LLMError(Exception):
    """All models failed."""


class ConfigError(LLMError):
    """The server is not configured (no API key)."""


class LLM:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @property
    def ready(self) -> bool:
        return self.settings.has_key

    def _get_client(self):
        if not self.ready:
            raise ConfigError(NO_KEY_MESSAGE)
        if self._client is None:
            from google import genai
            from google.genai import types

            try:
                options = types.HttpOptions(timeout=self.settings.model_timeout_s * 1000)
                self._client = genai.Client(api_key=self.settings.api_key, http_options=options)
            except Exception:  # noqa: BLE001 - older SDKs: fall back to defaults
                self._client = genai.Client(api_key=self.settings.api_key)
        return self._client

    def stream(self, prompt: str) -> Iterator[tuple]:
        """Yields ("progress", chars_so_far) and finally ("done", full_text, model_used)."""
        client = self._get_client()
        for model in self.settings.models:
            try:
                text = ""
                for chunk in client.models.generate_content_stream(model=model, contents=prompt):
                    text += chunk.text or ""
                    yield ("progress", len(text))
                if text.strip():
                    yield ("done", text, model)
                    return
                log.warning("model %s returned an empty response", model)
            except Exception as exc:  # noqa: BLE001
                log.warning("model %s failed: %s", model, exc)
        raise LLMError("all models failed")

    def generate(self, prompt: str) -> tuple[str, str]:
        client = self._get_client()
        for model in self.settings.models:
            try:
                text = (client.models.generate_content(model=model, contents=prompt).text or "").strip()
                if text:
                    return text, model
            except Exception as exc:  # noqa: BLE001
                log.warning("model %s failed: %s", model, exc)
        raise LLMError("all models failed")
