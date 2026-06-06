# ADR-0022: Curation SLA + drift guard — make the human-in-loop knowledge contract measurable

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0005](0005-curated-knowledge-not-autonomous-learning.md) (curated, not autonomous), [ADR-0006](0006-references-retrieval-advisory-then-defer.md), [ADR-0010](0010-headless-ci-action-runner.md)
- **Informed by:** critic (Finding #5: "curation SLA stated but unmeasured and under-resourced")

## Context

The runner's differentiator is the **open, forkable, curated `references/` knowledge layer**
(ADR-0010), kept fresh by humans (ADR-0005 — no autonomous learning loop). ADR-0010 declared
a curation SLA of ~1–2 hrs/month per active repo. The critic's valid objection: that SLA is
stated but **unmeasured** — there's no signal for when curation is slipping, and no defined
fallback when it does. An unmeasured SLA that slips silently reverts the product to "no
learning" and lets the false-positive rate creep.

## Decision

1. **Define the SLA concretely.** Per **active** repo (≥5 PRs/week): curate ~2 reference
   entries/month; lower-volume repos ~1/month. "Curate" = read a real review, extract the
   generalizable tools-miss pattern, write/refresh a `references/` entry, validate on a
   small PR. This is a human task (ADR-0005); the runner never self-edits `references/`.
2. **Ship a drift-guard test** (Phase 1) — a deterministic, non-ML coverage check that
   measures the share of Stage-3 findings whose defect class is **not** represented by any
   `references/` entry. When uncovered-share exceeds a threshold (default ~20%), it emits a
   **list of candidate new entries** (defect classes seen but uncovered) for the operator —
   surfacing slip as data, not vibes. It is a **report, not a CI gate**.
3. **Define the fallback when the SLA slips** (≥2 months without curation while drift is
   high): the operator must take one explicit action — (a) narrow the default provider to
   the highest-quality model, (b) lower `max_findings`/raise the severity floor to protect
   signal, or (c) open a decision on automating curation (the deferred learning loop behind
   ADR-0005's volume trigger). The choice is recorded; silent stagnation is not allowed.

## Alternatives considered

- **Leave the SLA as a prose aspiration** (status quo from ADR-0010) — no maintenance cost
  now, but it's the exact unmeasured-slip risk the critic named. Rejected.
- **Autonomous learning loop** (auto-mine PRs into `references/`) — would "solve" curation,
  but violates ADR-0005's human-in-loop decision and reintroduces drift/quality risk.
  Rejected (stays deferred behind the ADR-0005 trigger).
- **A heavy analytics/telemetry pipeline** to track curation — overkill and non-portable
  (ADR-0006). Rejected for a stdlib coverage report.

## Consequences

**Positive:** the knowledge-layer differentiator has a measurable health signal and a named
fallback; slip becomes visible and actionable; honors ADR-0005/0006 (human-curated, no RAG).

**Negative:** the drift-guard is a heuristic (defect-class coverage, not true FP causation)
— a proxy, documented as such; the operator still must do the curation hours (the SLA is
real work, not automated away).

**Neutral:** the guard runs on demand / in the eval harness
([ADR-0023](0023-quality-eval-harness.md)), not in the review hot path.

## Revisit when

- Active-repo count grows past what one operator can curate (~the ADR-0005 volume trigger) →
  open the automate-curation / community-contribution decision.
- The drift-guard's coverage proxy diverges from measured FP rate → improve the signal or
  replace it.
