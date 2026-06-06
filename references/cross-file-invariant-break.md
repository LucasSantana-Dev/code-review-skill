# Cross-file invariant break

- **Defect class:** cross-file-invariant
- **Tier:** 2
- **Applies to:** language-agnostic (needs repo context)
- **Typical severity:** P1

## Why tools miss it

Single-file analysis is the default for linters and most SAST; type-checkers catch a broken
signature but not a broken *contract* that lives in convention, data shape, or ordering. The
change under review looks correct in isolation — the break is at a distance, in a caller, a
consumer of a serialized payload, or another module that relied on a guarantee this diff
quietly dropped. Coverage of the changed file says nothing about the file that now breaks.

## What to look for

- **Changed shape, distant reader:** a field renamed/removed/retyped in a struct that's
  serialized to a queue, cache, DB column, or API response another service deserializes.
- **Weakened guarantee:** a function that *used* to be sorted / non-null / deduped / idempotent
  and now isn't — and a caller depends on the old guarantee.
- **Enum/constant drift:** a new enum case or changed constant that some `switch`/map elsewhere
  doesn't handle.
- **Ordering / timing contract:** code that assumed A runs before B; the diff reorders or makes
  one async.
- **Default change:** a default value/flag flipped here that other call sites silently inherit.

## Bad / Good

```ts
// shared/types.ts — diff makes `email` optional
export interface User { id: string; email?: string }   // was: email: string

// elsewhere, untouched by this PR, now silently wrong:
// notify.ts
sendEmail(user.email.toLowerCase())   // was safe; now can throw on undefined
```
**Good:** keep the invariant (don't loosen `email`), or update every consumer and add a guard
at each — and say so in the PR.

## How to confirm it's real (evidence)

- **`factual`** when the type system or a test proves the break: cite the consumer `file:line`
  and the now-invalid assumption, ideally with the typecheck error or a failing test. ("`User.email`
  is now optional at `types.ts:4`; `notify.ts:21` calls `.toLowerCase()` unguarded.")
- **`behavioral`** when the contract is by convention, not types (a serialized shape, an
  ordering assumption) — you can't prove the consumer breaks without runtime/data context. Trace
  the dependency, name the at-risk site, and rate by agreement.
- Use repo-wide search (grep/refs) to *find the consumers* before asserting — don't claim a
  break you haven't located.

## Often appears as

Renamed/removed field on a serialized type · loosened nullability · changed sort/dedup
guarantee · unhandled new enum case · reordered effects · flipped default inherited downstream.
