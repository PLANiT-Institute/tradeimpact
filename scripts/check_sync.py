#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Theory <-> code sync check (build brief §5). Fails CI when the two drift.

Verifies, for every row of theory/SYNC.md:
  1. the [anchor] exists as <a id="..."> in a theory doc (or NOTES.md),
  2. the cited code file exists and carries the [anchor] token in a docstring/comment,
  3. the cited test node exists (file + function).
And the reverse: every [anchor] token found in engine code appears in the table, and
every <a id> anchor in the docs appears in the table.

Zero dependencies — run with any python3:  python3 scripts/check_sync.py
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SYNC = REPO / "theory" / "SYNC.md"
DOCS = [
    REPO / "Whitepaper & Guidelines" / "TI_Whitepaper_v1.5.md",
    REPO / "Whitepaper & Guidelines" / "TI_Automotive_Technical_Guideline_v1.8.md",
    REPO / "ti-framework" / "NOTES.md",
]
ENGINE = REPO / "ti-framework" / "ti_framework"
TESTS = REPO / "ti-framework" / "tests"

ANCHOR_RE = re.compile(r'<a id="([a-z0-9.\-]+)"></a>')
TOKEN_RE = re.compile(r"\[((?:eq|rule)-[a-z0-9.\-]+)\]")
ROW_RE = re.compile(
    r"^\|\s*\[((?:eq|rule)-[a-z0-9.\-]+)\][^|]*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|",
    re.M,
)


def main() -> int:
    errors: list[str] = []

    doc_anchors: set[str] = set()
    for doc in DOCS:
        doc_anchors |= set(ANCHOR_RE.findall(doc.read_text()))

    code_tokens: dict[str, set[str]] = {}  # anchor -> files containing its token
    for py in ENGINE.rglob("*.py"):
        for tok in TOKEN_RE.findall(py.read_text()):
            code_tokens.setdefault(tok, set()).add(str(py.relative_to(REPO / "ti-framework")))

    rows = ROW_RE.findall(SYNC.read_text())
    if not rows:
        print("check_sync: no table rows parsed from theory/SYNC.md")
        return 1
    table_anchors = {a for a, _, _ in rows}

    for anchor, code_path, test_node in rows:
        if anchor not in doc_anchors:
            errors.append(f"[{anchor}] not anchored in any theory doc")
        cp = REPO / "ti-framework" / code_path
        if not cp.exists():
            errors.append(f"[{anchor}] cited code file missing: {code_path}")
        elif anchor not in code_tokens or code_path not in code_tokens[anchor]:
            errors.append(f"[{anchor}] token not found in {code_path}")
        tf, _, fn = test_node.partition("::")
        tp = REPO / "ti-framework" / tf
        if not tp.exists():
            errors.append(f"[{anchor}] cited test file missing: {tf}")
        elif fn and not re.search(rf"^def {re.escape(fn)}\b", tp.read_text(), re.M):
            errors.append(f"[{anchor}] test {fn} not found in {tf}")

    for anchor in sorted(doc_anchors - table_anchors):
        errors.append(f"doc anchor [{anchor}] has no SYNC.md row (theory rule with no code+test)")
    for anchor in sorted(set(code_tokens) - table_anchors):
        errors.append(f"code token [{anchor}] in {sorted(code_tokens[anchor])} has no SYNC.md row")

    if errors:
        print(f"check_sync: FAIL ({len(errors)} problems)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"check_sync: OK — {len(rows)} rows, {len(doc_anchors)} anchors, all three-way linked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
