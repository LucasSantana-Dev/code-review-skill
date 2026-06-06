# ADR-0016: Diff-scope + trivial-skip (Stage 2) — changed hunks + bounded context, not full files

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0010](0010-headless-ci-action-runner.md), [ADR-0012](0012-five-stage-pipeline-architecture.md)
- **Informed by:** design tracks + critic; CodeRabbit/WhatsCode diff-scoping; hunk-based review literature

## Context

Cost is the binding constraint for a self-hosted runner. Large diffs blow the token
budget or the context window. Comparable systems all diff-scope. But scoping trades against
the SKILL.md "cross-file invariant" defect class — context cut too aggressively misses
invariants that live a few lines or a few files away. This stage must pick a defensible
default and **document its blind spot honestly** (the critic flagged the cross-file gap as
acknowledged-but-unsolved).

## Decision

1. **Hunk + bounded context.** For each changed file, extract changed hunks and include
   **N = 10 lines** of context before/after each hunk (tunable via `.code-review.yml`).
   Collapse adjacent hunks within the radius. Pass the minimal diff to Stage 3 — **never
   whole files**.
2. **Budget guard.** If the scoped diff exceeds the token budget (default ~16K), truncate
   **at hunk boundaries** (never mid-hunk), warn in the summary, and allow
   `--force-large-diff` to override.
3. **Trivial-skip (opt-out, default on).** Before scoping, skip the LLM entirely when the
   change is trivial — total changed LOC below a threshold (default 50) **and**
   whitespace/comment/rename-only — and post only any Stage-1 findings with a
   "trivial diff, skipped" note. Configurable threshold; `skip_trivial: false` disables it;
   a PR label / `--force-review` overrides for a small-but-critical fix.
4. **Cross-file scope, MVP boundary (documented limitation).** Stage 2 looks at the
   changed file + its **direct imports** only — **not** the whole codebase. The runner
   **documents** that invariants living far outside the diff are out of local scope and
   are better caught by enabling Semgrep (Stage 1). A light "changed-signature usage scan"
   (grep callers of changed functions/types into the prompt context) is a **Phase-1**
   addition, not MVP.

## Alternatives considered

- **Full-file (or whole-repo) diffs to the LLM** — simpler scoping, but token cost
  explodes and exceeds budgets with little ROI. Rejected.
- **Token-chunk large diffs across multiple calls** — complex sequencing, loses cross-hunk
  signal, harder dedup. Deferred (not MVP).
- **AST-based scope (only relevant functions)** — precise, but needs per-language AST
  parsers → violates stdlib-thin and is fragile. Rejected.
- **N = 5 (aggressive) / N = 20 (conservative)** — N=10 is the measured-balanced default;
  the others remain config values, tuned in Phase 1 against cross-file miss rate.

## Consequences

**Positive:** predictable, bounded token cost per PR; faster, lower-hallucination reviews;
trivial PRs cost nothing.

**Negative:** the scope heuristic **will** miss cross-file invariants beyond the diff +
direct imports — accepted and documented for MVP, partially mitigated by Semgrep; trivial-
skip risks skipping a tiny critical change (mitigated by the force-review override).

**Neutral:** N and the trivial threshold are knobs, not architecture — tunable without code change.

## Revisit when

- Real PRs show >5% of true findings are cross-file invariants missed by the heuristic →
  ship the Phase-1 changed-signature usage scan or widen N for risky paths.
- Trivial-skip is observed dropping real findings → tighten the predicate.
- Budget-guard truncation fires often → users split PRs, or raise the budget knowingly.
