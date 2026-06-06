# ADR-0006: References retrieval — agent-driven advisory selection now; defer deterministic filtering

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Supersedes:** (none — extends ADR-0005's curated `references/` library)
- **Superseded by:**

## Context

ADR-0005 made the `references/` library (curated defect-pattern markdown) the product's
compounding core. That raised an immediate question: **how does the right entry get into the
review's context as the library grows** (7 today → tens, maybe low-hundreds by human curation)?
The previous critic flagged this as "waved at but not designed." Research + an adversarial
critic settled it.

Findings that bound the answer:
- **Forkability disqualifies the operator's RAG index.** `~/.claude/rag-index` (embeddings +
  sqlite + MCP server) is the operator's *personal* environment; a fork of the skill does not
  ship with it. Any retrieval that depends on it breaks the open/forkable constraint ADR-0005
  protects. Ruled out.
- **Load-all cost** is ~5K tokens at 7 entries, ~35K at ~50, ~135K at ~200 (each entry
  ~600–700 tokens). Tolerable now; material later.
- **More is worse, on a quality axis, not just cost.** LLM evidence (lost-in-the-middle,
  few-shot dilution) says inject a *handful* of relevant items; dumping many mostly-irrelevant
  entries degrades output before the token budget bites.
- **Industry consensus** (CodeRabbit path-instructions, Cursor `.mdc` globs, Copilot `applyTo`,
  Continue rules) selects guidance by glob/metadata; embeddings/BM25 are secondary, only at scale.
- **The real mechanism is the agent's inference** of which defect-classes a diff risks — which is
  the core review act anyway. References are *advisory priors*, not a precise routing decision;
  consulting a related-but-imperfect entry is low-harm.
- The critic's verdict on the elaborate version (manifest + language tags + an "optional"
  selector script) was **RECONSIDER**: over-engineered for the current scale, the "optional"
  script was a contradiction, and a hand-maintained manifest would drift.

## Decision

Keep references selection **agent-driven and advisory** at the current scale, add the one cheap
guard that removes a real drift trap, and **defer** the retrieval machinery behind an explicit
trigger:

1. **The agent selects.** SKILL.md frames `references/` as priors to consult for the
   defect-classes the diff plausibly touches (the reviewer is already reasoning about classes).
   It reads the README index (a cheap catalog) and loads the few matching entry bodies. No new
   runtime mechanism; works in any agent that can read files.
2. **Frontmatter is the metadata of record** (`Defect class`, `Tier` already present). Do **not**
   invest in granular `applies-to` language tags now — defect-class is the selector; most entries
   are language-agnostic.
3. **Drift-guard the index with a test.** A unit test asserts the README index table lists
   exactly the entry files with matching defect-class + tier — so the catalog can't silently go
   stale as entries are added/edited. (No CI in this repo by choice; the test suite is the gate.)
4. **Defer** the deterministic selector script, metadata/language filtering, and BM25/embeddings.
   They are not built now.

## Alternatives considered

- **Manifest + metadata tags + optional selector script (the original proposal).** Rejected:
  critic-flipped as over-engineered for 7 entries; "optional script" is a contradiction (either
  it's the primary, deterministic mechanism or it's theater); hand-maintained manifest drifts.
- **Reuse the operator's `~/.claude/rag-index` (semantic retrieval).** Rejected: not shippable
  with a fork; couples the open skill to one machine.
- **Bundled BM25 / embeddings selector.** Deferred: only pays off >~150–200 entries and adds
  weight that fights "simple + forkable."
- **Pure flat load-all, indefinitely.** Rejected as the *long-term* answer: dilution degrades
  review quality well before the token budget does. It is, however, effectively what (1) reduces
  to at today's small N.
- **Aider-style single always-loaded "top patterns" file.** Rejected: collapses the
  per-pattern structure that makes entries forkable and individually curatable.

## Consequences

**Positive:**
- Zero new runtime machinery; fully portable (markdown + the agent). A fork works out of the box.
- Honest about the mechanism: references are advisory priors; imperfect selection degrades
  gracefully (the skill still has its rubric + the target repo's own conventions).
- The drift-guard test keeps the catalog trustworthy at near-zero cost, in the repo's existing
  test-driven style.

**Negative:**
- Selection quality rides on the agent's judgment; at larger N it will start pulling too many or
  the wrong entries (this is the trigger to revisit, below).
- The README index stays hand-maintained (the test only *guards* it; it doesn't generate it) —
  a small per-entry curation step.

**Neutral:**
- A deterministic `scripts/refs.py select --class <c>` (PRIMARY, not optional) is the designed
  next step once the trigger fires — select by coarse defect-class, not language.

## Revisit when

- The library exceeds **~25–30 entries**, or reviews visibly pull too many / the wrong references
  (relevance dilution observed) — whichever comes first. Then build the deterministic
  defect-class selector script as the primary mechanism (the orchestrator runs it and injects the
  result), capped at ~3–7 entries per review.
- Entries exceed **~150–200** or selection needs semantic matching beyond defect-class → add
  BM25, then embeddings, in that order (still stdlib-first; no operator-personal infra).
- If language-specific entries become common (>~20 across multiple languages), add `applies-to`
  language filtering at that point — not before.

## References

- Research (2026-06-06): infra/portability grounding (rag-index is operator-personal, not
  shippable); how comparable tools select diff-relevant guidance (glob/metadata consensus;
  3–7 snippet budget; scale thresholds for BM25/embeddings).
- Critic verdict (2026-06-06): RECONSIDER on the elaborate proposal → simplified to advisory +
  drift-guard + deferred selector.
- Related: ADR-0003 (skill packaging), ADR-0005 (curated knowledge layer).
