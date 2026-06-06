# References — the curated pattern library

The corpus that makes this skill a *review*, not a linter. Each file is one **defect pattern
that automated tools (lint, types, SAST, coverage, AI-generated tests) systematically miss** —
the [tools-miss frontier](../SKILL.md) — written so a reviewer can recognize it in a diff and
justify the finding with evidence.

This library is the product's open, forkable core (ADR-0005): the differentiator of a free,
open code reviewer is not smarter inference — it's a transparent, version-controlled, *forkable*
body of real-review knowledge that a proprietary, locked "learnings" database can never be.

## How the skill uses it

During a review, after mapping the change, the reviewer scans this directory for entries whose
**Applies to** matches the change's language/framework and whose **Defect class** matches what
the diff plausibly touches — and uses them as concrete priors for what to look for and how to
prove it. Entries reinforce calibration: each says what makes the finding `factual` vs
`behavioral` (see SKILL.md *Ordered calibration procedure*).

## How it compounds (curation, not autonomous learning)

There is **no self-training loop** — by deliberate decision (ADR-0005), because at low PR
volume an autonomous loop's ROI is upside-down and it risks drifting on its own unvalidated
output. Instead the library grows by **human curation**: when a review surfaces a *novel,
generalizable* pattern (one that transfers across repos in a language/framework), add or refine
an entry here. Make this a step in your review/release checklist.

**What does NOT belong here:** repo-specific conventions ("in *this* service we always inject a
logger"). Those don't transfer; they live in the *target repo's* own `CLAUDE.md` / `AGENTS.md`
/ ADRs, which the skill already reads (context-first). Keeping repo-specifics out keeps this
library forkable and drift-free.

## Curation source: learn from how elite projects review

A primary, repeatable way to grow this library: study how big, well-run open-source projects
actually review — both their **codified guidelines** and their **real review threads** — and
distill the generalizable patterns here. Their reviewers have already found, named, and
explained the defects automated tools miss; we encode that, stripped of repo-specifics.

**Two sources, both worth mining:**

1. **Codified review guidelines** — how they decide blocking vs. nit, what to look for, how to
   phrase it:
   - **Google** — *Code Review Developer Guide* (`google.github.io/eng-practices`): the standard
     of review ("approve once it improves overall code health, even if imperfect"),
     what-to-look-for, how-to-write-comments, `Nit:` labeling.
   - **Linux kernel** — `Documentation/process/submitting-patches`: one-logical-change-per-patch,
     justification/"why", `Reviewed-by` vs `Acked-by`.
   - **Chromium** — *Respectful Code Reviews*: assume competence; ask, don't shame.
   - **Kubernetes** — reviewing PRs: comment-not-block by default; keep scope narrow.
   - **Rust** — *API Guidelines* + rustc conventions: public-API surface as a first-class gate.
   - **OWASP** — *Secure Code Review*: the security-logic classes, and that human judgment dominates.

2. **Real review threads** — merged PRs with substantive discussion where a human caught what
   tools couldn't (logic, intent, cross-file, api-misuse, concurrency, authz). Find them with
   `gh search prs --merged`, `gh pr view <n> --comments`, project mailing lists, and "great
   review" write-ups.

**Procedure (each pass):**
1. Pick 1–2 projects + one defect class to deepen.
2. Read the relevant guideline section; pull 3–8 real review comments that caught a tools-miss
   defect (quote + link).
3. For each recurring, **transferable** pattern, write or refine a `references/` entry in the
   format below — strip repo-specifics, tag *Applies to*, and capture the reviewer's *evidence
   technique* (how they proved it) in *How to confirm it's real*.
4. Drop anything true for only one project's codebase — that belongs in the target repo's own
   docs, not here.

This pass is how the entries citing real PRs (React #18000, Bitcoin #14588, Kafka #15557, …)
were derived; re-run it periodically to keep the library current as idioms evolve.

## Entry format

Copy this skeleton into `references/<kebab-case-name>.md`:

```markdown
# <Pattern name>

- **Defect class:** <semantic-correctness | business-logic | intent-mismatch |
  cross-file-invariant | api-misuse | architecture | concurrency | security-logic>
- **Tier:** 1 | 2 | flag-don't-approve
- **Applies to:** <languages/frameworks, or "language-agnostic">
- **Typical severity:** P0 | P1 | P2

## Why tools miss it
<1–3 lines: which gate would you expect to catch this, and why it structurally can't.>

## What to look for
<the trigger/smell as it appears in a diff — concrete enough to spot.>

## Bad / Good
<a minimal before/after; keep it short and illustrative.>

## How to confirm it's real (evidence)
<what makes this `factual` here vs `behavioral`; what to cite to prove it.>

## Often appears as
<related smells, common variants, where it tends to recur.>
```

## Curation rules

- **One pattern per file.** Generalizable, not repo-specific.
- **Tag transferability honestly** in *Applies to* — a TS/Express example is noise in a
  Python/FastAPI diff; say so.
- **Tie to evidence tiers** so entries reinforce calibration rather than encourage assertion.
- **Prune** entries that stop earning their place (stale framework, superseded idiom).
- **Don't duplicate** the dimension checklists or smell catalog in [REFERENCE.md](../REFERENCE.md);
  those are exhaustive coverage. Entries here are high-yield *patterns* with examples.

## Index

> Keep this table in sync when adding/editing an entry — one row per file, with its defect
> class and tier. `tests/test_references_index.py` enforces the sync (it's the review agent's
> cheap catalog; see ADR-0006). Selection is the agent's call by defect class today; a
> deterministic selector arrives only when the library outgrows that (~25–30 entries).

| Pattern | Class | Tier |
|---|---|---|
| [intent-implementation-mismatch](intent-implementation-mismatch.md) | intent-mismatch | 1 |
| [business-logic-edge-cases](business-logic-edge-cases.md) | business-logic | 1 |
| [missing-error-path-multi-step](missing-error-path-multi-step.md) | api-misuse | 1 |
| [unhandled-enum-variant](unhandled-enum-variant.md) | semantic-correctness | 1 |
| [cross-file-invariant-break](cross-file-invariant-break.md) | cross-file-invariant | 2 |
| [concurrency-ordering](concurrency-ordering.md) | concurrency | flag-don't-approve |
| [broken-access-control](broken-access-control.md) | security-logic | flag-don't-approve |
