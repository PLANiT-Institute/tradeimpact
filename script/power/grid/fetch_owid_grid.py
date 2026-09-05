"""Download the grid carbon-intensity series for every country from Our World in Data (Ember).

Source of truth: Our World in Data grapher "Carbon intensity of electricity generation"
(https://ourworldindata.org/grapher/carbon-intensity-electricity), which republishes Ember's
Yearly Electricity Data (https://ember-energy.org/data/yearly-electricity-data/) as gCO2e/kWh
per country and year. The grapher's CSV export carries all entities, so one download covers
every destination country a project may sit in. Licence CC BY 4.0.

Run from the repository root:  .venv/bin/python script/power/grid/fetch_owid_grid.py
"""

from __future__ import annotations

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
RAW = DATA / "grid" / "raw" / "owid_carbon_intensity_electricity.csv"
URL = "https://ourworldindata.org/grapher/carbon-intensity-electricity.csv"
SOURCE_ID = "owid_ember_grid_intensity"


def main() -> None:
    """Download the CSV export and register it."""
    RAW.parent.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(URL, headers={"User-Agent": "tradeimpact/1.0"})
    with urllib.request.urlopen(request, context=context, timeout=120) as response:
        RAW.write_bytes(response.read())
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "Our World in Data (Ember Yearly Electricity Data)",
            "title": "Carbon intensity of electricity generation, gCO2e/kWh, all countries",
            "url": "https://ourworldindata.org/grapher/carbon-intensity-electricity",
            "how_obtained": f"CSV export downloaded from {URL} by "
            "script/power/grid/fetch_owid_grid.py",
            "accessed_date": date.today().isoformat(),
            "license": "CC BY 4.0",
            "used_by": "grid;targets;model",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "grid",
        RAW,
        SOURCE_ID,
        "carbon-intensity-electricity.csv",
        "OWID grapher CSV export, all entities",
        data_root=DATA,
    )
    print(f"{RAW.relative_to(REPO)}: {RAW.stat().st_size:,} bytes, sha256 {digest[:16]}")


if __name__ == "__main__":
    main()
