"""Download the Japanese makers' US sales releases and write their tables as raw CSV.

The publishers put these tables in a web page rather than a file, and a web page is not a raw
input here, so this script reads the published tables and writes them out as CSV exactly as
printed: one row per label with the calendar-year-to-date column of the release year and of the
comparison year. The CSV is the raw file; the release URL, the retrieval date and the SHA-256
are recorded in the registry beside it.

    toyota   Toyota Motor North America, "Reports <year> U.S. Sales Results". The company's own
             pressroom refuses automated access (Cloudflare, HTTP 403 verified), so the release
             is read from the PR Newswire distribution of the same text. Two tables: models by
             division, and an electrified summary giving model x powertrain.
    nissan   Nissan Group, "Reports <year> calendar year U.S. sales", from Nissan's own US
             newsroom. Four tables: Nissan Division models, Infiniti models, totals, and a split
             of Nissan Division volumes into North American production and imports.

Run from the repository root:  .venv/bin/python script/auto/sales/fetch_us_releases.py
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
}
FIELDS = ["table", "row", "label", "units_cy", "units_cy_prior"]

RELEASES = {
    "tmna_us_sales": {
        "year": 2025,
        "prior": 2024,
        "url": (
            "https://www.prnewswire.com/news-releases/"
            "toyota-motor-north-america-reports-2025-us-sales-results-302652746.html"
        ),
        "publisher_url": (
            "https://pressroom.toyota.com/toyota-motor-north-america-reports-2025-u-s-sales-results/"
        ),
        "source_id": "tmna_us_sales_release",
        "publisher": "Toyota Motor North America",
        "title": (
            "Toyota Motor North America Reports 2025 U.S. Sales Results: US sales by model for "
            "the Toyota and Lexus divisions, and a second table giving model by powertrain "
            "(hybrid, plug-in hybrid, battery electric, fuel cell)"
        ),
        "how": (
            "the company pressroom refuses automated access (HTTP 403, Cloudflare), so the "
            "tables were read from the PR Newswire distribution of the same release and written "
            "to CSV by script/auto/sales/fetch_us_releases.py"
        ),
        "cy_column": 5,
        "prior_column": 6,
    },
    "nissan_us_sales": {
        "year": 2025,
        "prior": 2024,
        "url": (
            "https://usa.nissannews.com/en-US/releases/"
            "nissan-group-reports-2025-calendar-year-and-2025-fourth-quarter-us-sales"
        ),
        "publisher_url": (
            "https://usa.nissannews.com/en-US/releases/"
            "nissan-group-reports-2025-calendar-year-and-2025-fourth-quarter-us-sales"
        ),
        "source_id": "nissan_us_sales_release",
        "publisher": "Nissan Group (Nissan Motor Corporation US newsroom)",
        "title": (
            "Nissan Group Reports 2025 Calendar Year and Fourth Quarter U.S. Sales: US sales by "
            "model for the Nissan and Infiniti divisions, with Nissan Division volumes split "
            "into North American production and imports; no powertrain split"
        ),
        "how": (
            "tables read from the company's own US newsroom and written to CSV by "
            "script/auto/sales/fetch_us_releases.py"
        ),
        "cy_column": 5,
        "prior_column": 6,
    },
}
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TABLE = re.compile(r"<table[^>]*>(.*?)</table>", re.S)


def text(fragment: str) -> str:
    """Tag-free, entity-decoded cell text."""
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", " ").strip()


def tables(page: str) -> list[list[list[str]]]:
    """Every table of the page as a list of rows of cells."""
    out = []
    for table in TABLE.findall(page):
        rows = [[text(c) for c in CELL.findall(tr)] for tr in ROW.findall(table)]
        out.append([r for r in rows if any(r)])
    return out


def main() -> None:
    """Fetch each release and write its tables as one raw CSV."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    for stem, spec in RELEASES.items():
        dest = RAW / f"{stem}_{spec['year']}.csv"
        if dest.exists() and not args.force:
            status = "kept"
        else:
            req = urllib.request.Request(str(spec["url"]), headers=HEADERS)
            with urllib.request.urlopen(req, context=context, timeout=120) as r:
                page = r.read().decode("utf-8", "replace")
            rows_out = []
            for ti, table in enumerate(tables(page)):
                if len(table) < 5:
                    continue
                for ri, row in enumerate(table):
                    label = row[0] if row else ""
                    if not label:
                        continue
                    cy = (
                        row[int(str(spec["cy_column"]))]
                        if len(row) > int(str(spec["cy_column"]))
                        else ""
                    )
                    prior = (
                        row[int(str(spec["prior_column"]))]
                        if len(row) > int(str(spec["prior_column"]))
                        else ""
                    )
                    rows_out.append(
                        {
                            "table": ti,
                            "row": ri,
                            "label": label,
                            "units_cy": cy,
                            "units_cy_prior": prior,
                        }
                    )
            if not rows_out:
                raise SystemExit(f"{spec['url']}: no tables found")
            with dest.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows_out)
            status = "fetched"
        upsert_source(
            {
                "source_id": str(spec["source_id"]),
                "publisher": str(spec["publisher"]),
                "title": str(spec["title"]),
                "url": str(spec["publisher_url"]),
                "how_obtained": str(spec["how"]),
                "accessed_date": accessed,
                "license": (
                    "company press release; redistribution of the table is a licence question"
                ),
                "used_by": "extract_us_releases.py",
            }
        )
        digest = upsert_raw_file(
            "sales",
            dest,
            str(spec["source_id"]),
            f"tables of the {spec['year']} US sales release",
            f"calendar years {spec['year']} and {spec['prior']}; {status} {accessed} "
            f"from {spec['url']}",
        )
        print(f"{stem}: {status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
