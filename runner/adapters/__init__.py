"""Adapter registry — selects a provider impl at runtime (ADR-0014)."""
from __future__ import annotations

from ..models import ReviewConfig
from .anthropic import AnthropicAdapter
from .mock import MockAdapter

# Phase 0 ships Anthropic (BYOK, validated first) + a mock for plumbing tests.
# OpenAI-compatible (P1) and Ollama (P3) are registered as they land.
_REGISTRY = {
    "anthropic": AnthropicAdapter,
    "mock": MockAdapter,
}

_DEFERRED = {
    "openai-compatible": "OpenAI-compatible adapter is Phase 1 (ADR-0014/0019)",
    "ollama": "Ollama free-fallback adapter is Phase 3 (ADR-0014/0019)",
}


def get_adapter(config: ReviewConfig):
    provider = (config.provider or "anthropic").lower()
    if provider in _REGISTRY:
        return _REGISTRY[provider](config)
    if provider in _DEFERRED:
        raise NotImplementedError(_DEFERRED[provider])
    raise ValueError(f"unknown provider {provider!r}; known: {sorted(_REGISTRY)}")
