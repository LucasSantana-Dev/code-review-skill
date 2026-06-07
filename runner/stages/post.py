"""Stage 5 — post (ADR-0020).

Phase 0: DRY-RUN ONLY — write findings.json (rich schema) + summary.md, post
nothing. The live path (shelling out to scripts/post_review.py as the bot
identity) is Phase 2 and is stubbed below so the seam is explicit.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..models import SCHEMA_VERSION, SEV_RANK
from .merge import placement

_SEV_LABEL = {"P0": "P0 — Blocker", "P1": "P1 — Incorrect / missing coverage",
              "P2": "P2 — Quality", "P3": "P3 — Polish"}


def to_findings_object(response, ctx) -> dict:
    """The rich Phase-0 findings.json object (ADR-0013 / Phase-0 spec)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "verdict": response.verdict,
        "summary": response.summary,
        "repo": ctx.repo,
        "pr": ctx.pr,
        "head_sha": ctx.head_sha,
        "findings": [f.to_dict() for f in response.findings],
    }


def to_post_review_list(findings) -> list:
    """Project Findings onto the list shape scripts/post_review.py consumes (P2)."""
    out = []
    for f in findings:
        d = {"path": f.path, "line": f.line, "severity": f.severity,
             "title": f.title, "body": f.body}
        if f.suggestion:
            d["suggestion"] = f.suggestion
        if f.end_line and f.end_line > f.line:
            d["start_line"] = f.line
            d["line"] = f.end_line
        out.append(d)
    return out


def render_summary_md(response, ctx, config) -> str:
    findings = response.findings
    counts = {s: sum(1 for f in findings if f.severity == s) for s in ("P0", "P1", "P2", "P3")}
    lines = [f"## Verdict\n{response.verdict} — {response.summary or 'see findings below'}\n"]
    inline = [f for f in findings if placement(f, config) == "inline"]
    summary_only = [f for f in findings if placement(f, config) == "summary"]
    for sev in ("P0", "P1", "P2", "P3"):
        group = [f for f in inline if f.severity == sev]
        if group:
            lines.append(f"## {_SEV_LABEL[sev]}")
            for f in group:
                loc = f"`{f.path}:{f.line}`"
                lines.append(f"- {loc} — **{f.title}** · {f.body}"
                             + (f"\n  ```suggestion\n  {f.suggestion}\n  ```" if f.suggestion else ""))
            lines.append("")
    if summary_only:
        lines.append("## Summary-only (below inline floor)")
        for f in sorted(summary_only, key=lambda x: SEV_RANK[x.severity]):
            lines.append(f"- **{f.severity}** `{f.path}:{f.line}` — {f.title} _(confidence {f.confidence:.2f})_")
        lines.append("")
    lines.append("## Dimensions checked")
    lines.append(" · ".join(config.dimensions) + f"  ·  P0:{counts['P0']} P1:{counts['P1']} P2:{counts['P2']} P3:{counts['P3']}")
    return "\n".join(lines) + "\n"


def write_dry_run(out_dir, response, ctx, config) -> dict:
    """Write findings.json + summary.md to out_dir; return their paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    findings_path = out / "findings.json"
    summary_path = out / "summary.md"
    findings_path.write_text(json.dumps(to_findings_object(response, ctx), indent=2) + "\n",
                             encoding="utf-8")
    summary_path.write_text(render_summary_md(response, ctx, config), encoding="utf-8")
    return {"findings": str(findings_path), "summary": str(summary_path)}


def post_live(response, ctx, config):  # pragma: no cover - Phase 2
    """Live posting via scripts/post_review.py under the bot identity (ADR-0020)."""
    raise NotImplementedError(
        "live posting is Phase 2 (ADR-0019/0020); it depends on the GitHub App "
        "bot identity (ADR-0004). Phase 0 is dry-run only — use write_dry_run()."
    )
