#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Destination-market use, energy, and policy-pathway inputs for EU27 passenger cars.

This adapter closes the inputs that the Trade Impact calculation contract requires before a
lifetime result may be published: annual vehicle-kilometres, operating lifetime, fleet
service-intensity baseline, grid intensity, and the S1/S2/S3 fleet and power pathways.

Every published value is derived from a committed source snapshot. Nothing is defaulted: a
country that has no sourced value for an input keeps ``None`` and is reported as missing, and
every value carries the tier and the derivation that produced it.

Sources (all open, machine readable):
    Eurostat road_tf_veh       car traffic performance, million vehicle-km
    Eurostat road_tf_vehmov    road traffic performance fallback, million vehicle-km
    Eurostat road_eqs_carpda   passenger-car stock by motor energy
    Eurostat road_eqs_carage   passenger-car stock by age class
    Eurostat env_air_gge       GHG inventory by CRF source sector
    Ember / Our World in Data  electricity carbon intensity, gCO2/kWh

Refresh the snapshot with ``--refresh``; normal builds transform the committed file only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "data-pipeline" / "source-snapshots" / "destination_eu27_inputs.json"

EUROSTAT_API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
EUROSTAT_BROWSER = "https://ec.europa.eu/eurostat/databrowser/view/{ds}/default/table?lang=en"
OWID_GRID_CSV = (
    "https://ourworldindata.org/grapher/carbon-intensity-electricity.csv"
    "?v=1&csvType=full&useColumnShortNames=true"
)
OWID_GRID_PAGE = "https://ourworldindata.org/grapher/carbon-intensity-electricity"
EMBER_URL = "https://ember-energy.org/data/yearly-electricity-data/"
EU_CLIMATE_LAW_URL = "https://eur-lex.europa.eu/eli/reg/2021/1119/oj/eng"
EU_2040_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024DC0063"
EEA_REALWORLD_URL = "https://climate-energy.eea.europa.eu/topics/transport/real-world-emissions/data"
EEA_REALWORLD_NEWS_URL = (
    "https://climate.ec.europa.eu/news-other-reads/news/"
    "publication-real-world-co2-emissions-and-fuel-consumption-cars-and-vans-collected-2022-2024-07-26_en"
)

# Repo-wide country codes use the EEA registration convention (GR for Greece); Eurostat uses EL.
EU27 = (
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU",
    "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
)
_EUROSTAT_TO_REPO = {"EL": "GR"}
EU_AGGREGATE = "EU27_2020"
_ISO3_TO_REPO = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY", "CZE": "CZ",
    "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR", "DEU": "DE", "GRC": "GR",
    "HUN": "HU", "IRL": "IE", "ITA": "IT", "LVA": "LV", "LTU": "LT", "LUX": "LU",
    "MLT": "MT", "NLD": "NL", "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK",
    "SVN": "SI", "ESP": "ES", "SWE": "SE",
}

COHORT_YEAR = 2024
# Trend windows exclude 2020-2021: pandemic mobility and generation are not a policy trend.
TREND_START = 2015
TREND_EXCLUDE = (2020, 2021)
# Plausibility band for an annual per-car distance. A value outside it means the traffic series
# and the stock series describe different populations, so the tier ladder falls through.
VKT_MIN_KM, VKT_MAX_KM = 3_000.0, 30_000.0
# In-use fleet CO2 intensity outside this band means the inventory and the stock describe
# different populations - cross-border refuelling is the usual cause - so the value is flagged
# and tiered down rather than published as a clean country benchmark.
FLEET_INTENSITY_MIN, FLEET_INTENSITY_MAX = 80.0, 320.0
# Operating lifetime is bracketed by the observed mean age. For a fleet in steady state the mean
# operating life is at least the mean age (exponential scrappage) and at most twice it (every car
# retiring at the same age). The central value is the midpoint of that bracket.
LIFETIME_MIN_Y, LIFETIME_MAX_Y = 10, 25
LIFETIME_CENTRAL_MULTIPLE = 1.5
# Midpoints for the Eurostat age bands. The open top band is closed at 25 years, which is the
# assumption the derivation discloses (and the T +/- 3 sensitivity brackets).
_AGE_BAND_MIDPOINT = {"Y_LT2": 1.0, "Y2-5": 3.5, "Y5-10": 7.5, "Y10-20": 15.0, "Y_GT20": 25.0}

