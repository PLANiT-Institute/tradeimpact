"""Download the GEM wiki page of every plant in scope, as wikitext through the MediaWiki API.

Source of truth: Global Energy Monitor's wiki (https://www.gem.wiki), the page each tracker row
links to in ``GEM.Wiki URL``. Pages carry the project narrative the tracker itself does not:
who built the plant (EPC), who supplied the boiler and turbines, who lent or insured, who
operates it, and the ownership history with shares. The wikitext is fetched through the wiki's
own API (``api.php?action=parse&prop=wikitext``), which returns the page source rather than the
rendered HTML, and every page is stored in one JSON file keyed by its URL so a single raw file and
hash record the fetch. Licence CC BY 4.0.

Run from the repository root:  .venv/bin/python script/power/roles/fetch_gem_wiki.py [--refresh]
"""

from __future__ import annotations

import json
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
from power_io import DATA, REPO, hand_file_required, read_csv  # noqa: E402
from registry import upsert_raw_file, upsert_source  # noqa: E402

PROJECTS = DATA / "projects" / "processed" / "projects_gem.csv"
RAW = DATA / "roles" / "raw" / "gem_wiki_pages.json"
API = "https://www.gem.wiki/w/api.php"
SOURCE_ID = "gem_wiki"
USER_AGENT = "tradeimpact/1.0 (research; sanghyun@planit.institute)"
PAUSE_SECONDS = 0.25


def page_title(url: str) -> str:
    """The wiki page title from its URL."""
    return urllib.parse.unquote(url.rstrip("/").rsplit("/", 1)[-1]).replace("_", " ")


def fetch_wikitext(title: str, context: ssl.SSLContext) -> dict[str, object]:
    """One page's wikitext (or the API error) through the MediaWiki parse action."""
    query = urllib.parse.urlencode(
        {"action": "parse", "page": title, "prop": "wikitext", "format": "json"}
    )
    request = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        payload = json.load(response)
    if "error" in payload:
        return {"title": title, "error": payload["error"].get("info", "unknown error")}
    parse = payload["parse"]
    return {"title": parse["title"], "pageid": parse["pageid"], "wikitext": parse["wikitext"]["*"]}


def main() -> None:
    """Fetch every distinct wiki page of the units in scope; keep pages already on disk."""
    if not PROJECTS.exists():
        hand_file_required(PROJECTS, "run script/power/projects/extract_gem_tracker.py")
    refresh = "--refresh" in sys.argv[1:]
    urls = sorted({r["wiki_url"] for r in read_csv(PROJECTS) if r["wiki_url"]})
    pages: dict[str, dict[str, object]] = {}
    if RAW.exists() and not refresh:
        pages = json.loads(RAW.read_text(encoding="utf-8")).get("pages", {})
    context = ssl.create_default_context(cafile=certifi.where())
    fetched = errors = 0
    for url in urls:
        if url in pages and "wikitext" in pages[url]:
            continue
        try:
            page = fetch_wikitext(page_title(url), context)
        except Exception as exc:  # noqa: BLE001 - one bad page must not stop the run
            page = {"title": page_title(url), "error": str(exc)}
        page["url"] = url
        page["fetched"] = date.today().isoformat()
        pages[url] = page
        fetched += 1
        errors += "error" in page
        time.sleep(PAUSE_SECONDS)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(
        json.dumps(
            {"api": API, "fetched": date.today().isoformat(), "pages": pages}, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Global Energy Monitor",
            "title": "GEM.wiki project pages (wikitext): ownership history, financing, contractors,"
            "equipment suppliers and operators of the power plants in scope",
            "url": "https://www.gem.wiki",
            "how_obtained": f"wikitext of each page linked from the tracker, through {API} "
            "(action=parse) by script/power/roles/fetch_gem_wiki.py",
            "accessed_date": date.today().isoformat(),
            "license": "CC BY 4.0",
            "used_by": "roles",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "roles",
        RAW,
        SOURCE_ID,
        "api.php?action=parse (one JSON per page, bundled)",
        f"{len(pages)} pages, {sum(1 for p in pages.values() if 'error' in p)} without wikitext",
        data_root=DATA,
    )
    print(
        f"{RAW.relative_to(REPO)}: {len(pages)} pages ({fetched} fetched now, {errors} errors), "
        f"{RAW.stat().st_size / 1e6:.1f} MB, sha256 {digest[:16]}"
    )


if __name__ == "__main__":
    main()
