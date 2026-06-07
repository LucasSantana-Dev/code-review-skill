import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runner.models import ReviewConfig  # noqa: E402
from runner.pipeline import run  # noqa: E402
from runner.stages.post import write_dry_run  # noqa: E402

FIXTURE_DIFF = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,5 @@
 def login(u, p):
+    token = "SECRET-abc"
+    # placeholder
+    return token  # BUG here
 # done
"""


def test_pipeline_dry_run_with_mock_adapter(tmp_path):
    cfg = ReviewConfig(provider="mock")
    response, ctx, meta = run(cfg, FIXTURE_DIFF, repo="o/r", head_sha="deadbeef")

    severities = {f.severity for f in response.findings}
    assert "P0" in severities and "P1" in severities      # SECRET -> P0, BUG -> P1
    assert response.verdict == "changes-required"

    paths = write_dry_run(tmp_path, response, ctx, cfg)
    findings_obj = json.loads(Path(paths["findings"]).read_text())
    assert findings_obj["verdict"] == "changes-required"
    assert findings_obj["schema_version"] == "1.0"
    assert len(findings_obj["findings"]) >= 2
    assert Path(paths["summary"]).exists()
    assert "## Verdict" in Path(paths["summary"]).read_text()


def test_pipeline_skips_trivial_diff():
    cfg = ReviewConfig(provider="mock", skip_trivial=True)
    trivial_diff = "--- a/x.txt\n+++ b/x.txt\n@@ -1,1 +1,2 @@\n a\n+\n"
    response, ctx, meta = run(cfg, trivial_diff)
    assert response.verdict == "approve"
    assert response.findings == []
