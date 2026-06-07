## Dimension: correctness

Find code that runs and type-checks but computes the wrong thing or breaks an invariant.

Checklist (REFERENCE.md#correctness):
- Logic matches stated intent; edge cases (empty, null, zero, max, unicode, concurrency).
- Off-by-one, boundary conditions, integer/float precision, timezone/date handling.
- Error paths return/throw correctly; no swallowed errors; failures are observable.
- Async: awaited promises, no floating promises, races, cancellation, ordering.
- Idempotency where retried; transactions cover multi-step state changes.
- Cross-file invariants the change could break (callers, contracts) — within the diff's
  immediate blast radius only.

Patterns to recognize (advisory, from references/): intent-vs-implementation mismatch,
business-logic edge cases, missing error path in multi-step ops, unhandled enum variant.
