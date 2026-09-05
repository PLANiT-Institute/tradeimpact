"""Download the IPCC 2006 Guidelines chapter that carries the default CO2 emission factors.

Source of truth: 2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 2 (Energy),
Chapter 2 Stationary Combustion, Table 2.2 "Default emission factors for stationary combustion in
energy industries" (kg CO2 per TJ, with the 95 % lower and upper bounds), published by the IPCC
Task Force on National Greenhouse Gas Inventories (https://www.ipcc-nggip.iges.or.jp/public/2006gl/).
The PDF is kept so that the hand transcription in method/ipcc_2006_table_2_2.csv can be verified
against its text by the extractor.

Run from the repository root:  .venv/bin/python script/power/emission_factors/fetch_ipcc_defaults.py
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
RAW = DATA / "emission_factors" / "raw" / "ipcc_2006_v2_ch2_stationary_combustion.pdf"
URL = (
    "https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/"
    "V2_2_Ch2_Stationary_Combustion.pdf"
)
SOURCE_ID = "ipcc_2006_v2_ch2"


def main() -> None:
    """Download the chapter and register it."""
    RAW.parent.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(URL, context=context, timeout=120) as response:
        RAW.write_bytes(response.read())
    upsert_source(
        {
            "source_id": SOURCE_ID,
            "publisher": "IPCC Task Force on National Greenhouse Gas Inventories",
            "title": (
                "2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 2 Energy, "
                "Chapter 2 Stationary Combustion (Table 2.2 default CO2 emission factors, "
                "energy industries)"
            ),
            "url": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol2.html",
            "how_obtained": (
                f"chapter PDF downloaded from {URL} by "
                "script/power/emission_factors/fetch_ipcc_defaults.py; Table 2.2 transcribed by "
                "hand into emission_factors/method/ipcc_2006_table_2_2.csv and verified against "
                "the PDF text by the extractor"
            ),
            "accessed_date": date.today().isoformat(),
            "license": "IPCC copyright; reproduction of tables permitted with acknowledgement",
            "used_by": "emission_factors",
        },
        data_root=DATA,
    )
    digest = upsert_raw_file(
        "emission_factors",
        RAW,
        SOURCE_ID,
        "V2_2_Ch2_Stationary_Combustion.pdf",
        "IPCC 2006 GL Vol 2 Ch 2",
        data_root=DATA,
    )
    print(f"{RAW.relative_to(REPO)}: {RAW.stat().st_size:,} bytes, sha256 {digest[:16]}")


if __name__ == "__main__":
    main()
