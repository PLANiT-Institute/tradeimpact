"""Download the documents the technology defaults are transcribed from, one file per source.

Input   projects/method/technology_documents.csv   source_key, url, kind, what it states
Output  projects/raw/technology_documents/<source_key>.<ext>   the document as served
        projects/raw/technology_documents/index.csv            URL, bytes, SHA-256, fetch date

``technology_defaults.csv`` holds a lifetime, capacity factor and efficiency per fuel and
technology. Those are hand-transcribed numbers, so the documents they come from have to be on
disk for a reader to check them: ``verify_technology_defaults.py`` reads the heat rates straight
out of the EIA report's text and compares them with the transcription.

The IEA-ETSAP technology briefs cited in the first version of the defaults are no longer served
(iea-etsap.org redirects the E-TechDS PDF paths to its home page), so the thermal-efficiency
citation moved to the EIA report, which is live and machine-readable.

Run from the repository root:
    .venv/bin/python script/power/projects/fetch_technology_documents.py [--refresh]
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

SOURCES = DATA / "projects" / "method" / "technology_documents.csv"
RAW_DIR = DATA / "projects" / "raw" / "technology_documents"
INDEX = RAW_DIR / "index.csv"
SOURCE_ID = "technology_parameter_documents"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 tradeimpact/1.0 (research; sanghyun@planit.institute)"
)
EXTENSIONS = {"pdf": ".pdf", "html": ".html", "csv": ".csv", "json": ".json"}
PAUSE_SECONDS = 1.0
INDEX_FIELDS = [
    "source_key",
    "file",
    "url",
    "publisher",
    "content_type",
    "bytes",
    "sha256",
    "fetched",
    "what_it_states",
]


def fetch(url: str, context: ssl.SSLContext) -> tuple[bytes, str]:
    """The document bytes and its content type."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context, timeout=180) as response:
        return response.read(), response.headers.get("Content-Type", "")


def main() -> None:
    """Fetch every document not already on disk; write the index and register it."""
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
        except Exception as exc:  # noqa: BLE001 - one unreachable document must not stop the run
            print(f"  FAILED {key}: {exc}")
            failed += 1
            continue
        path.write_bytes(body)
        fetched += 1
        index.append(
            {
                "source_key": key,
                "file": name,
                "url": source["url"],
                "publisher": source["publisher"],
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
            "publisher": "US Energy Information Administration; Global Energy Monitor; IRENA",
            "title": "Documents behind the technology defaults: plant heat rates, plant "
            "lifetimes and capacity factors by technology",
            "url": "https://www.eia.gov/analysis/studies/powerplants/capitalcost/",
            "how_obtained": "each document downloaded from the URL listed in "
            "projects/method/technology_documents.csv by "
            "script/power/projects/fetch_technology_documents.py and stored under "
            "data/power/projects/raw/technology_documents/ with its URL, bytes and SHA-256 in "
            "index.csv; the heat rates are read back out of the text by "
            "script/power/projects/verify_technology_defaults.py",
            "accessed_date": date.today().isoformat(),
            "license": "US government work (EIA, public domain); GEM wiki CC BY-SA 4.0; "
            "IRENA copyright, quoted with attribution",
            "used_by": "projects",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "projects",
        INDEX,
        SOURCE_ID,
        "technology parameter documents (one file per source_key)",
        f"index of {len(index)} documents in raw/technology_documents/, each with URL and SHA-256",
        data_root=DATA,
    )
    print(
        f"{RAW_DIR.relative_to(REPO)}: {len(index)} documents on disk ({fetched} fetched now, "
        f"{failed} failed); index.csv sha256 {digest[:16]}"
    )


if __name__ == "__main__":
    main()
