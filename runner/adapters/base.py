"""Provider-agnostic model-adapter contract (ADR-0014).

Isolates auth / request shape / structured-output / retries from the pipeline.
BYOK frontier first (Anthropic validated first); Ollama is the free fallback (P3).
"""
from __future__ import annotations

import abc

from ..models import ReviewConfig, ReviewResponse

# JSON schema the LLM must conform to for each finding (ADR-0013 / Phase-0 spec).
FINDING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["path", "line", "severity", "title", "body",
                 "dimension", "evidence_type", "confidence"],
    "properties": {
        "path": {"type": "string"},
        "line": {"type": "integer"},
        "end_line": {"type": "integer"},
        "severity": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "suggestion": {"type": "string"},
        "dimension": {"type": "string"},
        "evidence_type": {"type": "string",
                          "enum": ["factual", "behavioral", "speculative"]},
        "confidence": {"type": "number"},
    },
}

REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdict", "summary", "findings"],
    "properties": {
        "verdict": {"type": "string",
                    "enum": ["approve", "approve-with-nits", "changes-required"]},
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": FINDING_SCHEMA},
    },
}


class ModelAdapter(abc.ABC):
    """One review call: system prompt + diff context -> structured findings."""

    name = "base"

    def __init__(self, config: ReviewConfig):
        self.config = config

    @abc.abstractmethod
    def review(self, system_prompt: str, diff_context: str) -> ReviewResponse:
        """Return a ReviewResponse with Finding objects parsed from the model."""
        raise NotImplementedError

    def estimate_tokens(self, text: str) -> int:
        """Rough heuristic (~4 chars/token); good enough for budget guards."""
        return max(1, len(text) // 4)
