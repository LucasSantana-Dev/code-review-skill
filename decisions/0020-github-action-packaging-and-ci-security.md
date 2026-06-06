# ADR-0020: GitHub Action packaging + CI security — composite action, `pull_request` trigger, least privilege, bot identity

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0004](0004-github-app-posting-identity.md) (bot posting identity), [ADR-0010](0010-headless-ci-action-runner.md), [ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md)
- **Informed by:** design tracks + critic; GitHub Security Lab "Preventing Pwn Requests"; GitHub Actions secure-use + metadata docs (2026)

## Context

The runner ships as a GitHub Action that handles secrets (an LLM key, a GitHub App private
key) and **posts to PRs** — a security-sensitive surface. Three hard-to-reverse, security-
load-bearing choices must be made before code: the action *type*, the *event trigger*
(fork-PR safety), and *how the bot token is minted*. The critic flagged fork-PR security
and the active bot-identity blocker as gaps.

## Decision

1. **Composite action** (`action.yml` + embedded steps calling Python), **not** Docker or
   JavaScript. Reuses the existing stdlib scripts with **zero new dependencies** and no
   container boot; portable across runners. (The runner already assumes Python 3.9 + `git`
   + `gh` + `openssl`, as the skill does — [ADR-0011](0011-monorepo-structure-and-python-stdlib-runtime.md).)
2. **`pull_request` trigger, never `pull_request_target`.** The runner needs no base-repo
   secrets to read a diff and review it, so it uses the safe trigger that does **not**
   expose secrets to untrusted fork code (mitigates the "pwn request" / Poisoned Pipeline
   Execution class). The LLM key + App key are provided by the *consuming* workflow's
   secrets, only on non-fork or maintainer-approved runs.
3. **Least-privilege permissions:** `contents: read`, `pull-requests: write`,
   `metadata: read`. No `admin`, `workflow`, or broad write.
4. **Bot token minted in-action via the existing `app_token.py`** (stdlib + `openssl`),
   **not** a third-party token action — single source of truth with the skill, full control
   if GitHub's token format changes (as it did Apr–May 2026). The
   `CODE_REVIEW_BOT_LOGIN` guard in `post_review.py` refuses any non-bot identity, so a
   misconfigured CI can never post under a personal account.
5. **Input/output contract** at `action.yml`: inputs `provider`, `model`, `api-key`,
   `api-endpoint`, `github-app-id`, `github-app-key`, `config-path`, `severity-floor`
   (default P1), `dry-run`; outputs `findings-count`, `findings-file`, `summary-file`,
   `review-url`. Secrets are passed as inputs from `secrets.*`, never hardcoded, never logged.

## Alternatives considered

- **Docker action** — strong isolation, but slow container boot, Linux-only, and overkill
  for a thin Python wrapper. Rejected.
- **JavaScript action** — fastest native, but needs Node + bundling Python; contradicts the
  Python-first, stdlib-thin choice. Rejected.
- **`pull_request_target`** — needed only if reviewing forks required base-repo secrets;
  it doesn't, and the trigger is the primary fork-PR attack surface. Rejected.
- **`actions/create-github-app-token` (or a third-party token action)** — official/maintained,
  but vendor lock-in on trivial logic the project already owns and tests. Rejected; keep `app_token.py`.

## Consequences

**Positive:** zero new dependencies; safe-by-default against fork-PR attacks; minimal blast
radius; one token-minting code path shared with the skill; honest bot identity enforced by guard.

**Negative:** composite actions give no environment guarantees (Python/`gh`/`openssl` must
exist on the runner — documented prerequisite); a future feature needing base-repo secrets
would force a trigger rethink (separate ADR); bot identity (key/ID/login) **must be
configured before Phase 2** — it is the carried blocker from
[ADR-0004](0004-github-app-posting-identity.md) and
[ADR-0019](0019-phase-0-mvp-scope.md).

**Neutral:** Marketplace discoverability is identical across action types.

## Revisit when

- A feature genuinely requires base-repo secrets on fork PRs → open a dedicated security ADR
  before touching the trigger.
- `openssl` is unavailable on a target runner → document; fall back to a token action there only.
- A new capability needs a broader permission → justify it in its own ADR (don't widen silently).
