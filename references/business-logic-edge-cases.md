# Business-logic & edge cases

- **Defect class:** business-logic
- **Tier:** 1
- **Applies to:** language-agnostic
- **Typical severity:** P1 (P0 when money/safety/data-loss)

## Why tools miss it

There is no rule file for "what this feature is supposed to do." Linters and SAST match
syntactic patterns; type-checkers prove shapes, not domain correctness; coverage proves the
happy path executed. The boundary cases that matter — empty input, the last page, a partial
failure, a zero/negative amount, a leap second, a currency with no minor unit — are invisible
unless a human reasons about the domain and the states the spec *implies*.

## What to look for

- **Boundaries:** empty collection, single element, max length, first/last page, the off-by-one
  at a range edge.
- **Partial failure:** a multi-step operation where step 2 fails after step 1 committed — is it
  atomic, compensated, or left half-done?
- **Money / time / units:** float for currency, missing timezone/DST handling, mixing units,
  rounding that loses cents, naive `date` math across month/year ends.
- **Forgotten states:** the spec implies states (pending/refunded/expired) the code never
  handles; an enum gained a variant but a `switch` didn't.
- **Quantity assumptions:** "there's always exactly one" / "the list is never empty" baked in
  without a guard.

## Bad / Good

```python
# Feature: "split a bill evenly across participants"
# bad — divides by len with no guard; empty party → ZeroDivisionError,
#        and integer cents are silently lost
def share(total_cents, people):
    return total_cents // len(people)

# good — guard the empty case; account for the remainder so cents aren't lost
def shares(total_cents, people):
    if not people:
        raise ValueError("no participants to split across")
    base, extra = divmod(total_cents, len(people))
    return [base + (1 if i < extra else 0) for i in range(len(people))]
```

## How to confirm it's real (evidence)

- **`behavioral`** is the common tag: the failure depends on an input (empty party, the
  boundary value). Pick the confidence within 0.5–0.8 by how many reviewers would agree the
  case is reachable in this system.
- **`factual`** when you can point to it concretely: a repo test that exercises the edge and
  fails, a typed enum whose new variant is unhandled at `file:line`, or an input the public API
  plainly accepts that hits the bug.
- Make it actionable: name the *specific* input that breaks it, not "edge cases not handled."

## Often appears as

Off-by-one · unguarded `len`/index · non-atomic multi-step write · float money · missing
timezone · unhandled enum variant · "can't be empty/null here" assumptions.
