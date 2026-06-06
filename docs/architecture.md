# Architecture — code-review headless CI Action runner

**Status:** Design (pre-code) · **Date:** 2026-06-06 · **Decisions:** [ADR-0010](../decisions/0010-headless-ci-action-runner.md)–[ADR-0024](../decisions/0024-versioning-and-release-strategy.md)

The runner runs the **existing** review engine — `SKILL.md` judgment, `REFERENCE.md`
checklists, the forkable `references/` library, and the `post_review.py` / `app_token.py`
plumbing — **headless in CI, with no Claude Code present**, driven by any LLM (BYO frontier
key, or local Ollama). It is a *semantic* reviewer that assumes linters/SAST already ran;
it is **not** a linter and not "Sonar 2.0". This document is the system map; the per-decision
rationale lives in `decisions/`.

## 1. Principles (the constraints every choice answers to)

- **Thin & stdlib** — Python ≥3.9, standard library only in production; shell out to
  `git`/`gh`/linters/Semgrep; no required third-party deps. ([ADR-0011](../decisions/0011-monorepo-structure-and-python-stdlib-runtime.md))
- **Reuse, don't rebuild** — one judgment layer + one posting layer, shared with the
  interactive skill; the runner is a headless wrapper. ([ADR-0010](../decisions/0010-headless-ci-action-runner.md))
- **Optimized AI, not no-AI** — deterministic pre-filter + diff-scoping carry the cheap
  findings; the LLM does the semantic work. ([ADR-0012](../decisions/0012-five-stage-pipeline-architecture.md))
- **Calibrated** — every finding carries `dimension` + `evidence_type` + `confidence`; the
  ADR-0002 gate decides what posts. ([ADR-0013](../decisions/0013-data-model-and-findings-schema.md), [ADR-0018](../decisions/0018-merge-and-confidence-gating-stage-4.md))
- **Provider-agnostic** — BYOK frontier is the quality path; Ollama is the free fallback;
  the pipeline never hard-binds a vendor. ([ADR-0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md))

## 2. The 5-stage pipeline

```
                ┌──────────────────────────── ReviewContext ───────────────────────────┐
   PR / diff ──▶│  (pr, repo, base_sha, head_sha, changed_files, hunks, repo_config)    │
                └──────────────────────────────────────────────────────────────────────┘
                       │
  Stage 1  PRE-FILTER  │  run/parse linters + Semgrep on changed files (SARIF→Finding)
  (0 tokens)           │  → prefilter_findings: Finding[]   evidence=factual, conf≈0.99
                       ▼
  Stage 2  SCOPE       │  diff → changed hunks + N=10 context; collapse; drop trivial;
  (0 tokens)           │  budget-guard (truncate at hunk boundary) → scoped diff
                       ▼
  Stage 3  LLM REVIEW  │  per-dimension prompt = SKILL.md + REFERENCE.md + 2–3 references/
  (tokens)             │  + ADR-0002 calibration rubric + "don't re-flag Stage-1" context
                       │  → llm_findings: Finding[]  (structured output; tagged by dimension)
                       ▼
  Stage 4  MERGE+GATE  │  dedup Stage1 ∪ Stage3 by fingerprint; apply ADR-0002 matrix;
  (0 tokens)           │  sort; mark fix-eligibility → gated_findings: Finding[]
                       ▼
  Stage 5  POST        │  post_review.py → batched PR review + resolvable inline threads
  (0 tokens)           │  (bot identity via app_token.py); or dry-run → findings.json+summary.md
                       ▼
              re-review loop: on push, diff vs stamped baseline SHA → Stages 2–4 on delta
```

Stages share **no mutable state**; each consumes a typed input and returns typed output, so
each is independently testable, profileable, and skippable. The orchestrator
(`runner/pipeline.py`) is the only component that knows the order.
([ADR-0012](../decisions/0012-five-stage-pipeline-architecture.md))

## 3. Data model (the contract between stages)

Immutable, hashable stdlib dataclasses ([ADR-0013](../decisions/0013-data-model-and-findings-schema.md)):

- `DiffHunk(path, start_line, end_line, content, side)`
- `Finding(path, line, severity, title, body, dimension, evidence_type, confidence,
  source, fingerprint, end_line?, suggestion?)` — hashes on `fingerprint =
  path:line:category_slug`, so a linter + the LLM flagging the same issue collapse to one.
- `ReviewContext(pr, repo, base_sha, head_sha, changed_files, hunks, repo_config,
  prefilter_findings)`

