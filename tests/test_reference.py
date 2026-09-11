"""The reference register has to stay well formed, and the landscape note has to stay in step.

No network here: whether a link still resolves is `script/reference/check_references.py`, which
is run on demand. These tests are the structural ones — a duplicate key, a reference nobody
cites, a citation to a document that does not exist, a family the landscape note never defines.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
REFERENCE = REPO / "reference"
REGISTER = REFERENCE / "references.csv"
LANDSCAPE = REFERENCE / "landscape.md"
METHODOLOGY = REPO / "methodology"
REQUIRED = (
    "key",
    "family",
    "title",
    "publisher",
    "year",
    "url",
    "doi",
    "access",
    "what_it_states",
    "relation_to_ti",
    "cited_in",
)
ACCESS = {"free", "registration", "paywalled"}


def register() -> list[dict[str, str]]:
    with REGISTER.open(newline="") as f:
        return list(csv.DictReader(f))


def test_every_row_carries_the_columns_the_register_promises() -> None:
    rows = register()
    assert rows, "the register is empty"
    assert set(REQUIRED) <= set(rows[0]), "a promised column is missing from the header"
    for r in rows:
        where = r.get("key") or "<no key>"
        assert re.fullmatch(r"[a-z0-9_]+", r["key"]), f"{where}: key must be a lowercase slug"
        assert r["title"] and r["publisher"] and r["year"], f"{where}: title, publisher, year"
        assert r["url"] or r["doi"], f"{where}: needs a url or a doi"
        assert r["access"] in ACCESS, f"{where}: access must be one of {sorted(ACCESS)}"


def test_no_reference_is_entered_twice() -> None:
    rows = register()
    keys = [r["key"] for r in rows]
    assert len(keys) == len(set(keys)), "duplicate key"
    urls = [r["doi"] or r["url"] for r in rows]
    assert len(urls) == len(set(urls)), "the same document is registered twice"


def test_every_reference_says_what_it_states_and_how_it_relates() -> None:
    """The two judgement columns are the point of the register; a stub is worse than nothing."""
    for r in register():
        assert len(r["what_it_states"]) > 80, f"{r['key']}: what_it_states is a stub"
        assert len(r["relation_to_ti"]) > 60, f"{r['key']}: relation_to_ti is a stub"
        assert "related work" not in r["relation_to_ti"].lower(), f"{r['key']}: say the relation"


def test_a_citation_names_a_methodology_document_that_exists() -> None:
    documents = {p.stem for p in METHODOLOGY.glob("*.md")}
    for r in register():
        for citation in (c.strip() for c in r["cited_in"].split(";") if c.strip()):
            stem = citation.split(" ")[0]
            assert stem in documents, f"{r['key']}: cited_in names {stem!r}, which is not on file"


@pytest.mark.skipif(not LANDSCAPE.exists(), reason="landscape note not written yet")
def test_the_landscape_note_only_cites_keys_that_are_in_the_register() -> None:
    """A slug in the note is a registered reference or a family name, never a dangling one."""
    rows = register()
    known = {r["key"] for r in rows} | {r["family"] for r in rows}
    cited = set(re.findall(r"`([a-z0-9_]{4,})`", LANDSCAPE.read_text()))
    unknown = {k for k in cited if k not in known and "_" in k}
    assert not unknown, f"the landscape note cites keys that are not registered: {sorted(unknown)}"


@pytest.mark.skipif(not LANDSCAPE.exists(), reason="landscape note not written yet")
def test_every_family_in_the_register_is_defined_in_the_landscape_note() -> None:
    text = LANDSCAPE.read_text()
    for family in sorted({r["family"] for r in register()}):
        assert f"`{family}`" in text, f"family {family!r} is used but never defined"


# ---------------------------------------------------------------- the library on disk


RAW = REFERENCE / "raw"
RAW_INDEX = RAW / "index.csv"


def raw_index() -> list[dict[str, str]]:
    with RAW_INDEX.open(newline="") as f:
        return list(csv.DictReader(f))


@pytest.mark.skipif(not RAW_INDEX.exists(), reason="the documents have not been fetched")
def test_every_reference_is_either_on_disk_or_explains_why_not() -> None:
    """No silent gaps: a reference has its document, or a reason a reader can act on."""
    index = {r["key"]: r for r in raw_index()}
    for row in register():
        entry = index.get(row["key"])
        assert entry is not None, f"{row['key']}: not in reference/raw/index.csv"
        if entry["file"]:
            assert (RAW / entry["file"]).exists(), f"{row['key']}: {entry['file']} is missing"
            assert len(entry["sha256"]) == 64, f"{row['key']}: no hash for the file on disk"
        else:
            assert entry["note"].startswith("not_saved: "), f"{row['key']}: unexplained gap"
            assert len(entry["note"]) > 40, f"{row['key']}: the reason is too thin to act on"


@pytest.mark.skipif(not RAW_INDEX.exists(), reason="the documents have not been fetched")
def test_no_document_sits_in_the_library_without_a_reference() -> None:
    """A file nobody cites is a file nobody can check."""
    keys = {r["key"] for r in register()}
    on_disk = {p.stem for p in RAW.iterdir() if p.is_file() and p.name != "index.csv"}
    assert on_disk <= keys, f"documents with no register row: {sorted(on_disk - keys)}"
