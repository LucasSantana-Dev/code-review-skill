# ADR-0023: Quality/eval harness — measure false-positive rate + verdict quality on real PRs

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0010](0010-headless-ci-action-runner.md) (FP-rate rollback trigger), [ADR-0019](0019-phase-0-mvp-scope.md)
- **Informed by:** critic (Finding #13 + Gap: "success criteria not testable; no test harness")

## Context

ADR-0010's rollback trigger is "FP rate from the Action exceeds the interactive skill's" —
but the critic correctly noted there was **no way to measure that**. "Spot-checked: no new
false positives" is not a number. Without a harness, you can't know when Phase 0–2 is done,
whether a model/provider change regressed quality, or whether the runner is safe to promote.

## Decision

Build a **lightweight, manual-validation eval harness** (`eval/measure.py`), run on demand
(**not** a CI gate initially — it's a data-collection instrument):

1. **Labeled test set, committed to the repo** (`eval/test_prs.json`): ~5–10 Lucky PRs +
   2–3 public OSS PRs, each with a small ground-truth list of expected major findings
   (P0/P1 + expected P2 categories). Kept small (~10) to avoid bloat.
2. **Two ground-truth modes, sequenced** (operator decision favored fast iteration first):
   - **Phase 0–2: action-vs-skill** — compare the runner's verdict/findings to the
     *interactive skill's* verdict on the same PR. Fast, sufficient to catch regressions.
   - **Phase 2+: human ground truth** — promote to human-labeled expected findings once the
     runner is stable on real PRs.
3. **Metrics:** true/false positives, false negatives, precision/recall/F1, token cost,
   and pre-filter yield (% of findings at zero tokens). Output a CSV + a short report.
4. **Wire the success gates** (replacing the un-testable prose in
   [the spec](../docs/specs/2026-06-06-ci-action-runner.md)) as concrete numbers:
   FP rate **< 5%** vs the baseline; missed P0/P1 **< 10%**; token cost **≤ ~$1.50** per
   medium (200–600 LOC) PR; pre-filter yield **≥ 30%**. Phase 0 "done" = reproduces the
   skill's verdict on Lucky #1263 with **zero new P0/P1/P2** findings.
5. The harness also hosts the **curation drift-guard**
   ([ADR-0022](0022-curation-sla-and-drift-guard.md)).

## Alternatives considered

- **No measurement** — cheapest, but can't detect quality regressions or honor ADR-0010's
  rollback trigger. Rejected.
- **Heavy automated oracle** (trained labels, full automation) — not solo-maintainable and
  premature. Rejected for manual validation on a small set.
- **Human ground truth from day one** — gold standard but labor-heavy; slows Phase 0.
  Sequenced after action-vs-skill instead.
- **A/B on all live PRs** — slow signal, risky on real reviews. Rejected.

## Consequences

**Positive:** ADR-0010's rollback trigger becomes operable; provider/model comparisons are
local and cheap; the success criteria are finally numbers; transparent to users (committed
test set + report).

**Negative:** ~10 test PRs limit generalization; human validation is required per case
(real operator time); the harness is separate code to maintain (kept small, no deps).

**Neutral:** lives outside the review hot path — zero impact on runtime/cost.

## Revisit when

- After ~20 real-world PRs → expand the test set and consider automating verdict comparison.
- If a provider/model swap regresses FP rate beyond the gate → block the promotion, tighten
  pre-filter/prompt before adding spend (ADR-0010 trigger).
