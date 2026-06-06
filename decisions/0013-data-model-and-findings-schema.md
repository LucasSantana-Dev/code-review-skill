# ADR-0013: Data model + findings schema — preserve dimension, evidence, and confidence as first-class fields

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0002](0002-confidence-calibration-for-gating-matrix.md) (severity×confidence gating), [ADR-0012](0012-five-stage-pipeline-architecture.md)
- **Informed by:** design tracks + critic (Critical Finding #2: "SKILL.md judgment must not be flattened to a dimension-agnostic schema")

## Context

The runner's competitive edge (ADR-0010) is the calibrated semantic *judgment* of the
skill — its 9-dimension taxonomy and its evidence/confidence discipline (ADR-0002). The
critic's hardest finding: if the headless runner flattens findings to
`{path, line, severity, title, body}`, the judgment is lost in translation and the Action
degrades to linter-level noise. The gating matrix (ADR-0002) *cannot run* if `evidence`
and `confidence` aren't first-class outputs. Stages also need clean, hashable types to
pass data and to dedup (Stage 4).

## Decision

Define lightweight **immutable, hashable stdlib `@dataclass` types** (no Pydantic) that
make dimension, evidence, and confidence first-class. The canonical `Finding`:

```python
@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str          # 'P0' | 'P1' | 'P2' | 'P3'
    title: str             # < 70 chars
    body: str              # evidence → impact → fix
    dimension: str         # correctness | security | maintainability | scalability
                           # | architecture | efficiency | resource-safety | tests | best-practices
    evidence_type: str     # 'factual' | 'behavioral' | 'speculative'   (per ADR-0002)
    confidence: float      # 0.0–1.0
    source: str            # 'prefilter:<tool>' | 'llm:<dimension>' | 'manual'
    fingerprint: str       # dedup key = f"{path}:{line}:{category_slug}"
    end_line: int | None = None
    suggestion: str | None = None   # committable block, ≤ ~5 lines, factual only
```

Supporting types: `DiffHunk(path, start_line, end_line, content, side)` and
`ReviewContext(pr, repo, base_sha, head_sha, changed_files, hunks, repo_config,
prefilter_findings)`.

Rules:
- `Finding` hashes/dedups on `fingerprint` (= `path:line:category_slug`), **not** on
  `body`/`confidence` — so a linter and the LLM flagging the same issue collapse to one,
  but two *different* issues on the same line stay distinct (the slug differentiates them).
- Serialization at the post boundary is `json.dumps(asdict(finding))`; the on-the-wire
  JSON schema for findings is normative and lives in the Phase-0 spec.
- The schema carries a `__schema_version__` marker so a future field add is detectable.

## Alternatives considered

- **Flat dict / raw JSON throughout** — simplest, but no type safety, runtime errors at
  stage boundaries, and (fatally) drops `dimension`/`evidence`/`confidence` → breaks
  ADR-0002 gating. Rejected — this is exactly the critic's blocking finding.
- **Pydantic `BaseModel`** — better validation + serialization, but an external dependency
  (violates [ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md) stdlib-thin).
  Rejected; revisit only if validation pain is real.
- **Severity-only schema, infer dimension from prompt** — loses provenance; can't audit
  per-dimension false-positive rates. Rejected.

## Consequences

**Positive:** ADR-0002's gating runs unchanged in Stage 4; per-dimension FP rates are
auditable; dedup is one line (`set(findings)`); stage I/O is self-documenting + mypy-checkable.

**Negative:** the model must be pinned before code and versioned if it drifts; hashing
that ignores `confidence` means the merge stage must explicitly keep the max-confidence
copy of a duplicate (Stage-4 logic, [ADR-0018](0018-merge-and-confidence-gating-stage-4.md)).

**Neutral:** the JSON shape is a superset of `post_review.py`'s current input — extra
fields (`dimension`, `evidence_type`, `confidence`) are carried for gating and dropped
when not needed for posting.

## Revisit when

- Real-world posting needs a field the model lacks (e.g., `category_url`, `cwe`) → add it
  + bump `__schema_version__` + update tests before shipping.
- The `path:line:category_slug` fingerprint produces dedup collisions or misses on real
  PRs → refine the slug derivation (audit in Phase 1).
