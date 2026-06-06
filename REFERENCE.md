# Code Review — Dimension checklists, smell catalog & PR-posting mechanics

Reference for `code-review`. Use the relevant sections; don't run every check on every
diff — scope to what the change actually touches.

## Correctness

- Logic matches stated intent; edge cases (empty, null, zero, max, unicode, concurrency).
- Off-by-one, boundary conditions, integer/float/precision, timezone/date handling.
- Error paths return/throw correctly; no swallowed errors; failures are observable.
- Async: awaited promises, no floating promises, race conditions, cancellation, ordering.
- Idempotency where retried; transactions cover multi-step state changes.

## Security

- Input validation + sanitization at trust boundaries (don't trust the client/DB/3rd-party).
- Injection: SQL/NoSQL/command/template/path-traversal/SSRF/XSS.
- Secrets: none hardcoded or logged; query strings/tokens not sent to logs or telemetry.
- AuthN/AuthZ on every privileged path; no IDOR; least privilege.
- Deserialization, regex DoS (catastrophic backtracking), unbounded allocation.

## Maintainability

- A new engineer can follow it: clear names, single responsibility, low nesting.
- Function/file size and cyclomatic complexity reasonable (target <50 lines / CC <10);
  flag the *outliers*, not every long function.
- DRY without premature abstraction; no copy-paste drift between near-identical blocks.
- Comments explain *why*, not *what*; no stale/misleading comments; no dead code.
- Change is localized; touched files trace to the stated request (no scope creep).

## Scalability

- Behavior at 10×/100× input: pagination/streaming vs load-all-in-memory.
- N+1 queries, unindexed lookups, full scans, missing composite indexes for the access pattern.
- Unbounded growth: caches/maps/queues without eviction or size cap; per-request work that
  grows with total data.
- Hot-path allocation, sync I/O on the request path, lock contention, head-of-line blocking.
- Statefulness that blocks horizontal scaling (in-process state that should be shared/external).

## Architecture / structure

- Respects existing boundaries, layering, and ADRs; dependencies point the right way
  (no inward leaks, no new cycles).
- Right seam: is logic in the right module/layer? Does it belong behind an interface?
- Coupling/cohesion: changes ripple appropriately; no god-objects or feature-envy.
- Public surface (API/types/events) is minimal, stable, and hard to misuse.
- Configuration/feature-flag/migration handled where it belongs, not inline.

## Efficiency

- Algorithmic complexity appropriate; no accidental O(n²) over realistic inputs.
- Redundant work: recomputation, repeated parsing/serialization, needless copies.
- Batching/caching opportunities only where they pay off and don't add staleness bugs.
- Bundle/startup cost for client code; lazy-load where heavy.

## Resource safety (leaks)

- Every open resource is closed on *all* paths: files, sockets, DB connections/pools,
  streams, subscriptions, timers/intervals, watchers, event listeners.
- Cleanup on error and on teardown/shutdown (try/finally, defer, `using`, disposers).
- No retained references that prevent GC (closures capturing large scope, growing caches).
- Backpressure on streams/queues; bounded concurrency.

## Code smells (name the smell, point to recurrences)

Long method · large class/file · long parameter list · primitive obsession · feature envy ·
data clumps · shotgun surgery · divergent change · duplicated code · dead code ·
speculative generality · temporal coupling · boolean/flag params · deep nesting / arrow code ·
magic numbers/strings · stringly-typed · leaky abstraction · god object · anemic model ·
nullable-everywhere · exception-as-control-flow · silent catch · TODO/FIXME debt.

## Test coverage & quality

- New behavior has tests that would *fail without the change* (assert behavior, not calls).
- Edge cases + error paths covered, not just the happy path.
- Tests are deterministic (no real time/network/random), isolated, and readable.
- No disabled/`skip`/`xfail`/`@ts-nocheck` masking failures; mocks match real contracts.
- Coverage cite: new-code coverage number when the repo gates on it; name the uncovered lines.

## Best practices / conventions

- Follows the repo's existing idioms (read neighbors): error handling, logging, config,
  imports, naming, formatting, commit/PR conventions.
- Logging/observability at the right level; no PII; structured where the repo expects it.
- Backward compatibility / migration safety (additive schema, API versioning, rollouts).
- Docs/ADR updated when the change establishes or breaks a convention.

---

## PR posting & re-review

Mechanics for *PR-comment mode*. The bundled `scripts/post_review.py` wraps the `gh`
CLI so a single bad line never sinks the whole review and thread state is reconciled
deterministically. `gh auth status` must succeed first.

**Posting identity.** The review is posted under whatever account `gh` (or `GH_TOKEN`) is
authenticated as — **never post under a human operator's personal account.** Authenticate
`gh` as a dedicated machine/bot account (or set `GH_TOKEN` to its PAT) before posting. Set
`CODE_REVIEW_BOT_LOGIN=<bot-login>` and the script refuses to post/resolve/reply unless the
authenticated login matches it. The posted summary uses a neutral `## Code review` header —
do not stamp it with a persona label.

### Findings JSON

A list of objects; one object = one inline thread:

```json
[
  {"path": "src/api/upload.ts", "line": 42, "severity": "P1",
   "title": "unawaited write can lose data on crash",
   "body": "`fs.writeFile` is fire-and-forget; an error here is swallowed…",
   "suggestion": "  await fs.promises.writeFile(dest, buf)"}
]
```

- `severity` ∈ `P0|P1|P2|P3`. `side` defaults to `RIGHT`. `start_line` makes a multi-line thread.
- `suggestion` (optional) renders as a committable ` ```suggestion ` block — small, single-location fixes only.
- Findings whose `line` isn't in the PR diff are auto-folded into the review summary
  (GitHub rejects inline comments off the diff) instead of failing the post.

### Commands

```bash
S=scripts/post_review.py
python3 $S post <PR> findings.json --event COMMENT      # batch-post; stamps baseline SHA
python3 $S post <PR> findings.json --event COMMENT --dry-run   # preview payload, post nothing
python3 $S threads <PR>          # our open/resolved threads + last baseline SHA (JSON)
python3 $S baseline <PR>         # just the last baseline SHA
python3 $S reply <PR> <thread_id> "Resolved in <sha>: …"
python3 $S resolve <thread_id> [<thread_id> …]
```

`--repo <owner>/<name>` overrides the auto-detected repo. `--event REQUEST_CHANGES` when a
P0/P1 stands; `APPROVE` only when genuinely clean; `COMMENT` otherwise.

### Re-review loop (incremental)

1. `threads <PR>` → list open threads + the `baseline` SHA from the prior review body.
2. `git diff <baseline>..HEAD` → scope to what changed since the last pass.
3. Per open thread, re-read the code at its `path:line`:
   - **Outdated** (`isOutdated: true` — the line moved or changed since the comment) →
     re-read at the code's *current* location, don't trust the stale `line`. If the issue
     is gone, `reply` "Resolved in `<sha>`: …" then `resolve`; if it still applies, `reply`
     with the updated location.
   - **Fixed** → `reply` "Resolved in `<sha>`: …" then `resolve <thread_id>`.
   - **Still open** → leave it, or `reply` with the precise remaining gap.
4. New issues introduced by the fix → collect into a fresh `findings.json` and `post` again
   (the new review stamps a new baseline).
5. Only resolve threads **you** authored. Never resolve/dismiss a human reviewer's thread.

### Raw API (if the script is unavailable)

```bash
# Batched review with inline threads:
gh api repos/{o}/{r}/pulls/{N}/reviews --method POST --input - <<'JSON'
{"event":"COMMENT","body":"## Code review …\n<!-- code-review:baseline=<sha> -->",
 "comments":[{"path":"src/foo.ts","line":42,"side":"RIGHT","body":"**P1** …"}]}
JSON

# List threads + resolution state:
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){
  pullRequest(number:$n){reviewThreads(first:100){nodes{id isResolved isOutdated
  comments(first:1){nodes{path line author{login}}}}}}}}' -F o=O -F r=R -F n=N

