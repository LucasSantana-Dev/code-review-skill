"""CLI entrypoint (Phase-0 spec): review a local diff or a PR in dry-run.

    python3 -m runner (--pr N | --diff PATH) [--provider ...] [--model ...] [--out DIR]
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import load_config
from .diffsource import get_diff
from .pipeline import run
from .stages.post import write_dry_run


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="runner", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--pr", type=int, help="PR number (diff fetched via gh)")
    src.add_argument("--diff", help="path to a local unified-diff/patch file")
    p.add_argument("--repo", help="owner/name (required with --pr)")
    p.add_argument("--provider", help="anthropic (default) | mock")
    p.add_argument("--model", help="model id, e.g. claude-sonnet-4-6")
    p.add_argument("--api-key-env", dest="api_key_env",
                   help="env var holding the API key (default CODE_REVIEW_API_KEY)")
    p.add_argument("--api-endpoint", dest="api_endpoint", help="override API endpoint")
    p.add_argument("--config", help="path to .code-review.yml")
    p.add_argument("--severity-floor", dest="severity_floor", help="P0|P1|P2|P3 (default P1)")
    p.add_argument("--no-skip-trivial", dest="no_skip_trivial", action="store_true",
                   help="review even trivial diffs")
    p.add_argument("--force-large-diff", dest="force_large_diff", action="store_true",
                   help="bypass the token-budget truncation")
    p.add_argument("--out", default="./review", help="output dir (default ./review)")
    p.add_argument("--dry-run", action="store_true",
                   help="(Phase 0 is always dry-run; flag accepted for forward-compat)")
    p.add_argument("--version", action="version", version=f"runner {__version__}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args)
    try:
        src = get_diff(args, config)
        response, ctx, meta = run(
            config, src["diff"], repo=src["repo"], base_sha=src["base_sha"],
            head_sha=src["head_sha"], pr=src["pr"],
        )
    except (RuntimeError, NotImplementedError, FileNotFoundError) as e:
        sys.stderr.write(f"error: {e}\n")
        return 2

    paths = write_dry_run(args.out, response, ctx, config)
    counts = {s: sum(1 for f in response.findings if f.severity == s)
              for s in ("P0", "P1", "P2", "P3")}
    sys.stderr.write(
        f"[dry-run] verdict={response.verdict} "
        f"P0:{counts['P0']} P1:{counts['P1']} P2:{counts['P2']} P3:{counts['P3']}"
        + (" (diff truncated)" if meta.get("truncated") else "")
        + f"\n  -> {paths['findings']}\n  -> {paths['summary']}\n"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
