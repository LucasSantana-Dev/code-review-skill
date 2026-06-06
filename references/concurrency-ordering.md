# Concurrency: ordering & state assumptions across async boundaries

- **Defect class:** concurrency
- **Tier:** flag-don't-approve
- **Applies to:** language-agnostic (event-driven, async/await, threads, multi-consumer state)
- **Typical severity:** P1 (data loss / silent corruption under the wrong interleaving)

## Why tools miss it

Type-checkers verify a callback's signature; linters don't model *when* it fires relative to
others. The code reads correct in isolation; the break is a runtime interleaving — a read that
assumes a prior write happened, a lock taken in the wrong order, a non-atomic
read-modify-write. Catching it needs a human to trace the timeline and name the bad window.
This class is **high false-positive** (the unsafe interleaving may be unreachable in practice),
so **raise it as a question with the precise scenario — don't assert a fix.** Real reviewers
prove it by walking the phases. (See React
[#18000](https://github.com/facebook/react/pull/18000): a torn mutable source wasn't version-
reset on all readers after an error unwind, so the re-render kept hitting the same error.)

## What to look for

- A handler that reads state set by another handler, assuming order without a guard or an
  explicit dependency (`await`/promise chain/barrier).
- Lock acquisition whose order isn't the codebase's documented hierarchy → deadlock when two
  paths race.
- Check-then-act / read-modify-write on shared state that isn't atomic (TOCTOU).
- "Assumes X initialized first", "must run after Y" in comments, with nothing enforcing it.
- Shared mutable state touched by >1 renderer/worker/request without synchronization.

## Bad / Good

```ts
// bad — two independent listeners; 'data' can fire before 'load' sets `user`
let user: User | null = null
el.addEventListener("load", () => { user = fetchUser() })
el.addEventListener("data", () => { send(user!.id) })  // throws if 'data' wins the race

// good — sequence the dependency (or guard the read)
await new Promise(r => el.addEventListener("load", r, { once: true }))
user = fetchUser()
el.addEventListener("data", () => { if (user) send(user.id) })
```

## How to confirm it's real (evidence)

- This class is **flag-don't-approve**: phrase it as a high-severity *question* naming the exact
  interleaving ("if `data` fires before `load`, `user` is null at `x.ts:12`"). Tag **`behavioral`**
  unless you can force it.
- It becomes **`factual`** when a repo test reproduces the bad order (or a stress/race test
  fails), or a documented lock hierarchy is provably violated at `file:line`.
- Don't claim certainty about probability from static code; describe the window, don't assert
  the odds.

## Often appears as

Event-listener races · missing `await`/promise chain between dependent steps · lock-order
inversion / deadlock · non-atomic read-modify-write · TOCTOU · shared state mutated by multiple
workers without a barrier · stale read after error unwind.
