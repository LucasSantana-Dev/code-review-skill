"""Anthropic BYOK adapter (ADR-0014/0017) — validated first in Phase 0.

Stdlib `urllib` only (ADR-0011). Uses a forced tool call to get schema-valid
structured output (Anthropic constrained decoding). Reads the API key from the
env var named by config.api_key_env. Network + key required to actually run;
the pipeline is exercised key-free via the mock adapter.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ..models import ReviewResponse, finding_from_dict
from .base import REVIEW_SCHEMA, ModelAdapter

DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
_TOOL_NAME = "report_review"


class AnthropicAdapter(ModelAdapter):
    name = "anthropic"

    def review(self, system_prompt: str, diff_context: str) -> ReviewResponse:
        key = os.environ.get(self.config.api_key_env)
        if not key:
            raise RuntimeError(
                f"no API key in ${self.config.api_key_env}; set it or use --provider mock"
            )
        endpoint = self.config.api_endpoint or DEFAULT_ENDPOINT
        payload = {
            "model": self.config.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": diff_context}],
            "tools": [{
                "name": _TOOL_NAME,
                "description": "Report the structured code review.",
                "input_schema": REVIEW_SCHEMA,
            }],
            "tool_choice": {"type": "tool", "name": _TOOL_NAME},
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": key,
                "anthropic-version": ANTHROPIC_VERSION,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:  # pragma: no cover - network path
            detail = e.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"Anthropic API {e.code}: {detail}") from e

        review = _extract_tool_input(data)
        findings = [finding_from_dict(f, default_source=f"llm:{f.get('dimension', 'review')}")
                    for f in review.get("findings", [])]
        return ReviewResponse(
            findings=findings,
            summary=review.get("summary", ""),
            verdict=review.get("verdict", "approve-with-nits"),
            usage=data.get("usage", {}),
        )


def _extract_tool_input(data: dict) -> dict:
    """Pull the forced tool_use input out of a Messages API response."""
    for block in data.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == _TOOL_NAME:
            return block.get("input", {}) or {}
    # Fallback: some compatible endpoints return text JSON.
    for block in data.get("content", []):
        if block.get("type") == "text":
            try:
                return json.loads(block.get("text", "{}"))
            except json.JSONDecodeError:
                pass
    return {"verdict": "approve", "summary": "", "findings": []}
