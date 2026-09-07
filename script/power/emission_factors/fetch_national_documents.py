"""Download the national inventory documents the country-specific emission factors are read from.

Input   emission_factors/method/national_documents.csv   source_key, country, url, publisher,
                                                         licence, what it states
Output  emission_factors/raw/national_documents/<source_key>.pdf   the document as served
        emission_factors/raw/national_documents/index.csv          URL, bytes, SHA-256, licence

``raw/national_emission_factors.csv`` cites a ``source_key`` per factor, and the extractor refuses
a row whose key is not in this index, whose URL does not match, or whose quote is not in the
document's own text. So no emission factor can enter the model without the inventory page a
reader can open, and no factor can be attributed to a country that did not publish it.

Some of these ministries serve an incomplete certificate chain or refuse Python's handshake; the
fetcher falls back to the system ``curl``, which still verifies the certificate, and records which
transport was used.

Run from the repository root:
    .venv/bin/python script/power/emission_factors/fetch_national_documents.py [--refresh]
"""

from __future__ import annotations

import hashlib
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, read_csv, write_csv  # noqa: E402
from registry import upsert_raw_file, upsert_source  # noqa: E402

SOURCES = DATA / "emission_factors" / "method" / "national_documents.csv"
RAW_DIR = DATA / "emission_factors" / "raw" / "national_documents"
INDEX = RAW_DIR / "index.csv"
SOURCE_ID = "national_inventory_documents"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 tradeimpact/1.0 (research; sanghyun@planit.institute)"
)
CURL = "/usr/bin/curl"
PAUSE_SECONDS = 1.5
EXTENSIONS = {"pdf": ".pdf", "html": ".html", "xlsx": ".xlsx"}
INDEX_FIELDS = [
    "source_key",
    "country",
    "file",
    "url",
    "publisher",
    "licence",
    "content_type",
    "bytes",
    "sha256",
    "fetched",
    "fetched_with",
    "what_it_states",
]


def fetch(url: str, context: ssl.SSLContext) -> tuple[bytes, str]:
    """The document bytes and its content type."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context, timeout=300) as response:
        return response.read(), response.headers.get("Content-Type", "")


def fetch_with_curl(url: str, into: Path) -> tuple[bytes, str]:
    """The document bytes and content type via the system curl, certificate still verified."""
    proc = subprocess.run(
        [
            CURL, "--silent", "--show-error", "--fail", "--location", "--max-time", "300",
            "--user-agent", USER_AGENT, "--write-out", "%{content_type}",
            "--output", str(into), url,
        ],
        capture_output=True,
        check=True,
        text=True,
    )  # fmt: skip
    return into.read_bytes(), proc.stdout.strip()


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
        name = key + EXTENSIONS.get(source["kind"], ".pdf")
        path = RAW_DIR / name
        if key in known and path.exists():
            index.append({**known[key], "what_it_states": source["what_it_states"]})
            continue
        transport = "urllib"
        try:
            body, content_type = fetch(source["url"], context)
        except urllib.error.URLError as exc:
            if not isinstance(exc.reason, ssl.SSLError):
                print(f"  FAILED {key}: {exc}")
                failed += 1
                continue
            print(f"  {key}: python TLS failed ({exc.reason}); retrying with the system curl")
            try:
                body, content_type = fetch_with_curl(source["url"], path)
                transport = "curl_system_trust"
            except Exception as curl_exc:  # noqa: BLE001 - one unreachable document must not stop
                print(f"  FAILED {key}: {curl_exc}")
                failed += 1
                continue
        except Exception as exc:  # noqa: BLE001 - one unreachable document must not stop the run
            print(f"  FAILED {key}: {exc}")
            failed += 1
            continue
        path.write_bytes(body)
        fetched += 1
        index.append(
            {
                "source_key": key,
                "country": source["country"],
                "file": name,
                "url": source["url"],
                "publisher": source["publisher"],
                "licence": source["licence"],
                "content_type": content_type,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "fetched": date.today().isoformat(),
                "fetched_with": transport,
                "what_it_states": source["what_it_states"],
            }
        )
        time.sleep(PAUSE_SECONDS)
    write_csv(INDEX, INDEX_FIELDS, sorted(index, key=lambda r: str(r["source_key"])))
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "the environment and energy ministries named per document",
            "title": "National greenhouse gas inventory reports and announced emission factors of "
            "the destination countries",
            "url": "https://unfccc.int/ghg-inventories-annex-i-parties/2024",
            "how_obtained": "each document downloaded from the URL listed in "
            "emission_factors/method/national_documents.csv by "
            "script/power/emission_factors/fetch_national_documents.py and stored under "
            "data/power/emission_factors/raw/national_documents/ with its URL, bytes, SHA-256 and "
            "licence in index.csv; every factor row cites the source_key of the document that "
            "states it and quotes the table line",
            "accessed_date": date.today().isoformat(),
            "license": "per document, recorded in raw/national_documents/index.csv",
            "used_by": "emission_factors",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "emission_factors",
        INDEX,
        SOURCE_ID,
        "national inventory documents (one file per source_key)",
        f"index of {len(index)} documents in raw/national_documents/, each with URL, SHA-256 "
        "and licence",
        data_root=DATA,
    )
    print(
        f"{RAW_DIR.relative_to(REPO)}: {len(index)} documents on disk ({fetched} fetched now, "
        f"{failed} failed); index.csv sha256 {digest[:16]}"
    )


if __name__ == "__main__":
    main()
