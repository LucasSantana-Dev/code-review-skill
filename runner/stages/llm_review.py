"""Stage 3 — LLM review (ADR-0017).

Assemble the per-dimension system prompt from the existing judgment layer
(SKILL.md/REFERENCE.md via the bundled prompt templates + the ADR-0002 rubric),
hand the scoped diff to the provider adapter, and return structured findings.
Phase 0: serial, single batched call over the enabled dimensions (ADR-0019).
"""
from __future__ import annotations

from pathlib import Path

from .scope import build_diff_context

_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def _read(name: str) -> str:
    p = _PROMPTS / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build_system_prompt(dimensions, prefilter_findings) -> str:
    parts = [_read("_rubric.md")]
    for dim in dimensions:
        body = _read(f"{dim}.md")
        if body:
            parts.append(body)
    if prefilter_findings:
        already = "\n".join(
            f"- {f.path}:{f.line} {f.title}" for f in prefilter_findings
        )
        parts.append("## Already reported by deterministic tools — DO NOT re-flag\n" + already)
    else:
        parts.append("## Already reported by deterministic tools — DO NOT re-flag\n(none — pre-filter is Phase 1)")
    parts.append(
        "## Output\nReturn the structured review (verdict, summary, findings). "
        "Tag every finding with dimension, evidence_type, and confidence. Only mark "
        "`factual` with a cited file:line needing no runtime context; reframe "
        "confidence < 0.5 findings as questions."
    )
    return "\n\n".join(p for p in parts if p.strip())


def review(ctx, adapter):
    """Run the model over the scoped diff; returns a ReviewResponse."""
    system_prompt = build_system_prompt(ctx.config.dimensions, ctx.prefilter_findings)
    diff_context = build_diff_context(ctx.hunks)
    return adapter.review(system_prompt, diff_context)