# EU climate framework anchors, used only where no sector-specific pathway value exists.
EU_2030_ECONOMY_REDUCTION = 0.55  # vs 1990, Regulation (EU) 2021/1119 Art. 4(1)
EU_2040_ECONOMY_REDUCTION = 0.90  # vs 1990, COM(2024) 63 recommended target
# EU domestic-transport pathway already published by the automotive adapter.
EU_TRANSPORT_BASE_2023_MT = 795.6
EU_TRANSPORT_TARGET_2030_MT = 583.0

# EEA real-world (OBFCM) gap, model year 2022 registrations.
REALWORLD_GAP = {"petrol": 0.211, "diesel": 0.171, "phev_relative": 3.14}


class SourceError(RuntimeError):
    """Raised when a remote source cannot be turned into the expected structure."""


def _sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "tradeimpact/0.1 source audit"})
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
        return response.read()


def _eurostat(dataset: str, **filters: str) -> dict[str, Any]:
    query = "&".join(f"{k}={v}" for k, v in filters.items())
    payload = json.loads(_fetch(f"{EUROSTAT_API}{dataset}?format=JSON&lang=EN&{query}"))
    if "value" not in payload or "dimension" not in payload:
        raise SourceError(f"eurostat {dataset}: unexpected payload")
    return payload


def flatten_jsonstat(payload: dict[str, Any]) -> dict[tuple[str, ...], float]:
    """Turn a JSON-stat 2.0 cube into {(dim value, ...): value} keyed in declared dimension order."""
    ids: list[str] = payload["id"]
    sizes: list[int] = payload["size"]
    inverse = [
        {pos: key for key, pos in payload["dimension"][name]["category"]["index"].items()}
        for name in ids
    ]
    out: dict[tuple[str, ...], float] = {}
    for position, value in payload["value"].items():
        remainder = int(position)
        key: list[str] = []
        for size, lookup in zip(reversed(sizes), reversed(inverse), strict=True):
            key.append(lookup[remainder % size])
            remainder //= size
        out[tuple(reversed(key))] = float(value)
    return out


def _series_by_country(
    payload: dict[str, Any], value_dims: dict[str, str]
) -> dict[str, dict[int, float]]:
    """Select one slice of a cube and return {repo country code: {year: value}}."""
    ids: list[str] = payload["id"]
    flat = flatten_jsonstat(payload)
    geo, time = ids.index("geo"), ids.index("time")
    wanted = {ids.index(dim): want for dim, want in value_dims.items() if dim in ids}
    out: dict[str, dict[int, float]] = {}
    for key, value in flat.items():
        if any(key[i] != want for i, want in wanted.items()):
            continue
        code = _EUROSTAT_TO_REPO.get(key[geo], key[geo])
        if code not in EU27:
            continue
        out.setdefault(code, {})[int(key[time])] = value
    return out


