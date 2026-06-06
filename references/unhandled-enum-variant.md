# Unhandled enum / variant after a new case is added

- **Defect class:** semantic-correctness
- **Tier:** 1
- **Applies to:** language-agnostic (strongest where a `default`/`else` swallows unknowns)
- **Typical severity:** P1

## Why tools miss it

A new case is added to a central enum/union/status set. Every distant `switch`/map/if-chain
that has a `default` branch still compiles and type-checks — the new case silently falls
through to a default written for *other* reasons (returns null, logs, renders blank), producing
wrong behavior with no error. Only an exhaustive match (or a reviewer who diffs the enum against
its handlers) catches it. This is a specific, very common case of a
[cross-file invariant break](cross-file-invariant-break.md), called out separately because its
*evidence technique* is distinct (exhaustiveness).

## What to look for

- An enum / union / status constant that *gained a value* in this PR (or recently).
- Handlers of that type — `switch`, lookup table, if-chain — **not** touched by the same PR.
- A `default:` / `else` that means "ignore" rather than "this is unreachable" — a magnet for
  silently mishandled new cases.
- Languages without forced exhaustiveness (or where it's opted out): TS without a `never` guard,
  Go switches, C/C++ without `-Wswitch`.

## Bad / Good

```ts
enum PaymentStatus { Pending, Completed, Failed, Refunded /* ← new in this PR */ }

// distant handler, untouched — Refunded silently renders blank
function label(s: PaymentStatus): string {
  switch (s) {
    case PaymentStatus.Pending:   return "loading…";
    case PaymentStatus.Completed: return "done";
    case PaymentStatus.Failed:    return "error";
    default:                      return "";        // bug: Refunded → ""
  }
}

// good — make the switch exhaustive so a new case fails to compile until handled
function label(s: PaymentStatus): string {
  switch (s) {
    case PaymentStatus.Pending:   return "loading…";
    case PaymentStatus.Completed: return "done";
    case PaymentStatus.Failed:    return "error";
    case PaymentStatus.Refunded:  return "refund issued";
    default: { const _exhaustive: never = s; return _exhaustive; }
  }
}
```

## How to confirm it's real (evidence)

- **`factual`** when exhaustiveness proves it: cite the compile error from a `never` guard /
  `-Wswitch` / Rust's non-exhaustive `match`, or a test exercising the new case that shows wrong
  output. Name the enum `file:line` and the unhandled handler `file:line`.
- **`behavioral`** when no exhaustiveness check exists: grep all handlers of the type, list which
  weren't updated, and reason about what the `default` does for the new case.

## Often appears as

New status/state not handled · new error code falling to a generic branch · new feature-flag
value ignored by old dispatchers · new HTTP method/event type unrouted · added discriminated-
union member with stale consumers.
