"""Download the GEM wiki page of every plant in scope, one readable text file per page.

Source of truth: Global Energy Monitor's wiki (https://www.gem.wiki), the page each tracker row
links to in ``GEM.Wiki URL``. Pages carry the project narrative the tracker itself does not:
who built the plant (EPC), who supplied the boiler and turbines, who lent or insured, who
operates it, and the ownership history with shares. Licence CC BY 4.0.

Each page is written as its own file under ``roles/raw/gem_wiki/`` so that anyone can open the
exact text a role row was read from:

    roles/raw/gem_wiki/<page_slug>.txt     a header naming the page, its URL, the API call and the
                                           fetch date, then the wikitext exactly as returned
    roles/raw/gem_wiki/index.csv           file, page title, URL, page id, SHA-256, fetch date

``index.csv`` is the hash record for the directory and is itself registered in
``registry/raw_files.csv``; every page file's own SHA-256 sits in the index, so a reader can
verify any single page without a 420-row registry.

Run from the repository root:  .venv/bin/python script/power/roles/fetch_gem_wiki.py [--refresh]
"""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, hand_file_required, read_csv, write_csv  # noqa: E402
from registry import upsert_raw_file, upsert_source  # noqa: E402

PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
RAW_DIR = DATA / "roles" / "raw" / "gem_wiki"
INDEX = RAW_DIR / "index.csv"
API = "https://www.gem.wiki/w/api.php"
SOURCE_ID = "gem_wiki"
USER_AGENT = "tradeimpact/1.0 (research; sanghyun@planit.institute)"
PAUSE_SECONDS = 0.25
#: The line the wikitext starts after; the extractor splits on it.
MARKER = "--- wikitext as returned by the API ---"
INDEX_FIELDS = ["file", "page_title", "url", "pageid", "sha256", "fetched", "note"]


def page_title(url: str) -> str:
    """The wiki page title from its URL."""
    return urllib.parse.unquote(url.rstrip("/").rsplit("/", 1)[-1]).replace("_", " ")


def slug(title: str) -> str:
    """A safe file name for a page title."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_")[:120]


def fetch_wikitext(title: str, context: ssl.SSLContext) -> dict[str, object]:
    """One page's wikitext (or the API error) through the MediaWiki parse action."""
    query = urllib.parse.urlencode(
        {"action": "parse", "page": title, "prop": "wikitext", "format": "json"}
    )
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        payload = json.load(response)
    if "error" in payload:
        return {"error": payload["error"].get("info", "unknown error")}
    parse = payload["parse"]
    return {"title": parse["title"], "pageid": parse["pageid"], "wikitext": parse["wikitext"]["*"]}


def write_page(path: Path, title: str, url: str, page: dict[str, object]) -> str:
    """Write one page file with its provenance header; return its SHA-256."""
    header = "\n".join(
        [
            f"# GEM wiki page: {title}",
            f"# URL: {url}",
            f"# Fetched: {date.today().isoformat()} from {API}?action=parse&prop=wikitext",
            "# Publisher: Global Energy Monitor (gem.wiki). Licence: CC BY 4.0.",
            "# Read by: script/power/roles/extract_wiki_roles.py -> "
            "data/power/roles/processed/gem_wiki_roles.csv",
            "# The text below the marker is the page source exactly as the API returned it.",
            MARKER,
            "",
        ]
    )
    body = str(page.get("wikitext") or f"[no wikitext: {page.get('error', 'unknown error')}]")
    path.write_text(header + body + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Fetch every distinct wiki page of the units in scope; keep pages already on disk."""
    if not PROJECTS.exists():
        hand_file_required(PROJECTS, "run script/power/projects/extract_gem_tracker.py")
    refresh = "--refresh" in sys.argv[1:]
    urls = sorted({r["wiki_url"] for r in read_csv(PROJECTS) if r["wiki_url"]})
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    known = {r["url"]: r for r in read_csv(INDEX)} if INDEX.exists() and not refresh else {}
    context = ssl.create_default_context(cafile=certifi.where())
    index: list[dict[str, object]] = []
    fetched = errors = 0
    for url in urls:
        title = page_title(url)
        name = f"{slug(title)}.txt"
        path = RAW_DIR / name
        if url in known and path.exists() and "no wikitext" not in path.read_text()[:2000]:
            index.append(known[url])
            continue
        try:
            page = fetch_wikitext(title, context)
        except Exception as exc:  # noqa: BLE001 - one bad page must not stop the run
            page = {"error": str(exc)}
        digest = write_page(path, str(page.get("title") or title), url, page)
        fetched += 1
        errors += "error" in page
        index.append(
            {
                "file": name,
                "page_title": page.get("title") or title,
                "url": url,
                "pageid": page.get("pageid", ""),
                "sha256": digest,
                "fetched": date.today().isoformat(),
                "note": page.get("error", ""),
            }
        )
        time.sleep(PAUSE_SECONDS)
    write_csv(INDEX, INDEX_FIELDS, sorted(index, key=lambda r: str(r["file"])))
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Global Energy Monitor",
            "title": "GEM.wiki project pages: ownership history, financing, contractors, equipment "
            "suppliers and operators of the power plants in scope",
            "url": "https://www.gem.wiki",
            "how_obtained": f"wikitext of each page linked from the tracker, through {API} "
            "(action=parse) by script/power/roles/fetch_gem_wiki.py; one text file per page under "
            "data/power/roles/raw/gem_wiki/ with its URL in the header and its hash in index.csv",
            "accessed_date": date.today().isoformat(),
            "license": "CC BY 4.0",
            "used_by": "roles",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "roles",
        INDEX,
        SOURCE_ID,
        "api.php?action=parse (one page per call)",
        f"index of {len(index)} page files in raw/gem_wiki/, each with its URL and SHA-256; "
        f"{sum(1 for r in index if r.get('note'))} pages returned no wikitext",
        data_root=DATA,
    )
    print(
        f"{RAW_DIR.relative_to(REPO)}: {len(index)} page files ({fetched} fetched now, "
        f"{errors} errors); index.csv sha256 {digest[:16]}"
    )


if __name__ == "__main__":
    main()
