"""Run the whole automotive pipeline in order and stop at the first failure.

Steps (each is a standalone script; see script/auto/README.md):
    extraction   raw/ -> processed/ for every dataset
    derivation   S1/S2 rates per market
    model        reference, impact, sensitivity, aggregation, data quality
    database     every CSV under data/auto -> data/auto/database/tradeimpact_auto.sqlite
    dashboard    static reader of the database file -> data/auto/database/dashboard.html
    checks       ruff (lint) and pytest (numerical and consistency tests)

Exit status is non-zero if any step fails, so `run_all.py && git commit` can never commit a
partial state. Pass --skip-fetch (default) or --fetch to also re-download the EEA snapshots
(they are pinned; fetching only adds brands that are not yet on disk).

Run from the repository root:  .venv/bin/python script/auto/run_all.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = sys.executable

EXTRACT = [
    "sales/extract_eea_registrations.py",
    "sales/extract_kia_ir.py",
    "sales/extract_hyundai_ir.py",
    "sales/extract_hyundai_us_retail.py",
    "sales/extract_hyundai_sales_by_model.py",
    "sales/extract_kia_america.py",
    "sales/extract_jada.py",
    "sales/extract_us_releases.py",
    "sales/extract_global_sales.py",
    "vehicle_technology/extract_eea_certified.py",
    "vehicle_technology/extract_epa_fueleconomy.py",
    "vehicle_technology/extract_epa_trends.py",
    "vehicle_technology/extract_kea_fuel_economy.py",
    "vehicle_technology/extract_mlit_fuel_economy.py",
    "vehicle_usage/extract_eu27_eurostat.py",
    "vehicle_usage/extract_fhwa_vm1.py",
    "vehicle_usage/extract_abs_mvc.py",
    "vehicle_usage/extract_abs_smvu.py",
    "vehicle_usage/extract_nhtsa_survival.py",
    "vehicle_usage/extract_molit_registrations.py",
    "vehicle_usage/extract_kotsa_tmacs.py",
    "vehicle_usage/extract_mlit_fuel_survey.py",
    "vehicle_usage/extract_airia_vehicle_age.py",
    "country_emissions/extract_eu27_snapshot.py",
    "country_emissions/extract_owid_grid.py",
    "country_emissions/extract_epa_inventory.py",
    "country_emissions/extract_anga_inventory.py",
    "country_emissions/extract_kr_inventory.py",
    "country_emissions/extract_jp_inventory.py",
    "trade_flows/extract_trade_flows.py",
    "dashboard/fetch_map_assets.py",
]
DERIVE = [
    "emission_targets/derive_eu27_rates.py",
    "emission_targets/derive_us_rates.py",
    "emission_targets/derive_au_rates.py",
    "emission_targets/derive_kr_rates.py",
    "emission_targets/derive_jp_rates.py",
]
MODEL = [
    "model/build_cohorts.py",
    "model/build_reference.py",
    "model/build_reference_us.py",
    "model/build_reference_kr.py",
    "model/build_reference_jp.py",
    "model/build_ti.py",
    "model/build_sensitivity.py",
    "model/aggregate_country.py",
    "model/build_data_quality.py",
    "model/build_coverage.py",
    "model/build_reconciliation.py",
    "model/build_global_coverage.py",
    "model/build_database.py",
    "model/build_dashboard.py",
]
CHECKS = [
    [PY, "-m", "ruff", "check", "script", "tests"],
    [PY, "-m", "pytest", "-q", "tests"],
]


def run(cmd: list[str], label: str) -> None:
    """Run one command from the repository root; raise on failure."""
    start = time.perf_counter()
    result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    tail = (result.stdout.strip().splitlines() or [""])[-1]
    status = "ok  " if result.returncode == 0 else "FAIL"
    print(f"[{status}] {label:48s} {elapsed:5.1f}s  {tail[:90]}")
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"step failed: {label}")


def main() -> None:
    """Execute every stage in order."""
    for group in (EXTRACT, DERIVE, MODEL):
        for script in group:
            run([PY, str(REPO / "script" / "auto" / script)], script)
    for cmd in CHECKS:
        run(cmd, " ".join(cmd[2:]))
    print("pipeline complete")


if __name__ == "__main__":
    main()