def refresh_snapshot(accessed_date: str, path: Path = SNAPSHOT) -> Path:
    """Fetch every remote source and commit one hash-pinned snapshot."""
    raw: dict[str, Any] = {
        "car_traffic_mio_vkm": _series_by_country(
            _eurostat(
                "road_tf_veh",
                vehicle="CAR", mot_nrg="TOTAL", regisveh="TER_REGNAT", unit="MIO_VKM",
                sinceTimePeriod=str(TREND_START),
            ),
            {},
        ),
        "car_traffic_fallback_mio_vkm": _series_by_country(
            _eurostat(
                "road_tf_vehmov",
                vehicle="CAR", regisveh="TERNAT_REG", unit="MIO_VKM",
                sinceTimePeriod=str(TREND_START),
            ),
            {},
        ),
        "car_stock": _series_by_country(
            _eurostat(
                "road_eqs_carpda",
                unit="NR", mot_nrg="TOTAL", leg_form="TOTAL", sinceTimePeriod=str(TREND_START),
            ),
            {},
        ),
        "car_co2_kt": _series_by_country(
            _eurostat(
                "env_air_gge",
                airpol="CO2", src_crf="CRF1A3B1", unit="THS_T", sinceTimePeriod=str(TREND_START),
            ),
            {},
        ),
        "grid_intensity_gco2_kwh": {},
        "car_age_bands": {},
        "eu_power_co2_kt": {},
    }

    # Age distribution: keep every band for the latest year each country reports.
    age = _eurostat("road_eqs_carage", unit="NR", sinceTimePeriod=str(TREND_START))
    ids = age["id"]
    geo, time, band = ids.index("geo"), ids.index("time"), ids.index("age")
    bands: dict[str, dict[int, dict[str, float]]] = {}
    for key, value in flatten_jsonstat(age).items():
        code = _EUROSTAT_TO_REPO.get(key[geo], key[geo])
        if code not in EU27 and code != EU_AGGREGATE:
            continue
        bands.setdefault(code, {}).setdefault(int(key[time]), {})[key[band]] = value
    raw["car_age_bands"] = bands

    # EU27 public electricity and heat production, for the pro-rata power pathway.
    power = _eurostat(
        "env_air_gge",
        airpol="CO2", src_crf="CRF1A1A", unit="THS_T", geo="EU27_2020", sinceTimePeriod="1990",
    )
    ids = power["id"]
    time = ids.index("time")
    raw["eu_power_co2_kt"] = {
        int(key[time]): value for key, value in flatten_jsonstat(power).items()
    }

    # EU27 domestic transport, 1990 baseline for the pro-rata 2040 transport pathway.
    transport = _eurostat(
        "env_air_gge",
        airpol="GHG", src_crf="CRF1A3", unit="MIO_T", geo="EU27_2020", sinceTimePeriod="1990",
    )
    ids = transport["id"]
    time = ids.index("time")
    raw["eu_transport_ghg_mt"] = {
        int(key[time]): value for key, value in flatten_jsonstat(transport).items()
    }

    # Grid intensity, Ember via Our World in Data.
    reader = csv.DictReader(io.StringIO(_fetch(OWID_GRID_CSV).decode()))
    grid: dict[str, dict[int, float]] = {}
    for row in reader:
        code = _ISO3_TO_REPO.get(row["code"])
        if not code:
            continue
        value = row["co2_intensity__gco2_kwh"]
        if value:
            grid.setdefault(code, {})[int(row["year"])] = float(value)
    raw["grid_intensity_gco2_kwh"] = grid

    snapshot = {
        "accessed_date": accessed_date,
        "cohort_year": COHORT_YEAR,
        "raw": raw,
        "raw_sha256": _sha256(raw),
    }
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    return path


# --- derivations -----------------------------------------------------------------


def _latest(series: dict[int, float] | dict[str, float], not_after: int) -> tuple[int, float] | None:
    pairs = [(int(y), v) for y, v in series.items() if int(y) <= not_after]
    return max(pairs) if pairs else None


def log_linear_rate(series: dict[int, float], not_after: int) -> tuple[float, int, int] | None:
    """Fit ln(value) = a + b*year and return (decline fraction/yr, first year, last year).

    A positive result means the quantity is falling, matching the engine's ``r`` convention.
    """
    points = [
        (int(y), v)
        for y, v in series.items()
        if TREND_START <= int(y) <= not_after and int(y) not in TREND_EXCLUDE and v > 0
    ]
    if len(points) < 4:
        return None
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(math.log(v) for _, v in points) / n
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    sxy = sum((x - mean_x) * (math.log(v) - mean_y) for x, v in points)
    if sxx == 0:
        return None
    slope = sxy / sxx
    return (1.0 - math.exp(slope), min(x for x, _ in points), max(x for x, _ in points))


def cagr_decline(base: float, target: float, years: int) -> float:
    """Annual decline fraction taking ``base`` to ``target`` over ``years``."""
    if base <= 0 or target <= 0 or years <= 0:
        raise SourceError("cannot derive a decline rate from non-positive values")
    return 1.0 - (target / base) ** (1.0 / years)


def _mean_age(by_year: dict[str, dict[str, float]], not_after: int) -> tuple[float, int] | None:
    """Stock-weighted mean car age from the latest year that reports the whole age partition.

    A year that reports only some bands is skipped rather than renormalised: the missing band is
    not empty, it is merged into a neighbouring one, and treating it as zero biases the mean down.
    """
    candidates = sorted(
        (int(year) for year, bands in by_year.items() if _AGE_BAND_MIDPOINT.keys() <= bands.keys()),
        reverse=True,
    )
    for year in candidates:
        if year > not_after + 1:  # the stock series is published one year ahead of the cohort
            continue
        bands = by_year[str(year)]
        weighted = sum(midpoint * bands[band] for band, midpoint in _AGE_BAND_MIDPOINT.items())
        total = sum(bands[band] for band in _AGE_BAND_MIDPOINT)
        if total > 0:
            return weighted / total, year
    return None


