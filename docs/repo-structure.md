# Repository structure — target layout

**Status:** Design (pre-code) · **Date:** 2026-06-06 · **Decision:** [ADR-0011](../decisions/0011-monorepo-structure-and-python-stdlib-runtime.md)

The runner extends **this** repo (monorepo) so `SKILL.md`, `REFERENCE.md`, and `references/`
stay the single source of truth for both the interactive skill and the headless Action. The
runner is purely **additive** — no existing skill code is refactored.

## Legend

`(existing)` already in the repo · `(NEW)` added by the runner work · phase tag = when it lands.

```
code-review-skill/
├── SKILL.md                         (existing)  review judgment — shared by skill + Action
├── REFERENCE.md                     (existing)  per-dimension checklists + smell catalog
├── README.md                        (existing)  → expanded: skill vs Action, quick start  (P2)
├── action.yml                       (NEW, P2)   composite GitHub Action metadata  (ADR-0020)
├── pyproject.toml                   (existing)  → version synced with action.yml  (ADR-0024)
├── CHANGELOG.md                     (existing)  → runner phases
│
├── references/                      (existing)  forkable knowledge layer (shared)
│   ├── README.md
│   ├── broken-access-control.md
│   ├── business-logic-edge-cases.md
│   ├── concurrency-ordering.md
│   ├── cross-file-invariant-break.md
│   ├── intent-implementation-mismatch.md
│   ├── missing-error-path-multi-step.md
│   └── unhandled-enum-variant.md
│
├── scripts/                         (existing)  reused UNCHANGED by the runner
│   ├── post_review.py               (existing)  batched PR review + thread mgmt + baseline SHA
│   └── app_token.py                 (existing)  GitHub App token minter (stdlib + openssl)
│
├── runner/                          (NEW)       the headless engine  (ADR-0012)
│   ├── __init__.py
│   ├── pipeline.py                  (P0)        orchestrator: stage order, dry-run vs post
│   ├── models.py                    (P0)        Finding, DiffHunk, ReviewContext  (ADR-0013)
│   ├── config.py                    (P0→P4)     .code-review.yml + inputs + CLAUDE.md  (ADR-0021)
│   ├── cli.py                       (P0)        `python3 -m runner` entrypoint (CLI + action glue)
│   ├── stages/
│   │   ├── prefilter.py             (P1)        Stage 1: linters/Semgrep → SARIF → Finding  (ADR-0015)
│   │   ├── scope.py                 (P0)        Stage 2: hunks + N=10 context, trivial-skip  (ADR-0016)
│   │   ├── llm_review.py            (P0)        Stage 3: prompt build + structured output  (ADR-0017)
│   │   ├── merge.py                 (P0)        Stage 4: dedup + ADR-0002 gating  (ADR-0018)
│   │   └── post.py                  (P0 dry / P2 live)  Stage 5 → scripts/post_review.py
│   ├── adapters/
│   │   ├── base.py                  (P0)        ModelAdapter contract  (ADR-0014)
│   │   ├── anthropic.py             (P0)        BYOK, validated first
│   │   ├── openai_compat.py         (P1)        BYOK OpenAI-compatible (incl. local servers)
│   │   └── ollama.py                (P3)        free local fallback
│   └── prompts/
│       ├── _rubric.md               (P0)        ADR-0002 calibration rubric (verbatim, shared)
│       ├── correctness.md           (P0)        dimension template
│       └── security.md              (P0)        dimension template (others phase in: P1+)
│
├── eval/                            (NEW, P1)   quality harness (not CI-gated)  (ADR-0023)
│   ├── measure.py                   (P1)        run on test PRs → FP/FN/precision/recall/cost CSV
│   ├── drift_guard.py               (P1)        references/ coverage drift report  (ADR-0022)
│   ├── test_prs.json                (P1)        committed ground truth (~10 PRs)
│   └── results/                     (P1)        CSV + reports (gitignored except samples)
│
├── tests/                           (existing + NEW)
│   ├── test_post_review.py          (existing)
│   ├── test_app_token.py            (existing)
│   ├── test_models.py               (NEW, P0)
│   ├── test_scope.py                (NEW, P0)
│   ├── test_llm_review.py           (NEW, P0)   mocks the adapter
│   ├── test_merge.py                (NEW, P0)
│   ├── test_prefilter.py            (NEW, P1)
│   ├── test_adapters.py             (NEW, P0)
│   ├── test_integration.py          (NEW, P0)   full pipeline on a fixture PR (dry-run)
│   └── fixtures/                    (NEW)       sample diffs, SARIF outputs, mock responses
│
├── .code-review.yml.example         (NEW, P0)   minimal config template  (ADR-0021)
│
├── .github/workflows/
│   ├── ci.yml                       (existing/NEW)  unit tests + typecheck + lint
│   └── self-review.yml              (NEW, P2)   dogfood: the Action reviews this repo's PRs
│
├── docs/
│   ├── architecture.md              (NEW)       system map  (this design)
│   ├── repo-structure.md            (NEW)       this file
│   ├── roadmap.md                   (NEW)       features + phases + gates
│   ├── glossary.md                  (NEW)       shared vocabulary
│   ├── documentation-plan.md        (NEW)       what user docs will exist (and when)
│   ├── PROMPT_CONSTRUCTION_RESEARCH.md  (existing)
│   └── specs/
│       ├── 2026-06-06-ci-action-runner.md       (existing)  high-level spec
│       └── 2026-06-06-phase-0-mvp.md            (NEW)       implementable Phase-0 spec
│
└── decisions/
    ├── 0001…0010                    (existing)
    └── 0011…0024                    (NEW)        this design package  (ADR-0011 … ADR-0024)
```

## Notes

- **`scripts/` is frozen** for this work — `post_review.py` / `app_token.py` are reused as-is;
  any change to them is its own PR, not part of the runner build.
- **Two entrypoints, one engine:** `action.yml` (CI) and `python3 -m runner` (CLI/local) both
  call `runner/pipeline.py`. ([ADR-0011](../decisions/0011-monorepo-structure-and-python-stdlib-runtime.md))
- **Stdlib-only in `runner/`** — `urllib` for HTTP, `json` for I/O, a tiny in-tree reader for
  the flat `.code-review.yml` subset; `PyYAML` only adopted when nested path-rules ship.
  ([ADR-0021](../decisions/0021-config-schema-code-review-yml.md))
- File counts/names are the *target*; the build follows the phase tags in
  [roadmap.md](roadmap.md), not all at once.
