# ADR-0010: Extend with a headless GitHub Action runner (CI-runnable, BYO/local model) — not a standalone CodeRabbit clone

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** ADR-0003 (kept it a skill, "not MCP/CLI/Action" — the Action is now the justified demand trigger), ADR-0009 (Claude-Code-first; this is the deferred headless/cross-agent trigger firing)
- **Informed by:** `/research-and-decide` (5 parallel research angles + adversarial critic, 2026-06-06)

## Context

The goal raised: a "free, self-hostable, optimized, lightweight CodeRabbit alternative," possibly
**without AI**. Research + critic (verdict: BUILD-WITH-CHANGES) reshaped it:

- **"Without AI" is not viable for semantic review.** Deterministic-only catches ~30–40% (linter/SAST
  level); ~76% of real defect classes (intent-vs-implementation, cross-file invariants,
  missing-error-paths) require LLM reasoning. A no-AI reviewer *is* "Sonar 2" — the rejected thing.
  Semantic review **requires** an LLM; the lever is making it **cheap**, not removing it.
- **A generic self-hostable clone would be redundant.** PR-Agent / Qodo Merge already exist (OSS,
  self-hostable, BYO-LLM, ~15K★) and CodeRabbit has a free tier. Competing head-on is a rebuild.
- **The real, non-redundant edge** is this project's **open, forkable, curated `references/`
  knowledge layer + calibration discipline** (SKILL.md) — not "another reviewer."

## Decision

**Build a thin headless GitHub Action runner that extends the existing skill — do NOT build a
standalone CodeRabbit-scale product.** The Action:

1. **Reuses the engine** — the review judgment (`SKILL.md` / `REFERENCE.md` / `references/`) and the
   PR plumbing (`post_review.py` + `app_token.py`, already Python-stdlib + bot identity).
2. **Provider-agnostic model** — BYO frontier API key (Anthropic/OpenAI/…) **or** a local model via
   Ollama. The user picks at runtime; the runner doesn't hard-bind a provider.
3. **"Lightweight" = optimized AI usage, not no-AI** — a deterministic pre-filter (existing linters/
   Semgrep) handles the ~40% of findings that don't need an LLM at zero token cost; the LLM pass is
   diff-scoped (changed hunks + minimal blast radius) + prompt-cached. Skip trivial diffs.
4. **Runs headless in CI** — no Claude Code present, no server/queue/dashboard. Free (BYO key or local),
   self-hostable (it's *your* CI + *your* model), lightweight (a script + a model you point at).
5. **Positioned as a semantic reviewer** that assumes linters/SAST already ran — explicitly NOT a
   linter, NOT Sonar. Differentiation = the open knowledge layer + cost optimization + self-hosting.
6. **Learning is owned honestly** — read repo `CLAUDE.md`/`AGENTS.md`/path-rules + the curated
   references; declare a curation SLA (~1–2 hrs/month per active repo). Heavy RAG stays deferred
   (ADR-0005/0006 hold).

**Explicitly deferred:** a true standalone product and the **fork-PR-Agent-vs-build-new** comparison —
a separate ADR, only if org-scale ambition appears.

## Alternatives considered

- **Standalone self-hosted product (fork PR-Agent or build new)** — rejected now: crowded market
  (PR-Agent + CodeRabbit-free), high solo-maintenance burden, redundant without a sharp niche. Kept as
  a future, separately-gated decision.
- **Stay skill-only** — rejected: there's real demand for CI/headless review and the Action is a cheap,
  high-reuse extension; not building it leaves the engine locked inside interactive Claude Code.
- **Without-AI / deterministic-only** — rejected: it's a linter/SAST (the "Sonar 2" we refuse), ~30–40%
  signal. Category error, not a feature trade.
- **Hard-bind one model/provider** — rejected: provider-agnostic (BYO + local) is what makes it "free"
  for everyone and avoids single-vendor pricing/availability risk.

## Consequences

**Positive:** delivers free + self-hostable + lightweight honestly; reuses the working engine (no
rebuild); positions on the defensible open knowledge layer; fires ADR-0009's trigger with the *thin*
option, not the heavy infra it warned against.

**Negative:** reverses ADR-0003's "no Action" stance (accepted — demand now exists); a new artifact to
maintain (Action + provider adapters); GitHub-App/CI plumbing has real edge cases; **learning/curation
is now mandatory** for competitive false-positive rates, with a declared SLA; still adjacent to a
crowded market — the wedge must stay the knowledge layer, not feature-parity.

**Neutral:** the interactive Claude Code skill is unchanged; the Action is an additional form factor
over the same engine.

## Revisit when

- The Action's review quality (FP rate) on real PRs is worse than the interactive skill → tighten the
  deterministic pre-filter / scoping before adding model spend.
- Org-scale / multi-tenant demand appears → open the deferred standalone-product + fork-PR-Agent ADR.
- Maintaining provider adapters or the curation SLA outgrows the solo operator → narrow providers or
  automate curation before it stagnates (ADR-0005's stagnation risk).
- A frontier model gets cheap enough that the deterministic pre-filter stops paying for itself → simplify.
