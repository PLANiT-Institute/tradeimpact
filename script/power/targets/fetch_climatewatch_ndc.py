"""Download every country's NDC target content from Climate Watch (WRI) as two readable CSVs.

Source of truth: Climate Watch, "NDC Content" (https://www.climatewatchdata.org/ndcs-content), the
World Resources Institute's structured reading of every NDC in the UNFCCC registry, versioned by
submission (INDC, first NDC, updated first NDC, second NDC, third NDC). Its public API returns,
per country and per submission, the GHG target as stated, its type (base year / baseline
scenario / fixed level / intensity / trajectory), the target year and the sectors covered — which
is what the S2 pathway of each destination is read from. Licence CC BY 4.0; citation
"Climate Watch. World Resources Institute. https://www.climatewatchdata.org".

The API answers JSON keyed by indicator and country; it is flattened here into files a person can
open and check row by row:

    targets/raw/climatewatch_ndc_content.csv      iso3, country, submission, indicator, indicator
                                                  name, value (one row per stated value)
    targets/raw/climatewatch_ndc_submissions.csv  submission slug, ordering, long name — the order
                                                  the extractor uses to pick the latest NDC

Run from the repository root:  .venv/bin/python script/power/targets/fetch_climatewatch_ndc.py
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from power_io import DATA, REPO, write_csv  # noqa: E402
from registry import upsert_raw_file, upsert_source  # noqa: E402

CONTENT = DATA / "targets" / "raw" / "climatewatch_ndc_content.csv"
SUBMISSIONS = DATA / "targets" / "raw" / "climatewatch_ndc_submissions.csv"
API = "https://www.climatewatchdata.org/api/v1"
INDICATORS = [
    "ghg_target",
    "ghg_target_type",
    "time_target_year",
    "coverage_sectors",
    "ghg_target_base_year",
    "ghg_target_baseline",
    "ghg_target_fixed_level",
    "ghg_target_intensity",
    "ghg_target_trajectory",
]
SOURCE_ID = "climatewatch_ndc_content"
CONTENT_FIELDS = [
    "iso3",
    "submission",
    "indicator",
    "indicator_name",
    "value",
    "source_url",
    "fetched",
]
SUBMISSION_FIELDS = ["submission", "ordering", "long_name", "description"]


def get(url: str, context: ssl.SSLContext) -> dict:
    """GET a JSON document."""
    request = urllib.request.Request(url, headers={"User-Agent": "tradeimpact/1.0"})
    with urllib.request.urlopen(request, context=context, timeout=180) as response:
        return json.load(response)


def flatten(text: object) -> str:
    """A stated value as one line: markup removed, whitespace collapsed."""
    t = re.sub(r"<[^>]+>", " ", str(text or ""))
    return re.sub(r"\s+", " ", t).strip()


def main() -> None:
    """Fetch the indicator values for all countries and the submission list; register both files."""
    context = ssl.create_default_context(cafile=certifi.where())
    indicators_url = f"{API}/ndcs?indicators={','.join(INDICATORS)}"
    indicators = get(indicators_url, context)["indicators"]
    documents = get(f"{API}/data/ndc_content/documents", context)["data"]
    today = date.today().isoformat()
    rows: list[dict[str, object]] = []
    for indicator in indicators:
        for iso3, values in indicator["locations"].items():
            for v in values:
                rows.append(
                    {
                        "iso3": iso3,
                        "submission": v.get("document_slug", ""),
                        "indicator": indicator["slug"],
                        "indicator_name": indicator["name"],
                        "value": flatten(v.get("value")),
                        "source_url": f"https://www.climatewatchdata.org/ndcs/country/{iso3}",
                        "fetched": today,
                    }
                )
    rows.sort(key=lambda r: (str(r["iso3"]), str(r["indicator"]), str(r["submission"])))
    write_csv(CONTENT, CONTENT_FIELDS, rows)
    write_csv(
        SUBMISSIONS,
        SUBMISSION_FIELDS,
        [
            {
                "submission": d["slug"],
                "ordering": d["ordering"],
                "long_name": d["long_name"],
                "description": d.get("description", ""),
            }
            for d in sorted(documents, key=lambda d: d["ordering"])
        ],
    )
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Climate Watch (World Resources Institute)",
            "title": (
                "NDC Content: GHG target as stated, target type, target year and sectors covered "
                "per country and per NDC submission, read from the UNFCCC NDC registry"
            ),
            "url": "https://www.climatewatchdata.org/ndcs-content",
            "how_obtained": (
                f"JSON from the public API {indicators_url} and {API}/data/ndc_content/documents "
                "by script/power/targets/fetch_climatewatch_ndc.py, flattened to one row per "
                "country x indicator x submission; each row carries the country page it came from"
            ),
            "accessed_date": today,
            "license": "CC BY 4.0",
            "used_by": "targets",
        },
        data_root=DATA,
    )
    for path, note in (
        (CONTENT, f"{len(rows)} rows: country x indicator x submission, value as stated"),
        (SUBMISSIONS, f"{len(documents)} NDC submission types in the order they supersede"),
    ):
        upsert_raw_file("targets", path, SOURCE_ID, "ndcs (API response)", note, data_root=DATA)
    countries = {r["iso3"] for r in rows}
    print(
        f"{CONTENT.relative_to(REPO)}: {len(rows)} rows, {len(countries)} countries, "
        f"{len(INDICATORS)} indicators; {SUBMISSIONS.name}: {len(documents)} submission types"
    )


if __name__ == "__main__":
    main()
