# SPDX-License-Identifier: GPL-3.0-or-later
"""Column contracts, validation, and parsing helpers for the data workbook.

The workbook is a *template*: most cells are empty ("TO COLLECT"), some are textual
status markers ("FLAG: ...", "TO EXTRACT"). The helpers here turn that into typed,
``None``-tolerant values and never fabricate a default (see NOTES.md §5).
"""

from __future__ import annotations

from ti_framework.models import BenchmarkStatus, DataTier, Powertrain

# --- Sheet names -----------------------------------------------------------
SHEET_LAYER1 = "Layer1_NDC_benchmark"
SHEET_LAYER2 = "Layer2_vehicle_params"
SHEET_REG = "Registration_Vcv"
SHEET_LEVEL2 = "Level2_production"
SHEET_SUPPORT = "Support_params"

# --- Expected column headers (contract). Loader matches by header text, not index. ---
LAYER1_COLUMNS = [
    "Operating country",
    "Code",
    "Grid intensity G_c(0) gCO2/kWh (2024)",
    "NDC headline target",
    "Base yr",
    "Target yr",
    "Reduction low (frac)",
    "Reduction high (frac)",
    "Econ-wide rate low (%/yr)",
    "Econ-wide rate high (%/yr)",
    "r_fleet S1 (STEPS)",
    "r_fleet S2 (NDC)",
    "r_fleet S3 (NZE)",
    "r_power S1 (STEPS)",
    "r_power S2 (NDC)",
    "r_power S3 (NZE)",
    "Benchmark status",
    "Source",
]

LAYER2_COLUMNS = [
    "Brand",
    "Model",
    "Powertrain (BEV/PHEV/HEV/ICE)",
    "Segment",
    "EV efficiency (kWh/km)",
    "ICE emission intensity (gCO2/km)",
    "PHEV utility factor",
    "Real-world correction factor",
    "Source",
    "Tier (A/B/C)",
    "Status",
]

REG_COLUMNS = [
    "Operating country",
    "Code",
    "Year",
    "Brand",
    "Model",
    "Powertrain",
    "Units",
    "Segment",
    "Source DB",
    "Tier",
    "Status",
]

# Tokens that mean "not real data" when found in a cell.
_PLACEHOLDER_TOKENS = (
    "TO COLLECT",
    "TO EXTRACT",
    "FLAG",
    "N/A",
    "PENDING",
    "—",
    "-",
    "[",  # bracketed schema seeds like "[model]"
)


class SchemaError(ValueError):
    """Raised when a sheet's header row does not match the expected contract."""


def is_placeholder(value: object) -> bool:
    """True if a cell holds a status marker / seed rather than real data."""
    if value is None:
        return True
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return True
        up = s.upper()
        return any(tok in up for tok in _PLACEHOLDER_TOKENS)
    return False


def num(value: object) -> float | None:
    """Coerce a cell to float, returning None for placeholders / non-numerics."""
    if is_placeholder(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace("%", "")
        # a textual range like "53–61" is not a single value -> caller handles ranges
        try:
            return float(s)
        except ValueError:
            return None
    return None


def text(value: object) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def parse_tier(value: object) -> DataTier:
    s = text(value)
    if not s:
        return DataTier.UNKNOWN
    up = s.upper()[0]
    return {"A": DataTier.A, "B": DataTier.B, "C": DataTier.C}.get(up, DataTier.UNKNOWN)


def parse_powertrain(value: object) -> Powertrain | None:
    s = text(value)
    if not s or is_placeholder(value):
        return None
    up = s.upper()
    for pt in Powertrain:
        if pt.value in up:
            return pt
    return None


def parse_rate_fraction(value: object) -> float | None:
    """Normalise a reduction rate to a fraction/yr.

    Workbook rates are given as %/yr (e.g. 4.34 means 0.0434). Values already < 1 are
    treated as fractions and passed through. Heuristic logged by caller via the return.
    """
    v = num(value)
    if v is None:
        return None
    if v < 0:
        return None
    return v / 100.0 if v >= 1.0 else v


def parse_status(value: object) -> BenchmarkStatus:
    """Map the workbook 'Benchmark status' text to a BenchmarkStatus."""
    s = text(value)
    if not s:
        return BenchmarkStatus.COMPUTED
    up = s.upper()
    if "NO BENCHMARK" in up or "NO NDC" in up:
        return BenchmarkStatus.FLAG_NO_BENCHMARK
    if "INTENSITY" in up:
        return BenchmarkStatus.FLAG_INTENSITY
    if "BAU" in up:
        return BenchmarkStatus.FLAG_BAU
    if "BASELINE" in up:
        return BenchmarkStatus.FLAG_NO_BASELINE
    if "PEAK" in up:
        return BenchmarkStatus.FLAG_PEAK
    if up.startswith("FLAG"):
        return BenchmarkStatus.FLAG_NO_BENCHMARK
    return BenchmarkStatus.COMPUTED


FLAG_REASONS = {
    BenchmarkStatus.FLAG_NO_BENCHMARK: "No active NDC — no S2 benchmark derivable",
    BenchmarkStatus.FLAG_INTENSITY: "GDP-intensity target — not an absolute emissions path",
    BenchmarkStatus.FLAG_BAU: "Target vs BAU projection — no base-year level",
    BenchmarkStatus.FLAG_NO_BASELINE: "Absolute avoided target — no stated baseline",
    BenchmarkStatus.FLAG_PEAK: "Target vs undefined emissions peak",
}


def gco2_per_km_to_kg(value: float | None) -> float | None:
    return None if value is None else value / 1000.0


def gco2_per_kwh_to_kg(value: float | None) -> float | None:
    return None if value is None else value / 1000.0


def validate_headers(actual: list[object], expected: list[str], sheet: str) -> None:
    """Validate a header row against the expected contract (prefix match, tolerant of trailing)."""
    norm = [text(c) or "" for c in actual]
    for i, exp in enumerate(expected):
        if i >= len(norm) or norm[i].strip() != exp:
            got = norm[i] if i < len(norm) else "<missing>"
            raise SchemaError(
                f"Sheet '{sheet}' column {i}: expected '{exp}', got '{got}'. "
                "Workbook schema does not match the contract in io/schema.py."
            )
