"""Immutable, hashable data model shared across pipeline stages.

ADR-0013: dimension / evidence_type / confidence are first-class so the
ADR-0002 gate (Stage 4) can run and the skill's judgment isn't flattened.
Stdlib dataclasses only (no Pydantic) — ADR-0011.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Optional

SCHEMA_VERSION = "1.0"

SEVERITIES = ("P0", "P1", "P2", "P3")
SEV_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
DIMENSIONS = (
    "correctness", "security", "maintainability", "scalability", "architecture",
    "efficiency", "resource-safety", "tests", "best-practices",
)
EVIDENCE = ("factual", "behavioral", "speculative")


def slugify(text: str, max_words: int = 6) -> str:
    """Derive a short category slug from a rule id or finding title."""
    words = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-").split("-")
    return "-".join(w for w in words if w)[:60] or "issue"


def make_fingerprint(path: str, line: int, category: str) -> str:
    """Dedup key (ADR-0013): path:line:category_slug."""
    return f"{path}:{line}:{slugify(category)}"


@dataclass(frozen=True)
class DiffHunk:
    path: str
    start_line: int          # first line on the NEW side
    end_line: int            # last touched line on the NEW side
    content: str             # raw hunk text (incl. @@ header + context)
    side: str = "RIGHT"


@dataclass(frozen=True, eq=False)
class Finding:
    path: str
    line: int
    severity: str            # P0 | P1 | P2 | P3
    title: str               # < 70 chars
    body: str                # evidence -> impact -> fix
    dimension: str
    evidence_type: str       # factual | behavioral | speculative
    confidence: float        # 0.0..1.0
    source: str              # 'prefilter:<tool>' | 'llm:<dimension>' | 'manual'
    fingerprint: str
    end_line: Optional[int] = None
    suggestion: Optional[str] = None

    # Dedup identity is the fingerprint only (ADR-0013) — body/confidence ignored.
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Finding) and self.fingerprint == other.fingerprint

    def __hash__(self) -> int:
        return hash(self.fingerprint)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


def finding_from_dict(d: dict, default_source: str = "llm") -> Finding:
    """Build a Finding from a provider/tool dict, coercing + filling defaults."""
    path = str(d.get("path", "")).strip()
    line = int(d.get("line", 0) or 0)
    severity = str(d.get("severity", "P2")).upper()
    if severity not in SEVERITIES:
        severity = "P2"
    dimension = str(d.get("dimension", "correctness"))
    evidence = str(d.get("evidence_type", "behavioral"))
    if evidence not in EVIDENCE:
        evidence = "behavioral"
    try:
        confidence = float(d.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))
    category = d.get("category") or d.get("rule_id") or d.get("title") or dimension
    fp = d.get("fingerprint") or make_fingerprint(path, line, str(category))
    end_line = d.get("end_line")
    return Finding(
        path=path,
        line=line,
        severity=severity,
        title=str(d.get("title", "")).strip()[:200],
        body=str(d.get("body", "")).strip(),
        dimension=dimension,
        evidence_type=evidence,
        confidence=confidence,
        source=str(d.get("source") or default_source),
        fingerprint=fp,
        end_line=int(end_line) if end_line else None,
        suggestion=(str(d["suggestion"]).strip() if d.get("suggestion") else None),
    )


@dataclass
class ReviewConfig:
    """Resolved runtime config (defaults < .code-review.yml < CLI/env) — ADR-0021."""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key_env: str = "CODE_REVIEW_API_KEY"
    api_endpoint: Optional[str] = None
    dimensions: tuple = ("correctness", "security")   # Phase-0 MVP — ADR-0019
    severity_floor: str = "P1"
    context_radius: int = 10                          # N — ADR-0016
    skip_trivial: bool = True
    trivial_loc: int = 50
    max_tokens_budget: int = 16000
    force_large_diff: bool = False
    dry_run: bool = True                              # Phase 0 forces dry-run — ADR-0019


@dataclass
class ReviewContext:
    pr: Optional[int]
    repo: Optional[str]
    base_sha: Optional[str]
    head_sha: Optional[str]
    config: ReviewConfig
    changed_files: list = field(default_factory=list)
    hunks: list = field(default_factory=list)         # list[DiffHunk]
    prefilter_findings: list = field(default_factory=list)  # list[Finding] (empty in P0)


@dataclass
class ReviewResponse:
    findings: list = field(default_factory=list)      # list[Finding]
    summary: str = ""
    verdict: str = "approve-with-nits"
    usage: dict = field(default_factory=dict)
