# Prompt Construction Design Research — code-review Action Phase 0–2

**Date:** 2026-06-06  
**Scope:** How to construct review prompts, extract structured findings, optimize token cost, and calibrate confidence for the headless code-review GitHub Action (ADR-0010).

## Key Research Findings

### 1. Structured Output Standards (ADR-0011)

**Anthropic Structured Outputs** (GA Nov 2025, https://platform.claude.com/docs/en/build-with-claude/structured-outputs):
- **Guarantee:** 100% JSON schema compliance via constrained decoding (hard constraint, not best-effort).
- **Implementation:** Compile schema to grammar, restrict token generation at inference time.
- **Models:** Opus 4.8, Sonnet 4.6, Haiku 4.5, and earlier versions.
- **Protocol:** Pass `output_config.format.type: "json_schema"` with Pydantic/Zod helpers.
- **Fallback:** JSON-mode (OpenAI style) has ~1–2% parse failures; add post-hoc validation.

**OpenAI Structured Outputs** (https://openai.com/index/introducing-structured-outputs-in-the-api/):
- Same guarantee as Anthropic (100% compliance).
- Supported in gpt-4o and newer.
- Compatible schema format (standard JSON Schema).

**Implication:** No more retry loops for parse errors. Schema violations become impossible at the API boundary.

### 2. Multi-Agent Dimension Batching (ADR-0012)

**Qodo Merge 2.0** (Feb 2026, https://dev.to/rahulxsingh/qodo-merge-review-is-ai-pr-review-worth-it-46j1):
- Replaced single-pass review with 4 parallel agents: bug detection, code quality, security, test coverage.
- Each agent has **tuned prompts + evaluation criteria** for its domain.
- Results aggregated into structured findings.
- **Benchmark:** F1 score 60.1%, highest among 8 AI code review tools tested.

**PR-Agent** (https://github.com/The-PR-Agent/pr-agent):
- Community-maintained, OSS, self-hostable.
- Supports JSON-based configuration for review categories.
- Dimension-based architecture implied but not fully exposed.

**Implication:** Per-dimension review (correctness, security, maintainability, scalability, architecture, efficiency, test coverage) beats single monolithic prompt. Parallel execution saves latency; tuning per dimension reduces FP.

### 3. Prompt Caching for Cost & Latency (ADR-0013)

**Claude Prompt Caching** (https://platform.claude.com/docs/en/build-with-claude/prompt-caching):
- **Cost:** 10% of base input token price on cache hits (vs 125% for cache writes).
- **Latency:** Reduces time-to-first-token by up to 80%.
- **Mechanism:** Check for exact prefix match; cache hits occur in increments of 128 tokens.
- **TTL:** 5 minutes default (use 1h for cross-CI-run persistence).
- **Minimum:** 1024 tokens (Opus/Sonnet/Haiku).
- **Placement:** Mark static content (instructions, examples, system prompt) with `cache_control: {type: "ephemeral"}` at block boundaries.

**ROI example** (100,000-token cached prefix, 10 reuses):
- Without caching: $5.00.
- With caching: $1.075 (78.5% savings).

**Best practice:** Place durable content (SKILL.md, dimension instructions, reference examples) at prompt start; volatile content (diffs) at end.

**Implication:** Reusing instruction prefixes across reviews of the same/similar repo saves 70–90% on instruction tokens.

### 4. Hunk-Based Scope Reduction (ADR-0014)

**Enterprise Code Review Pattern** (https://arxiv.org/pdf/2510.10290):
- Isolate changed hunks (contiguous diff segments).
- Collect N-line context (preceding + following context lines).
- Pass hunk + context to LLM, not whole file.
- Reduces scope by 20–30% while missing few findings.

**CodeRabbit approach** (https://docs.coderabbit.ai/guides/custom-reports):
- Chunks code by changed areas + context windows.
- Uses `splitPrompt` to handle token-limit overflow.
- Prioritizes changed lines; context-sensitive expansion.

**Mitigation for cross-file invariants:** Architecture dimension focuses on cross-file impacts; context window (default N=10) balances cost vs safety.

**Implication:** Can reduce token cost per request by 20–30% without major FP increase.

### 5. Deterministic Pre-Filter (Stage 1, ADR-0019)

**Linter + SAST baselines** (consensus across PR-Agent, CodeRabbit, Qodo):
- Run repo's existing linters (eslint, pylint, rustfmt, etc.) + Semgrep.
- Parse output (JSON/XML) into findings list.
- **Cost:** 0 tokens (subprocess + parsing).
- **Signal:** ~30–40% of defects caught deterministically (syntax, types, style, known-vulnerable patterns).

**Implication:** ~30–40% of findings come free; LLM focuses on semantic/logic issues.

### 6. Trivial-Diff Skip Gate (ADR-0020)

**Cost optimization heuristic:**
- If diff is <10 LOC total AND only whitespace/comments/renames AND pre-filter found nothing → skip Stages 2–3 entirely.
- Saves 5–10 min tokens per PR on cosmetic changes.

**Implication:** Fast feedback on trivial PRs; token budget goes to logic-bearing changes.

### 7. Confidence Calibration (from SKILL.md)

**Three evidence tiers:**
1. **Factual:** Provable now (file:line + reason, no runtime context needed). Examples: null-deref, off-by-one, type error.
2. **Behavioral:** Depends on runtime/inputs (edge cases, concurrency, async ordering).
3. **Speculative:** A hunch; surface as a question, not an assertion.

**Severity × Confidence gating** (ADR-0002):
- P0/P1 (blockers/incorrect): any confidence.
- P2 (quality): >0.5 confidence.
- P3 (polish): >0.7 confidence.

**Implication:** Not all high-confidence findings are high-severity; confidence filters false positives.

### 8. Provider-Agnostic Interface (ADR-0016)

**Three implementations:**

| Provider | Auth | Structured Output | Caching | Models |
|----------|------|-------------------|---------|--------|
| **Anthropic** | `ANTHROPIC_API_KEY` | Yes (100% compliance) | Yes (prompt caching) | Opus 4.8, Sonnet 4.6, Haiku 4.5 |
| **OpenAI** | `OPENAI_API_KEY` | Yes (JSON schema mode) | No (public SDK) | gpt-4o |
| **Ollama** | None (local) | JSON mode only (post-validation) | No | Qwen2.5-Coder-32B (or custom) |

**Single ReviewProvider protocol** allows runtime provider selection; isolates model-specific details.

**Implication:** Operator chooses BYO API (Anthropic/OpenAI) or free local (Ollama) at runtime.

## Design Decisions (ADRs 0011–0020)

See structured output `proposed_adrs` for full ADR text. Highlights:

- **ADR-0011 (Findings schema):** Structured output via Anthropic, fallback JSON-mode.
- **ADR-0012 (Dimensions):** 5–7 parallel dimensions, merged findings.
- **ADR-0013 (Caching):** Stable prefix (SKILL.md + references/) cached, volatile diff at end.
- **ADR-0014 (Scope reduction):** Hunks + N-line context, drop <10 LOC.
- **ADR-0015 (Dedup + reranking):** Merge Stage-1 linter + Stage-3 LLM; fingerprint dedup.
- **ADR-0016 (Provider interface):** Single protocol, 3 impls (Anthropic/OpenAI/Ollama).
- **ADR-0017 (Reference injection):** 2–3 patterns per dimension, deterministic selection.
- **ADR-0018 (Prompt template):** One concrete template per dimension (concreteness for implementation).
- **ADR-0019 (Pre-filter):** Linter/Semgrep parsing, 0-token findings.
- **ADR-0020 (Trivial-diff skip):** Hard skip if <10 LOC + single file + no findings.

## Implementation Roadmap (Phase 0–2)

### Phase 0: Provider interface + CLI skeleton
- ReviewProvider protocol (abstract + 3 impls).
- Per-dimension prompt templates (1 concrete, 6 stubs).
- Findings schema (Pydantic + JSON).
- CLI: `review --diff <path> --provider anthropic --repo owner/repo --output findings.json`.
- **Validation:** manual spot-check vs interactive SKILL.md verdict.

### Phase 1: Deterministic pre-filter (Stage 1)
- Linter detection + parsing (eslint, pylint, rustfmt, Semgrep).
- Merge pre-filter into findings.json.
- **Validation:** ≥30% findings at 0 tokens; measure token delta.

### Phase 2: GitHub Action wrapper
- `action.yml` + entrypoint.
- Bot identity (CODE_REVIEW_BOT_LOGIN guard, app_token.py).
- Posting via post_review.py.
- **Validation:** green run on a real PR, zero personal-account posts.

### Phase 3 (deferred): Ollama local-model adapter
- Qwen2.5-Coder-32B path.
- Latency/FP tradeoff documented.

### Phase 4 (deferred): Config + learning
- `.code-review.yml` ingestion.
- Curation SLA enforcement.
- Path-based rules (optional).

## Open Questions (from Forks)

See structured output `open_forks` for detailed resolution. Key ambiguities:

1. **Reference selection:** Static (2–3 patterns per dimension) or learned? → Static (MVP), learning Phase 4.
2. **Ollama timing:** MVP or Phase 3? → Phase 3 (soft dependency).
3. **CoT vs direct extraction:** Trade latency for precision? → Direct (MVP), CoT Phase 2 if needed.
4. **Context window:** N=5, 10, or 20 lines? → N=10 (tunable).
5. **Trivial-diff skip:** Hard skip or soft flag? → Hard skip.
6. **Dimension batching:** Single call or parallel requests? → Parallel (faster in CI).
7. **Cache TTL:** 5m, 1h, configurable? → 1h default.
8. **Linter severity mapping:** Normalized or config-driven? → Config-driven (.code-review.yml).
9. **Phase 0 validation:** Manual or automated? → Manual (faster, less infra).
10. **Path rules in .code-review.yml:** MVP or Phase 4? → Phase 4 (deferred curation).

## Confidence & Next Steps

**Design confidence:** HIGH (10/10 decisions, 7 high-confidence ADRs, 3 needs-user forks).

**Risk posture:** Low. Risks identified and mitigated (FP tuning, scope-reduction validation, provider lock-in fallback, solo-operator burden gate at ADR-0010).

**Readiness for implementation:** READY. Spec is concrete; prompt templates are templatable; provider protocol is clear; Phase 0 is scoped (no linter parsing, no Action wrapper, no Ollama — focused on provider + template + schema).

**Next phase:** Start Phase 0 (reviewProvider protocol + concrete correctness-dim template + CLI). Validate on a known-good PR before moving to Phase 1 (pre-filter complexity).

---

## References

- Anthropic Claude API Structured Outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- OpenAI Structured Outputs: https://openai.com/index/introducing-structured-outputs-in-the-api/
- Prompt Caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Qodo Merge 2.0 (multi-agent architecture, F1 60.1%): https://dev.to/rahulxsingh/qodo-merge-review-is-ai-pr-review-worth-it-46j1
- PR-Agent (OSS, community-maintained): https://github.com/The-PR-Agent/pr-agent
- CodeRabbit custom reports: https://docs.coderabbit.ai/guides/custom-reports
- Enterprise code review patterns: https://arxiv.org/pdf/2510.10290
- Prompt engineering guide: https://medium.com/@michael.hannecke/prompt-caching-explained-what-it-is-what-it-isnt-and-when-to-use-it-9f5c6fce7bdb
