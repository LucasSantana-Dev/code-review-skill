# ADR-0024: Versioning + release — semver, major-version tag, pre-release v0.1.0, Marketplace

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0007](0007-distribution-license-contribution.md) (public distribution), [ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md)
- **Informed by:** design tracks; GitHub Action versioning conventions (`actions/checkout`-style major tags)

## Context

Consuming repos pin a GitHub Action by ref. Without a versioning contract, consumers pin to
`main` (unstable) or a commit SHA (no updates). The Action and the skill live in one repo
([ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md)) but evolve on different
clocks — the judgment layer (`SKILL.md`/`references/`) changes independently of the Action
surface, so their versioning must not be conflated.

## Decision

1. **Semantic versioning** for Action releases: `vMAJOR.MINOR.PATCH`, keeping `action.yml`
   and `pyproject.toml` versions in sync.
2. **Moving major-version tag.** Publish exact tags (`v0.1.0`) and move a `v0` (later `v1`)
   tag to the latest compatible release, matching the ecosystem norm
   (`uses: …/code-review@v1`). Consumers pin to `v0` (auto-patch), `v0.1.0` (exact), or
   `main` (rolling — discouraged for production).
3. **First release `v0.1.0` is a pre-release**, labeled "Phase 0–2 MVP; quality-harness
   results pending." Graduate to a stable `v0.2.0`+ after ~20 real PRs and passing
   [eval gates](0023-quality-eval-harness.md).
4. **Publish to GitHub Marketplace** (the project is public + Apache-2.0,
   [ADR-0007](0007-distribution-license-contribution.md)/[ADR-0008](0008-permissive-not-copyleft-for-the-corpus.md));
   the Action is usable by direct ref before Marketplace approval.
5. **Independent clocks.** Do **not** bump `SKILL.md`/`references/` on Action releases — the
   judgment layer versions on its own; the Action depends on it in-repo. Backward
   compatibility (`post_review.py` contract, action inputs) holds within a major version;
   deprecations are announced 2 releases ahead.
6. **Manual release** (`gh release create` + tag) for now — no release-automation bot at
   solo scale.

## Alternatives considered

- **Exact tags only (`@v1.2.3`)** — reproducible, but consumers must chase every patch
  manually. Rejected as the only option (offered alongside the moving major tag).
- **Branch refs (`@main`)** — always-latest, but unstable; breaks consumers on any commit.
  Rejected as the recommended path.
- **`release-please`/semantic-release automation** — nice at team scale, adds a bot + config
  for a solo operator. Deferred.
- **Versioning the skill and Action together** — simpler mental model, but forces a release
  every time the judgment layer changes. Rejected — independent clocks.

## Consequences

**Positive:** consumers get a stable, familiar pin model; honest pre-release sets
expectations; the judgment layer evolves without forcing Action churn.

**Negative:** a manual tag + release-notes step per release; backward-compat discipline
within a major version; two version numbers (Action vs implied skill) to reason about.

**Neutral:** semver + moving major tag is the boring, expected ecosystem default.

## Revisit when

- Release cadence outgrows manual steps, or a second maintainer joins → adopt release automation.
- A breaking change to `action.yml` inputs or `post_review.py` is needed → cut a new major + migration note.
