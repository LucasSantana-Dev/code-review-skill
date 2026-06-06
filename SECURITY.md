# Security

## The token model — no shared secret

This skill posts reviews to GitHub under a **bot identity you own**. There is no hosted service and
no shared credential: each user registers their *own* GitHub App (or machine account) and supplies
their *own* private key. `scripts/app_token.py` mints a short-lived (≈1h) installation token
locally — it signs an RS256 JWT via `openssl` and exchanges it. The key is read from an env var or
file path **you** control; it is never written to disk by the script and never transmitted anywhere
except GitHub's token endpoint. See [ADR-0004](decisions/0004-github-app-posting-identity.md).

**Your responsibilities:**
- **Never commit your App's private key.** Keep it in a secret store (e.g. the OS keychain) or a
  file outside the repo; pass it via env/path at run time.
- **Scope the App minimally** — Pull requests: write, Contents: read, Metadata: read. Don't grant
  admin/security scopes it doesn't need.
- **Never use someone else's App or a shared key.** Forks must register their own.

Because there is no central secret, a compromise of this repository cannot leak any user's token —
the isolation is per-installation by design.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately**, not in a public issue:

- Open a GitHub **Security Advisory** on this repository (Security → Report a vulnerability), or
- email the maintainer (see the GitHub profile).

Include repro steps and affected version/commit. This is a solo-maintained project; expect an
initial acknowledgment within a few days. Fixes land on `main` with a CHANGELOG note.

## Supply-chain note

Public registries may auto-index this repo and its forks. Verify you're installing from
`LucasSantana-Dev/code-review-skill` (or a fork you trust) before running the scripts, and read the
diff on update — the code is small and stdlib-only by design, so it's auditable.
