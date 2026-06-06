# Architecture Decision Records

Numbered, append-only decisions. Each records the *why* so it isn't rediscovered later.
Format: Context · Decision · Alternatives · Consequences · Revisit when.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-reviewers-and-fixers.md) | Reviewers and fixers | Accepted |
| [0002](0002-confidence-calibration-for-gating-matrix.md) | Confidence calibration for the gating matrix | Accepted |
| [0003](0003-keep-bundled-script-skill-packaging.md) | Keep bundled-script skill packaging | Accepted (Action superseded by 0010/0020) |
| [0004](0004-github-app-posting-identity.md) | GitHub App posting identity | Accepted |
| [0005](0005-curated-knowledge-not-autonomous-learning.md) | Curated knowledge, not autonomous learning | Accepted |
| [0006](0006-references-retrieval-advisory-then-defer.md) | References retrieval advisory, then defer | Accepted |
| [0007](0007-distribution-license-contribution.md) | Distribution / license / contribution | Accepted |
| [0008](0008-permissive-not-copyleft-for-the-corpus.md) | Permissive (Apache-2.0), not copyleft | Accepted |
| [0009](0009-cross-agent-reach-defer-with-decision-tree.md) | Cross-agent reach — defer with decision tree | Accepted |
| [0010](0010-headless-ci-action-runner.md) | Headless CI Action runner (extend, don't clone) | Accepted |
| **[0011](0011-monorepo-structure-and-python-stdlib-runtime.md)** | Monorepo extension + Python-stdlib runtime | Accepted |
| **[0012](0012-five-stage-pipeline-architecture.md)** | Five-stage pipeline architecture | Accepted |
| **[0013](0013-data-model-and-findings-schema.md)** | Data model + findings schema (dimension/evidence/confidence) | Accepted |
| **[0014](0014-provider-agnostic-adapter-byok-first-ollama-fallback.md)** | Provider adapter — BYOK first, Ollama fallback | Accepted |
| **[0015](0015-deterministic-pre-filter-stage-1.md)** | Deterministic pre-filter (Stage 1) | Accepted |
| **[0016](0016-diff-scope-and-trivial-skip-stage-2.md)** | Diff-scope + trivial-skip (Stage 2) | Accepted |
| **[0017](0017-prompt-construction-and-structured-output-stage-3.md)** | Prompt construction + structured output (Stage 3) | Accepted |
| **[0018](0018-merge-and-confidence-gating-stage-4.md)** | Merge + confidence×evidence gating (Stage 4) | Accepted |
| **[0019](0019-phase-0-mvp-scope.md)** | Phase-0 MVP scope (+ cut-list) | Accepted |
| **[0020](0020-github-action-packaging-and-ci-security.md)** | GitHub Action packaging + CI security | Accepted |
| **[0021](0021-config-schema-code-review-yml.md)** | Config schema (`.code-review.yml`) | Accepted |
| **[0022](0022-curation-sla-and-drift-guard.md)** | Curation SLA + drift guard | Accepted |
| **[0023](0023-quality-eval-harness.md)** | Quality/eval harness | Accepted |
| **[0024](0024-versioning-and-release-strategy.md)** | Versioning + release strategy | Accepted |

ADR-0011 … 0024 are the **pre-code design package** for the CI Action runner — see
[docs/DESIGN.md](../docs/DESIGN.md) for the package overview and reading order.
