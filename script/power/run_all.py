"""Run the power-sector pipeline in order and stop at the first failure or missing hand file.

Steps (each a standalone script; see script/power/README.md):
    fetch (with --fetch)   country codes, OWID grid series, IPCC chapter PDF
    extraction             geography, grid, emission factors, projects (GEM), roles
    derivation             S1/S2 grid-intensity rates per destination
    model                  reference path, unit-level impact, attribution by role
    checks                 ruff and pytest

Exit status: 0 when every step ran; 3 when a step stopped on a HAND-GATHERED input that is not
on disk yet (shown as [hand], with the file and how to obtain it); 1 on any other failure.

Run from the repository root:  .venv/bin/python script/power/run_all.py [--fetch]
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PY = sys.executable
EXIT_HAND = 3

FETCH = [
    "geography/fetch_country_codes.py",
    "grid/fetch_owid_grid.py",
    "emission_factors/fetch_ipcc_defaults.py",
    "targets/fetch_climatewatch_ndc.py",
    "geography/fetch_map_geometry.py",
]
STEPS = [
    "geography/extract_country_codes.py",
    "grid/extract_owid_grid.py",
    "emission_factors/extract_emission_factors.py",
    "projects/extract_gem_tracker.py",
    "roles/extract_gem_ownership.py",
    "roles/extract_roles.py",
    "targets/extract_ndc_anchors.py",
    "targets/derive_power_rates.py",
    "model/build_reference_power.py",
    "model/build_ti_power.py",
    "model/aggregate_roles.py",
    "model/build_sensitivity_power.py",
    "model/build_database.py",
    "report/build_report.py",
]
CHECKS = [
    ("ruff check script tests", [PY, "-m", "ruff", "check", "script", "tests"]),
    ("pytest -q tests/test_power.py", [PY, "-m", "pytest", "-q", "tests/test_power.py"]),
]


def run(label: str, cmd: list[str]) -> int:
    """Run one step, print its status line and last output line, return its exit code."""
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).strip().splitlines()
    tail = out[-1] if out else ""
    status = {0: "ok  ", EXIT_HAND: "hand"}.get(proc.returncode, "FAIL")
    print(f"[{status}] {label:<48} {time.time() - t0:5.1f}s  {tail[:100]}")
    if proc.returncode == EXIT_HAND:
        print("\n".join("       " + line for line in out if line))
    elif proc.returncode:
        print("\n".join("       " + line for line in out[-25:]))
    return proc.returncode


def main() -> None:
    """Run fetchers (optional), extractors, derivations, model and checks in order."""
    steps = list(STEPS)
    if "--fetch" in sys.argv[1:]:
        steps = FETCH + steps
    for step in steps:
        code = run(step, [PY, str(HERE / step)])
        if code == EXIT_HAND:
            print(
                "\npipeline paused: a hand-gathered input is missing (see above and "
                "data/power/output/method.md, section 'Hand-gathered inputs')"
            )
            sys.exit(EXIT_HAND)
        if code:
            sys.exit(1)
    for label, cmd in CHECKS:
        if run(label, cmd):
            sys.exit(1)
    print("pipeline complete")


if __name__ == "__main__":
    main()
