# Documentation plan

**Status:** Design (pre-code) · **Date:** 2026-06-06 · **Decision:** doc structure per design track 7

What user-facing docs will exist, what each covers, and **when** it's written. We write the
**plan** now (pre-code) and the docs themselves as their feature lands — we do not write
user guides for unbuilt features. Tone throughout: technical, CLI-first (no screenshots),
**honest about limitations** ("we assume linters ran", "FP rate is X%", "cross-file invariants
beyond the diff are out of local scope").

## Principle: link, don't duplicate

`SKILL.md` / `REFERENCE.md` remain the canonical judgment layer. Docs **link** to them
(`See REFERENCE.md#correctness`) rather than restating checklists — one source of truth.

## Planned docs

| Doc | Audience | Covers | Lands |
|---|---|---|---|
| **README.md** (expanded) | first-time visitor | what it is (semantic reviewer that finds what linters miss) · why (the open forkable `references/`) · skill vs Action · install both · **copy-paste quick start** · cost estimate · FAQ | P2 |
| **docs/ACTION.md** | adopter | how the Action works (5 stages, brief) · setup + prerequisites · `action.yml` inputs/outputs · re-review loop · troubleshooting (no diff, budget hit, linter absent, bad key) · perf tips | P2 |
| **docs/CLI.md** | local user / CI-on-other-platforms | `python3 -m runner` usage · dry-run examples · output format (`findings.json`/`summary.md`) | P0 |
| **docs/PROVIDERS.md** | adopter | **BYOK** setup (Anthropic; OpenAI-compatible incl. Together/Groq/OpenRouter) · **Ollama** free fallback (setup, recommended model, latency/FP caveat) · comparison table (cost/latency/FP, once measured) | P1 (BYOK) → P3 (Ollama) |
| **docs/CONFIG.md** | adopter | `.code-review.yml` reference · precedence (input > yml > CLAUDE.md > default) · minimal vs extended schema | P0 (minimal) → P4 (path-rules) |
| **docs/CONTRIBUTING-REFERENCES.md** | contributor | what belongs in `references/` (tools-miss patterns, not repo rules) · entry template · how to add (read a real review → extract pattern → write → test) · the **curation SLA** · examples with source PRs | P2 |
| **docs/SECURITY.md** | adopter / auditor | threat model · `pull_request` (not `_target`) rationale · least-privilege permissions · secret handling · bot-identity guard · fork-PR safety · GitHub App setup steps | P2 |
| **docs/EVAL.md** | maintainer / curious adopter | why measure · defining test PRs + ground truth · running `eval/measure.py` · interpreting FP/FN/cost · adding a test PR | P1 |

## Already written (this pre-code package — design docs, not user guides)

- `docs/architecture.md` — system map (5-stage pipeline, data model, judgment-to-headless, security).
- `docs/repo-structure.md` — target layout.
- `docs/roadmap.md` — features + phases + gates + rollback triggers.
- `docs/glossary.md` — shared vocabulary.
- `docs/specs/2026-06-06-phase-0-mvp.md` — implementable Phase-0 spec.
- `docs/specs/2026-06-06-ci-action-runner.md` — high-level runner spec (existing).
- `decisions/0011–0024` — the decision record.

## Cross-references to keep honest

- README + ACTION.md link to **roadmap.md** for "what's not built yet" so users never assume a
  deferred feature exists (the cut-list in [ADR-0019](../decisions/0019-phase-0-mvp-scope.md) is the source of truth).
- SECURITY.md + ACTION.md state the **bot-identity prerequisite** for posting
  ([ADR-0004](../decisions/0004-github-app-posting-identity.md)) up front.
- PROVIDERS.md states the **BYOK-first / Ollama-fallback** stance and the local-model FP caveat
  ([ADR-0014](../decisions/0014-provider-agnostic-adapter-byok-first-ollama-fallback.md)).
