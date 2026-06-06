"""Drift-guard for the references library catalog (ADR-0006).

Asserts that references/README.md's index table lists *exactly* the entry files
that exist, with matching Defect class + Tier. This keeps the cheap catalog the
review agent reads from silently going stale as entries are added/edited — the
test suite is the gate (this repo has no CI by choice).

Run: python3 -m pytest tests/ -q   (or: python3 tests/test_references_index.py)
"""
import re
from pathlib import Path

REFS_DIR = Path(__file__).resolve().parent.parent / "references"
README = REFS_DIR / "README.md"

_CLASS_RE = re.compile(r"^- \*\*Defect class:\*\*\s*(.+?)\s*$", re.MULTILINE)
_TIER_RE = re.compile(r"^- \*\*Tier:\*\*\s*(.+?)\s*$", re.MULTILINE)
# Index row: | [slug](slug.md) | class | tier |
_ROW_RE = re.compile(
    r"^\|\s*\[[^\]]+\]\(([^)]+)\.md\)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$",
    re.MULTILINE,
)


def _entry_files():
    return sorted(p for p in REFS_DIR.glob("*.md") if p.name != "README.md")


def _first_value(regex, text, path):
    m = regex.search(text)
    assert m, f"{path.name}: missing required frontmatter line {regex.pattern!r}"
    # take only the leading token before any parenthetical/aside, normalized
    return m.group(1).split("(")[0].strip()


def _entries_from_files():
    """slug -> (defect_class, tier) parsed from each entry's frontmatter."""
    out = {}
    for p in _entry_files():
        text = p.read_text(encoding="utf-8")
        out[p.stem] = (
            _first_value(_CLASS_RE, text, p),
            _first_value(_TIER_RE, text, p),
        )
    return out


def _entries_from_index():
    """slug -> (class, tier) parsed from the README index table."""
    text = README.read_text(encoding="utf-8")
    return {
        slug.strip(): (cls.split("(")[0].strip(), tier.strip())
        for slug, cls, tier in _ROW_RE.findall(text)
    }


def test_index_lists_exactly_the_entry_files():
    files = set(_entries_from_files())
    indexed = set(_entries_from_index())
    missing = files - indexed
    stale = indexed - files
    assert not missing, f"references/README.md index missing rows for: {sorted(missing)}"
    assert not stale, f"references/README.md index has stale rows (no such file): {sorted(stale)}"


def test_index_class_and_tier_match_frontmatter():
    files = _entries_from_files()
    index = _entries_from_index()
    mismatches = {
        slug: {"file": files[slug], "index": index[slug]}
        for slug in files
        if slug in index and files[slug] != index[slug]
    }
    assert not mismatches, f"index class/tier disagree with entry frontmatter: {mismatches}"


def test_every_entry_has_class_and_tier():
    # _entries_from_files asserts presence; this makes the contract explicit and
    # fails loudly if an entry omits required frontmatter.
    entries = _entries_from_files()
    assert entries, "no reference entries found"
    for slug, (cls, tier) in entries.items():
        assert cls, f"{slug}: empty Defect class"
        assert tier, f"{slug}: empty Tier"


if __name__ == "__main__":
    test_index_lists_exactly_the_entry_files()
    test_index_class_and_tier_match_frontmatter()
    test_every_entry_has_class_and_tier()
    print("ok: references index in sync with entry files")
