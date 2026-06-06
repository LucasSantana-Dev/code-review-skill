# Feature roadmap — code-review CI Action runner

**Status:** Design (pre-code) · **Date:** 2026-06-06 · **Anchor:** [ADR-0019](../decisions/0019-phase-0-mvp-scope.md) (MVP scope + cut-list)

Tiers are **MVP** (Phase 0–2 pilot), **v1** (stabilize), **later** (deferred behind demand
or a measured trigger). The point of the tiering is to keep the runner *thin* — every "later"
item is a recorded deferral, not an omission.

## Feature tiers

### MVP — the smallest runner that proves the thesis on a real PR
- 5-stage pipeline (pre-filter → scope → LLM → merge → post). ([ADR-0012](../decisions/0012-five-stage-pipeline-architecture.md))
- Immutable data model + findings schema with `dimension`/`evidence`/`confidence`. ([ADR-0013](../decisions/0013-data-model-and-findings-schema.md))
- **Dimensions: correctness + security** (operator decision). ([ADR-0019](../decisions/0019-phase-0-mvp-scope.md))
- **Provider: BYOK Anthropic** adapter, validated first. ([ADR-0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md))
- Serial, single batched LLM call; structured output (constrained decoding). ([ADR-0017](../decisions/0017-prompt-construction-and-structured-output-stage-3.md))
- Diff-scope (hunks + N=10) + trivial-skip + budget guard. ([ADR-0016](../decisions/0016-diff-scope-and-trivial-skip-stage-2.md))
- Confidence×evidence gating reusing the ADR-0002 matrix. ([ADR-0018](../decisions/0018-merge-and-confidence-gating-stage-4.md))
- Deterministic pre-filter (stack linter + Semgrep, graceful skip, SARIF). ([ADR-0015](../decisions/0015-deterministic-pre-filter-stage-1.md))
- **Dry-run** mode (findings.json + summary.md, no posting). ([ADR-0019](../decisions/0019-phase-0-mvp-scope.md))
- Composite GitHub Action, `pull_request` trigger, least-privilege, bot identity. ([ADR-0020](../decisions/0020-github-action-packaging-and-ci-security.md))
- Incremental re-review against baseline SHA (reuses `post_review.py`).
- Zero-config defaults; minimal `.code-review.yml` (provider/model/key). ([ADR-0021](../decisions/0021-config-schema-code-review-yml.md))

### v1 — stabilize, measure, broaden carefully
- **OpenAI-compatible** BYOK adapter (OpenAI/Together/Groq/OpenRouter + local servers).
- Remaining dimensions phased in (maintainability, scalability, architecture, efficiency,
  resource-safety, tests, best-practices) — one at a time, FP-audited per dimension.
- **Per-dimension parallel** calls (once serial quality is validated).
- **Prompt caching** (Anthropic native) once Phase-1 measures >~10% net savings.
- Light **cross-file usage scan** (grep callers of changed signatures into context).
- Quality/eval harness graduates to human ground truth. ([ADR-0023](../decisions/0023-quality-eval-harness.md))
- `.code-review.yml` path-rules + `CLAUDE.md`/`AGENTS.md` ingestion. ([ADR-0021](../decisions/0021-config-schema-code-review-yml.md))
- GitHub Marketplace stable release (`v0.2.0`+). ([ADR-0024](../decisions/0024-versioning-and-release-strategy.md))

### later — deferred behind demand or a measured trigger
- **Native Ollama** free-fallback adapter (latency/FP documented). ([ADR-0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md))
- Token-cost dashboard / structured-metrics export.
- Multi-linter pre-filter beyond stack default + Semgrep (config-driven).
- Autonomous learning loop — **deferred** (human curation holds, [ADR-0005](../decisions/0005-curated-knowledge-not-autonomous-learning.md)).
- Multi-forge (GitLab/Gitea) — **deferred** (plumbing is GitHub-specific).
- Standalone hosted service / dashboard — **out of scope** (separate ADR if org-scale demand appears).

## Phases (sequencing + validation gate per phase)

| Phase | Delivers | Validation gate (must pass to proceed) |
|---|---|---|
| **P0** Provider + CLI skeleton | `ModelAdapter` + Anthropic adapter; Stages 2–5 via CLI; **dry-run** | Reproduce the interactive skill's verdict on **Lucky #1263** from the CLI — **zero new P0/P1/P2** findings vs the chat review |
| **P1** Deterministic pre-filter | Stage 1 (detect/run/parse linters+Semgrep, SARIF, dedup); eval harness + drift guard | **≥30%** of findings from the pre-filter at **zero tokens** on a real PR; measured token delta vs no-prefilter |
| **P2** GitHub Action + posting | `action.yml`, composite wrapper, bot-identity wiring | Green CI run posting as the **bot** (not a personal account) on a Lucky PR; baseline SHA stamped; human can resolve threads |
| **P3** Ollama fallback | native Ollama adapter; latency/FP documented | A full review at **zero API cost**; FP rate recorded vs the Anthropic path |
| **P4** Project-aware config + learning | `.code-review.yml` path-rules + `CLAUDE.md` ingestion; curation SLA wired | A path rule **demonstrably changes** a posted finding; one curated `references/` entry added |

**Bot-identity prerequisite:** P2 depends on the GitHub App key/ID/`CODE_REVIEW_BOT_LOGIN`
being configured ([ADR-0004](../decisions/0004-github-app-posting-identity.md)). P0–P1 are
dry-run / CLI and **do not** need it, so implementation is not blocked.

## Success criteria (pilot = P0–P2), as numbers ([ADR-0023](../decisions/0023-quality-eval-harness.md))

- Posts a bot-identity review in CI on a real PR — **zero** personal-identity posts.
- FP rate **< 5%** vs the interactive-skill baseline (no new false positives spot-checked on 3–5 PRs).
- Missed **P0/P1 < 10%**.
- Token cost **≤ ~$1.50** per medium (200–600 LOC) PR.
- Pre-filter yield **≥ 30%** (zero-token findings).

## Rollback / replan triggers ([ADR-0010](../decisions/0010-headless-ci-action-runner.md))

- Action FP rate **exceeds** the interactive skill's → stop; tighten pre-filter/scoping before
  adding model spend.
- Provider-adapter or curation-SLA maintenance outgrows the solo operator → narrow providers /
  automate curation ([ADR-0022](../decisions/0022-curation-sla-and-drift-guard.md)).
- The pilot needs **>2 temporary shims** or exposes **>3 friction points** → escalate to a
  fresh `/research-and-decide` gate before continuing (no-big-bang discipline).
- The "later" cut-list stops shrinking across two phases → re-scope; don't let deferred become permanent.
