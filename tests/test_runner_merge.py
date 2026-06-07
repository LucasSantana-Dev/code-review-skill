import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runner.models import Finding, ReviewConfig  # noqa: E402
from runner.stages.merge import merge_and_gate, placement  # noqa: E402


def f(fp, severity, conf=0.9, source="llm:correctness", line=1):
    return Finding(path="a.py", line=line, severity=severity, title="t", body="b",
                   dimension="correctness", evidence_type="behavioral", confidence=conf,
                   source=source, fingerprint=fp)


def test_dedup_keeps_higher_severity():
    kept, verdict = merge_and_gate(
        [f("a.py:1:x", "P2", source="prefilter:eslint")],
        [f("a.py:1:x", "P1", source="llm:correctness")],
        ReviewConfig(),
    )
    assert len(kept) == 1
    assert kept[0].severity == "P1"
    assert kept[0].evidence_type == "factual"   # two independent sources agree
    assert verdict == "changes-required"


def test_gate_drops_low_confidence_low_severity():
    cfg = ReviewConfig(severity_floor="P1")
    kept, verdict = merge_and_gate([], [
        f("a.py:1:a", "P2", conf=0.4, line=1),   # below P2 floor 0.5 -> drop
        f("a.py:2:b", "P3", conf=0.6, line=2),   # below P3 floor 0.7 -> drop
        f("a.py:3:c", "P2", conf=0.6, line=3),   # kept -> summary (below inline floor P1)
    ], cfg)
    fps = {k.fingerprint for k in kept}
    assert fps == {"a.py:3:c"}
    assert placement(kept[0], cfg) == "summary"
    assert verdict == "approve-with-nits"


def test_placement_inline_for_blocker():
    cfg = ReviewConfig(severity_floor="P1")
    assert placement(f("a.py:1:x", "P0"), cfg) == "inline"
    assert placement(f("a.py:1:x", "P1"), cfg) == "inline"


def test_clean_diff_approves():
    kept, verdict = merge_and_gate([], [], ReviewConfig())
    assert kept == [] and verdict == "approve"
