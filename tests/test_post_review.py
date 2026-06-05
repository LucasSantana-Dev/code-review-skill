"""Unit tests for post_review.py — the deterministic plumbing under the skill.

Run: python3 -m pytest tests/ -q   (or: python3 tests/test_post_review.py)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import post_review as pr  # noqa: E402


def test_fmt_comment_body_basic():
    out = pr.fmt_comment_body({"severity": "P1", "title": "bug", "body": "why"})
    assert "bug" in out and "why" in out


def test_fmt_comment_body_suggestion_block():
    out = pr.fmt_comment_body(
        {"severity": "P2", "title": "t", "body": "b", "suggestion": "  fixed()"}
    )
    assert "```suggestion" in out and "fixed()" in out


def test_diff_lines_uses_filename_not_path(monkeypatch):
    # Regression guard: the GitHub /files API returns `filename`, not `path`.
    fake = [{"filename": "src/a.ts", "patch": "@@ -1,2 +1,3 @@\n ctx\n+a\n+b"}]
    monkeypatch.setattr(pr, "sh", lambda *a, **k: json.dumps(fake))
    valid = pr.diff_lines("o", "n", 1)
    assert valid["src/a.ts"] == {2, 3}  # the two added lines, at new-file positions


def test_diff_lines_binary_file_has_no_lines(monkeypatch):
    monkeypatch.setattr(pr, "sh", lambda *a, **k: json.dumps([{"filename": "x.png"}]))
    assert pr.diff_lines("o", "n", 1)["x.png"] == set()


if __name__ == "__main__":
    # Tiny runner so the file works without pytest installed.
    import types

    class _MP:
        def setattr(self, obj, name, val):
            setattr(obj, name, val)

    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and isinstance(fn, types.FunctionType):
            try:
                fn(_MP()) if fn.__code__.co_argcount else fn()
                print(f"ok   {name}")
            except Exception as e:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
