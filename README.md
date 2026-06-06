# code-review

A code-review skill for agentic coding tools (built for Claude Code). It does an
evidence-driven critique across correctness, security, maintainability, scalability,
architecture, efficiency, resource leaks, code smells, and tests — and can post findings to
a GitHub PR as a CodeRabbit/cubic-style batched review with resolvable inline threads, a
fix → re-review loop, size-gated reviewer fan-out, and human-gated self-verifying fixers.

## Install

Clone (or fork) into your Claude Code skills directory:

```bash
git clone https://github.com/LucasSantana-Dev/code-review-skill ~/.claude/skills/code-review
```

That's the whole install — `SKILL.md` + `scripts/` (Python stdlib only) + `references/`. Update
later with `git pull`. Forking is encouraged: the `references/` library is meant to be extended
(see [CONTRIBUTING.md](CONTRIBUTING.md)).

> `scripts/sync.sh` is a maintainer convenience that mirrors this repo into several local skill
> dirs (`~/.claude/skills/`, `~/.claude-env/skills/`, `~/.agents/skills/`); end users only need
> the single clone above.

## License & openness

Permissively licensed (Apache-2.0 — see [LICENSE](LICENSE)). The [`references/`](references/)
library is *deliberately* open, forkable, and community-curatable — the opposite of a proprietary
locked "learnings" database. We keep it open by intent and by keeping it good, not by a copyleft
clause ([ADR-0008](decisions/0008-permissive-not-copyleft-for-the-corpus.md)): the upstream
library stays fresher than any closed fork, and contributions compound here. Send your patterns
back — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Why a bundled script, not an MCP server?

A skill is `SKILL.md` + bundled resources, and **bundled scripts are the canonical pattern**
for deterministic work (Anthropic's own `pdf`/`docx`/`xlsx` skills ship Python). This skill is
deliberately two-layered:

- **Judgment** (`SKILL.md` + `REFERENCE.md`) — the review reasoning. This is what
  makes it a *skill*, and it ports anywhere the Agent Skills spec is supported.
- **Mechanics** (`scripts/post_review.py`) — deterministic, error-prone GitHub plumbing
  (batched inline threads, GraphQL resolve/reply, baseline-SHA re-review, off-diff folding).
  The agent supplies findings as JSON; the script makes no judgment calls and its code never
  enters the model's context.

**Scope (honest):** the *posting* path shells out to the `gh` CLI, so it targets Claude Code
(and skills-spec agents) with `gh` installed and authenticated — it is **not** claimed to run
unchanged in headless CI or non-script agents. Overhead is a few hundred ms per `gh` call,
immaterial for on-demand use. If cross-agent/headless posting becomes a need, the migration
path is to extract these operations into an **MCP server** — deliberately deferred until then
(see [decisions/0003](decisions/0003-keep-bundled-script-skill-packaging.md)).

## Layout

```
SKILL.md                  # the skill instructions (the agent reads this)
REFERENCE.md              # dimension checklists, smell catalog, fan-out + fixer mechanics
scripts/post_review.py    # deterministic GitHub plumbing (post / threads / resolve / reply)
scripts/app_token.py      # mint a GitHub App installation token (post as a bot, not a person)
tests/test_post_review.py # unit tests for the plumbing
tests/test_app_token.py   # unit tests for the token minter
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

> **Prerequisites:** the review-only modes need only the repo. The `--comment` and `--fix`
> modes post to GitHub via the `gh` CLI, so `gh auth status` must succeed first.

## post_review.py

Wraps the `gh` CLI so a single bad line never sinks the whole review and thread state
reconciles deterministically. `gh auth status` must succeed first.

```bash
S=scripts/post_review.py
python3 $S post <PR> findings.json --event COMMENT --body-file review.md  # batch-post
python3 $S post <PR> findings.json --dry-run                              # preview payload
python3 $S threads <PR>                                                   # open/resolved + baseline
python3 $S baseline <PR>                                                  # just the last baseline SHA
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
