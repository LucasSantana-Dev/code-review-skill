"""Deterministic mock adapter — lets the CLI + tests run end-to-end without a key.

Not a real reviewer: it flags any added line containing the literal token `BUG`
as a P1 correctness finding, and `SECRET` as a P0 security finding. Used for
dry-run smoke tests and CI of the pipeline plumbing, never for real review.
"""
from __future__ import annotations

from ..models import Finding, ReviewResponse, make_fingerprint


class MockAdapter:
    name = "mock"

    def __init__(self, config):
        self.config = config

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def review(self, system_prompt: str, diff_context: str) -> ReviewResponse:
        findings = []
        line_no = 0
        path = "<diff>"
        for raw in diff_context.splitlines():
            if raw.startswith("--- ") and "(lines" in raw:
                # synthetic per-hunk header emitted by the scope stage
                path = raw[4:].split(" (lines")[0].strip()
                continue
            if raw.startswith("@@"):
                continue
            if raw.startswith("+") and not raw.startswith("+++"):
                line_no += 1
                body = raw[1:]
                if "SECRET" in body:
                    findings.append(_f(path, line_no, "P0", "security",
                                       "possible hardcoded secret",
                                       "An added line references SECRET; verify no credential is committed."))
                elif "BUG" in body:
                    findings.append(_f(path, line_no, "P1", "correctness",
                                       "BUG marker on changed line",
                                       "Added line is annotated BUG; confirm the defect is resolved, not shipped."))
        verdict = ("changes-required" if any(f.severity in ("P0", "P1") for f in findings)
                   else "approve-with-nits" if findings else "approve")
        return ReviewResponse(findings=findings, summary="Mock review (plumbing smoke test).",
                              verdict=verdict, usage={"input_tokens": 0, "output_tokens": 0})


def _f(path, line, severity, dimension, title, body) -> Finding:
    return Finding(
        path=path, line=line, severity=severity, title=title, body=body,
        dimension=dimension, evidence_type="factual", confidence=0.9,
        source="llm:mock", fingerprint=make_fingerprint(path, line, title),
    )
