"""Download every page the company-disclosure role register cites, one file per source.

Input   roles/method/company_ir_sources.csv    source_key, company_id, url, kind, what it states
Output  roles/raw/company_ir/<source_key>.<ext>   the page exactly as served, under a header for
                                                  text formats (HTML and PDF are stored as served)
        roles/raw/company_ir/index.csv            source_key, company_id, url, content type,
                                                  bytes, SHA-256, fetch date, what it states

The register in ``roles/raw/company_ir_roles.csv`` cites a ``source_key`` per fact, and the
extractor refuses a row whose key is not in this index or whose URL does not match it — so every
role and every share can be traced to a page that is on disk and hash-recorded. ``index.csv`` is
the hash record for the directory and is itself registered in ``registry/raw_files.csv``.

Run from the repository root:  .venv/bin/python script/power/roles/fetch_company_ir.py [--refresh]
"""

from __future__ import annotations

import hashlib
import ssl
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, read_csv, write_csv  # noqa: E402
from registry import upsert_raw_file, upsert_source  # noqa: E402

SOURCES = DATA / "roles" / "method" / "company_ir_sources.csv"
RAW_DIR = DATA / "roles" / "raw" / "company_ir"
INDEX = RAW_DIR / "index.csv"
SOURCE_ID = "company_ir_pages"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 tradeimpact/1.0 (research; sanghyun@planit.institute)"
)
PAUSE_SECONDS = 1.0
EXTENSIONS = {"html": ".html", "pdf": ".pdf", "json": ".json", "csv": ".csv"}
INDEX_FIELDS = [
    "source_key",
    "company_id",
    "file",
    "url",
    "content_type",
    "bytes",
    "sha256",
    "fetched",
    "what_it_states",
]


def fetch(url: str, context: ssl.SSLContext) -> tuple[bytes, str]:
    """The page bytes and its content type."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context, timeout=120) as response:
        return response.read(), response.headers.get("Content-Type", "")


def main() -> None:
    """Fetch every source page not already on disk; write the index and register it."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    refresh = "--refresh" in sys.argv[1:]
    known = {r["source_key"]: r for r in read_csv(INDEX)} if INDEX.exists() and not refresh else {}
    context = ssl.create_default_context(cafile=certifi.where())
    index: list[dict[str, object]] = []
    fetched = failed = 0
    for source in read_csv(SOURCES):
        key = source["source_key"]
        name = key + EXTENSIONS.get(source["kind"], ".html")
        path = RAW_DIR / name
        if key in known and path.exists():
            index.append({**known[key], "what_it_states": source["what_it_states"]})
            continue
        try:
            body, content_type = fetch(source["url"], context)
        except Exception as exc:  # noqa: BLE001 - one unreachable page must not stop the run
            print(f"  FAILED {key}: {exc}")
            failed += 1
            continue
        path.write_bytes(body)
        fetched += 1
        index.append(
            {
                "source_key": key,
                "company_id": source["company_id"],
                "file": name,
                "url": source["url"],
                "content_type": content_type,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "fetched": date.today().isoformat(),
                "what_it_states": source["what_it_states"],
            }
        )
        time.sleep(PAUSE_SECONDS)
    write_csv(INDEX, INDEX_FIELDS, sorted(index, key=lambda r: str(r["source_key"])))
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "the companies themselves and the trade press named per page",
            "title": "Company disclosure pages cited by the power role register: overseas business "
            "overviews, project pages and contract announcements",
            "url": "https://www.kepco.co.kr/eng/business/overseas/business-overview.do",
            "how_obtained": "each page downloaded from the URL listed in "
            "roles/method/company_ir_sources.csv by script/power/roles/fetch_company_ir.py and "
            "stored under data/power/roles/raw/company_ir/ with its URL, bytes and SHA-256 in "
            "index.csv; the register cites the source_key of the page that states each fact",
            "accessed_date": date.today().isoformat(),
            "license": "company and publisher copyright; quoted for research with attribution",
            "used_by": "roles",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "roles",
        INDEX,
        SOURCE_ID,
        "company disclosure pages (one file per source_key)",
        f"index of {len(index)} pages in raw/company_ir/, each with its URL and SHA-256",
        data_root=DATA,
    )
    print(
        f"{RAW_DIR.relative_to(REPO)}: {len(index)} pages on disk ({fetched} fetched now, "
        f"{failed} failed); index.csv sha256 {digest[:16]}"
    )


if __name__ == "__main__":
    main()
