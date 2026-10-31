"""Runtime configuration, read from environment variables (and backend/.env in development)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_MODEL = "gemma-4-31b-it"


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    api_key: str = ""
    model: str = DEFAULT_MODEL
    # Gemma 4 first. Fallbacks only run if Gemma is unavailable, so a demo never dies.
    fallback_models: tuple[str, ...] = ("gemma-4-26b-a4b-it", "gemini-2.5-flash")
    environment: str = "development"
    allowed_origins: tuple[str, ...] = ()
    max_files: int = 5
    max_file_bytes: int = 5 * 1024 * 1024
    max_pdf_pages: int = 50
    max_chars_per_file: int = 12_000
    max_chars_total: int = 30_000
    rate_limit_per_minute: int = 8
    model_timeout_s: int = 90
    trust_proxy: bool = False
    dist_dir: Path = ROOT_DIR / "frontend" / "dist"
    sample_file: Path = ROOT_DIR / "samples" / "sample_evidence.txt"

    @property
    def models(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.model, *self.fallback_models)))

    @property
    def production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def has_key(self) -> bool:
        return bool(self.api_key) and self.api_key != "your_key_here"

    @property
    def max_request_bytes(self) -> int:
        return self.max_files * self.max_file_bytes + 1_000_000


def load_settings() -> Settings:
    origins = tuple(o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip())
    return Settings(
        api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        model=os.getenv("MODEL", "").strip() or DEFAULT_MODEL,
        environment=os.getenv("ENVIRONMENT", "development").strip(),
        allowed_origins=origins,
        max_files=_int("MAX_FILES", 5),
        max_file_bytes=_int("MAX_FILE_MB", 5) * 1024 * 1024,
        rate_limit_per_minute=_int("RATE_LIMIT_PER_MINUTE", 8),
        trust_proxy=_bool("TRUST_PROXY"),
    )
