# Changelog

All notable changes to the code-review skill. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); this skill is not semver-versioned yet.

## [Unreleased]

### Added
- Size-gated reviewer **fan-out** (`--fan-out`): parallel per-dimension reviewers above a
  ~600-LOC / 15-file / 8k-token threshold; single strong reviewer by default.
- Human-gated, self-verifying **fixer mode** (`--fix`): one worktree-isolated fixer per
  finding; mechanical+factual+high-confidence auto-apply, logic propose-only, never `main`.
- `confidence` (0–1) and `evidence` (factual/behavioral/speculative) on findings, with a
  severity × confidence **gating matrix** (inline / summary / drop).
- Consensus-boost **dedup** keyed `(path, line, category)`.
- `post_review.py --body-file` so the review body carries verdict + summary + what's-good.
- Unit tests for `post_review.py` (`tests/`).

### Fixed
- `post_review.py diff_lines` read `f["path"]` but the GitHub *list-PR-files* API returns
  `filename` — every real post would `KeyError`. Now uses `filename`.

### Notes
- Documented that self-authored PRs must post with `--event COMMENT` (GitHub 422s
  `REQUEST_CHANGES`/`APPROVE` on your own PR).
- ADR 0001 records the scoped architecture decision and the deferred always-on/auto-fix
  build behind explicit evidence triggers.
