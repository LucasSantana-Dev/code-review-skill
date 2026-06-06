# Intent vs. implementation mismatch

- **Defect class:** intent-mismatch
- **Tier:** 1
- **Applies to:** language-agnostic
- **Typical severity:** P1

## Why tools miss it

Linters, type-checkers, and SAST only see the code — they have no access to the PR description,
the issue it claims to close, the function name, or the comment above it. Coverage confirms a
line ran, not that it does the *intended* thing. The code can be internally consistent and
fully green while doing something other than what the author promised. Only a reader comparing
**claim ↔ behavior** catches this.

## What to look for

- The PR title/description says "X" but the diff does "X′" (a near-neighbor, or only part of X).
- A function/variable name asserts a guarantee the body doesn't keep (`validateAndSave` that
  saves without validating; `getActiveUsers` that returns all users; `isEmpty` that checks
  `null` but not `[]`).
- A comment describes the old behavior; the code beneath it was changed without updating it.
- A bugfix PR that adds a test but the production change doesn't actually alter the faulty path.
- A "rename only" / "no behavior change" PR that quietly changes a default, a comparison, or an
  early-return.

## Bad / Good

```js
// PR: "clamp retries to the configured max"
// bad — name & PR say clamp; code caps the floor, not the ceiling
function clampRetries(n) {
  return Math.max(n, MAX_RETRIES)   // never returns less than MAX_RETRIES — inverted
}

// good
function clampRetries(n) {
  return Math.min(n, MAX_RETRIES)
}
```

## How to confirm it's real (evidence)

- **`factual`** when the mismatch is provable from the artifact: quote the PR/issue text or the
  name/comment, then the contradicting `file:line`. ("PR says clamp to max; `retry.js:12`
  returns `Math.max(n, MAX)`, which enforces a minimum.") No runtime context needed.
- **`behavioral`** when the intended behavior depends on inputs you can't see from the diff
  (e.g. the spec is ambiguous about empty input). Then ask the author rather than assert.
- Strongest evidence: a test in the repo that encodes the *stated* intent and fails against the
  diff.

## Often appears as

Inverted boolean/condition · wrong comparison operator · stale doc-comment · partial fix (test
added, prod path untouched) · scope creep hidden in a "rename" · off-by-one dressed as the
"intended" boundary.