`dimension`, `evidence_type`, and `confidence` are **first-class** — without them the
ADR-0002 gate (Stage 4) cannot run and the skill's judgment would be flattened to
linter-level noise (the critic's blocking finding).

## 4. How the skill's judgment reaches a headless LLM (the crux)

There is no Claude Code in CI, so the judgment must be **transmitted as a prompt and
recovered as structured data** ([ADR-0017](../decisions/0017-prompt-construction-and-structured-output-stage-3.md)):

1. **System prompt = the judgment layer, assembled per dimension:** the dimension's
   `SKILL.md` checklist + `REFERENCE.md` section + 2–3 advisory `references/` entries chosen
   by defect class (interpolated, **not** RAG — [ADR-0006](../decisions/0006-references-retrieval-advisory-then-defer.md)) + the **ADR-0002 calibration rubric verbatim** + the output schema.
2. **User prompt = volatile context:** the Stage-2 scoped diff + the Stage-1 findings marked
   "already reported, do not re-flag."
3. **Calibration is in the prompt, not hoped for:** only cite `factual` with `file:line` +
   reason; otherwise `behavioral`/`speculative`; `confidence < 0.5` must be phrased as a
   question. Every finding emits `dimension`/`evidence_type`/`confidence`.
4. **Structured output, tiered by provider reliability:** Anthropic Structured Outputs
   (constrained decoding) → OpenAI-compatible JSON-schema → Ollama JSON-mode + validate-and-
   retry. One shared schema, `additionalProperties:false`.
5. **MVP is one serial batched call** over the enabled dimensions (correctness + security);
   the prefix is structured so it can later become a **cache breakpoint** and the call can
   fan out to **parallel per-dimension** without a rewrite (both deferred —
   [ADR-0019](../decisions/0019-phase-0-mvp-scope.md)).

## 5. Provider abstraction

One contract, provider-specific impls ([ADR-0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md)):

```python
class ModelAdapter(Protocol):
    def review(self, system_prompt: str, diff_context: str, config: ReviewConfig) -> ReviewResponse: ...
    def estimate_tokens(self, text: str) -> int: ...
# ReviewResponse = { findings: Finding[], usage: {input_tokens, output_tokens, cached, cost} }
```

| Adapter | Role | Structured output | Caching | Ships |
|---|---|---|---|---|
| **Anthropic** (BYOK) | quality path, validated first | constrained decoding | native (later phase) | P0 |
| **OpenAI-compatible** (BYOK) | OpenAI/Together/Groq/OpenRouter + local OpenAI servers | JSON-schema/JSON-mode | provider-dependent | P1 |
| **Ollama** (local) | free fallback | JSON-mode + retry | none | P3 |

Default model names use current identifiers (e.g. `claude-sonnet-4-6` for cost/quality,
`claude-opus-4-8` for max quality) — not legacy aliases.

## 6. Posting & re-review (reused, unchanged)

Stage 5 calls `post_review.py` to post one **batched** review (summary + one resolvable
inline thread per finding), stamping the baseline SHA in the body. On the next push the
runner reads the baseline + open threads, re-runs Stages 2–4 on the delta, and replies /
resolves **its own** threads only (never a human's). The GitHub App bot token is minted
in-action by `app_token.py`; `CODE_REVIEW_BOT_LOGIN` refuses any non-bot identity.
([ADR-0004](../decisions/0004-github-app-posting-identity.md), [ADR-0020](../decisions/0020-github-action-packaging-and-ci-security.md))

## 7. Security model (CI)

- **`pull_request` trigger, never `pull_request_target`** — no base-repo secrets exposed to
  untrusted fork code (mitigates Poisoned Pipeline Execution). ([ADR-0020](../decisions/0020-github-action-packaging-and-ci-security.md))
- **Least privilege:** `contents: read`, `pull-requests: write`, `metadata: read`.
- **Secrets** (LLM key, App private key) are workflow `secrets.*` passed as inputs — never
  logged, never echoed.
- **Composite action** — no container, no new deps; assumes Python 3.9 + `git` + `gh` +
  `openssl` (documented prerequisite).
- **Bot-identity guard** structurally prevents a misconfigured CI from posting as a person.

## 8. Module map (target)

```
runner/
  pipeline.py        # orchestrator: stage order, dry-run vs post
  models.py          # Finding, DiffHunk, ReviewContext  (ADR-0013)
  config.py          # .code-review.yml + inputs + CLAUDE.md  (ADR-0021)
  stages/
    prefilter.py     # Stage 1  (ADR-0015)
    scope.py         # Stage 2  (ADR-0016)
    llm_review.py    # Stage 3  (ADR-0017)
    merge.py         # Stage 4  (ADR-0018)
    post.py          # Stage 5 → scripts/post_review.py
  adapters/
    base.py          # ModelAdapter contract  (ADR-0014)
    anthropic.py     # BYOK, validated first
    openai_compat.py # BYOK OpenAI-compatible (P1)
    ollama.py        # free fallback (P3)
  prompts/           # per-dimension templates  (ADR-0017)
scripts/             # post_review.py, app_token.py   (existing, unchanged)
references/          # forkable knowledge layer       (existing, shared)
eval/                # quality harness + drift guard   (ADR-0022, ADR-0023)
action.yml           # composite action               (ADR-0020)
```

See [repo-structure.md](repo-structure.md) for the full tree and
[roadmap.md](roadmap.md) for what lands in which phase.
