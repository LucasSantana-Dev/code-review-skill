"""Stage 4 — merge + confidence×evidence gating (ADR-0018, applies ADR-0002).

Dedup Stage-1 (pre-filter) ∪ Stage-3 (LLM) by fingerprint, gate via the
severity×confidence matrix, sort, derive the verdict. Deterministic, 0 tokens.
This module is the single source of truth for inline vs summary vs drop.
"""
from __future__ import annotations

from dataclasses import replace

from ..models import SEV_RANK, Finding

# Confidence floor below which a low-severity finding is dropped (ADR-0002).
_MIN_CONF = {"P2": 0.5, "P3": 0.7}


def _merge_pair(a: Finding, b: Finding) -> Finding:
    """Collapse two findings with the same fingerprint: higher severity wins."""
    keep, other = (a, b) if SEV_RANK[a.severity] <= SEV_RANK[b.severity] else (b, a)
    evidence = "factual" if {a.evidence_type, b.evidence_type} != {"factual"} and (
        a.evidence_type == "factual" or b.evidence_type == "factual") else keep.evidence_type
    # two independent sources agreeing -> treat as factual
    if a.source.split(":")[0] != b.source.split(":")[0]:
        evidence = "factual"
    body = keep.body
    if other.body and other.body not in body:
        body = f"{body}\n\n(also: {other.body})"
    return replace(keep, confidence=max(a.confidence, b.confidence),
                   evidence_type=evidence, body=body,
                   source=f"{keep.source}+{other.source}")


def placement(f: Finding, config) -> str:
    """inline | summary | drop — the ADR-0002 gate (severity_floor + confidence)."""
    floor = SEV_RANK.get(config.severity_floor, 1)
    if f.severity in _MIN_CONF and f.confidence < _MIN_CONF[f.severity]:
        return "drop"
    return "inline" if SEV_RANK[f.severity] <= floor else "summary"


def merge_and_gate(prefilter_findings, llm_findings, config):
    """Return (kept_findings_sorted, verdict)."""
    by_fp = {}
    for f in list(prefilter_findings) + list(llm_findings):
        if f.fingerprint in by_fp:
            by_fp[f.fingerprint] = _merge_pair(by_fp[f.fingerprint], f)
        else:
            by_fp[f.fingerprint] = f

    kept = [f for f in by_fp.values() if placement(f, config) != "drop"]
    kept.sort(key=lambda f: (SEV_RANK[f.severity], f.path, f.line))
    return kept, derive_verdict(kept)


def derive_verdict(findings) -> str:
    if any(f.severity in ("P0", "P1") for f in findings):
        return "changes-required"
    return "approve-with-nits" if findings else "approve"
