# ADR-0009: Cross-agent reach — stay Claude-Code-first, defer infra behind a demand-differentiated decision tree

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Supersedes:** (none)
- **Superseded by:**
- **Refines:** ADR-0003 (corrects its "MCP is the cross-agent migration path" framing)

## Context

The tool just shipped public, Claude-Code-first. The open question: support other agents/
environments (Cursor, Codex, Copilot, Continue, headless CI), and if so how, without losing the
bundled-stdlib-script simplicity? ADR-0003 named an MCP server as the eventual cross-agent
migration path. Research (cross-agent standards landscape + MCP mechanics + a repo portability
inventory) + an adversarial critic reframed the answer.

What the research established:
- **The tool is already ~65–70% portable for free.** The rubric/taxonomy/calibration
  (`SKILL.md`+`REFERENCE.md`), the `references/` corpus, and the stdlib scripts are reusable
  anywhere. The ~30–35% that's Claude-Code-specific is the *orchestration*: the Workflow fan-out
  primitive, Task-tool fixer dispatch, memory hooks, frontmatter, slash-arg parsing — and these
  **degrade gracefully** (single-pass review is the default; fixers are optional).
- **Two real cross-agent standards exist** (2026): `SKILL.md`/`npx skills` (installs the same skill
  across 51+ agents) and `AGENTS.md` (tree-walked "README for agents", read by 20+ agents). These
  carry *reasoning* (markdown). They handle *installation/discovery*, not execution parity.
- **MCP carries tools/resources, NOT reasoning.** Even with an MCP server, every agent still needs
  the rubric in its own prompt. So MCP is the right tool only for sharing the *posting plumbing*
  across agents — not for portability. ADR-0003's "MCP is the migration path" conflated the two.
- **Honest scope:** rubric + references = portable everywhere; *execution* = Claude-Code-class;
  *posting* requires `gh` CLI + the `CODE_REVIEW_BOT_LOGIN`/App-token setup (ADR-0004) in any env.

## Decision

**Stay Claude-Code-first and build no cross-agent infrastructure now.** The tool is already
appropriately portable; do not add MCP, a CLI, a GitHub Action, AGENTS.md, or per-agent shims
(`.cursor/rules`, `.github/instructions`) on spec. Keep the README's existing honest scope; add one
precise sentence clarifying the portable-knowledge-vs-Claude-execution split so no one over-expects.

Resolve the *next* move by **who actually shows up** (a demand-differentiated decision tree), not by
guessing now:

- **Demand = headless/automated PR review in CI** → build a thin **GitHub Action** that drives the
  scripts + an LLM API call (a different product shape; plausibly the *higher-value* direction —
  do not assume interactive agents are the next user).
- **Demand = interactive use in another agent** (Cursor/Codex/Copilot) → it's largely already there
  via `npx skills`/AGENTS.md (the knowledge is portable). Add a thin pointer `AGENTS.md` + document
  the `gh`/bot-identity setup; build an **MCP server only for the shared posting plumbing** if
  *multiple* agents need it.
- **No demand** → stay as-is.

## Alternatives considered

- **Build an MCP server now** (ADR-0003's stated path). Rejected: MCP doesn't carry the review
  reasoning (the hard part), only the plumbing; standing-process infra cost outweighs the solo
  on-demand benefit. Reserved for *shared posting tools* if multi-agent demand appears.
- **Add AGENTS.md + per-agent shims now.** Rejected/deferred: no demand signal; adds a second
  instruction surface and implies cross-agent support the solo maintainer isn't committing to.
- **Ship a portable CLI + GitHub Action now.** Deferred: real value *iff* headless/CI demand
  materializes; premature for a just-shipped on-demand tool. Comparable tools (Semgrep, Qodo) ship
  multiple form factors only once a shared core + audience exist.
- **Claim "works cross-agent" in the README.** Rejected: overclaims — execution + posting aren't
  portable unchanged; would invite friction and support load.

## Consequences

**Positive:** zero new maintenance for a solo maintainer; no overclaiming; the portable core is
honestly reusable today; the next move is pre-decided per demand type, so a real signal triggers a
fast, correct build rather than a guess.

**Negative:** non-Claude users get only the *knowledge* for free, not a turnkey tool; a team wanting
CI review must wait for the Action (or roll their own). Accepted until demand is shown.

**Neutral:** ADR-0003's bundled-script choice stands; only its "MCP = migration path" framing is
corrected here.

## Revisit when

- **First concrete demand signal**, routed by the decision tree above (CI/headless → Action;
  interactive cross-agent → skills-standard + AGENTS.md + optional MCP posting tools).
- A **second contributor** or **non-Claude user** opens an issue asking how to run it elsewhere →
  add the thin AGENTS.md + setup docs then.
- Multiple agents end up **duplicating the posting plumbing** → that's the trigger for an MCP
  posting-tools server (the only justified MCP use).

## References

- Research (2026-06-06): cross-agent standards (`npx skills`/AGENTS.md), MCP-vs-reasoning mechanics,
  repo portability inventory (~65–70% portable; Claude-only orchestration degrades gracefully).
- Critic verdict (2026-06-06): PROCEED-WITH-CHANGES — don't overclaim portability, reframe the MCP
  rejection (category error), surface the next-user decision tree, defer AGENTS.md.
- Related: ADR-0003 (packaging; refined here), ADR-0004 (posting identity), ADR-0007 (distribution).
