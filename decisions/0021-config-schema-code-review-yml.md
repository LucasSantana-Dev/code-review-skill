# ADR-0021: Config schema (`.code-review.yml`) — optional, minimal in Phase 0, layered precedence

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0005](0005-curated-knowledge-not-autonomous-learning.md), [ADR-0019](0019-phase-0-mvp-scope.md)
- **Informed by:** design tracks + critic (Finding #10: "configuration explosion, no precedence"); CodeRabbit `.coderabbit.yaml` path-instructions

## Context

Project-aware behavior (which provider, which dimensions, path rules, severity floor,
budget) is how the runner adapts to a repo without ML — consistent with ADR-0005 (curated,
not learned). But a 30-field config is adoption friction, and the critic flagged that the
design listed many knobs with no precedence rule. The MVP must work with **zero config**.

## Decision

1. **`.code-review.yml` is optional.** With no config file, the runner works from sane
   defaults + action inputs. A 3-line workflow gets value immediately.
2. **Minimal Phase-0 surface** — only what's needed to run:
   ```yaml
   provider: anthropic            # anthropic | openai-compatible | ollama
   model: claude-sonnet-4-6       # provider default if omitted
   api_key_env: CODE_REVIEW_API_KEY
   ```
   Everything else (severity_floor=P1, skip_trivial=true, context N=10, dimensions=
   correctness+security, all paths reviewed) is a **hardcoded default** in Phase 0.
3. **Extended surface phases in later** (P2/P4), additively and forward-compatibly:
   `severity_floor`, `skip_trivial` + threshold, `dimensions`, `linters`, `path_rules`
   (glob include/exclude + per-path dimension weight), `budget_tokens`, `bot_login`,
   `cache` toggle. Unknown keys are **warned, not fatal** (forward-compat).
4. **Precedence, highest → lowest, documented and tested:**
   **CLI flag / action input  >  `.code-review.yml`  >  `CLAUDE.md`/`AGENTS.md` conventions
   >  built-in default.** `CLAUDE.md`/`AGENTS.md` ingestion is **read-only project context**
   (P4), never executable config.
5. **YAML is parsed by a tiny in-tree reader** for the flat MVP subset (stdlib), avoiding a
   `PyYAML` dependency until the schema genuinely needs nested structures
   ([ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md)).

## Alternatives considered

- **Required config** — explicit, but kills "copy 3 lines and go" onboarding. Rejected.
- **Env-vars only** — less discoverable, not version-controlled with the repo. Rejected as
  the primary surface (env still works via `api_key_env`).
- **Adopt `PyYAML` from day one** — convenient nesting, but a dependency for a flat MVP
  schema. Deferred until path-rules (nested) actually ship.
- **Org-level / GitHub-settings config** — overkill for per-repo control. Deferred behind demand.

## Consequences

**Positive:** zero-config onboarding; transparent, version-controlled per-repo tuning;
clear precedence avoids "which knob won?" confusion; forward-compatible parsing.

**Negative:** an in-tree YAML reader covers only the flat subset (must adopt `PyYAML` when
nesting lands — a known, scoped future cost); documentation must keep the schema + precedence
authoritative.

**Neutral:** config is data, not architecture — additive growth without code churn.

## Revisit when

- Path-rules / nested config ship → adopt `PyYAML` (or `tomllib`) and retire the in-tree reader.
- The schema exceeds ~10 documented options → split into sections or a reference table.
- `CLAUDE.md` ingestion needs more than advisory context → its own ADR (avoid scope creep into learning).
