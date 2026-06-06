# ADR-0018: Merge + confidence×evidence gating (Stage 4) — reuse the ADR-0002 matrix unchanged

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0002](0002-confidence-calibration-for-gating-matrix.md) (the gating matrix this stage applies)
- **Informed by:** design tracks + critic (Conflict #6/#7: evidence field must be exposed; dedup ownership must be explicit)

## Context

Stage 1 (deterministic, high-confidence) and Stage 3 (LLM, calibrated) both produce
`Finding`s. Posting everything the LLM returns floods PRs with low-confidence nitpicks and
burns reviewer trust — the exact failure mode ADR-0002 exists to prevent. The runner must
apply the **same** calibration gate as the interactive skill so its false-positive rate
matches, and must merge the two sources without double-posting.

## Decision

Stage 4 is deterministic (0 tokens) and does four things, in order:

1. **Dedup / merge** by `fingerprint` (`path:line:category_slug`,
   [ADR-0013](0013-data-model-and-findings-schema.md)). When Stage-1 and Stage-3 agree on
   a fingerprint: keep one finding, take the **higher severity**, mark `evidence_type`
   toward `factual` (two independent sources agree), and merge bodies. When multiple LLM
   dimensions hit one fingerprint: keep the highest-severity, note the others in the body.
2. **Gate** via ADR-0002's severity×confidence matrix (sourced from `REFERENCE.md`, not
   re-defined here): P0/P1 post inline at any confidence; P2/P3 post inline only above the
   confidence/evidence floor, else fold into the summary; speculative low-confidence items
   are summary-only or dropped. Defaults are configurable via `severity_floor`.
3. **Sort** by severity (P0 first), then line, then confidence.
4. **Mark fix-eligibility** (advisory): only `factual` + P0/P1 + high confidence carry a
   `suggestion` block — consistent with the skill's `--fix` discipline; the runner does
   **not** auto-apply.

The gate is the **single source of truth** for what posts inline vs. summary vs. drops;
no other stage filters on confidence.

## Alternatives considered

- **Post everything the LLM returns** — simplest, but high noise, breaks ADR-0002, damages
  trust. Rejected.
- **Push gating into the prompt** ("only return high-confidence findings") — loses the
  audit trail of what was considered-and-filtered, and trusts the model to self-censor.
  Rejected — gate deterministically in Stage 4.
- **Keep Stage-1 and Stage-3 findings separate in the output** — confuses the reader with
  duplicates. Rejected — merge into one ranked list.

## Consequences

**Positive:** inline threads stay high-signal; the runner's FP rate tracks the interactive
skill's by construction; low-confidence insight is preserved in the summary rather than lost.

**Negative:** dedup must keep the max-confidence copy (because `Finding.__hash__` ignores
confidence — [ADR-0013](0013-data-model-and-findings-schema.md)); edge cases (P1 at low
confidence still posts inline — intentional) need explicit tests; Stage-1→P0–P3 severity
mapping must be sane.

**Neutral:** ~30 LOC of gating logic, fully unit-testable on fixtures.

## Revisit when

- A post-Phase-2 audit shows low-confidence P2s are reaching inline threads, or summary-only
  findings are being ignored → tune the matrix (in ADR-0002, not here).
- Dedup misses true duplicates or collapses distinct issues → refine the `category_slug`.
