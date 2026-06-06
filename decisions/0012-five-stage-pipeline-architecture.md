# ADR-0012: Five-stage pipeline architecture for the headless runner

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0010](0010-headless-ci-action-runner.md)
- **Informed by:** design tracks + critic, 2026-06-06; CodeRabbit / Qodo Merge / WhatsApp WhatsCode hybrid-pipeline patterns (G-Research, BitsAI-CR arXiv:2501.15134)

## Context

ADR-0010 committed to a *thin* runner whose "lightweight" property comes from a
deterministic pre-filter + diff-scoping + caching, not from removing the LLM. That
implies more than one processing step. The architecture must avoid the monolithic
"one giant LLM call" pitfall (opaque cost, every finding costs tokens, hard to profile)
while staying simple enough for a solo maintainer. Every comparable production reviewer
(CodeRabbit, Qodo Merge, WhatsCode) uses a multi-stage deterministic + LLM + merge
pipeline.

## Decision

Structure the runner as **five composable stages with explicit input/output contracts
and no shared mutable state**:

| # | Stage | Cost | Owns |
|---|-------|------|------|
| 1 | **Pre-filter** (deterministic) | 0 tokens | run/parse linters + Semgrep → `Finding[]` ([ADR-0015](0015-deterministic-pre-filter-stage-1.md)) |
| 2 | **Scope** | 0 tokens | diff → changed hunks + context radius; drop trivial ([ADR-0016](0016-diff-scope-and-trivial-skip-stage-2.md)) |
| 3 | **LLM review** | tokens | per-dimension prompts (SKILL.md + references/) → `Finding[]` ([ADR-0017](0017-prompt-construction-and-structured-output-stage-3.md)) |
| 4 | **Merge & gate** | 0 tokens | dedup Stage-1 ∪ Stage-3; confidence×evidence gate ([ADR-0018](0018-merge-and-confidence-gating-stage-4.md)) |
| 5 | **Post** | 0 tokens | `post_review.py` → batched PR review + re-review loop ([ADR-0020](0020-github-action-packaging-and-ci-security.md)) |

Stages pass immutable data objects ([ADR-0013](0013-data-model-and-findings-schema.md)).
Each stage is independently testable, profileable, and skippable (e.g., `--skip-prefilter`
for fast local iteration). The pipeline orchestrator (`runner/pipeline.py`) is the only
component that knows the stage order; stages know nothing about each other.

## Alternatives considered

- **Monolithic single LLM call** — simplest prompt, but 100% of findings cost tokens,
  cost is opaque, and there's no pre-filter leverage. Rejected — it's the expensive,
  un-optimizable thing ADR-0010 rejected.
- **Tightly-coupled stages with shared state** — easier to write first, but a bug in one
  stage corrupts others; can't profile or skip stages. Rejected.
- **A dataflow framework (Dagster/Beam-style)** — adds a heavy dependency for a 5-step
  linear pipeline. Rejected (violates stdlib-thin, [ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md)).

## Consequences

**Positive:** distributed maintenance burden (a Stage-2 bug can't crash Stage-5); clean
test seams (mock the adapter, test Stage 3 in isolation); operator can disable stages;
cost is attributable per stage.

**Negative:** five stage contracts to define and keep stable — a schema bug at a boundary
cascades; dry-run/replay for debugging spans five steps; the data model
([ADR-0013](0013-data-model-and-findings-schema.md)) must be pinned before implementation.

**Neutral:** the interactive skill is unchanged; the pipeline is a headless wrapper over
the same judgment.

## Revisit when

- Production false-positive rate exceeds the interactive skill's (>~15%) → the boundary
  to inspect is almost always Stage 2 (scope too narrow) or Stage 3 (prompt too broad).
- Any single stage exceeds ~200 LOC → split it.
- A genuine need for parallel fan-out on huge diffs appears → revisit the linear contract
  (deferred per [ADR-0019](0019-phase-0-mvp-scope.md)).
