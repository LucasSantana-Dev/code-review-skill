"""Pipeline orchestrator (ADR-0012) — the only component that knows stage order.

Phase 0 runs Stages 2 -> 3 -> 4 (Stage 1 pre-filter is Phase 1; Stage 5 dry-run
is done by the CLI via stages.post.write_dry_run).
"""
from __future__ import annotations

from .adapters import get_adapter
from .models import ReviewContext, ReviewResponse
from .stages import llm_review, merge
from .stages.scope import scope


def run(config, diff_text: str, repo=None, base_sha=None, head_sha=None,
        pr=None, adapter=None) -> tuple:
    """Return (ReviewResponse, ReviewContext, meta)."""
    hunks, changed_files, trivial, meta = scope(diff_text, config)

    ctx = ReviewContext(pr=pr, repo=repo, base_sha=base_sha, head_sha=head_sha,
                        config=config, changed_files=changed_files, hunks=hunks,
                        prefilter_findings=[])  # Stage 1 is Phase 1

    if trivial:
        return (ReviewResponse(findings=[], summary="Trivial diff — skipped.",
                               verdict="approve"), ctx, meta)
    if not hunks:
        return (ReviewResponse(findings=[], summary="No reviewable changes in diff.",
                               verdict="approve"), ctx, meta)

    adapter = adapter or get_adapter(config)
    llm_resp = llm_review.review(ctx, adapter)
    kept, verdict = merge.merge_and_gate(ctx.prefilter_findings, llm_resp.findings, config)
    return (ReviewResponse(findings=kept, summary=llm_resp.summary, verdict=verdict,
                           usage=llm_resp.usage), ctx, meta)
