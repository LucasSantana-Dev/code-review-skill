# ADR-0008: Permissive (Apache-2.0), not copyleft, for the references corpus

- **Status:** Accepted (license application bundled with the go-public step — see ADR-0007)
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Supersedes:** (none — finalizes the license facet of ADR-0007)
- **Superseded by:**

## Context

ADR-0007 chose Apache-2.0 single-license but debated only *within* permissive options (MIT vs
Apache-2.0). A sharper question went unexamined: the `references/` library is the open core, and
the product's whole thesis is that it's *not* a proprietary locked knowledge base. So **should the
corpus be copyleft / share-alike — to stop a competitor forking it into a closed product
(enclosure)?** This ADR settles that, after a dedicated research + critic pass.

Decisive facts:
- **Operational use, not static docs.** At review time the agent *reads* a reference and weaves
  its guidance (sometimes paraphrasing/quoting snippets) into the review comments it posts on a
  user's PR and into the user's repo. Reference content flows into user-generated output.
- **Share-alike would create a perceived "infection" risk.** Under CC-BY-SA on `references/`, an
  adopting org's legal team will ask "do our PR review threads / code become CC-BY-SA because the
  tool quoted a pattern?" Even if legally unlikely, the *uncertainty* is an adoption blocker.
  Permissive (Apache-2.0) removes the question entirely. No comparable tool (aider, Continue,
  PR-Agent, Tabby) uses mixed permissive+restrictive licensing.
- **Copyleft protection here is symbolic.** Research + critic agreed: a competitor can paraphrase/
  reframe patterns to evade derivative status, and a solo maintainer has no resources to enforce
  share-alike. Copyleft would buy friction, not protection.
- **CC-on-code is a gray zone.** CC licenses explicitly don't apply to software code; the entries
  contain code snippets, so CC-BY-SA on the markdown is ambiguous about the snippets.

## Decision

Keep the project **permissive: Apache-2.0, single license for everything** (code + `references/`),
affirming ADR-0007. **Do not** split the license or apply copyleft/share-alike to the corpus.

Pursue anti-enclosure by **non-license means**, which is where the real protection lives:
1. **Curation quality + velocity** — the upstream library stays better and fresher than any
   closed fork (a fork goes stale the moment it diverges).
2. **First-mover community** — contributions compound upstream; a closed fork forfeits them.
3. **A stated intent**, not a legal clause — a short README note that the corpus is intentionally
   open, forkable, and community-curatable. Honesty over an unenforceable guardrail.

## Alternatives considered

- **Split: Apache-2.0 `scripts/` + CC-BY-SA-4.0 `references/`** (the research's leading option;
  precedent: MDN, freeCodeCamp, OWASP). **Rejected:** perceived share-alike infection of the user's
  review outputs is an adoption blocker; enforcement is symbolic for a solo maintainer; CC-on-code
  is a gray zone; and the precedents are large orgs with legal/governance teams (Mozilla, FCC,
  OWASP foundation) — not a solo maintainer.
- **CC-BY-SA-4.0 for the whole repo.** Rejected: CC isn't for code at all.
- **MPL-2.0 (weak, file-level copyleft).** Rejected: a knowledge corpus grows by *adding* files,
  which MPL leaves proprietary-able — so it barely protects the corpus while still adding copyleft
  friction.
- **GPL/AGPL (strong copyleft).** Rejected: kills dev-tool adoption; wrong instrument for a
  reference corpus.
- **Keep MIT.** Rejected per ADR-0007 (no explicit contribution grant; weaker governance signal).

## Consequences

**Positive:** maximum adoption (no legal-team friction, no perceived-infection question); one
license for contributors, forkers, and users; clean treatment of embedded code; honest about what
actually protects the corpus.

**Negative:** a competitor *may* fork `references/` into a closed product — accepted, because
copyleft wouldn't really stop that (paraphrase evades it) and the upstream-freshness + community
moat is the better defense.

**Neutral:** if the project ever gains an institutional backer that *can* enforce share-alike, or
enclosure becomes a demonstrated, material harm, the calculus changes (see revisit).

## Revisit when

- A competitor actually **encloses the corpus** AND the maintainer gains real enforcement
  capacity (a foundation/backer, or counsel) — only then does copyleft become more than symbolic.
- Legal counsel advises that share-alike would give **material** (not symbolic) protection for
  this specific operational-use shape.
- The project's value shifts from the corpus to novel, patentable code (then patent/contribution
  terms dominate — already covered by Apache-2.0).

## References

- Research (2026-06-06): full license option set centered on permissive-vs-copyleft + enclosure;
  precedents (MDN, freeCodeCamp, OWASP) and the "share-alike is largely symbolic for a solo
  corpus" finding.
- Critic verdict (2026-06-06): RECONSIDER → Apache-2.0 single license; the perceived
  share-alike-infection-of-outputs risk + enforceability-theater were decisive.
- Related: ADR-0005 (open core), ADR-0007 (distribution/license/contribution — license facet
  finalized here).
