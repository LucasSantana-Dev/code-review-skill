# Glossary — code-review runner

**Status:** Living · **Date:** 2026-06-06

Shared vocabulary for the design package. A term defined here means the same thing in every
ADR, spec, and doc — the critic flagged ambiguous terms (blast radius, hunk, fingerprint) as a
gap, so they are pinned here.

- **Runner** — the headless engine that runs the review pipeline in CI (or via CLI) with no
  Claude Code present. ([ADR-0010](../decisions/0010-headless-ci-action-runner.md))
- **Skill** — the interactive Claude Code form (`SKILL.md`). Same judgment layer as the runner.
- **Judgment layer** — `SKILL.md` + `REFERENCE.md` + `references/`: the calibrated review
  knowledge, shared verbatim by skill and runner.
- **Dimension** — one review lens (correctness, security, maintainability, scalability,
  architecture, efficiency, resource-safety, code smells, test coverage). MVP enables
  **correctness + security**. ([ADR-0019](../decisions/0019-phase-0-mvp-scope.md))
- **Finding** — one review result: `path, line, severity, title, body, dimension,
  evidence_type, confidence, source, fingerprint, [end_line], [suggestion]`. ([ADR-0013](../decisions/0013-data-model-and-findings-schema.md))
- **Severity** — P0 blocker · P1 incorrect · P2 quality · P3 polish. (SKILL.md taxonomy.)
- **evidence_type** — `factual` (provable at file:line, no runtime context) · `behavioral`
  (input/timing dependent) · `speculative` (hunch → phrase as a question). Drives gating. ([ADR-0002](../decisions/0002-confidence-calibration-for-gating-matrix.md))
- **confidence** — `0.0–1.0`; > 0.7 high, 0.5–0.7 moderate, < 0.5 question-form.
- **Gating matrix** — the ADR-0002 severity × confidence rule deciding inline vs summary vs
  drop. Applied **only** in Stage 4. ([ADR-0018](../decisions/0018-merge-and-confidence-gating-stage-4.md))
- **Pre-filter (Stage 1)** — deterministic step that runs/parses existing linters + Semgrep
  on changed files, producing zero-token findings. ([ADR-0015](../decisions/0015-deterministic-pre-filter-stage-1.md))
- **Hunk** — a contiguous block of changed lines in a diff (a `@@ … @@` section), the unit
  Stage 2 scopes around.
- **Context radius (N)** — lines of unchanged code kept before/after each hunk for the LLM.
  Default **N=10**, tunable. ([ADR-0016](../decisions/0016-diff-scope-and-trivial-skip-stage-2.md))
- **Blast radius** — the set of code a change could break beyond the changed lines (callers,
  invariants, contracts). MVP scope = changed file + direct imports; wider blast radius is a
  documented limitation. ([ADR-0016](../decisions/0016-diff-scope-and-trivial-skip-stage-2.md))
- **Trivial-skip** — skipping the LLM when a diff is below the LOC threshold (default 50) and
  whitespace/comment/rename-only. Opt-out (`skip_trivial: false`).
- **Fingerprint** — the dedup key `path:line:category_slug` (`category_slug` = normalized rule
  id / defect class). Equal fingerprints collapse to one finding in Stage 4.
- **SARIF** — Static Analysis Results Interchange Format (2.1.0); the normalized format the
  pre-filter prefers when parsing linter/Semgrep output. ([ADR-0015](../decisions/0015-deterministic-pre-filter-stage-1.md))
- **Adapter** — a per-provider implementation of the `ModelAdapter` contract; isolates
  auth/request/structured-output/caching/retries from the pipeline. ([ADR-0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md))
- **BYOK** — Bring Your Own Key: the user supplies a frontier-model API key (the quality path).
- **Ollama / free fallback** — local model path (no API cost), the fallback when BYOK isn't used.
- **Structured output** — provider mechanism that forces schema-valid JSON (Anthropic
  constrained decoding; OpenAI JSON-schema; Ollama JSON-mode + validate-and-retry).
- **Dry-run** — compute + write `findings.json`/`summary.md`, post nothing. Phase-0 mode.
- **Baseline SHA** — the commit stamped in a posted review's body; re-review diffs against it.
- **Re-review** — incremental re-run on a new push, scoped to the delta since the baseline SHA;
  resolves the bot's own threads only.
- **Bot identity** — the GitHub App (`…[bot]`) the runner posts as; `CODE_REVIEW_BOT_LOGIN`
  guards against personal-account posts. ([ADR-0004](../decisions/0004-github-app-posting-identity.md))
- **Curation SLA** — the human-in-loop commitment to refresh `references/` (~1–2 hrs/mo per
  active repo), measured by the drift guard. ([ADR-0022](../decisions/0022-curation-sla-and-drift-guard.md))
- **Drift guard** — a coverage report flagging defect classes seen in reviews but not covered
  by any `references/` entry. ([ADR-0022](../decisions/0022-curation-sla-and-drift-guard.md))
- **Eval harness** — the off-path tool measuring FP/FN/precision/recall/cost on labeled test
  PRs. ([ADR-0023](../decisions/0023-quality-eval-harness.md))
