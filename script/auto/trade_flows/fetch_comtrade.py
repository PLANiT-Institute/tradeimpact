"""Fetch passenger-car trade flows for the non-EU importers from UN Comtrade (public preview API).

Source of truth: UN Comtrade, HS classification, annual, customs code C00. Two views per
exporter x importer pair so the reconciliation is visible: the exporter's reported exports
(Korea 410, Japan 392 -> United States 842, Australia 36; flowCode X) and the importer's
reported imports (mirror; flowCode M). All HS 8703 six-digit sub-headings, years 2022-2025.
Quantities: Comtrade's ``qty`` is "number of items" (unit code 5) and may be flagged
``isQtyEstimated``; ``altQty`` is net weight (kg). Each response is saved verbatim as
data/auto/trade_flows/raw/comtrade_<reporter>_<flow>_<partner>_<year>.json and registered
(the preview endpoint accepts one period per request).

The public preview endpoint needs no key but is rate-limited; the script pauses between calls.

Run from the repository root:  .venv/bin/python script/auto/trade_flows/fetch_comtrade.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import ssl
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
RAW = DATA / "trade_flows" / "raw"
HS_TABLE = DATA / "trade_flows" / "method" / "hs_passenger_cars.csv"
API = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
SOURCE_PAGE = "https://comtradeplus.un.org/"
SOURCE_ID = "un_comtrade_public"
USER_AGENT = "tradeimpact/0.2 source acquisition"
COUNTRIES = {"KR": 410, "JP": 392, "US": 842, "AU": 36}
EXPORTERS, IMPORTERS = ("KR", "JP"), ("US", "AU")
PERIODS = ("2022", "2023", "2024", "2025")
PAUSE_S = 2.0


def fetch(url: str, context: ssl.SSLContext) -> dict:
    """GET one preview query."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300, context=context) as response:  # noqa: S310
        payload = json.loads(response.read().decode())
    if "data" not in payload:
        raise SystemExit(f"Comtrade: unexpected payload {str(payload)[:200]}")
    return payload


def register(path: Path, url: str, accessed: str, note: str) -> None:
    """Upsert the raw file's row in data/auto/raw_files.csv."""
    registry = DATA / "raw_files.csv"
    rows = list(csv.DictReader(registry.open(newline="")))
    rows = [r for r in rows if not (r["dataset"] == "trade_flows" and r["file"] == path.name)]
    rows.append(
        {
            "dataset": "trade_flows",
            "file": path.name,
            "source_id": SOURCE_ID,
            "original_name": "Comtrade public preview (JSON)",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "note": f"{note}; fetched {accessed} from {url}",
        }
    )
    with registry.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    """Exporter-reported and importer-reported flows for every exporter x importer pair."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="overwrite pinned raw files")
    args = parser.parse_args()
    codes = ",".join(r["hs6"] for r in csv.DictReader(HS_TABLE.open(newline="")))
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    queries = []
    for exp in EXPORTERS:
        for imp in IMPORTERS:
            queries.append((exp, "X", imp, COUNTRIES[exp], COUNTRIES[imp]))
            queries.append((imp, "M", exp, COUNTRIES[imp], COUNTRIES[exp]))
    for reporter, flow, partner, rep_code, par_code in queries:
        for year in PERIODS:
            out = RAW / f"comtrade_{reporter.lower()}_{flow.lower()}_{partner.lower()}_{year}.json"
            if out.exists() and not args.force:
                print(f"{out.relative_to(REPO)}: pinned, skipped")
                continue
            params = {
                "reporterCode": rep_code,
                "period": year,
                "partnerCode": par_code,
                "cmdCode": codes,
                "flowCode": flow,
            }
            url = f"{API}?{urllib.parse.urlencode(params)}"
            payload = fetch(url, context)
            direction = "exports to" if flow == "X" else "imports from"
            note = (
                f"{reporter} reported {direction} {partner}, HS 8703 sub-headings, "
                f"{year}, {payload.get('count')} records"
            )
            out.write_text(
                json.dumps(
                    {
                        "accessed_date": accessed,
                        "source_id": SOURCE_ID,
                        "source_page": SOURCE_PAGE,
                        "request_url": url,
                        "reporter": reporter,
                        "flow": flow,
                        "partner": partner,
                        "period": year,
                        "response": payload,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            register(out, url, accessed, note)
            print(f"{out.relative_to(REPO)}: {payload.get('count')} records")
            time.sleep(PAUSE_S)


if __name__ == "__main__":
    main()
