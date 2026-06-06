# Spec & Plan — Headless CI Action Runner

**Status:** Planned · **Decision:** [ADR-0010](../../decisions/0010-headless-ci-action-runner.md) ·
**Date:** 2026-06-06

A thin GitHub Action that runs the existing review engine headless in CI (no Claude Code present),
against a BYO or local model. Free + self-hostable + lightweight. Positioned on the open curated
knowledge layer, **not** as a generic CodeRabbit/PR-Agent clone.

## Goal

`code-review` reviews a PR in CI and posts a CodeRabbit-style batched review (summary + resolvable
inline threads) as the bot identity — using the same judgment (`SKILL.md`/`REFERENCE.md`/`references/`)
and plumbing (`post_review.py`/`app_token.py`) as the interactive skill, driven by any LLM.

## In scope

- A GitHub Action (`action.yml` + a runner entrypoint) + a callable CLI (same entrypoint).
- A **provider-agnostic model interface**: one adapter contract, impls for (a) BYO frontier API key
  (Anthropic/OpenAI/compatible), (b) local Ollama. Provider chosen by config/env at runtime.
- A **deterministic pre-filter** stage (run/parse existing linters + Semgrep where present) that
  resolves concrete violations at zero token cost and shrinks the LLM's surface.
- **Cost-optimized LLM pass**: diff-scoping (changed hunks + minimal blast radius), prompt caching,
  per-dimension batching, skip-trivial-diff guard.
- **Project-aware config**: read repo `CLAUDE.md`/`AGENTS.md` + a `.code-review.yml` (path rules,
  enabled dimensions, severity floor, model/provider, budget) + the curated `references/`.
- Reuse `post_review.py` for posting + the fix→re-review baseline loop.

## Out of scope (deferred / explicit non-goals)

- A standalone hosted service / multi-tenant dashboard / webhook server (→ separate ADR; fork-PR-Agent
  vs build-new comparison if org-scale ambition appears).
- Heavy/portable RAG index (ADR-0006 holds — deferred).
- Autonomous learning loop (ADR-0005 holds — curation stays human-in-loop).
- Re-implementing linters/SAST (we assume they ran; we consume their output, we are not "Sonar 2").

## Runner I/O contract (the spec)

```
Input:  --pr <N> | --diff <path> ; --repo owner/name ; provider+model config ; .code-review.yml
Stage 1 (deterministic): run/parse available linters+semgrep → concrete findings (0 tokens)
Stage 2 (scope):         diff → changed hunks + blast radius; drop trivial; build minimal context
Stage 3 (LLM review):    per-dimension prompts (SKILL.md taxonomy + relevant references/) → findings
                         JSON {path,line,severity,title,body[,suggestion]} ; prompt-cached
Stage 4 (merge):         dedup Stage-1 ∪ Stage-3; severity-classify; confidence-gate (ADR-0002)
Stage 5 (post):          post_review.py post <N> findings.json --body-file summary.md --event <…>
                         (bot identity via app_token.py; COMMENT unless P0/P1)
Re-review:               incremental against the stamped baseline SHA (existing loop)
Exit:                    non-zero only on infra error; review verdict is data, not a gate (configurable)
```

## Phased plan

- **Phase 0 — Provider interface + CLI skeleton.** Define the model-adapter contract; implement the
  BYO-API adapter; CLI that runs Stages 2–5 on a local diff (no Action yet). *Validate:* reproduce the
  interactive skill's verdict on Lucky #1263 from the CLI.
- **Phase 1 — Deterministic pre-filter (Stage 1).** Detect + parse repo linters/Semgrep; merge/dedup
  into findings. *Validate:* ≥30% of findings resolved with zero tokens on a real PR; measured token
  delta vs no-prefilter.
- **Phase 2 — GitHub Action wrapper.** `action.yml`, inputs (provider, model, budget, config path),
  bot-identity wiring. *Validate:* green run on a Lucky PR posting as the bot from CI.
- **Phase 3 — Local-model adapter (Ollama).** Qwen2.5-Coder-32B path; document the latency/FP tradeoff.
  *Validate:* a full review with zero API cost; FP rate recorded vs the API path.
- **Phase 4 — Project-aware config + learning.** `.code-review.yml` + `CLAUDE.md`/`AGENTS.md` ingestion;
  document the curation SLA. *Validate:* a path-rule demonstrably changes a finding.

## Success criteria (pilot = Phase 0–2)

- Posts a bot-identity review in CI on a real PR, matching the interactive skill's verdict quality
  (spot-checked: no new false positives vs the chat review).
- Token cost per medium PR is measured and ≤ the BYO-API target (~$0.30–1.50); ≥30% findings from the
  zero-token pre-filter.
- Zero personal-identity posts (the `CODE_REVIEW_BOT_LOGIN` guard holds in CI).

## Rollback / replan triggers

- FP rate from the Action exceeds the interactive skill's → stop, tighten pre-filter/scoping before more.
- Provider-adapter or curation maintenance outgrows the solo operator → narrow providers / automate curation.
- The pilot needs >2 temporary shims or exposes >3 friction points → escalate to a fresh decision
  (per the no-big-bang gate) before continuing.

## Open prerequisite (carried over)

Bot posting identity (GitHub App key/ID/login) is **not yet configured** — Phase 2 depends on it
(see `pilot_review_1_and_posting_blocker` memory + ADR-0004). Wire it before Phase 2.
