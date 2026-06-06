# Pre-code design package — code-review CI Action runner

**Status:** Defined, awaiting ratification before implementation · **Date:** 2026-06-06

Everything is defined before a line of runner code is written. This is the entry point and
reading order. Nothing here is built yet — the build follows [roadmap.md](roadmap.md) phase by
phase, each behind a validation gate.

## What this is

A **thin, headless GitHub Action** that runs the existing review engine
(`SKILL.md`/`REFERENCE.md`/`references/` + `post_review.py`/`app_token.py`) in CI with no
Claude Code present, driven by any LLM (BYO frontier key, or local Ollama). Free, self-hostable,
lightweight. A *semantic* reviewer that assumes linters/SAST already ran — **not** a linter,
**not** "Sonar 2.0". Differentiator: the open, forkable, curated knowledge layer + calibration
discipline. ([ADR-0010](../decisions/0010-headless-ci-action-runner.md))

## How this package was produced

A parallel multi-agent design fan-out (7 grounded tracks, web-researched) → an **adversarial
critic** that *rejected* the raw output as incoherent and 2–3× over-"thin" (47 colliding ADRs)
→ consolidation into a single, sequentially-numbered, cross-referenced decision set with the
critic's cut-list applied. Two genuine product forks were ratified by the operator (below).

## Reading order

1. **[architecture.md](architecture.md)** — the system map: 5-stage pipeline, data model, how
   the skill's judgment reaches a headless LLM, provider abstraction, security model.
2. **[roadmap.md](roadmap.md)** — feature tiers (MVP/v1/later), phases P0–P4, per-phase
   validation gates, success criteria as numbers, rollback triggers.
3. **[repo-structure.md](repo-structure.md)** — target directory layout (what's new vs reused).
4. **specs** — [Phase-0 MVP](specs/2026-06-06-phase-0-mvp.md) (implementable: CLI, JSON schema,
   worked prompt, validation gate) and the [high-level runner spec](specs/2026-06-06-ci-action-runner.md).
5. **[glossary.md](glossary.md)** — shared vocabulary.
6. **[documentation-plan.md](documentation-plan.md)** — what user docs will exist and when.
7. **[decisions/](../decisions/README.md)** — ADR-0011 … 0024, the decision record.

## The decisions (ADR-0011 … 0024)

| Area | ADR |
|---|---|
| Repo + runtime | [0011](../decisions/0011-monorepo-structure-and-python-stdlib-runtime.md) monorepo + Python-stdlib |
| Architecture | [0012](../decisions/0012-five-stage-pipeline-architecture.md) 5-stage pipeline |
| Data | [0013](../decisions/0013-data-model-and-findings-schema.md) data model + findings schema |
| Providers | [0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md) adapter — BYOK first, Ollama fallback |
| Stage 1 | [0015](../decisions/0015-deterministic-pre-filter-stage-1.md) deterministic pre-filter |
| Stage 2 | [0016](../decisions/0016-diff-scope-and-trivial-skip-stage-2.md) diff-scope + trivial-skip |
| Stage 3 | [0017](../decisions/0017-prompt-construction-and-structured-output-stage-3.md) prompt construction + structured output |
| Stage 4 | [0018](../decisions/0018-merge-and-confidence-gating-stage-4.md) merge + confidence gating |
| Scope | [0019](../decisions/0019-phase-0-mvp-scope.md) Phase-0 MVP scope + cut-list |
| Action | [0020](../decisions/0020-github-action-packaging-and-ci-security.md) packaging + CI security |
| Config | [0021](../decisions/0021-config-schema-code-review-yml.md) `.code-review.yml` |
| Curation | [0022](../decisions/0022-curation-sla-and-drift-guard.md) curation SLA + drift guard |
| Quality | [0023](../decisions/0023-quality-eval-harness.md) eval harness |
| Release | [0024](../decisions/0024-versioning-and-release-strategy.md) versioning + release |

Locked priors this package designs *within*: [0002](../decisions/0002-confidence-calibration-for-gating-matrix.md)
(gating), [0004](../decisions/0004-github-app-posting-identity.md) (bot identity),
[0005](../decisions/0005-curated-knowledge-not-autonomous-learning.md) (no autonomous learning),
[0006](../decisions/0006-references-retrieval-advisory-then-defer.md) (advisory refs / RAG deferred),
[0010](../decisions/0010-headless-ci-action-runner.md) (thin Action runner).

## Operator-ratified product forks (2026-06-06)

- **MVP dimensions = correctness + security** — proves the "catches what linters/tests miss"
  thesis without the heft of the full taxonomy. ([ADR-0019](../decisions/0019-phase-0-mvp-scope.md))
- **Providers = BYOK frontier first (Anthropic validated first), Ollama as the free fallback** —
  quality path leads; free/self-hostable stays honest. ([ADR-0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md))

## Carried prerequisite (not solved by design)

GitHub App bot identity (key / ID / `CODE_REVIEW_BOT_LOGIN`) is **not yet configured**. Phase 0
is dry-run and does **not** need it; **Phase 2 (posting) does.** Wire it before P2.
([ADR-0004](../decisions/0004-github-app-posting-identity.md))

## Next step

Ratify (or amend) this package. On approval, implementation starts at **Phase 0** per the
[roadmap](roadmap.md) — CLI + Anthropic adapter + Stages 2–5 dry-run — gated on reproducing the
interactive skill's verdict on Lucky #1263. No runner code is written before then.
