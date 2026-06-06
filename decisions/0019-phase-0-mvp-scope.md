# ADR-0019: Phase-0 MVP scope — deliberately small, serial, dry-run, correctness + security

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0010](0010-headless-ci-action-runner.md) ("thin runner")
- **Informed by:** critic (Major Finding #12: "the design was 2–3× 'thin'"); operator decisions 2026-06-06 (dimensions = correctness + security; providers = BYOK-first, Ollama fallback)

## Context

The pre-code design surfaced 80+ candidate features. The adversarial critic's headline
verdict: the proposed MVP was **2–3× heavier than ADR-0010's "thin" mandate** — 5 providers,
7 parallel dimensions, multi-linter, prompt caching, `CLAUDE.md` parsing, path rules. Scope
creep is the failure mode that kills solo projects. This ADR is the **single anchor** that
defines the minimal Phase-0 MVP and **records the explicit cut-list** so deferral is a
decision, not an omission.

## Decision

**Phase-0 MVP is the smallest runner that proves the thesis on a real PR.** It ships:

- **Dimensions: correctness + security only** (operator decision). These are the
  highest-value semantic classes — the logic/security bugs linters and AI-written tests
  miss — and they validate the "catches what others miss" thesis. Remaining dimensions
  phase in later.
- **Provider: BYOK frontier, Anthropic validated first** (operator decision: "BYOK ideal,
  else Ollama"). The OpenAI-compatible adapter and the native Ollama fallback follow
  immediately after the engine's quality is baselined on Anthropic
  ([ADR-0014](0014-provider-agnostic-adapter-byok-first-ollama-fallback.md)).
- **Execution: serial, single batched LLM call** (both dimensions in one call,
  [ADR-0017](0017-prompt-construction-and-structured-output-stage-3.md)).
- **Mode: dry-run only** — Phase 0 writes `findings.json` + `summary.md` to disk and posts
  **nothing**. This **unblocks all implementation** despite the bot-identity prerequisite
  (below) and makes validation safe.
- The 5-stage pipeline, the rich findings schema, diff-scoping + trivial-skip, and the
  ADR-0002 gate — all present from Phase 0 (they're the spine, not the scope creep).

**Explicit cut-list (deferred, with the phase that owns each):**

| Deferred | Phase | Why deferred now |
|---|---|---|
| OpenAI-compatible adapter | P0→P1 | validate engine on one provider first |
| Native Ollama fallback | P3 | latency/FP unknown; baseline on BYOK first |
| Per-dimension **parallel** calls | P2+ | serial proves quality before concurrency |
| Dimensions beyond correctness+security | P1+ | add security-validated, then breadth |
| Multi-linter pre-filter (beyond stack default + Semgrep) | P4 | config-driven opt-in |
| Prompt caching | P1 | measure savings before adding cache-invalidation |
| `.code-review.yml` path rules / `CLAUDE.md` parsing | P2/P4 | hardcoded sane defaults first |
| GitHub Action posting | P2 | depends on bot identity; Phase 0 is dry-run |

**Blocking prerequisite (carried, not solved here):** GitHub App bot identity (key / ID /
`CODE_REVIEW_BOT_LOGIN`, [ADR-0004](0004-github-app-posting-identity.md)) is **not yet
configured on this machine**. Phase 0's dry-run design means it does **not** block Phase 0;
it **does** gate Phase 2 (posting). Documented as a Phase-2 prerequisite.

## Alternatives considered

- **Correctness-only MVP (critic's pick)** — leanest, but a single dimension reads close to
  what existing tools do and undersells the wedge. Operator chose correctness + security.
- **Full taxonomy + parallel + 3 providers from day one** — most "complete", but it is the
  2–3× scope the critic rejected; slowest to first validation. Rejected.
- **Post for real in Phase 0** — faster to a "live" demo, but blocked on bot identity and
  risks a personal-account post. Rejected — dry-run first.

## Consequences

**Positive:** a buildable, validatable MVP within the thin mandate; the cut-list makes every
deferral auditable; dry-run unblocks Phase 0 around the identity prerequisite.

**Negative:** the MVP is visibly minimal (two dimensions, one provider, no posting) — a
deliberate trade for speed-to-signal; later phases must actually execute or the cut-list
silently becomes the product.

**Neutral:** every cut item has an owning phase in [the roadmap](../docs/roadmap.md).

## Revisit when

- Phase-0 validation on real PRs passes the success gates → promote P1 items (security
  hardening of prompts, OpenAI-compatible adapter, caching measurement).
- The cut-list stops shrinking across two phases → re-scope or narrow ambition (don't let
  "deferred" become permanent).
