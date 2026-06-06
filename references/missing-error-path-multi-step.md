# Missing error path in a multi-step operation

- **Defect class:** api-misuse
- **Tier:** 1
- **Applies to:** language-agnostic (DB writes, queues, caches, resource acquisition, distributed ops)
- **Typical severity:** P1 (leak / stale state) · P0 (data corruption if uncompensated)

## Why tools miss it

Linters check that a `try`/`catch` exists; coverage checks the happy path ran. Neither asks
*what happens when step 1 commits and step 2 fails*: is the whole thing atomic, is step 1
compensated, or is it left half-done? The error path lives in the design's intent, not in any
single statement — so static tools see a valid sequence and a valid catch, and miss the
orphaned write. Real reviewers catch this by tracing each failure point. (See Kafka
[#15557](https://github.com/apache/kafka/pull/15557): a replica acknowledged then failed
before catching up — the "acknowledged-but-not-caught-up" window had no reversal path.)

## What to look for

- A sequence of 2+ effects (write → publish, insert → index, acquire → use) where a later step
  can fail after an earlier one already committed — with no rollback/compensation.
- A "transaction" assumed to wrap both steps, but the code spans modules and never threads the
  transaction context through.
- A resource acquired (lock, file, connection, subscription) without a matching release on the
  error path.
- Partial success treated as success ("if any of them queued, we're done").

## Bad / Good

```python
# bad — DB row is committed; if the cache write throws, state is now inconsistent
def create_user(name, email):
    user = User.create(db, name=name, email=email)   # step 1 committed
    cache.set(f"user:{user.id}", user)               # step 2 can fail → orphaned/stale
    return user

# good — compensate on failure (or wrap both in one transaction)
def create_user(name, email):
    user = User.create(db, name=name, email=email)
    try:
        cache.set(f"user:{user.id}", user)
    except CacheError:
        User.delete(db, user.id)   # roll back step 1
        raise
    return user
```

## How to confirm it's real (evidence)

- **`factual`** when a repo test injects a failure at step 2 and shows step 1's effect persists
  (orphaned row, stale cache, leaked handle) — cite the test, or the missing `finally`/rollback
  at `file:line`.
- **`behavioral`** when the interleaving depends on runtime failure you can't force statically:
  name both steps, the failure point between them, and whether the spec requires atomicity; rate
  by independent-reviewer agreement.

## Often appears as

Uncompensated write-then-publish · resource acquired but not released on error · cache update
decoupled from the source write · missing cleanup in a constructor/initializer · implicit
atomicity assumed across function or service boundaries.
