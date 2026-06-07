"""Stage 2 — scope (ADR-0016).

Parse a unified diff into hunks on the NEW side, detect trivial diffs, and apply
a token budget guard (truncate at hunk boundaries). Deterministic, 0 tokens.
"""
from __future__ import annotations

import re

from ..models import DiffHunk

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_COMMENT_PREFIXES = ("#", "//", "/*", "*", "<!--", '"""', "'''", "--")


def parse_unified_diff(diff_text: str):
    """Return (hunks, changed_files). Line numbers are NEW-side."""
    hunks, changed_files = [], []
    path = None
    new_line = 0
    cur = None

    def finish(c):
        return DiffHunk(path=c["path"], start_line=c["start"],
                        end_line=c["last"], content="\n".join(c["lines"]))

    for raw in diff_text.splitlines():
        if raw.startswith("+++ "):
            p = raw[4:].strip().split("\t")[0]
            if p.startswith("b/"):
                p = p[2:]
            path = None if p == "/dev/null" else p
            if path and path not in changed_files:
                changed_files.append(path)
            cur = None
            continue
        if (raw.startswith("--- ") or raw.startswith("diff --git")
                or raw.startswith("index ") or raw.startswith("similarity ")
                or raw.startswith("rename ") or raw.startswith("new file")
                or raw.startswith("deleted file")):
            cur = None
            continue
        m = _HUNK_RE.match(raw)
        if m:
            if cur:
                hunks.append(finish(cur))
            if path is None:        # deletion / /dev/null target — nothing to review
                cur = None
                continue
            new_line = int(m.group(1))
            cur = {"path": path, "start": new_line, "last": new_line, "lines": [raw]}
            continue
        if cur is None:
            continue
        cur["lines"].append(raw)
        if raw.startswith("+"):
            cur["last"] = new_line
            new_line += 1
        elif raw.startswith("-") or raw.startswith("\\"):
            pass                    # removed line / "no newline" marker — new side unchanged
        else:
            cur["last"] = new_line
            new_line += 1
    if cur:
        hunks.append(finish(cur))
    return hunks, changed_files


def _is_comment_or_blank(line_body: str) -> bool:
    s = line_body.strip()
    return s == "" or any(s.startswith(p) for p in _COMMENT_PREFIXES)


def is_trivial(diff_text: str, loc_threshold: int) -> bool:
    """Trivial = below the LOC threshold AND every changed line is blank/comment."""
    changed = 0
    has_code = False
    for raw in diff_text.splitlines():
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+") or raw.startswith("-"):
            changed += 1
            if not _is_comment_or_blank(raw[1:]):
                has_code = True
    return changed < loc_threshold and not has_code


def scope(diff_text: str, config):
    """Return (hunks, changed_files, trivial, meta)."""
    trivial = config.skip_trivial and is_trivial(diff_text, config.trivial_loc)
    hunks, changed_files = parse_unified_diff(diff_text)
    meta = {"truncated": False, "dropped_hunks": 0}

    # Budget guard — truncate at hunk boundaries (ADR-0016), never mid-hunk.
    if not config.force_large_diff and hunks:
        budget_chars = config.max_tokens_budget * 4
        kept, used = [], 0
        for h in hunks:
            if used + len(h.content) > budget_chars and kept:
                meta["truncated"] = True
                break
            kept.append(h)
            used += len(h.content)
        meta["dropped_hunks"] = len(hunks) - len(kept)
        hunks = kept
    return hunks, changed_files, trivial, meta


def build_diff_context(hunks) -> str:
    """Render hunks for the LLM with per-hunk path/line headers."""
    parts = []
    for h in hunks:
        parts.append(f"--- {h.path} (lines {h.start_line}-{h.end_line}) ---\n{h.content}")
    return "\n\n".join(parts)
