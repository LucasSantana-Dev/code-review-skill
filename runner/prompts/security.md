## Dimension: security

Find changes that introduce a vulnerability or weaken an existing control. Logic-level
security the linters miss, not generic SAST noise.

Checklist (REFERENCE.md#security):
- Input validation / injection (SQL, command, path traversal, SSRF, template, XSS).
- AuthN/AuthZ: missing or broken permission checks, privilege escalation, IDOR/broken
  access control, tenant isolation.
- Secrets: hardcoded credentials/keys/tokens, secrets logged or echoed.
- Unsafe deserialization, SSTI, prototype pollution, unsafe `eval`/dynamic exec.
- TOCTOU / race-based auth bypass; missing rate limits on sensitive endpoints.
- Sensitive-data exposure (PII in logs/responses), weak crypto, missing output encoding.

Patterns to recognize (advisory, from references/): broken-access-control,
intent-implementation-mismatch (a "rate limit" PR that actually caches, etc.).
