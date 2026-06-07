import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runner.models import ReviewConfig  # noqa: E402
from runner.stages.scope import (  # noqa: E402
    build_diff_context, is_trivial, parse_unified_diff, scope,
)

CODE_DIFF = """diff --git a/foo.py b/foo.py
index 111..222 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,4 @@
 def f(x):
-    return x
+    # BUG: off by one
+    return x + 1
 # end
"""

TRIVIAL_DIFF = """--- a/x.txt
+++ b/x.txt
@@ -1,2 +1,3 @@
 a
+
 b
"""


def test_parse_unified_diff_line_numbers_and_files():
    hunks, files = parse_unified_diff(CODE_DIFF)
    assert files == ["foo.py"]
    assert len(hunks) == 1
    h = hunks[0]
    assert h.path == "foo.py"
    assert h.start_line == 1 and h.end_line == 4
    assert "+    return x + 1" in h.content


def test_is_trivial():
    assert is_trivial(TRIVIAL_DIFF, 50) is True       # whitespace-only, small
    assert is_trivial(CODE_DIFF, 50) is False         # real code change


def test_scope_returns_hunks_and_context_header():
    cfg = ReviewConfig()
    hunks, files, trivial, meta = scope(CODE_DIFF, cfg)
    assert trivial is False and len(hunks) == 1
    ctx = build_diff_context(hunks)
    assert "--- foo.py (lines 1-4) ---" in ctx


def test_scope_skips_trivial_when_enabled():
    cfg = ReviewConfig(skip_trivial=True)
    _, _, trivial, _ = scope(TRIVIAL_DIFF, cfg)
    assert trivial is True
