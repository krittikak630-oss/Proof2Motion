"""Strict, self-cleaning models for what the AI returns. Anything odd is coerced or trimmed."""
from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()[:600]


def _page(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 0 < number < 10_000 else None


def _status(value: Any) -> str:
    cleaned = str(value or "").strip().lower().replace(" ", "_")
    if cleaned in {"supported", "unsupported"}:
        return cleaned
    return "partial"


def _duration(value: Any) -> int:
    try:
        return min(max(int(value), 3), 8)
    except (TypeError, ValueError):
        return 5


def _cap(limit: int):
    return lambda value: (value if isinstance(value, list) else [])[:limit]


Text = Annotated[str, BeforeValidator(_text)]
Page = Annotated[int | None, BeforeValidator(_page)]
Status = Annotated[Literal["supported", "partial", "unsupported"], BeforeValidator(_status)]
Duration = Annotated[int, BeforeValidator(_duration)]


class Support(BaseModel):
    file: Text = ""
    quote: Text = ""
    page: Page = None
    verified: bool = False


class Claim(BaseModel):
    claim: Text = ""
    status: Status = "partial"
    support: Annotated[list[Support], BeforeValidator(_cap(5))] = []
    note: Text = ""


class Scene(BaseModel):
    scene: int = 0
    title: Text = ""
    narration: Text = ""
    visual: Text = ""
    on_screen_text: Text = ""
    duration_sec: Duration = 5


class Analysis(BaseModel):
    title: Text = "Untitled case"
    summary: Text = ""
    claims: Annotated[list[Claim], BeforeValidator(_cap(12))] = []
    gaps: Annotated[list[Text], BeforeValidator(_cap(10))] = []
    storyboard: Annotated[list[Scene], BeforeValidator(_cap(5))] = []
