"""Build the provider and licence catalogue for the automotive sources, ARCDW-style.

The sources register (``registry/sources.csv``) carries a free-text licence on every one of its
rows, which meant the same licence was written 20 different ways and a redistribution question had
no single answer. This lifts the licence out of the source row and into two normalised tables, the
way the Arc data-exchange layer keeps DATA_PROVIDER / DATASET / METHODOLOGY:

    registry/licences.csv        one row per distinct licence, with the verified canonical URL and
                                 a redistribution verdict for the raw file
                                 (open / derived_only / no)
    registry/data_providers.csv  one row per publishing organisation, pointing at its licence
    registry/sources.csv         gains a ``provider_id`` column, so a source resolves to a provider
                                 and thence to one licence — the licence has exactly one home

The redistribution verdict answers deliverable D-10: whether a raw file may be republished in the
open dataset. Processed outputs are always publishable — they are facts plus this project's own
method, not a republication of anyone's copyrighted table — so the verdict governs only the raw
drop. ``open`` may be republished with attribution; ``derived_only`` means only our transformation
may (UN Comtrade original bulk, JADA back series); ``no`` means the raw stays local (company IR
workbooks and press tables, whose numbers are facts we may state but whose files we may not host).

Run from the repository root:  .venv/bin/python script/auto/registry/build_catalog.py
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REG = REPO / "data" / "auto" / "registry"
ACCESSED = "2026-09-14"

#: licence_id -> (name, url, category, raw_redistribution, attribution, summary)
LICENCES = {
    "cc_by_4_0": (
        "Creative Commons Attribution 4.0 International",
        "https://creativecommons.org/licenses/by/4.0/",
        "open",
        "open",
        "yes",
        "Copy and redistribute in any medium, including commercially, with attribution.",
    ),
    "eurostat_reuse": (
        "European Commission reuse (Decision 2011/833/EU)",
        "https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Copyright/licence_policy",
        "open",
        "open",
        "yes",
        "Reproduction and dissemination, commercial or not, authorised provided Eurostat is "
        "acknowledged; editorial content under CC BY 4.0.",
    ),
    "eur_lex_reuse": (
        "European Union reuse of Commission documents (2011/833/EU)",
        "https://eur-lex.europa.eu/content/legal-notice/legal-notice.html",
        "open",
        "open",
        "yes",
        "Reuse of EU legal texts authorised with the source acknowledged; EU logos excepted.",
    ),
    "us_public_domain": (
        "US Government work, public domain (17 U.S.C. 105)",
        "https://www.usa.gov/government-works",
        "public_domain",
        "open",
        "cite",
        "A work of the US federal government carries no domestic copyright; free to reuse, "
        "the source is cited by convention rather than by licence.",
    ),
    "kogl_type_1": (
        "Korea Open Government Licence, Type 1",
        "https://www.kogl.or.kr/info/licenseTypeEn.do",
        "open",
        "open",
        "yes",
        "Use including commercial use and redistribution, with the source attributed.",
    ),
    "kr_public_data": (
        "data.go.kr public data (no use restriction, KOGL Type 1 equivalent)",
        "https://www.data.go.kr",
        "open",
        "open",
        "yes",
        "Public data released with no restriction on use; treated as KOGL Type 1, attribute.",
    ),
    "unfccc_public_domain": (
        "UNFCCC terms of use (official texts, public domain)",
        "https://unfccc.int/this-site/terms-of-use",
        "public_domain",
        "open",
        "yes",
        "Official UNFCCC texts, data and documents may be freely downloaded, copied and printed "
        "with no change to the content and the source acknowledged; other use needs authorisation.",
    ),
    "un_comtrade": (
        "UN Comtrade data use policy",
        "https://uncomtrade.org/docs/faqs-on-use-and-re-dissemination/",
        "conditional",
        "derived_only",
        "yes",
        "Transformed (derived) data is free of restriction to redistribute; re-dissemination of "
        "original data above 100,000 records requires a licence fee, so only our aggregates ship.",
    ),
    "odbl_1_0": (
        "Open Data Commons Open Database License 1.0",
        "https://opendatacommons.org/licenses/odbl/1-0/",
        "open_sharealike",
        "open",
        "yes",
        "Share, create and adapt with attribution and share-alike on the database.",
    ),
    "isc": (
        "ISC License",
        "https://opensource.org/license/isc-license-txt",
        "open",
        "open",
        "yes",
        "Permissive reuse and redistribution with the copyright notice retained; the underlying "
        "Natural Earth geometry is itself public domain.",
    ),
    "publisher_attribution": (
        "Publisher permits reproduction with attribution",
        "",
        "attribution",
        "open",
        "yes",
        "The publisher's own terms permit reproduction of the figures with attribution "
        "(IRENA publications; ifeu / Oeko-Institut report).",
    ),
    "jp_estat_terms": (
        "e-Stat / Japanese government standard terms of use",
        "https://www.e-stat.go.jp/en/terms-of-use",
        "open",
        "open",
        "yes",
        "Free use including reproduction and redistribution, commercial included, with the "
        "source shown (the Japanese government standard terms, compatible with CC BY 4.0).",
    ),
    "mlit_terms": (
        "MLIT website terms of use",
        "https://www.mlit.go.jp/link.html",
        "open",
        "open",
        "yes",
        "Free use with the source shown, following the Japanese government standard terms.",
    ),
    "jada_terms": (
        "JADA new-vehicle registration statistics",
        "https://www.jada.or.jp/data/",
        "conditional",
        "derived_only",
        "yes",
        "Current monthly tables are free to download; the back series is licensable, so only the "
        "extracted nameplate figures ship, not the source workbook.",
    ),
    "airia_terms": (
        "AIRIA statistics, attribution required",
        "https://www.airia.or.jp/publish/",
        "attribution",
        "open",
        "yes",
        "Free to use with the AIRIA source line shown.",
    ),
    "jp_gov_publication": (
        "Japanese government publication (GIO / NIES inventory)",
        "https://www.nies.go.jp/gio/en/",
        "attribution",
        "open",
        "yes",
        "National inventory published for public use; reproduce with the source acknowledged.",
    ),
    "kr_gov_publication": (
        "Korean government publication, attribution",
        "https://www.2050cnc.go.kr",
        "attribution",
        "open",
        "yes",
        "Government strategy and scenario documents published for public use; "
        "attribute the source.",
    ),
    "company_ir": (
        "Company investor-relations / press material, no explicit reuse licence",
        "",
        "restricted",
        "no",
        "cite",
        "The reported figures are facts this project may state and analyse, but the source "
        "workbook or press table carries no reuse licence and is not republished; it stays local.",
    ),
}

#: provider_id -> (name, type, website, licence_id)
PROVIDERS = {
    "eea": (
        "European Environment Agency",
        "Government agency",
        "https://www.eea.europa.eu",
        "cc_by_4_0",
    ),
    "eurostat": (
        "Eurostat",
        "Government agency",
        "https://ec.europa.eu/eurostat",
        "eurostat_reuse",
    ),
    "ec": ("European Commission", "Government", "https://commission.europa.eu", "eur_lex_reuse"),
    "eu": ("European Union (EUR-Lex)", "Government", "https://eur-lex.europa.eu", "eur_lex_reuse"),
    "owid": (
        "Our World in Data (Ember)",
        "Not-for-profit",
        "https://ourworldindata.org",
        "cc_by_4_0",
    ),
    "us_epa": (
        "US Environmental Protection Agency",
        "Government agency",
        "https://www.epa.gov",
        "us_public_domain",
    ),
    "us_nhtsa": (
        "US National Highway Traffic Safety Administration",
        "Government agency",
        "https://www.nhtsa.gov",
        "us_public_domain",
    ),
    "us_fhwa": (
        "US Federal Highway Administration",
        "Government agency",
        "https://highways.dot.gov",
        "us_public_domain",
    ),
    "abs": (
        "Australian Bureau of Statistics",
        "Government agency",
        "https://www.abs.gov.au",
        "cc_by_4_0",
    ),
    "dcceew": (
        "Australian Government DCCEEW",
        "Government",
        "https://www.dcceew.gov.au",
        "cc_by_4_0",
    ),
    "unsd": (
        "United Nations Statistics Division (Comtrade)",
        "IGO",
        "https://comtradeplus.un.org",
        "un_comtrade",
    ),
    "unfccc": ("UNFCCC", "IGO", "https://unfccc.int", "unfccc_public_domain"),
    "kr_2050cnc": (
        "2050 Carbon Neutrality and Green Growth Commission (Korea)",
        "Government",
        "https://www.2050cnc.go.kr",
        "kr_gov_publication",
    ),
    "kr_molit": (
        "Korea Ministry of Land, Infrastructure and Transport",
        "Government",
        "https://www.molit.go.kr",
        "kr_public_data",
    ),
    "kr_gir": (
        "Korea Greenhouse Gas Inventory and Research Center",
        "Government agency",
        "https://www.gir.go.kr",
        "kr_public_data",
    ),
    "kr_kotsa": (
        "Korea Transportation Safety Authority",
        "Government agency",
        "https://www.kotsa.or.kr",
        "kr_public_data",
    ),
    "kr_kea": (
        "Korea Energy Agency",
        "Government agency",
        "https://www.energy.or.kr",
        "kr_public_data",
    ),
    "kr_nier": (
        "Korea National Institute of Environmental Research",
        "Government agency",
        "https://www.nier.go.kr",
        "kr_public_data",
    ),
    "jp_gio": (
        "Greenhouse Gas Inventory Office of Japan (NIES)",
        "Government agency",
        "https://www.nies.go.jp",
        "jp_gov_publication",
    ),
    "jp_mlit": (
        "Japan Ministry of Land, Infrastructure, Transport and Tourism",
        "Government",
        "https://www.mlit.go.jp",
        "mlit_terms",
    ),
    "jp_estat": (
        "Japan e-Stat (Statistics Bureau)",
        "Government agency",
        "https://www.e-stat.go.jp",
        "jp_estat_terms",
    ),
    "jp_airia": (
        "Automobile Inspection and Registration Information Association",
        "Not-for-profit",
        "https://www.airia.or.jp",
        "airia_terms",
    ),
    "jp_jada": (
        "Japan Automobile Dealers Association",
        "Industry association",
        "https://www.jada.or.jp",
        "jada_terms",
    ),
    "irena": (
        "International Renewable Energy Agency",
        "IGO",
        "https://www.irena.org",
        "publisher_attribution",
    ),
    "ifeu": (
        "ifeu / Oeko-Institut",
        "Research institute",
        "https://www.ifeu.de",
        "publisher_attribution",
    ),
    "hyundai": ("Hyundai Motor Company", "Company", "https://www.hyundai.com", "company_ir"),
    "kia": ("Kia Corporation", "Company", "https://www.kia.com", "company_ir"),
    "toyota": ("Toyota Motor Corporation", "Company", "https://www.toyota.com", "company_ir"),
    "nissan": (
        "Nissan Motor Corporation",
        "Company",
        "https://www.nissan-global.com",
        "company_ir",
    ),
    "topojson": (
        "topojson / world-atlas (Natural Earth)",
        "Open-source project",
        "https://github.com/topojson/world-atlas",
        "isc",
    ),
    "mledoze": (
        "mledoze/world-countries",
        "Open-source project",
        "https://github.com/mledoze/countries",
        "odbl_1_0",
    ),
}

#: source_id -> provider_id
SOURCE_PROVIDER = {
    "eea_co2_monitoring_2024": "eea",
    "eea_obfcm_real_world_2022": "eea",
    "eurostat_road_eqs_carpda": "eurostat",
    "eurostat_road_tf_veh": "eurostat",
    "eurostat_road_tf_vehmov": "eurostat",
    "eurostat_road_eqs_carage": "eurostat",
    "eurostat_env_air_gge_crf1a3b1": "eurostat",
    "eurostat_env_air_gge_crf1a1a": "eurostat",
    "eurostat_env_air_gge_crf1a3": "eurostat",
    "eurostat_comext_ds045409": "eurostat",
    "owid_ember_grid_intensity": "owid",
    "epa_ghg_inventory_2025": "us_epa",
    "epa_ghg_inventory_2025_annexes": "us_epa",
    "epa_fuel_economy_label": "us_epa",
    "epa_fueleconomy_vehicles": "us_epa",
    "epa_automotive_trends_my2024": "us_epa",
    "epa_ghg_typical_vehicle": "us_epa",
    "epa_emission_factors_hub": "us_epa",
    "nhtsa_809952": "us_nhtsa",
    "fhwa_vm1_2023": "us_fhwa",
    "abs_motor_vehicle_census_2021": "abs",
    "abs_survey_motor_vehicle_use_2020": "abs",
    "anga_odata_paris_inventory": "dcceew",
    "un_comtrade_public": "unsd",
    "unfccc_ndc_registry": "unfccc",
    "kr_ndc_2035": "unfccc",
    "us_ndc_2035": "unfccc",
    "jp_ndc_2035_2040": "unfccc",
    "eu_climate_law_2021_1119": "eu",
    "ec_2040_com_2024_63": "ec",
    "ec_2040_impact_assessment_transport": "ec",
    "kr_basic_plan_2023": "kr_2050cnc",
    "kr_2050_scenarios_2021": "kr_2050cnc",
    "molit_vehicle_registration": "kr_molit",
    "gir_inventory_co2": "kr_gir",
    "kotsa_road_ghg_vehicle_type": "kr_kotsa",
    "kotsa_tmacs_vkm": "kr_kotsa",
    "kea_fuel_economy_labels": "kr_kea",
    "nier_manufacturer_fleet_co2": "kr_nier",
    "gio_nies_inventory": "jp_gio",
    "mlit_fuel_economy_list": "jp_mlit",
    "mlit_fuel_consumption_survey": "jp_estat",
    "airia_vehicle_age": "jp_airia",
    "jada_registration_statistics": "jp_jada",
    "irena_green_hydrogen_cost_2020": "irena",
    "ifeu_phev_2025": "ifeu",
    "hyundai_ir_sales_results": "hyundai",
    "kia_america_sales_by_month": "kia",
    "kia_ir_retail_sales": "kia",
    "tmna_us_sales_release": "toyota",
    "toyota_global_sales": "toyota",
    "nissan_us_sales_release": "nissan",
    "nissan_global_sales": "nissan",
    "world_atlas_110m": "topojson",
    "world_countries_codes": "mledoze",
}

LICENCE_FIELDS = [
    "licence_id",
    "licence_name",
    "url",
    "category",
    "raw_redistribution",
    "attribution",
    "summary",
    "verified_date",
]
PROVIDER_FIELDS = ["provider_id", "provider_name", "provider_type", "website", "licence_id"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    """Write the two catalogue tables and stamp provider_id onto every source."""
    write_csv(
        REG / "licences.csv",
        LICENCE_FIELDS,
        [
            {
                "licence_id": lid,
                "licence_name": n,
                "url": u,
                "category": cat,
                "raw_redistribution": rr,
                "attribution": att,
                "summary": s,
                "verified_date": ACCESSED,
            }
            for lid, (n, u, cat, rr, att, s) in LICENCES.items()
        ],
    )
    write_csv(
        REG / "data_providers.csv",
        PROVIDER_FIELDS,
        [
            {
                "provider_id": pid,
                "provider_name": n,
                "provider_type": ty,
                "website": w,
                "licence_id": lic,
            }
            for pid, (n, ty, w, lic) in PROVIDERS.items()
        ],
    )

    # validate the mapping is total and consistent
    for pid, (_n, _ty, _w, lic) in PROVIDERS.items():
        if lic not in LICENCES:
            raise SystemExit(f"provider {pid} points at unknown licence {lic}")
    sources = read_csv(REG / "sources.csv")
    ids = {r["source_id"] for r in sources}
    missing = ids - set(SOURCE_PROVIDER)
    if missing:
        raise SystemExit(f"sources with no provider mapping: {sorted(missing)}")
    unknown = {p for p in SOURCE_PROVIDER.values() if p not in PROVIDERS}
    if unknown:
        raise SystemExit(f"source map points at unknown providers: {sorted(unknown)}")

    fields = list(sources[0].keys())
    if "provider_id" not in fields:
        fields.insert(
            fields.index("license") if "license" in fields else len(fields), "provider_id"
        )
    for r in sources:
        r["provider_id"] = SOURCE_PROVIDER[r["source_id"]]
    write_csv(REG / "sources.csv", fields, sources)

    # D-10: resolve every raw file to a redistribution verdict through its source's provider.
    raw = read_csv(REG / "raw_files.csv")
    lic_of = {pid: lic for pid, (_n, _t, _w, lic) in PROVIDERS.items()}
    redis_rows = []
    for rf in raw:
        # a hand-transcribed anchor file may cite several sources; they share a provider, so
        # the first names it
        pid = SOURCE_PROVIDER.get(rf["source_id"].split(";")[0], "")
        lic = lic_of.get(pid, "")
        redis_rows.append(
            {
                "dataset": rf["dataset"],
                "file": rf["file"],
                "source_id": rf["source_id"],
                "provider_id": pid,
                "licence_id": lic,
                "raw_redistribution": LICENCES[lic][3] if lic else "unmapped",
                "url": LICENCES[lic][1] if lic else "",
            }
        )
    write_csv(
        REG / "redistribution.csv",
        ["dataset", "file", "source_id", "provider_id", "licence_id", "raw_redistribution", "url"],
        redis_rows,
    )

    print(f"licences.csv: {len(LICENCES)} licences")
    print(f"data_providers.csv: {len(PROVIDERS)} providers")
    print(f"sources.csv: provider_id set on {len(sources)} sources")
    # redistribution summary for D-10
    verdict = {}
    lic_of = {pid: lic for pid, (_n, _t, _w, lic) in PROVIDERS.items()}
    for r in sources:
        rr = LICENCES[lic_of[r["provider_id"]]][3]
        verdict[rr] = verdict.get(rr, 0) + 1
    print("raw redistribution (sources):", verdict)
    rv = {}
    for r in redis_rows:
        rv[r["raw_redistribution"]] = rv.get(r["raw_redistribution"], 0) + 1
    print(f"redistribution.csv: {len(redis_rows)} raw files ->", rv)


if __name__ == "__main__":
    main()
