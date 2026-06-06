# ADR-0017: Prompt construction + structured output (Stage 3) — how SKILL.md judgment reaches a headless LLM

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0002](0002-confidence-calibration-for-gating-matrix.md), [ADR-0005](0005-curated-knowledge-not-autonomous-learning.md), [ADR-0006](0006-references-retrieval-advisory-then-defer.md), [ADR-0013](0013-data-model-and-findings-schema.md)
- **Informed by:** design tracks + critic (Critical Finding #2); Anthropic Structured Outputs + prompt caching docs; Qodo Merge per-dimension prompting

## Context

This is the heart of the runner and the critic's hardest gap: **how does the skill's
calibrated judgment actually reach an LLM when no Claude Code is present?** The answer
must be concrete enough to implement, must preserve the ADR-0002 evidence/confidence
discipline, and must return findings reliably as structured data — including from local
models that lack constrained decoding.

## Decision

1. **Per-dimension prompt templates built from the existing judgment layer.** For each
   enabled dimension, the system prompt is assembled from (a) that dimension's `SKILL.md`
   checklist + `REFERENCE.md` section, (b) the **calibration rubric** verbatim
   (factual/behavioral/speculative → confidence band, per ADR-0002), (c) 2–3 **advisory**
   `references/` entries selected by defect class (per ADR-0006 — interpolated, **not**
   RAG-indexed), and (d) the normative output schema. The diff (Stage-2 hunks) is the
   volatile suffix. The **Stage-1 findings are passed as "already reported — do not
   re-flag"** context.
2. **Calibration is encoded in the prompt, not hoped for.** The template instructs:
   *only* tag `factual` with a cited `file:line` + reason needing no runtime context;
   otherwise `behavioral`/`speculative`; reframe `confidence < 0.5` findings as questions,
   never assertions. Every finding must emit `dimension`, `evidence_type`, `confidence`
   (the fields ADR-0002's Stage-4 gate consumes).
3. **Structured output with a tiered reliability strategy.** Use **Anthropic Structured
   Outputs** (constrained decoding, ~100% schema adherence) on the Anthropic path; the
   **OpenAI-compatible** path uses JSON-schema / JSON mode; the **Ollama/local** path uses
   JSON mode + a **post-hoc validate-and-retry** layer (re-ask once on malformed JSON,
   then drop the offending block with a warning). One shared schema across all providers;
   `additionalProperties:false` to catch drift early.
4. **MVP is serial and single-call** (per [ADR-0019](0019-phase-0-mvp-scope.md)): the
   enabled dimensions (correctness + security) are reviewed in **one batched call** with a
   schema that returns findings tagged by `dimension`. **Per-dimension parallel calls and
   prompt caching are deferred to a later phase** (their cost/latency win is real but
   unproven on this workload, and Ollama doesn't cache) — the prompt is *structured* so
   that the static prefix can later become a cache breakpoint without a rewrite.

## Alternatives considered

- **One generic monolithic prompt** ("find all issues") — fewer moving parts, but lower
  precision and no per-dimension FP attribution; the schema would lose `dimension`. Rejected.
- **Per-dimension parallel fan-out in the MVP** — higher precision/latency win, but N
  concurrent calls + error handling before quality is validated, and no caching on local
  models. Deferred to a later phase (the template is parallel-ready).
- **Prompt caching in the MVP** — ~30–80% token savings on repeats, but provider-specific,
  needs cache-version invalidation on `SKILL.md`/`references/` change, and is a no-op for
  Ollama. Deferred; cache-version hashing is specified for when it lands.
- **Regex extraction from free text / tool-calling** — fragile or heavier than structured
  JSON. Rejected.

## Consequences

**Positive:** the skill's calibrated judgment transfers faithfully (dimension + evidence +
confidence are required outputs); structured output removes parse-retry churn on frontier
models; the design degrades gracefully to local models; the prefix is cache-ready for later.

**Negative:** 2 dimension templates to author + validate for the MVP (then more as
dimensions phase in); local-model JSON reliability needs the retry layer; deferring caching
leaves MVP token cost higher than the eventual steady state (acceptable, measured in Phase 1).

**Neutral:** reference selection is deterministic (defect-class → entries), not learned —
consistent with ADR-0005/0006.

## Revisit when

- Phase-1 measurement shows prompt-cache savings >~10% net → implement caching with the
  specified `SKILL.md`+`references/` content-hash cache key.
- A dimension's FP rate is an outlier → tighten its template / switch it to chain-of-thought.
- Local-model JSON parse-failure exceeds a documented bar → require BYOK for that path or
  add stricter grammar enforcement.
