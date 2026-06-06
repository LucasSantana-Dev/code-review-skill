# ADR-0007: Distribution, license & contribution model for the open release

- **Status:** Accepted (relicense to Apache-2.0 applied + repo made public, 2026-06-06)
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Supersedes:** (none — extends ADR-0003 packaging and ADR-0005 open-core thesis)
- **Superseded by:**

## Context

ADR-0005 makes the `references/` library a forkable, community-curatable open core. That only
means something if the project is actually distributed, licensed, and contributable. The repo is
currently **private**, MIT-licensed, with a strong baseline (README, CHANGELOG, 6 ADRs, 28 tests,
documented entry format) but no contribution/governance scaffolding. Research (3 strands) + an
adversarial critic settled the three coupled facets — channel, license, contribution — and a
pre-public gate.

Verified facts that bound the answer:
- The operator's RAG index and dotfile mirrors (`~/.claude-env`, `~/.agents`) are **not** part of
  a fork; the public install path is the universal `~/.claude/skills/`.
- A scrub of tracked files found **no secrets or absolute personal paths** (`.claude/` is
  gitignored). (The critic's "operator path in SKILL.md" was a hallucination from the gitignored
  backlog; SKILL.md frontmatter is clean. CHANGELOG is versioned; pyproject is 0.2.0.)
- Python-stdlib scripts are fully supported by both plain-skill and plugin distribution; only
  script *output* enters the context window. No hosted service is required by any channel.

## Decision

**1. Distribution — public git repo as the single source of truth.**
- Make the GitHub repo public; users `git clone` into `~/.claude/skills/code-review` or fork it.
- List in community skill registries (auto-indexing public repos; zero-cost discovery).
- Document `npx skills` as a *secondary* path with its caveat (it installs to `~/.agents/skills/`,
  which Claude Code does not read — so prefer `git clone` for Claude Code).
- **Defer** the Claude Code plugin marketplace manifest (`.claude-plugin/marketplace.json`): it
  adds per-release version-pin maintenance and stale-version risk with no demonstrated demand.
- No hosted service (consistent with ADR-0003).

**2. License — Apache-2.0** (switch from the current MIT).
- The project's stated goal is external contribution of reference patterns; Apache-2.0's explicit
  contribution grant (§5) + patent grant make contribution cleaner and signal a governed project,
  matching the comparable-tool cohort (aider, Continue, PR-Agent, Tabby). Relicensing is a one-file
  change now (sole author, pre-public) and costly later (needs every contributor's agreement).
- **Single license** for code + the markdown `references/` (no code/docs split; CC licenses aren't
  for code; embedded snippets are code).

**3. Contribution — minimal, low-friction.**
- A short `CONTRIBUTING.md` keyed to the existing `references/README.md` entry format + curation
  rules: one pattern per PR, the test suite (incl. the index drift-guard) must pass.
- A `PULL_REQUEST_TEMPLATE.md` with that checklist.
- Attribution via git history (optional `CONTRIBUTORS.md` later).
- **No DCO/CLA at launch** — ceremony at zero realistic volume; add DCO *if/when* external PRs
  actually arrive.
- `SECURITY.md` documenting the per-user GitHub App token model (no shared secret) + disclosure;
  `CODE_OF_CONDUCT.md` (Contributor Covenant).

**4. Pre-public gate** — before flipping visibility: scrub tracked files for secrets/personal
paths (done — clean), ensure README's install path leads with `~/.claude/skills/`, tests green on
a fresh checkout, governance files present. The flip to public and the relicense are deliberate,
maintainer-confirmed steps (public + registry-indexed is effectively one-way).

## Alternatives considered

- **Keep MIT.** Rejected after critique: simpler, but gives no explicit contribution clause and
  reads as "personal tool"; for a contribution-seeking open core, Apache-2.0 dominates, and
  switching is free only while solo + private.
- **Add the plugin marketplace manifest at launch.** Deferred: version-pin overhead + stale-version
  confusion without demand; plain public git is the leaner first step.
- **DCO/CLA at launch.** Deferred/rejected: friction for ~0 expected external PRs; the license's
  implied grant on PR suffices until volume appears.
- **`npx skills` as the primary channel.** Rejected: path mismatch (`~/.agents/skills/` vs Claude
  Code's `~/.claude/skills/`) makes it unreliable as the main path.
- **Stay private.** Rejected: contradicts the open-core thesis (ADR-0005); the tool's value is the
  shareable, forkable corpus.

## Consequences

**Positive:** a clean, governed public launch; forkers get everything (markdown + stdlib scripts)
with no service dependency; Apache-2.0 invites and protects contributions; deferring the plugin
manifest + DCO keeps maintainer burden near zero.

**Negative:** relicensing is a (small, deliberate) legal change to the maintainer's artifact; going
public is one-way (registries cache forks); some governance files to maintain.

**Neutral:** the plugin marketplace + DCO remain designed-but-deferred, addable on demand.

## Revisit when

- **External PRs start arriving** → add DCO (`git commit -s`) and a `CONTRIBUTORS.md`.
- **`/plugin install` demand appears** (users ask, or registry data shows it) → add
  `.claude-plugin/marketplace.json` and submit to the community plugin marketplace.
- **A second maintainer joins** → revisit governance (CODEOWNERS, release process).
- **A security report arrives** → revisit `SECURITY.md` disclosure SLA.

## References

- Research (2026-06-06): Agent-Skill distribution channels; license + contribution norms for a
  curated-content tool; repo readiness scrub.
- Critic verdict (2026-06-06): PROCEED-WITH-CHANGES (its "operator path in SKILL.md" CRITICAL was
  verified false/hallucinated; its license + defer-plugin + minimal-contribution arguments were
  adopted).
- Related: ADR-0003 (packaging), ADR-0004 (GitHub App identity), ADR-0005 (open core), ADR-0006
  (references retrieval).
