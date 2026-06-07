# CLI — `runner` (Phase 0, dry-run)

The Phase-0 runner reviews a local diff or a PR's diff with a BYOK frontier model,
across **correctness + security**, and writes the result to disk. It **posts nothing**
(dry-run); live PR posting is Phase 2 (ADR-0019/0020).

Run from the repo root (stdlib-only; no install needed):

```bash
# Review a local patch with the Anthropic BYOK adapter
export CODE_REVIEW_API_KEY=sk-ant-...
python3 -m runner --diff /tmp/change.patch --provider anthropic --model claude-sonnet-4-6

# Review a GitHub PR (diff fetched via gh)
python3 -m runner --pr 1263 --repo LucasSantana-Dev/Lucky

# Exercise the pipeline with no API key (deterministic mock adapter)
python3 -m runner --diff /tmp/change.patch --provider mock
```

Output (default `./review/`):
- `findings.json` — the rich schema object `{schema_version, verdict, summary, findings[]}`
  (ADR-0013).
- `summary.md` — a chat-style report (`## Verdict`, per-severity sections, dimensions line).

Key flags: `--provider` (anthropic|mock) · `--model` · `--api-key-env` (default
`CODE_REVIEW_API_KEY`) · `--api-endpoint` · `--config .code-review.yml` · `--severity-floor`
· `--no-skip-trivial` · `--force-large-diff` · `--out DIR`.

Exit codes: `0` success (the review is data, not a gate); `2` infra error (missing key,
bad diff, network). See `docs/specs/2026-06-06-phase-0-mvp.md` for the full contract and the
validation gate (reproduce the skill's verdict on Lucky #1263).
