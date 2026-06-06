# ADR-0014: Provider-agnostic model-adapter interface — BYOK frontier first, Ollama as the free fallback

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0010](0010-headless-ci-action-runner.md) (provider-agnostic model)
- **Informed by:** design tracks + critic; operator decision 2026-06-06 ("BYOK would be ideal, if not, then Ollama")

## Context

ADR-0010 locked a **provider-agnostic** model: the runner must not hard-bind one vendor;
the user picks at runtime (BYO frontier API *or* local Ollama). That interface is settled.
The remaining decision is the **adapter contract** and **which adapters the value
proposition leads with**. The operator's call: **bring-your-own-key (BYOK) frontier model
is the ideal/quality path; Ollama is the free fallback** for users who can't or won't use
a paid key. Both must be first-class so "free + self-hostable" stays honest, but BYOK is
the recommended default and the path we validate quality on first.

## Decision

1. **A single minimal adapter contract**, implemented per provider, isolating all
   provider-specific concerns (auth, request shape, structured-output mechanism, caching,
   retries) from the pipeline:

   ```python
   class ModelAdapter(Protocol):
       def review(self, system_prompt: str, diff_context: str,
                  config: ReviewConfig) -> ReviewResponse: ...
       def estimate_tokens(self, text: str) -> int: ...
   ```
   `ReviewResponse = { findings: Finding[], usage: {input_tokens, output_tokens, cached, cost} }`.

2. **BYOK is the primary, recommended path.** The MVP ships a **BYOK frontier adapter**:
   Anthropic (validated first — see [ADR-0019](0019-phase-0-mvp-scope.md)) plus an
   **OpenAI-compatible** adapter (one impl that targets the `/v1/chat/completions` shape
   used by OpenAI, Together, Groq, OpenRouter, **and** a local OpenAI-compatible server).
   Provider + model + key are chosen at runtime via config/env.

3. **Ollama is the free fallback**, shipped as a native adapter (HTTP to
   `:11434/api/generate`, JSON-mode + post-hoc validation since it lacks constrained
   decoding). It is documented as the no-API-cost option with an honest latency/FP caveat.
   Because the OpenAI-compatible adapter already covers local OpenAI-compatible servers,
   the native Ollama adapter is sequenced right after BYOK validation, not before it.

4. **No third-party LLM abstraction** (LiteLLM/LangChain) — adapters are stdlib `urllib`
   calls, < ~100 LOC each.

## Alternatives considered

- **Hard-bind Anthropic only** — simplest, but kills the "free/self-hostable" value prop
  and violates ADR-0010. Rejected.
- **Ship all of Anthropic + OpenAI-native + Ollama on day one** — broadest, but three
  full adapters to debug *before* the engine's quality is even validated; muddies the
  FP-rate baseline. Rejected in favor of validate-on-BYOK-then-fan-out.
- **Adopt LiteLLM** — removes boilerplate, but adds a dependency and hides provider-specific
  caching levers. Rejected (stdlib-thin, [ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md)).
- **Ollama-first (lead with free/local)** — strong for positioning, but local-model FP
  rate is unknown and would set a noisy first impression. Deferred to fallback role.

## Consequences

**Positive:** users control cost (BYO key for quality, or free local Ollama); one
OpenAI-compatible adapter unlocks many providers + local servers at once; adding a provider
is one ~100-LOC file; the core pipeline never changes; testing mocks the adapter.

**Negative:** ≥2 adapters to maintain (each with its own retry/structured-output path);
the OpenAI-compatible and Ollama JSON-mode paths have ~1–2% parse-failure risk (mitigated
by a validation+retry layer); structured-output reliability varies by model — a documented
caveat for local models.

**Neutral:** the contract is sync (MVP); a future async/batched path can wrap the same
contract.

## Revisit when

- Local-model structured-output reliability is measured worse than a documented bar on
  real PRs → tighten validation or recommend BYOK for that repo.
- A frequently-requested provider doesn't fit the OpenAI-compatible shape → add a dedicated
  adapter (evaluate maintenance vs demand).
- More than ~3 dedicated adapters are live in the wild → formalize the contract + a
  conformance test suite.
