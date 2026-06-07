"""Config resolution (ADR-0021): defaults < .code-review.yml < CLI/env.

Phase 0 reads only the flat scalar subset (+ an inline `dimensions: [a, b]` list)
with a tiny in-tree reader — PyYAML is deferred until nested path-rules ship.
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from .models import ReviewConfig

_BOOL = {"true": True, "false": False, "yes": True, "no": False, "1": True, "0": False}


def _coerce(value: str):
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        items = [x.strip().strip("'\"") for x in v[1:-1].split(",")]
        return tuple(x for x in items if x)
    if v.lower() in _BOOL:
        return _BOOL[v.lower()]
    if v.lstrip("-").isdigit():
        return int(v)
    return v.strip("'\"")


def read_flat_yaml(path: str) -> dict:
    """Parse the flat `key: value` subset of a .code-review.yml. Best-effort."""
    out = {}
    p = Path(path)
    if not p.exists():
        return out
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line or line[0] in " \t-":
            continue
        key, _, val = line.partition(":")
        key = key.strip().replace("-", "_")
        if val.strip():
            out[key] = _coerce(val)
    return out


def load_config(args) -> ReviewConfig:
    cfg = ReviewConfig()
    known = {f.name for f in fields(ReviewConfig)}

    # Layer 2: .code-review.yml (flat subset)
    cfg_path = getattr(args, "config", None) or ".code-review.yml"
    for k, v in read_flat_yaml(cfg_path).items():
        if k in known:
            setattr(cfg, k, v)

    # Layer 3: CLI args / env (highest precedence) — only when provided
    for name, attr in (("provider", "provider"), ("model", "model"),
                       ("api_key_env", "api_key_env"), ("api_endpoint", "api_endpoint"),
                       ("severity_floor", "severity_floor")):
        val = getattr(args, name, None)
        if val:
            setattr(cfg, attr, val)
    if getattr(args, "force_large_diff", False):
        cfg.force_large_diff = True
    if getattr(args, "no_skip_trivial", False):
        cfg.skip_trivial = False

    cfg.dry_run = True  # Phase 0 forces dry-run (ADR-0019); posting is Phase 2.
    return cfg
