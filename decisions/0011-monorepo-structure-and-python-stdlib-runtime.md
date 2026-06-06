# ADR-0011: Extend this repo as a monorepo; implement the runner in Python-stdlib

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0010](0010-headless-ci-action-runner.md) (thin headless Action runner), [ADR-0003](0003-keep-bundled-script-skill-packaging.md) (bundled-script packaging)
- **Informed by:** pre-code design package (parallel design tracks + adversarial critic, 2026-06-06)

## Context

The runner (ADR-0010) must live somewhere and be written in something. The interactive
skill already ships `post_review.py` + `app_token.py` (Python-stdlib only) and the
judgment layer (`SKILL.md`/`REFERENCE.md`/`references/`). The runner reuses all of it.
Two structural questions force a choice now because both are expensive to reverse later:
where the runner code lives, and what language/runtime it uses.

## Decision

1. **Monorepo — the runner lives in *this* repo**, alongside the skill, under a new
   `runner/` package (+ `action.yml` at the root). `SKILL.md`, `REFERENCE.md`,
   `references/`, `scripts/post_review.py`, `scripts/app_token.py` stay the **single
   source of truth**, read by both the interactive skill and the headless runner. No
   second repo, no duplication of the judgment layer.
2. **Python-stdlib runtime.** The runner is Python (≥3.9), matching the existing
   scripts. Core logic (diff parsing, file I/O, JSON, HTTP) uses the **standard library
   only**. We **shell out** to existing tools (`git`, `gh`, linters, Semgrep) rather
   than re-implement them. Provider HTTP calls use `urllib` (stdlib); no vendored SDK is
   required for the BYOK path. Sync execution only (no async runtime in the MVP).
3. `pytest` is a **test-only** dependency; production code imports nothing outside the
   stdlib.

## Alternatives considered

- **Separate action-only repo** — clean versioning boundary, but duplicates
  `SKILL.md`/`references/` → guaranteed drift between skill and Action (the one thing
  that must never diverge). Rejected.
- **TypeScript/Node action** — GitHub-Actions-native, but the skill is Python-first;
  a second language doubles the maintenance surface for a solo operator. Rejected.
- **Go** — fast, single binary, but adds a build step and a third language. Rejected.
- **Heavy Python deps (Pydantic, PyYAML, provider SDKs) by default** — convenient, but
  cuts against "thin" and adds supply-chain + install surface. Deferred: a minimal YAML
  reader is written in-tree; SDKs are optional, not required.

## Consequences

**Positive:** one curation path for `references/`; skill and Action can never drift;
a solo operator maintains one language; zero required runtime dependencies keeps the
Action portable to any runner with Python 3.9 + `git` + `gh` + `openssl` (already the
skill's assumptions).

**Negative:** the repo grows; new contributors see two invocation modes (skill vs Action)
and need onboarding; stdlib-only HTTP/JSON is slightly more verbose than using an SDK;
Python cold-start adds ~0.5–1 s per CI run (negligible).

**Neutral:** `git` history stays clean — the runner is purely additive; no refactor of
existing skill code.

## Revisit when

- A second maintainer/team wants to fork and version the Action independently → split repos.
- Any single runner module exceeds ~300 LOC of provider-specific glue → reconsider a thin SDK.
- Python cold-start or stdlib HTTP becomes a measured bottleneck → profile before adding deps.
