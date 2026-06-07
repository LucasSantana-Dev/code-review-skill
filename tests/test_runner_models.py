import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runner.models import (  # noqa: E402
    Finding, finding_from_dict, make_fingerprint, slugify,
)


def _finding(fp, severity="P1", conf=0.9):
    return Finding(path="a.py", line=1, severity=severity, title="t", body="b",
                   dimension="correctness", evidence_type="factual", confidence=conf,
                   source="llm:correctness", fingerprint=fp)


def test_dedup_identity_is_fingerprint_only():
    a = _finding("a.py:1:x", severity="P1", conf=0.9)
    b = _finding("a.py:1:x", severity="P2", conf=0.3)  # same fp, different fields
    c = _finding("a.py:2:y")
    assert a == b           # equal by fingerprint
    assert hash(a) == hash(b)
    assert len({a, b, c}) == 2


def test_to_dict_drops_none():
    f = _finding("a.py:1:x")
    d = f.to_dict()
    assert "suggestion" not in d and "end_line" not in d
    assert d["severity"] == "P1" and d["confidence"] == 0.9


def test_finding_from_dict_coerces_and_derives_fingerprint():
    f = finding_from_dict({"path": "x.ts", "line": "42", "severity": "bogus",
                           "title": "Null deref", "body": "...",
                           "confidence": 5}, default_source="llm:correctness")
    assert f.severity == "P2"            # invalid severity -> default
    assert f.confidence == 1.0           # clamped to [0,1]
    assert f.line == 42                  # coerced from str
    assert f.fingerprint == make_fingerprint("x.ts", 42, "Null deref")


def test_slugify():
    assert slugify("Off-by-one!! error") == "off-by-one-error"
    assert slugify("") == "issue"
