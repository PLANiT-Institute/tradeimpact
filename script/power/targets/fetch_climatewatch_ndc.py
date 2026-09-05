"""Download the structured NDC target content for every country from Climate Watch (WRI).

Source of truth: Climate Watch, "NDC Content" (https://www.climatewatchdata.org/ndcs-content), the
World Resources Institute's structured reading of every NDC in the UNFCCC registry, versioned by
submission (INDC, first NDC, updated first NDC, second NDC, third NDC). Its public API returns,
per country and per submission, the GHG target as stated, its type (base year / baseline
scenario / fixed level / intensity / trajectory), the target year and the sectors covered — which
is what the S2 pathway of each destination is read from. Licence CC BY 4.0; citation
"Climate Watch. World Resources Institute. https://www.climatewatchdata.org".

Run from the repository root:  .venv/bin/python script/power/targets/fetch_climatewatch_ndc.py
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.request
from datetime import date
from pathlib import Path

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from registry import upsert_raw_file, upsert_source  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "data" / "power"
RAW = DATA / "targets" / "raw" / "climatewatch_ndc_content.json"
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


def get(url: str, context: ssl.SSLContext) -> dict:
    """GET a JSON document."""
    request = urllib.request.Request(url, headers={"User-Agent": "tradeimpact/1.0"})
    with urllib.request.urlopen(request, context=context, timeout=180) as response:
        return json.load(response)


def main() -> None:
    """Fetch the indicator values for all countries and the submission list; register the file."""
    context = ssl.create_default_context(cafile=certifi.where())
    indicators_url = f"{API}/ndcs?indicators={','.join(INDICATORS)}"
    payload = {
        "fetched": date.today().isoformat(),
        "indicators_url": indicators_url,
        "documents_url": f"{API}/data/ndc_content/documents",
        "indicators": get(indicators_url, context)["indicators"],
        "documents": get(f"{API}/data/ndc_content/documents", context)["data"],
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
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
                "by script/power/targets/fetch_climatewatch_ndc.py"
            ),
            "accessed_date": date.today().isoformat(),
            "license": "CC BY 4.0",
            "used_by": "targets",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "targets",
        RAW,
        SOURCE_ID,
        "ndcs (API response)",
        f"{len(INDICATORS)} indicators, all countries, every submission",
        data_root=DATA,
    )
    countries = {iso for i in payload["indicators"] for iso in i["locations"]}
    print(
        f"{RAW.relative_to(REPO)}: {len(payload['indicators'])} indicators, {len(countries)} "
        f"countries, {len(payload['documents'])} submission types; sha256 {digest[:16]}"
    )


if __name__ == "__main__":
    main()
