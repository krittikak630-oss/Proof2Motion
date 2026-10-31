"""Check every quote the AI returns against the uploaded text. Unverifiable proof is flagged."""
from __future__ import annotations

import json
import re

from pydantic import ValidationError

from .schemas import Analysis

_QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"})


class ParseError(Exception):
    """The model did not return usable JSON."""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_QUOTES)).strip().lower()


def parse_analysis(raw: str) -> Analysis:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip(), flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ParseError("no JSON object in model output")
    try:
        data = json.loads(cleaned[start : end + 1])
        analysis = Analysis.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ParseError(str(exc)[:200]) from exc
    analysis.claims = [c for c in analysis.claims if c.claim]
    if not analysis.summary and not analysis.claims:
        raise ParseError("empty analysis")
    for index, scene in enumerate(analysis.storyboard, start=1):
        scene.scene = index
    return analysis


def _quote_in(quote: str, haystack: str) -> bool:
    segments = [s.strip(" .\"'") for s in re.split(r"\.\.\.|\u2026", _norm(quote))]
    segments = [s for s in segments if s]
    return bool(segments) and all(len(s) >= 6 and s in haystack for s in segments)


def verify_quotes(analysis: Analysis, corpus: dict[str, str]) -> dict[str, int]:
    """Marks each quote verified/unverified, fixes file names, downgrades unproven 'supported' claims."""
    normalised = {name: _norm(text) for name, text in corpus.items()}
    verified = total = 0
    for claim in analysis.claims:
        for support in claim.support:
            total += 1
            candidates = [support.file] if support.file in normalised else []
            candidates += [n for n in normalised if n not in candidates]
            for name in candidates:
                if _quote_in(support.quote, normalised[name]):
                    support.verified, support.file = True, name
                    verified += 1
                    break
        if claim.status == "supported" and not any(s.verified for s in claim.support):
            claim.status = "partial"
            claim.note = "Downgraded: no quote for this claim could be found in your files."
    return {"verified": verified, "total": total}
