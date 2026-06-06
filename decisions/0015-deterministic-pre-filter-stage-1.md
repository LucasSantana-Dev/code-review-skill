# ADR-0015: Deterministic pre-filter (Stage 1) — consume linters/Semgrep, never re-implement them

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0010](0010-headless-ci-action-runner.md), [ADR-0012](0012-five-stage-pipeline-architecture.md)
- **Informed by:** design tracks + critic (Critical Finding #3: "pre-filter detection + dedup were undefined"); G-Research / BitsAI-CR (~30–40% of findings are deterministic); SARIF 2.1.0

## Context

ADR-0010's "lightweight" depends on resolving the ~30–40% of findings that don't need an
LLM (syntax, types, known-vulnerable patterns) at **zero token cost**, by consuming tools
the repo already runs. The runner positions explicitly as a *semantic* reviewer that
**assumes linters/SAST already ran** — so it consumes their output rather than rebuilding
them. The critic blocked the first draft for leaving detection, normalization, dedup, and
error handling undefined; this ADR pins them.

## Decision

Stage 1 runs **before** the LLM and is fully specified:

1. **Detection (declarative-first, auto-detect-second).** Honor an explicit `linters:`
   list in `.code-review.yml` if present. Otherwise auto-detect by config-file presence +
   `which`: first-pass supported set is **Ruff** (Python), **ESLint** (JS/TS),
   **golangci-lint** (Go), and **Semgrep** (cross-language SAST). Others are deferred to
   config-driven opt-in (Phase 4) — not auto-run.
2. **Execution (diff-scoped).** Run each detected tool on the **changed files only** (via
   `git diff` paths + tool flags). A tool that is absent or errors is **skipped with a
   logged warning**, never fatal; the summary notes "ESLint failed/absent — Python checks
   only." Stage 1 returning empty is normal, not an error.
3. **Normalization.** Prefer each tool's **SARIF 2.1.0** output where available, else its
   JSON; map to the canonical `Finding`
   ([ADR-0013](0013-data-model-and-findings-schema.md)) with `evidence_type='factual'`,
   `confidence≈0.99`, `source='prefilter:<tool>'`. Linter severity → P0–P3 via a default
   map (error→P1, warning→P2, info/style→P3), overridable in `.code-review.yml`.
4. **Dedup fingerprint.** Canonical key `path:line:category_slug`, where `category_slug`
   is the normalized rule id (Semgrep's rule id is canonical; other tools' ids map to it
   where they overlap). Stage 1 dedups within itself; Stage 4 merges with LLM findings.
5. **Boundary.** The pre-filter **owns** what tools already report; Stage 3 is instructed
   **not to re-flag** anything in the Stage-1 set (passed as context). This is the
   token-saving mechanism, not just parallel checking.

## Alternatives considered

- **Skip the pre-filter; LLM on the full diff** — simplest, but ~40% of findings cost
  tokens needlessly and overlap what linters already post. Rejected.
- **Re-implement linters/SAST (an "all-in-one" engine)** — that is "Sonar 2.0", the
  rejected category (ADR-0010); massive maintenance for redundant capability. Rejected.
- **Mandatory pre-filter (error if no linters)** — punishes repos without linters.
  Rejected: graceful skip instead.
- **Per-tool bespoke parsers instead of SARIF** — works, but N fragile parsers; SARIF is
  the shared interchange that bounds that cost.

## Consequences

**Positive:** measurable zero-token findings (~30–40%); deterministic, no hallucination;
SARIF keeps the parser surface small; failures degrade gracefully.

**Negative:** depends on repos having linters configured; SARIF coverage varies by tool
(some need a converter); severity mapping needs sane defaults + override; the "don't
re-flag" instruction to Stage 3 must be reliable (tested).

**Neutral:** existing repo issues outside the diff are ignored by design (scope is the change).

## Revisit when

- Pre-filter yield is <20% on real PRs → tighten detection / add a high-value tool.
- A linter's noise (FP) leaks through → add a per-tool disable in `.code-review.yml`.
- A second non-SARIF tool needs a bespoke parser → standardize harder on SARIF or vendor a converter.
