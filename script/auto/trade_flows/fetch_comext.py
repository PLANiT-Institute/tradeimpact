"""Fetch EU27 member-state imports of passenger cars from Korea and Japan (Eurostat Comext).

Source of truth: Eurostat Comext dataset ds-045409 ("EU trade since 1988 by HS2-4-6 and CN8"),
via the Comext dissemination API (JSON-stat 2.0). One request per partner covers every HS 8703
six-digit sub-heading, every reporter (27 member states plus EU aggregates), flow 1 = imports,
indicators SUPPLEMENTARY_QUANTITY (number of vehicles) and VALUE_IN_EUROS fetched separately
(the API drops the quantity when both are requested together), years 2022-2025.
Each response is saved verbatim as data/auto/trade_flows/raw/comext_imports_<partner>.json and
registered in data/auto/raw_files.csv with URL, access date and hash.

Run from the repository root:  .venv/bin/python script/auto/trade_flows/fetch_comext.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import ssl
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "auto"
RAW = DATA / "trade_flows" / "raw"
HS_TABLE = DATA / "trade_flows" / "method" / "hs_passenger_cars.csv"
API = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/ds-045409"
DATASET_PAGE = "https://ec.europa.eu/eurostat/databrowser/view/ds-045409/default/table?lang=en"
SOURCE_ID = "eurostat_comext_ds045409"
USER_AGENT = "tradeimpact/0.2 source acquisition"
PARTNERS = {"KR": "Korea, Republic of", "JP": "Japan"}
YEARS = ("2022", "2023", "2024", "2025")


def main() -> None:
    """One pinned raw file per exporting country."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="overwrite pinned raw files")
    args = parser.parse_args()
    codes = [r["hs6"] for r in csv.DictReader(HS_TABLE.open(newline=""))]
    context = ssl.create_default_context(cafile=certifi.where())
    accessed = date.today().isoformat()
    for partner, name in PARTNERS.items():
        out = RAW / f"comext_imports_{partner.lower()}.json"
        if out.exists() and not args.force:
            print(f"{out.relative_to(REPO)}: pinned, skipped")
            continue
        responses: dict[str, dict] = {}
        urls: dict[str, str] = {}
        # The API returns a value for one indicator only when both are requested together, so
        # each indicator is fetched on its own and both responses are pinned in one raw file.
        for indicator in ("SUPPLEMENTARY_QUANTITY", "VALUE_IN_EUROS"):
            params = [
                ("format", "JSON"),
                ("lang", "EN"),
                ("freq", "A"),
                ("partner", partner),
                ("flow", "1"),
                ("indicators", indicator),
            ]
            params += [("product", c) for c in codes] + [("time", y) for y in YEARS]
            url = f"{API}?{urllib.parse.urlencode(params)}"
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=600, context=context) as response:  # noqa: S310
                payload = json.loads(response.read().decode())
            if "value" not in payload:
                raise SystemExit(f"Comext {partner} {indicator}: unexpected payload")
            responses[indicator] = payload
            urls[indicator] = url
        url = " ; ".join(urls.values())
        out.write_text(
            json.dumps(
                {
                    "accessed_date": accessed,
                    "source_id": SOURCE_ID,
                    "dataset_page": DATASET_PAGE,
                    "request_urls": urls,
                    "partner": partner,
                    "partner_name": name,
                    "flow": "imports",
                    "hs6": codes,
                    "years": list(YEARS),
                    "responses": responses,
                },
                sort_keys=True,
            )
            + "\n"
        )
        register(out, url, accessed, partner)
        n = {k: len(v["value"]) for k, v in responses.items()}
        print(f"{out.relative_to(REPO)}: values per indicator {n}")


def register(path: Path, url: str, accessed: str, partner: str) -> None:
    """Upsert the raw file's row in data/auto/raw_files.csv."""
    registry = DATA / "raw_files.csv"
    rows = list(csv.DictReader(registry.open(newline="")))
    rows = [r for r in rows if not (r["dataset"] == "trade_flows" and r["file"] == path.name)]
    rows.append(
        {
            "dataset": "trade_flows",
            "file": path.name,
            "source_id": SOURCE_ID,
            "original_name": "ds-045409 (JSON-stat 2.0)",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "note": (
                f"EU member-state imports of HS 8703 passenger cars from {partner}, units and "
                f"euros, 2022-2025; fetched {accessed} from {url}"
            ),
        }
    )
    with registry.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