def _pooled_age_distribution(
    all_bands: dict[str, dict[str, dict[str, float]]], not_after: int
) -> dict[str, dict[str, float]] | None:
    """Sum the age bands of every member state that publishes the whole partition.

    Eurostat publishes no EU-wide age distribution, so the stand-in for a country that reports
    only a stock total is the pooled distribution of the countries that do report it.
    """
    per_year: dict[int, dict[str, float]] = {}
    contributors: dict[int, int] = {}
    for code, by_year in all_bands.items():
        if code not in EU27:
            continue
        for year, bands in by_year.items():
            if not _AGE_BAND_MIDPOINT.keys() <= bands.keys() or int(year) > not_after + 1:
                continue
            bucket = per_year.setdefault(int(year), dict.fromkeys(_AGE_BAND_MIDPOINT, 0.0))
            for band in _AGE_BAND_MIDPOINT:
                bucket[band] += bands[band]
            contributors[int(year)] = contributors.get(int(year), 0) + 1
    usable = [y for y, n in contributors.items() if n >= 15]
    if not usable:
        return None
    year = max(usable)
    return {str(year): per_year[year]}


def _vkt_for(code: str, raw: dict[str, Any], stock: float | None) -> dict[str, Any] | None:
    """Annual km per registered car from the one traffic series whose population matches.

    Only ``road_tf_veh`` with ``TER_REGNAT`` is used: traffic performed *by vehicles registered
    in the reporting country*, which is the same population as the stock denominator. The other
    published series counts traffic *on the national territory by any vehicle*, including
    foreign ones, so dividing it by the national stock mixes two populations. Where both exist
    they disagree by up to two orders of magnitude, so the mismatched series is not a lower
    tier of the same measurement — it is a different one, and it is not used at all.
    """
    if not stock:
        return None
    series = raw["car_traffic_mio_vkm"].get(code)
    found = _latest(series, COHORT_YEAR) if series else None
    if found is None:
        return None
    year, mio_vkm = found
    vkt = mio_vkm * 1e6 / stock
    if not VKT_MIN_KM <= vkt <= VKT_MAX_KM:
        return None
    return {
        "value": vkt,
        "tier": "A" if year >= COHORT_YEAR - 2 else "B",
        "year": year,
        "derivation": (
            "Eurostat road_tf_veh (TER_REGNAT) car vehicle-kilometres divided by the "
            "registered car stock of the same year."
        ),
    }


def _eu_average_vkt(rows: list[dict[str, Any]]) -> float | None:
    """Stock-weighted EU average over countries that resolved a measured distance."""
    numerator = sum(r["vkt_km"] * r["car_stock"] for r in rows if r["vkt_km"] and r["car_stock"])
    denominator = sum(r["car_stock"] for r in rows if r["vkt_km"] and r["car_stock"])
    return numerator / denominator if denominator else None


def _observed_vkt_quantiles(rows: list[dict[str, Any]]) -> tuple[float, float] | None:
    """Lower and upper quartile of the measured distances, used as the proxy's honest band.

    The proxy stands in for markets that publish nothing. The spread of the markets that do
    publish is the only evidence available about how wrong it can be, so it becomes the band
    rather than an invented percentage.
    """
    measured = sorted(r["vkt_km"] for r in rows if r["vkt_km"] and r["car_stock"])
    if len(measured) < 4:
        return None

    def quantile(q: float) -> float:
        position = q * (len(measured) - 1)
        low = int(position)
        high = min(low + 1, len(measured) - 1)
        return measured[low] + (measured[high] - measured[low]) * (position - low)

    return quantile(0.25), quantile(0.75)


