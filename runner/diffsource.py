"""Acquire the unified diff to review — from a local patch or a PR via gh.

`git diff` / `gh pr diff` are shelled out (ADR-0011: shell out, don't reimplement).
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def from_patch(path: str, config) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    return {"diff": text, "repo": None, "base_sha": None, "head_sha": None, "pr": None}


def from_pr(pr: int, repo: str | None, config) -> dict:
    """Fetch a PR's diff with N-line context + its base/head SHAs via gh."""
    repo_args = ["--repo", repo] if repo else []
    diff = _sh(["gh", "pr", "diff", str(pr), *repo_args])
    head_sha = base_sha = None
    try:
        import json
        meta = json.loads(_sh(["gh", "pr", "view", str(pr), *repo_args,
                               "--json", "headRefOid,baseRefOid"]))
        head_sha, base_sha = meta.get("headRefOid"), meta.get("baseRefOid")
    except Exception:  # pragma: no cover - gh/network dependent
        pass
    return {"diff": diff, "repo": repo, "base_sha": base_sha, "head_sha": head_sha, "pr": pr}


def get_diff(args, config) -> dict:
    if getattr(args, "diff", None):
        return from_patch(args.diff, config)
    if getattr(args, "pr", None) is not None:
        return from_pr(args.pr, getattr(args, "repo", None), config)
    raise SystemExit("provide --diff <path> or --pr <N>")
