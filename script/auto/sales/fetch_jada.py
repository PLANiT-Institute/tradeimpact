"""Download JADA's free Japan new-vehicle registration statistics (annual editions).

Source of truth: 一般社団法人 日本自動車販売協会連合会 (Japan Automobile Dealers Association),
統計データ. Each statistics page lists one workbook per period; the link labels carry the period,
so this script reads the page and takes the annual (1月-12月) editions of the years asked for.
The file ids in the URLs are opaque and change when a workbook is reissued, which is why the page
is read rather than a URL constructed.

    pages/340  ブランド通称名別ランキング   nameplate ranking, passenger cars, top 50
               (kei cars and foreign brands excluded; Lexus is a brand of its own)
    pages/342  燃料別登録台数              registrations by maker and fuel (petrol, HEV, PHEV,
               diesel, BEV, FCEV, other); kei excluded; Lexus folded into Toyota
    pages/337  ブランド別登録台数（確報）    registrations by brand with an 内輸入 column, the
               units built outside Japan and sold in Japan

All three are registrations (market-side, ナンバーベース). JADA sells the back-series as paid
books (pages/517), so republication of these rows is a licence question for the provenance
audit; the files themselves are free to download.

Run from the repository root:
    .venv/bin/python script/auto/sales/fetch_jada.py 2024 2025
"""

from __future__ import annotations

import argparse
import html
import re
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "data" / "auto" / "sales" / "raw"
SOURCE_ID = "jada_registration_statistics"
BASE = "https://www.jada.or.jp"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
}
#: page id -> (file stem, what the workbook holds)
PAGES = {
    "340": ("jada_model_ranking", "ブランド通称名別ランキング: passenger-car nameplate ranking"),
    "342": ("jada_fuel_by_maker", "燃料別登録台数: registrations by maker and fuel"),
    "337": ("jada_brand_registrations", "ブランド別登録台数（確報）: registrations by brand"),
}
#: An annual edition labels itself 1月-12月 (the tilde is written two different ways).
ANNUAL = re.compile(r"(20\d\d)年\s*1月\s*[~～-]\s*12月")
LINK = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)


def fetch_page(page: str, context: ssl.SSLContext) -> str:
    """HTML of one statistics page."""
    req = urllib.request.Request(f"{BASE}/pages/{page}/", headers=HEADERS)
    with urllib.request.urlopen(req, context=context, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def annual_links(page_html: str) -> dict[int, str]:
    """{year: absolute file URL} for every annual workbook the page offers."""
    found: dict[int, str] = {}
    for href, label in LINK.findall(page_html):
        text = html.unescape(re.sub("<[^>]+>", " ", label))
        year = ANNUAL.search(text)
        if not year:
            continue
        query = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        path = query.get("file", [href])[0]
        if not re.search(r"\.(xlsx|xls)$", path):
            continue
        found[int(year.group(1))] = path if path.startswith("http") else BASE + path
    return found


def main() -> None:
    """Fetch the annual workbook of each statistics page for every year requested."""
    ap = argparse.ArgumentParser()
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": (
                "一般社団法人 日本自動車販売協会連合会 JADA (Japan Automobile Dealers Association)"
            ),
            "title": (
                "統計データ: new-vehicle registrations in Japan. Nameplate ranking (top 50, kei "
                "and foreign brands excluded), registrations by maker and fuel, and registrations "
                "by brand with the imported share"
            ),
            "url": f"{BASE}/pages/340/",
            "how_obtained": (
                "statistics pages 340, 342 and 337 read for their annual workbook links, which "
                "are then downloaded, by script/auto/sales/fetch_jada.py"
            ),
            "accessed_date": accessed,
            "license": (
                "association statistics, free to download; the back series is sold as paid books"
            ),
            "used_by": "extract_jada.py",
        }
    )
    for page, (stem, what) in PAGES.items():
        links = annual_links(fetch_page(page, context))
        for year in args.years:
            url = links.get(year)
            if url is None:
                print(f"{stem} {year}: no annual edition on pages/{page} ({sorted(links)})")
                continue
            dest = RAW / f"{stem}_{year}{Path(urllib.parse.urlparse(url).path).suffix}"
            if dest.exists() and not args.force:
                status = "kept"
            else:
                req = urllib.request.Request(
                    url, headers={**HEADERS, "Referer": f"{BASE}/pages/{page}/"}
                )
                with urllib.request.urlopen(req, context=context, timeout=120) as r:
                    data = r.read()
                if data[:2] not in (b"PK", b"\xd0\xcf"):
                    raise SystemExit(f"{url}: not a workbook ({data[:40]!r})")
                dest.write_bytes(data)
                status = "fetched"
            digest = upsert_raw_file(
                "sales",
                dest,
                SOURCE_ID,
                Path(urllib.parse.urlparse(url).path).name,
                f"{what}, calendar year {year}, from pages/{page}; {status} {accessed} from {url}",
            )
            print(f"{stem} {year}: {status} {dest.name} {dest.stat().st_size:,} B {digest[:12]}")


if __name__ == "__main__":
    main()