def build_records(path: Path = SNAPSHOT) -> dict[str, list[dict[str, Any]]]:
    """Transform the committed snapshot into destination-input records and their sources."""
    snapshot = json.loads(path.read_text())
    if snapshot["raw_sha256"] != _sha256(snapshot["raw"]):
        raise SourceError("destination snapshot hash mismatch")
    raw = snapshot["raw"]
    accessed = snapshot["accessed_date"]

    # --- EU-level pathway rates ---------------------------------------------------
    transport_mt = {int(y): v for y, v in raw["eu_transport_ghg_mt"].items()}
    power_kt = {int(y): v for y, v in raw["eu_power_co2_kt"].items()}
    if 1990 not in transport_mt or 1990 not in power_kt:
        raise SourceError("EU 1990 baseline missing from the inventory snapshot")
    power_base = _latest(power_kt, COHORT_YEAR)
    if power_base is None:
        raise SourceError("EU power-sector inventory has no recent observation")
    power_year, power_now = power_base

    r_fleet_s2 = cagr_decline(EU_TRANSPORT_BASE_2023_MT, EU_TRANSPORT_TARGET_2030_MT, 2030 - 2023)
    transport_2040 = transport_mt[1990] * (1.0 - EU_2040_ECONOMY_REDUCTION)
    r_fleet_s3 = cagr_decline(EU_TRANSPORT_BASE_2023_MT, transport_2040, 2040 - 2023)
    r_power_s2_raw = cagr_decline(
        power_now, power_kt[1990] * (1.0 - EU_2030_ECONOMY_REDUCTION), 2030 - power_year
    )
    r_power_s3 = cagr_decline(
        power_now, power_kt[1990] * (1.0 - EU_2040_ECONOMY_REDUCTION), 2040 - power_year
    )
    # A negative rate means the sector has already passed its pro-rata target. Committing the
    # benchmark to *rise* back up to that target would flatter every electrified product, so the
    # pathway is held flat instead and the condition is published rather than hidden.
    pathway_flags: list[str] = []
    r_power_s2 = r_power_s2_raw
    if r_power_s2_raw <= 0:
        r_power_s2 = 0.0
        pathway_flags.append(
            f"PATHWAY_ALREADY_MET: EU public electricity and heat CO2 in {power_year} "
            f"({power_now / 1000:.0f} MtCO2) is already below the pro-rata 2030 level "
            f"({power_kt[1990] * (1.0 - EU_2030_ECONOMY_REDUCTION) / 1000:.0f} MtCO2). The implied "
            f"rate is {r_power_s2_raw:+.4f}/yr; S2 grid intensity is held flat at the observed "
            "level instead of being allowed to rise."
        )

    # --- per-country records ------------------------------------------------------
    pooled_age = _pooled_age_distribution(raw["car_age_bands"], COHORT_YEAR)
    rows: list[dict[str, Any]] = []
    for code in EU27:
        stock_found = _latest(raw["car_stock"].get(code, {}), COHORT_YEAR)
        stock = stock_found[1] if stock_found else None
        vkt = _vkt_for(code, raw, stock)

        co2_found = _latest(raw["car_co2_kt"].get(code, {}), COHORT_YEAR)
        grid_found = _latest(raw["grid_intensity_gco2_kwh"].get(code, {}), COHORT_YEAR)

        age = _mean_age(raw["car_age_bands"].get(code, {}), COHORT_YEAR)
        age_tier = "A"
        if age is None and pooled_age is not None:
            age = _mean_age(pooled_age, COHORT_YEAR)
            age_tier = "C"  # pooled EU distribution stands in for an unreported country
        elif age[1] < COHORT_YEAR - 2:
            age_tier = "B"  # the country's own distribution, but not a recent vintage
        mean_age, age_year = age if age else (None, None)

        # Per-car CO2 is the observable that the benchmark is anchored on: it needs no distance.
        per_car_co2: dict[int, float] = {}
        for year, value in raw["car_co2_kt"].get(code, {}).items():
            year = int(year)
            car_stock = raw["car_stock"].get(code, {}).get(str(year))
            if car_stock:
                per_car_co2[year] = value * 1e9 / car_stock  # gCO2 per car per year
        fleet_trend = log_linear_rate(per_car_co2, COHORT_YEAR)
        grid_trend = log_linear_rate(
            {int(y): v for y, v in raw["grid_intensity_gco2_kwh"].get(code, {}).items()},
            COHORT_YEAR,
        )

        rows.append(
            {
                "country_code": code,
                "car_stock": stock,
                "car_stock_year": stock_found[0] if stock_found else None,
                "car_co2_kt": co2_found[1] if co2_found else None,
                "car_co2_year": co2_found[0] if co2_found else None,
                "vkt_km": vkt["value"] if vkt else None,
                "vkt_tier": vkt["tier"] if vkt else None,
                "vkt_year": vkt["year"] if vkt else None,
                "vkt_derivation": vkt["derivation"] if vkt else None,
                "grid_intensity_gco2_kwh": grid_found[1] if grid_found else None,
                "grid_intensity_year": grid_found[0] if grid_found else None,
                "mean_car_age_years": mean_age,
                "mean_car_age_year": age_year,
                "mean_car_age_tier": age_tier,
                "_fleet_trend": fleet_trend,
                "_grid_trend": grid_trend,
            }
        )

    fallback_vkt = _eu_average_vkt(rows)
    fallback_band = _observed_vkt_quantiles(rows)
    for row in rows:
        row["vkt_low"] = row["vkt_high"] = None
        if row["vkt_km"] is None and fallback_vkt is not None:
            row["vkt_km"] = fallback_vkt
            row["vkt_low"], row["vkt_high"] = fallback_band or (None, None)
            row["vkt_tier"] = "C"
            row["vkt_year"] = COHORT_YEAR
            row["vkt_derivation"] = (
                "EU average distance per registered car, stock-weighted over the member states "
                "that publish a matching traffic series. No national series is available. Those "
                "states skew to higher-mileage western markets, so this proxy is likely an "
                "over-estimate for the lower-income markets it stands in for, which pushes their "
                "product-side emissions up and their contribution down."
            )

    destination_inputs: list[dict[str, Any]] = []
    for row in rows:
        fleet_trend = row.pop("_fleet_trend")
        grid_trend = row.pop("_grid_trend")
        stock, vkt, co2_kt = row["car_stock"], row["vkt_km"], row["car_co2_kt"]

        fleet_intensity = None
        warnings: list[str] = list(pathway_flags)
        if stock and vkt and co2_kt is not None:
            fleet_intensity = co2_kt * 1e9 / (stock * vkt)  # gCO2 per km
        fleet_tier = "A" if row["vkt_tier"] == "A" else (row["vkt_tier"] or "C")
        if fleet_intensity is not None and not (
            FLEET_INTENSITY_MIN <= fleet_intensity <= FLEET_INTENSITY_MAX
        ):
            fleet_tier = "C"
            warnings.append(
                f"FLEET_INTENSITY_IMPLAUSIBLE: {fleet_intensity:.0f} gCO2/km is outside "
                f"{FLEET_INTENSITY_MIN:.0f}-{FLEET_INTENSITY_MAX:.0f}. The national car CO2 "
                "inventory and the registered stock cover different driving populations "
                "(cross-border refuelling), so this benchmark is tiered down to C."
            )
        if row["vkt_tier"] == "C":
            warnings.append(
                "VKT_PROXY: no national car traffic series is published, so the EU average "
                "distance per car is used. The benchmark side is unaffected (distance cancels "
                "in CO2 per car); the product side scales directly with this proxy."
            )

        lifetime = lifetime_low = lifetime_high = None
        if row["mean_car_age_years"]:
            def _clamp(years: float) -> int:
                return int(min(LIFETIME_MAX_Y, max(LIFETIME_MIN_Y, round(years))))

            mean_age = row["mean_car_age_years"]
            lifetime = _clamp(LIFETIME_CENTRAL_MULTIPLE * mean_age)
            lifetime_low = _clamp(mean_age)
            lifetime_high = _clamp(2 * mean_age)

        missing = [
            name
            for name, value in (
                ("annual vehicle-kilometres", vkt),
                ("fleet service-intensity baseline", fleet_intensity),
                ("grid intensity", row["grid_intensity_gco2_kwh"]),
                ("operating lifetime", lifetime),
                ("observed fleet trend (S1)", fleet_trend),
                ("observed grid trend (S1)", grid_trend),
            )
            if value is None
        ]

        destination_inputs.append(
            {
                "country_code": row["country_code"],
                "cohort_year": COHORT_YEAR,
                "vkt_km_per_year": vkt,
                "vkt_low_km_per_year": row["vkt_low"],
                "vkt_high_km_per_year": row["vkt_high"],
                "vkt_tier": row["vkt_tier"],
                "vkt_reference_year": row["vkt_year"],
                "vkt_derivation": row["vkt_derivation"],
                "car_stock": stock,
                "car_stock_reference_year": row["car_stock_year"],
                "car_co2_kt": co2_kt,
                "car_co2_reference_year": row["car_co2_year"],
                "fleet_intensity_base_gco2_per_km": fleet_intensity,
                "fleet_intensity_derivation": (
                    "Eurostat CRF 1.A.3.b.i car CO2 divided by the registered car stock and the "
                    "annual distance per car. It is an in-use fleet average, not a type-approval "
                    "value, so it is directly comparable with the certified product intensity "
                    "only after the real-world correction is applied to the product side."
                ),
                "fleet_intensity_tier": fleet_tier,
                "warnings": warnings,
                "grid_intensity_gco2_per_kwh": row["grid_intensity_gco2_kwh"],
                "grid_intensity_reference_year": row["grid_intensity_year"],
                "grid_intensity_tier": "A",
                "operating_lifetime_years": lifetime,
                "operating_lifetime_low_years": lifetime_low,
                "operating_lifetime_high_years": lifetime_high,
                "mean_car_age_years": row["mean_car_age_years"],
                "operating_lifetime_derivation": (
                    "Bracketed by the stock-weighted mean age from Eurostat road_eqs_carage. In "
                    "steady state the mean operating life is at least the mean age (exponential "
                    "scrappage) and at most twice it (a single retirement age); the published "
                    "central value is the midpoint and the bracket is carried into sensitivity. "
                    "The open top age band is closed at 25 years."
                    + (
                        ""
                        if row["mean_car_age_tier"] == "A"
                        else " This country publishes no complete age partition, so the EU27 "
                        "distribution stands in and the input is tiered down."
                    )
                ),
                "operating_lifetime_tier": "B" if row["mean_car_age_tier"] == "A" else "C",
                "mean_car_age_reference_year": row["mean_car_age_year"],
                "r_fleet_s1": fleet_trend[0] if fleet_trend else None,
                "r_fleet_s1_window": (
                    f"{fleet_trend[1]}-{fleet_trend[2]} excluding {TREND_EXCLUDE[0]}-{TREND_EXCLUDE[1]}"
                    if fleet_trend
                    else None
                ),
                "r_fleet_s2": r_fleet_s2,
                "r_fleet_s3": r_fleet_s3,
                "r_power_s1": grid_trend[0] if grid_trend else None,
                "r_power_s1_window": (
                    f"{grid_trend[1]}-{grid_trend[2]} excluding {TREND_EXCLUDE[0]}-{TREND_EXCLUDE[1]}"
                    if grid_trend
                    else None
                ),
                "r_power_s2": r_power_s2,
                "r_power_s3": r_power_s3,
                "prorata_used": "yes",
                "target_level": 3,
                "missing_required_inputs": missing,
                "source_ids": [
                    "eurostat-road-tf-veh",
                    "eurostat-road-eqs-carpda",
                    "eurostat-road-eqs-carage",
                    "eurostat-env-air-gge-crf",
                    "ember-owid-grid-intensity",
                    "eu-climate-law-2021-1119",
                    "ec-2040-impact-assessment-transport-pathway",
                ],
            }
        )

    pathway_notes = {
        "r_fleet_s1": (
            "Observed national trend in CO2 per registered car, log-linear over "
            f"{TREND_START}-{COHORT_YEAR} excluding {TREND_EXCLUDE[0]}-{TREND_EXCLUDE[1]}. It is an "
            "outturn, not a policy commitment."
        ),
        "r_fleet_s2": (
            "EU domestic-transport pathway, 795.6 MtCO2e in 2023 to 583 MtCO2e in 2030 "
            f"({r_fleet_s2:.4f}/yr). Regional sector proxy: it covers all domestic transport, not "
            "passenger cars alone, and is applied to every member state."
        ),
        "r_fleet_s3": (
            "EU domestic transport held to the recommended economy-wide 2040 target of -90% "
            f"against 1990 ({r_fleet_s3:.4f}/yr). Pro-rata: no transport sub-target exists."
        ),
        "r_power_s1": (
            "Observed national trend in electricity carbon intensity, log-linear over "
            f"{TREND_START}-{COHORT_YEAR} excluding {TREND_EXCLUDE[0]}-{TREND_EXCLUDE[1]}. "
            "Independently sourced from the fleet trend, so r_fleet != r_power by construction."
        ),
        "r_power_s2": (
            "EU public electricity and heat production held to the binding economy-wide 2030 "
            f"target of -55% against 1990 ({r_power_s2:.4f}/yr). Pro-rata, and applied to grid "
            "intensity under constant generation, which understates decarbonisation if demand "
            "grows: the resulting BEV benefit is conservative."
        ),
        "r_power_s3": (
            "The same pro-rata construction against the recommended 2040 target of -90% "
            f"({r_power_s3:.4f}/yr)."
        ),
    }

    sources = [
        {
            "source_id": "eurostat-road-tf-veh",
            "title": "Road traffic performance by vehicle category (road_tf_veh, road_tf_vehmov)",
            "publisher": "Eurostat",
            "url": EUROSTAT_BROWSER.format(ds="road_tf_veh"),
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": accessed,
            "license": "Eurostat reuse policy applies",
            "snapshot_sha256": snapshot["raw_sha256"],
            "notes": "Million vehicle-kilometres by passenger cars; the denominator of the "
            "distance-per-car derivation.",
        },
        {
            "source_id": "eurostat-road-eqs-carpda",
            "title": "Passenger cars by type of motor energy (road_eqs_carpda)",
            "publisher": "Eurostat",
            "url": EUROSTAT_BROWSER.format(ds="road_eqs_carpda"),
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": accessed,
            "license": "Eurostat reuse policy applies",
            "notes": "Registered passenger-car stock per country.",
        },
        {
            "source_id": "eurostat-road-eqs-carage",
            "title": "Passenger cars by age (road_eqs_carage)",
            "publisher": "Eurostat",
            "url": EUROSTAT_BROWSER.format(ds="road_eqs_carage"),
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": accessed,
            "license": "Eurostat reuse policy applies",
            "notes": "Age-class distribution behind the operating-lifetime derivation.",
        },
        {
            "source_id": "eurostat-env-air-gge-crf",
            "title": "Greenhouse gas emissions by source sector (env_air_gge), CRF 1.A.3.b.i and 1.A.1.a",
            "publisher": "Eurostat",
            "url": EUROSTAT_BROWSER.format(ds="env_air_gge"),
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": accessed,
            "license": "Eurostat reuse policy applies",
            "notes": "National inventory CO2 from cars and from public electricity and heat "
            "production, used for the fleet baseline and the power pathway.",
        },
        {
            "source_id": "ember-owid-grid-intensity",
            "title": "Carbon intensity of electricity generation",
            "publisher": "Ember, via Our World in Data",
            "url": OWID_GRID_PAGE,
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": accessed,
            "license": "Ember CC-BY-4.0; Our World in Data CC-BY",
            "notes": f"Country-level gCO2/kWh. Primary compilation: {EMBER_URL}. Regional averages "
            "are never substituted for a country value.",
        },
        {
            "source_id": "eu-climate-law-2021-1119",
            "title": "Regulation (EU) 2021/1119 (European Climate Law) and COM(2024) 63",
            "publisher": "European Union",
            "url": EU_CLIMATE_LAW_URL,
            "evidence_class": "official_primary",
            "published_date": None,
            "accessed_date": accessed,
            "license": "EUR-Lex reuse notice applies",
            "notes": f"-55% by 2030 and the recommended -90% by 2040 ({EU_2040_URL}), used only "
            "for the pro-rata pathways that have no sector sub-target.",
        },
        {
            "source_id": "eea-real-world-obfcm",
            "title": "Real-world CO2 emissions and fuel consumption of cars and vans",
            "publisher": "European Environment Agency / European Commission",
            "url": EEA_REALWORLD_URL,
            "evidence_class": "official_primary",
            "published_date": "2024-07-26",
            "accessed_date": accessed,
            "license": "EEA reuse policy applies",
            "notes": "On-board monitoring gap for model-year 2022 registrations: petrol "
            f"{REALWORLD_GAP['petrol']:.1%}, diesel {REALWORLD_GAP['diesel']:.1%}, PHEV "
            f"{REALWORLD_GAP['phev_relative']:.2f}x the type-approval value. "
            f"Announcement: {EEA_REALWORLD_NEWS_URL}",
        },
    ]

    return {
        "destination_inputs": destination_inputs,
        "sources": sources,
        "pathway_notes": [
            {"rate": key, "note": value} for key, value in sorted(pathway_notes.items())
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="refresh the committed snapshot")
    parser.add_argument("--accessed-date", default="2026-08-09")
    args = parser.parse_args()
    if args.refresh:
        refresh_snapshot(accessed_date=args.accessed_date)
    records = build_records()
    rows = records["destination_inputs"]
    complete = [r for r in rows if not r["missing_required_inputs"]]
    print(
        f"destination_eu adapter: {len(rows)} countries, {len(complete)} input-complete, "
        f"{len(records['sources'])} sources"
    )
    for row in rows:
        if row["missing_required_inputs"]:
            print(f"  {row['country_code']}: missing {', '.join(row['missing_required_inputs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
