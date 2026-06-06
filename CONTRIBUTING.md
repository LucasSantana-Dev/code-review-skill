# Contributing

Thanks for helping sharpen this reviewer. The most valuable contribution is a **new reference
pattern** — a defect class that automated tools (lint, types, SAST, coverage, AI-generated tests)
systematically miss, written so any reviewer can recognize and prove it.

## What we want

- **New `references/` entries** — generalizable defect patterns that transfer across repos in a
  language/framework. This is the project's open core (see [ADR-0005](decisions/0005-curated-knowledge-not-autonomous-learning.md)).
- **Improvements** to existing entries (clearer examples, better evidence technique).
- **Fixes** to the skill instructions or the bundled scripts (with a test).

## What doesn't belong here

- **Repo-specific conventions** ("in *our* service we always inject a logger") — those live in the
  *target* repo's `CLAUDE.md`/`AGENTS.md`, which the skill already reads. Keeping them out keeps
  this library forkable.
- Style/lint rules that an existing tool already enforces — this reviewer is for what they *miss*.

## Adding a reference pattern

1. Read the entry format and curation rules in [`references/README.md`](references/README.md).
2. Create `references/<kebab-case-name>.md` from the skeleton. Strip repo-specifics; tag
   *Applies to* honestly; put the reviewer's evidence technique in *How to confirm it's real*.
3. Add one row to the **Index** table in `references/README.md` (defect class + tier).
4. Run the tests — the index drift-guard must pass:
   ```bash
   python3 -m pytest tests/ -q
   ```
5. **One pattern per PR.** Open the PR; the template's checklist mirrors the above.

Grounding a pattern in a real review (a linked PR/thread from a well-run OSS project) makes it much
stronger — see the *Curation source* section in `references/README.md`.

## Changing scripts

`scripts/` is **Python standard library only** (no third-party deps). Match the existing house
style (deterministic CLI, JSON/plaintext stdout, actionable errors). Add or update a test in
`tests/`; keep the suite green.

## Attribution

Contributors are credited via git history. (No AI co-authorship trailers — human contributors
only.)

## Legal

By contributing you agree your contribution is licensed under the repository's `LICENSE`. We don't
require a CLA or DCO today; if external contribution volume grows we may add lightweight DCO
sign-off (`git commit -s`) — see [ADR-0007](decisions/0007-distribution-license-contribution.md).
