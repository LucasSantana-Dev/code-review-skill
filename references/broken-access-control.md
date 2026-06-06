# Broken access control (authz / IDOR)

- **Defect class:** security-logic
- **Tier:** flag-don't-approve
- **Applies to:** language-agnostic (server-side / API / data-access)
- **Typical severity:** P0

## Why tools miss it

SAST and secret scanners match *patterns* — hardcoded keys, injection sinks, known CVEs. Broken
access control is **logic**: the right check is simply absent, or present but scoped wrong. There
is no syntactic signature for "this handler trusts a user-supplied id without verifying the
caller owns it." Authorization is the #1 web risk precisely because it requires reasoning about
the privilege model and data ownership, which automated gates don't model. Tests usually cover
the *authorized* path, not the *unauthorized* one.

## What to look for

- **IDOR:** a resource fetched/updated by an id taken from the request (path/query/body) with no
  check that the authenticated principal may access *that* resource. `GET /orders/:id` returning
  any order.
- **Missing check on a new path:** a new endpoint/action added without the authz guard its
  siblings have.
- **Wrong scope:** authenticated ≠ authorized; role checked but not *ownership*; check on the
  parent but not the child resource.
- **Client-trusted authority:** role/permission/tenant read from a request field or JWT claim
  the client controls, rather than re-derived server-side.
- **Mass-assignment into privileged fields:** binding request body straight onto a model lets a
  user set `role`/`ownerId`/`isAdmin`.

## Bad / Good

```ts
// bad — any logged-in user can read any order by guessing the id (IDOR)
app.get("/orders/:id", requireAuth, async (req, res) => {
  const order = await db.order.findById(req.params.id)
  res.json(order)
})

// good — scope the lookup to the caller; ownership is enforced, not assumed
app.get("/orders/:id", requireAuth, async (req, res) => {
  const order = await db.order.findOne({ id: req.params.id, userId: req.user.id })
  if (!order) return res.sendStatus(404)   // 404, not 403 — don't confirm existence
  res.json(order)
})
```

## How to confirm it's real (evidence)

- This class is **flag-don't-approve**: raise it as a high-severity *question with the precise
  risk*, not an asserted certainty — you rarely see the full privilege model from a diff. Tag
  **`behavioral`** unless you can prove the gap.
- It becomes **`factual`** when the diff plainly shows a privileged path with no ownership/role
  check and you can name the unauthorized request that would succeed (`file:line` of the handler,
  the id source, the absent check).
- Don't downgrade for politeness: missing access control is P0. The calibration fix is to phrase
  it as a question ("Can a non-owner call this with another user's `id`?"), not to drop it.

## Often appears as

IDOR · missing authz on a new route · ownership-vs-authentication confusion · client-controlled
role/tenant · mass assignment · TOCTOU between check and use · confused-deputy via an internal
service call.