# Resolve a thread:
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -F id=THREAD_ID
```

---

## Reviewer fan-out (large diffs only)

Single-pass is the default. Fan out **only** above the size gate (>~600 changed LOC or
>~15 files, or explicit `--fan-out`) — below it, fan-out costs tokens + worktree overhead
with no precision gain.

**Drive with the `Workflow` primitive** (deterministic, budget-aware) — one lane per
dimension, each returning the standard findings shape via a JSON `schema`:

```js
// inside a Workflow script
const LANES = ['correctness','security','perf','tests','maintainability']
const byLane = await parallel(LANES.map(d => () =>
  agent(`Review this diff strictly through the ${d} lens. Return findings only.`,
        { label: `review:${d}`, schema: FINDINGS_SCHEMA })))
const all = byLane.filter(Boolean).flatMap(r => r.findings)
```

### Dedup before posting

Two lanes will flag the same line. Fingerprint each finding by `(path, line, category)`
(category = the issue kind: `null-deref`, `unused`, `race`, …). On collision: keep the
**max severity**, **average the confidences then +0.1 per extra agreeing lane** (capped at
1.0 — independent agreement is real signal), union the bodies, record `sources:[lanes]`.
Pseudocode:

```
key = `${f.path}:${f.line}:${f.category}`
if (seen[key]) {
  seen[key].severity   = maxSev(seen[key].severity, f.severity)
  seen[key].sources.push(f.lane)
  seen[key].confidence = min(1, avg(seen[key].confidence, f.confidence) + 0.1*(seen[key].sources.length-1))
  seen[key].body       = union(seen[key].body, f.body)
} else seen[key] = {...f, sources:[f.lane]}
```

### Confidence & evidence gating

After dedup, each finding's `(severity, confidence, evidence)` decides its disposition.
The orchestrator owns this — never a lane. Drop nitpicks before they become threads:

| severity \ confidence | ≥0.8 | 0.5–0.8 | <0.5 |
|---|---|---|---|
| **P0/P1** | inline thread | inline thread | inline thread |
| **P2** | inline thread | summary | drop |
| **P3** | inline (only if `factual`) | summary | drop |

- `evidence=factual` (provable now: type error, null-deref, a test assertion in the repo's suite, or a real type error the repo's own typecheck fails on;
  evidence must cite exact file:line and why no runtime context is needed — see SKILL.md *Evidence-tiered*) →
  confidence band 0.8–1.0; the only tier eligible for `--fix` auto-apply.
- `evidence=behavioral` (depends on runtime/inputs; not provable from static code alone) →
  confidence band 0.5–0.8; propose-only for `--fix`, never auto-applied.
- `evidence=speculative` (a hunch) → confidence band 0.0–0.5; never inline regardless of
  confidence; fold to *Open questions*. **Exception: P0/P1 findings always post inline
  (see matrix row above).**
- This matrix is the single biggest false-positive lever — most "AI reviewer noise" is
  low-confidence P3 nitpicks posted as inline threads. (CodeRabbit/Qodo both gate this way.)

#### Counter-example: factual vs. behavioral boundary

**Claim:** "This map grows unbounded and will OOM the server."

**Looks factual** — the code allocates a map, never clears it, so it must grow.

**Actually behavioral:** the growth depends on runtime input volume (how many cache keys are
created by users), which the static code cannot prove. The same code might be safe in a
low-volume service and unsafe under peak load. **Tag: behavioral (band 0.5–0.8).** Pick the
value within the band by the agreement question: if prior incidents on similar code in this
repo mean most reviewers would call it risky, that's the upper end (~0.7–0.8); a first
sighting with weaker agreement sits lower (~0.5–0.6).

**To make it factual**, cite one of these:
- "A test in the repo's suite at `file:line` demonstrates the OOM at typical load."
- "The repo's typecheck fails at `file:line` (cite the error)."
- "Commit `<sha>` added a test specifically for this bug; it fails without the fix."

Do not claim "I could write a test that shows this" or "under 100 req/sec for 24 hours it
would OOM" — that is hypothetical, not factual. Anchor to what *is* in the repo or what *has*
been observed (failed tests, failed typechecks, production incidents), not what *could be*
written or inferred.

---

## Fixer dispatch (`--fix`) — tiers, worktrees, verification

### Action tier matrix

| Finding | Path | Action |
|---|---|---|
| Mechanical + `evidence=factual` + `confidence≥0.8` (rename, dead-code, format, typo, missing-await on fire-and-forget) | non-protected | **auto-apply** |
| Logic-bearing (control flow, conditions, data flow, query/SQL, retry/timeout) — or any `behavioral`/`speculative` finding | non-protected | **propose-only** → show diff, get approval |
| Anything | protected (auth, payments, deploy/CI config, prisma migrations, `main`) | **propose-only**, never auto |
| `confidence < ~0.8` or non-`factual` | any | don't dispatch a fixer — leave the comment |

Auto-apply requires **all four**: mechanical · `factual` · `confidence≥0.8` · non-protected
path. Anything short of that is propose-only. (Auto-applying a `behavioral` fix is how a
plausible-but-wrong change reaches prod under deploy-on-merge.)

### Per-finding loop (sequential on one PR branch)

1. Create a worktree off the PR branch under the repo's worktrees dir; brief the fixer with
   the finding (`path:line`, evidence, the exact fix), the tier, and "push to PR branch only".
2. Fixer applies the fix **only at the finding's site** (surgical — no adjacent cleanup).
3. **Self-verify** — fixer runs the affected suite + `git diff` and returns *real* output.
4. **You re-verify** — never trust the fixer's "✅": run the suite yourself / read the diff.
   If green and the diff is exactly the fix → `reply` "Resolved in `<sha>`: …" + `resolve`.
   If not → re-brief or escalate to propose-only; do **not** resolve.
5. Next finding. Worktrees are isolated, but pushes to a single branch must be serialized
   (no two fixers pushing the same branch concurrently).

### Hard lines

- Never push to `main`; never `--admin`/force; never bypass the human pre-merge review
  (merge auto-arms a prod deploy — the human read is the last gate before users see it).
- A fixer that wants to change >1 site, touch a protected path, or alter a contract →
  stop and propose, don't apply.
- Resolve a thread only on **re-verified** green, authored by you (bot) — never a human's.
