# code-review

A senior-QA code-review skill for agentic coding tools (built for Claude Code). It does an
evidence-driven critique across correctness, security, maintainability, scalability,
architecture, efficiency, resource leaks, code smells, and tests — and can post findings to
a GitHub PR as a CodeRabbit/cubic-style batched review with resolvable inline threads, a
fix → re-review loop, size-gated reviewer fan-out, and human-gated self-verifying fixers.

This repo is the **canonical source** for the skill. Deployed copies live under
`~/.claude/skills/`, `~/.claude-env/skills/`, and `~/.agents/skills/`. To sync this repo
to those locations, run:

```bash
bash scripts/sync.sh
```

## Layout

```
SKILL.md                  # the skill instructions (the agent reads this)
REFERENCE.md              # dimension checklists, smell catalog, fan-out + fixer mechanics
scripts/post_review.py    # deterministic GitHub plumbing (post / threads / resolve / reply)
tests/test_post_review.py # unit tests for the plumbing
decisions/                # ADRs (why the skill is shaped the way it is)
CHANGELOG.md
```

## Modes

| Invocation | What it does |
|---|---|
| `/code-review` | Review the current diff / a PR; chat report only. |
| `/code-review <dir>` | Module deep-dive (architecture/maintainability/scalability). |
| `/code-review --pr <N> --comment` | Post a batched review with inline threads + summary. |
| `… --fan-out` | Parallel per-dimension reviewers (auto above the size gate). |
| `… --fix` | Dispatch human-gated, self-verifying fixers, one per finding. |

## post_review.py

Wraps the `gh` CLI so a single bad line never sinks the whole review and thread state
reconciles deterministically. `gh auth status` must succeed first.

```bash
S=scripts/post_review.py
python3 $S post <PR> findings.json --event COMMENT --body-file review.md  # batch-post
python3 $S post <PR> findings.json --dry-run                              # preview payload
python3 $S threads <PR>                                                   # open/resolved + baseline
python3 $S reply <PR> <thread_id> "Resolved in <sha>: …"
python3 $S resolve <thread_id> [<thread_id> …]
```

Notes:
- A finding whose `line` isn't in the PR diff auto-folds into the summary (GitHub rejects
  off-diff inline comments).
- On a PR you authored yourself, GitHub rejects `REQUEST_CHANGES`/`APPROVE` — use `COMMENT`.

## Findings JSON

```json
[{ "path": "src/x.ts", "line": 42, "severity": "P1",
   "title": "…", "body": "…",
   "confidence": 0.9, "evidence": "factual",
   "suggestion": "  await fix()" }]
```

`severity` ∈ `P0|P1|P2|P3`; `confidence` ∈ `[0,1]`; `evidence` ∈
`factual|behavioral|speculative`. Confidence × evidence gating decides inline vs summary
vs drop, and which fixes may auto-apply (see REFERENCE.md).

## Development

Install test dependencies and run the test suite:

```bash
pip install -e ".[test]"
python3 -m pytest tests/ -q
```

Tests can also run without pytest:

```bash
python3 tests/test_post_review.py
```

## License

MIT — see [LICENSE](LICENSE).
