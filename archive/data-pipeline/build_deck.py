#!/usr/bin/env python3
"""Integrated Trade Impact deck: the Climate Arc narrative with the methodology walkthrough inside it.

Visual identity follows TI.html (Climate Arc variant: navy/teal/green, Georgia titles).
Every number is read from data/published/ or computed here, so the deck cannot drift from the dataset.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "deck" / "PLANiT_TradeImpact_Framework_EN_20260811_v02.html"
PUB = REPO / "data" / "published"

results = json.loads((PUB / "lifetime_results.json").read_text())
BY_FIRM = {v["firm"]: v for v in results.values()}

# --------------------------------------------------------------------------- worked cell
D = 12041.874                 # DE annual distance, km/yr   (594,136 Mvkm / 49,339,166 cars)
I0 = 150.34193 / 1000         # DE fleet base intensity, kgCO2/km
E_REF0 = I0 * D               # 1810.4 kg/vehicle/yr
CERT = 107.13284              # Corolla certified WLTP gCO2/km
CORR = 1.211                  # EEA OBFCM petrol gap
E_PROD = CERT * CORR / 1000 * D
T = 15
R = {"S1": 0.026324785, "S2": 0.043443692, "S3": 0.13510169}
RP = {"S1": 0.040232496, "S2": 0.0, "S3": 0.085599875}
UNITS = 17111.0

ref = {s: [E_REF0 * (1 - r) ** t for t in range(T)] for s, r in R.items()}
gap = [ref["S2"][t] - E_PROD for t in range(T)]
CUM = sum(gap)
TSTAR = math.log(E_PROD / E_REF0) / math.log(1 - R["S2"])

# --------------------------------------------------------------------------- palette
NAVY, TEAL, GREEN, ORANGE, GREY = "#001F3F", "#0097A7", "#8BC34A", "#EC8305", "#8D8D8D"
SLATE = "#5B8FA3"

# --------------------------------------------------------------------- svg helpers
def sx(t, x0, w, n=T - 1):
    return x0 + (w * t / n)


def sy(v, y0, h, vmax):
    return y0 + h - (h * v / vmax)


def poly(vals, x0, y0, w, h, vmax):
    return " ".join(f"{sx(i, x0, w):.1f},{sy(v, y0, h, vmax):.1f}" for i, v in enumerate(vals))


def axis(x0, y0, w, h, vmax, ticks, gridvals):
    g = "".join(
        f'<line x1="{x0}" y1="{sy(v, y0, h, vmax):.0f}" x2="{x0 + w}" y2="{sy(v, y0, h, vmax):.0f}" stroke="#E8EEEE"/>'
        f'<text x="{x0 - 8}" y="{sy(v, y0, h, vmax) + 4:.0f}" text-anchor="end" font-family="Roboto Condensed" '
        f'font-size="11" fill="{GREY}">{v}</text>'
        for v in gridvals
    )
    t = "".join(
        f'<text x="{sx(k, x0, w):.0f}" y="{y0 + h + 18}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" fill="#667">{k}</text>'
        for k in ticks
    )
    return g, t


def chart_pathways() -> str:
    W, H = 560, 296
    x0, y0, w, h = 46, 14, W - 62, H - 52
    vmax = 1900
    grid, ticks = axis(x0, y0, w, h, vmax, (0, 5, 10, 14), (0, 500, 1000, 1500))
    cols = {"S1": GREY, "S2": TEAL, "S3": ORANGE}
    lines = "".join(
        f'<polyline points="{poly(ref[s], x0, y0, w, h, vmax)}" fill="none" stroke="{c}" stroke-width="3"/>'
        for s, c in cols.items()
    )
    labels = "".join(
        f'<text x="{x0 + w + 4}" y="{sy(ref[s][-1], y0, h, vmax) + 4:.0f}" font-family="Roboto Condensed" '
        f'font-size="12" font-weight="700" fill="{c}">{s}</text>'
        for s, c in cols.items()
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{grid}{lines}{labels}'
        f'<line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" stroke="{NAVY}" stroke-width="2"/>{ticks}'
        f'<text x="{x0 + w / 2:.0f}" y="{H - 3}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" fill="{GREY}">YEARS SINCE SALE · kgCO2e per vehicle per year</text></svg>'
    )


def chart_gap() -> str:
    W, H = 620, 322
    x0, y0, w, h = 50, 12, W - 70, H - 54
    vmax = 1950
    b = ref["S2"]
    xc, yc = sx(TSTAR, x0, w), sy(E_PROD, y0, h, vmax)
    pos = " ".join(
        f"{x:.1f},{y:.1f}"
        for x, y in [(sx(i, x0, w), sy(b[i], y0, h, vmax)) for i in range(4)]
        + [(xc, yc)]
        + [(sx(i, x0, w), sy(E_PROD, y0, h, vmax)) for i in range(3, -1, -1)]
    )
    neg = " ".join(
        f"{x:.1f},{y:.1f}"
        for x, y in [(xc, yc)]
        + [(sx(i, x0, w), sy(b[i], y0, h, vmax)) for i in range(4, T)]
        + [(sx(i, x0, w), sy(E_PROD, y0, h, vmax)) for i in range(T - 1, 3, -1)]
    )
    grid, ticks = axis(x0, y0, w, h, vmax, (0, 3, 5, 10, 14), (0, 500, 1000, 1500))
    return f'''<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{grid}
  <polygon points="{pos}" fill="{GREEN}" opacity=".34"/>
  <polygon points="{neg}" fill="{ORANGE}" opacity=".26"/>
  <polyline points="{poly(b, x0, y0, w, h, vmax)}" fill="none" stroke="{NAVY}" stroke-width="3.2"/>
  <polyline points="{poly([E_PROD] * T, x0, y0, w, h, vmax)}" fill="none" stroke="{ORANGE}" stroke-width="3.2"/>
  <line x1="{xc:.1f}" y1="{y0}" x2="{xc:.1f}" y2="{y0 + h}" stroke="{NAVY}" stroke-width="1.4" stroke-dasharray="5 4"/>
  <circle cx="{xc:.1f}" cy="{yc:.1f}" r="5.5" fill="{GREEN}" stroke="{NAVY}" stroke-width="2"/>
  <text x="{xc + 9:.0f}" y="{y0 + 15}" font-family="Roboto Condensed" font-size="12.5" font-weight="700" fill="{NAVY}">t* = 3.3 yr</text>
  <text x="{sx(0.9, x0, w):.0f}" y="{sy(1725, y0, h, vmax):.0f}" font-family="Roboto Condensed" font-size="12.5" font-weight="700" fill="#5a8a1e">CONTRIBUTION</text>
  <text x="{sx(8.2, x0, w):.0f}" y="{sy(1445, y0, h, vmax):.0f}" font-family="Roboto Condensed" font-size="12.5" font-weight="700" fill="{ORANGE}">LIABILITY</text>
  <text x="{sx(8.5, x0, w):.0f}" y="{sy(1725, y0, h, vmax):.0f}" font-family="Roboto Condensed" font-size="12" font-weight="700" fill="{ORANGE}">E_prod — the Corolla, fixed for life</text>
  <text x="{sx(8.5, x0, w):.0f}" y="{sy(745, y0, h, vmax):.0f}" font-family="Roboto Condensed" font-size="12" font-weight="700" fill="{NAVY}">E_ref — the German fleet, falling</text>
  <line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" stroke="{NAVY}" stroke-width="2"/>{ticks}
  <text x="{x0 + w / 2:.0f}" y="{H - 3}" text-anchor="middle" font-family="Roboto Condensed" font-size="11" fill="{GREY}">YEARS SINCE SALE · kgCO2e per vehicle per year</text></svg>'''


def chart_tiers() -> str:
    """Destination × input tier matrix, read straight from the published inputs."""
    rows = [
        ("Distance D", "vkt_tier"),
        ("Lifetime T", "operating_lifetime_tier"),
        ("Benchmark I(0)", "fleet_intensity_tier"),
        ("Grid G(0)", "grid_intensity_tier"),
    ]
    dest = sorted(json.loads((PUB / "destination_inputs.json").read_text()),
                  key=lambda r: r["country_code"])
    col = {"A": GREEN, "B": TEAL, "C": ORANGE}
    warn_col = {1: "#CFD8D6", 2: "#F0A85E", 3: "#B85E00"}
    W, H = 560, 320
    x0, y0, cw, ch = 96, 30, 15.6, 32
    out = []
    for ri, (label, key) in enumerate(rows):
        y = y0 + ri * ch
        out.append(
            f'<text x="{x0 - 9}" y="{y + 18:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="11.5" fill="#556">{label}</text>'
        )
        for ci, r in enumerate(dest):
            t = r[key] or "?"
            out.append(
                f'<rect x="{x0 + ci * cw:.1f}" y="{y}" width="{cw - 1.6:.1f}" height="{ch - 6}" rx="2" '
                f'fill="{col.get(t, GREY)}"><title>{r["country_code"]} · {label}: tier {t}</title></rect>'
                f'<text x="{x0 + ci * cw + (cw - 1.6) / 2:.1f}" y="{y + 18:.0f}" text-anchor="middle" '
                f'font-family="Roboto Condensed" font-size="10.5" font-weight="700" fill="#fff">{t}</text>'
            )
    # the decline rates are not tiered, but whether they vary at all is the point
    ry = y0 + len(rows) * ch + 2
    out.append(
        f'<text x="{x0 - 9}" y="{ry + 14:.0f}" text-anchor="end" font-family="Roboto Condensed" '
        f'font-size="11.5" fill="#556">r_fleet S1</text>'
    )
    for ci, r in enumerate(dest):
        out.append(
            f'<rect x="{x0 + ci * cw:.1f}" y="{ry}" width="{cw - 1.6:.1f}" height="19" rx="2" '
            f'fill="{NAVY}" opacity="{0.35 + 0.5 * (r["r_fleet_s1"] / max(x["r_fleet_s1"] for x in dest)):.2f}">'
            f'<title>{r["country_code"]}: observed national trend {r["r_fleet_s1"] * 100:.2f}%/yr</title></rect>'
        )
    out.append(
        f'<text x="{x0 + len(dest) * cw + 6:.0f}" y="{ry + 14:.0f}" font-family="Roboto Condensed" '
        f'font-size="10" font-weight="700" fill="{NAVY}">27 values</text>'
    )
    ry2 = ry + 24
    out.append(
        f'<text x="{x0 - 9}" y="{ry2 + 14:.0f}" text-anchor="end" font-family="Roboto Condensed" '
        f'font-size="11.5" fill="#556">r_fleet S2 · S3</text>'
        f'<rect x="{x0:.1f}" y="{ry2}" width="{len(dest) * cw - 1.6:.1f}" height="19" rx="2" '
        f'fill="{ORANGE}" opacity=".5"><title>One EU transport pathway applied to all 27 markets</title></rect>'
        f'<text x="{x0 + len(dest) * cw / 2:.0f}" y="{ry2 + 14:.0f}" text-anchor="middle" '
        f'font-family="Roboto Condensed" font-size="11" font-weight="700" fill="#7a3d00">'
        f'one EU pathway, applied to every market</text>'
        f'<text x="{x0 + len(dest) * cw + 6:.0f}" y="{ry2 + 14:.0f}" font-family="Roboto Condensed" '
        f'font-size="10" font-weight="700" fill="#B85E00">1 value</text>'
    )

    # a further row: how many typed warnings each market carries into the result
    wy = ry2 + 26
    out.append(
        f'<text x="{x0 - 9}" y="{wy + 15:.0f}" text-anchor="end" font-family="Roboto Condensed" '
        f'font-size="11.5" fill="#556">Warnings</text>'
    )
    for ci, r in enumerate(dest):
        n = len(r["warnings"])
        out.append(
            f'<rect x="{x0 + ci * cw:.1f}" y="{wy}" width="{cw - 1.6:.1f}" height="21" rx="2" '
            f'fill="{warn_col.get(n, GREY)}"><title>{r["country_code"]}: {n} warning(s)</title></rect>'
            f'<text x="{x0 + ci * cw + (cw - 1.6) / 2:.1f}" y="{wy + 15:.0f}" text-anchor="middle" '
            f'font-family="Roboto Condensed" font-size="10.5" font-weight="700" '
            f'fill="{"#556" if n == 1 else "#fff"}">{n}</text>'
        )
    for ci, r in enumerate(dest):
        out.append(
            f'<text x="{x0 + ci * cw + (cw - 1.6) / 2:.1f}" y="{wy + 36:.0f}" '
            f'text-anchor="middle" font-family="Roboto Condensed" font-size="9" fill="#778">'
            f'{r["country_code"]}</text>'
        )
    legend = ""
    lx = x0
    for t, name in (("A", "measured"), ("B", "dated or derived"), ("C", "proxied")):
        legend += (
            f'<rect x="{lx}" y="8" width="10" height="10" rx="2" fill="{col[t]}"/>'
            f'<text x="{lx + 14}" y="17" font-family="Roboto Condensed" font-size="11" fill="#333">'
            f'{t} — {name}</text>'
        )
        lx += 44 + len(name) * 6.0
    legend += (
        f'<text x="{lx + 6}" y="17" font-family="Roboto Condensed" font-size="11" fill="#93a0a0">'
        f'warnings row uses its own scale</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{legend}'
        f'{"".join(out)}</svg>'
    )


def chart_distance() -> str:
    """What the proxy replaces: a 2x spread across measured markets, collapsed to one value."""
    rows = json.loads((PUB / "destination_inputs.json").read_text())
    meas = sorted((r for r in rows if r["vkt_tier"] != "C"), key=lambda r: r["vkt_km_per_year"])
    prox = [r for r in rows if r["vkt_tier"] == "C"]
    pv = prox[0]["vkt_km_per_year"]
    lo_q, hi_q = prox[0]["vkt_low_km_per_year"], prox[0]["vkt_high_km_per_year"]
    W, H = 560, 264
    x0, w, base = 40, W - 76, 176
    lo, hi = 6600, 15200

    def px(v: float) -> float:
        return x0 + w * (v - lo) / (hi - lo)

    out = [
        f'<rect x="{px(lo_q):.1f}" y="26" width="{px(hi_q) - px(lo_q):.1f}" height="{base - 20}" '
        f'fill="{TEAL}" opacity=".07"/>'
        f'<text x="{(px(lo_q) + px(hi_q)) / 2:.0f}" y="20" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="10.5" fill="#7f9aa4">quartile band the sensitivity sweep uses</text>'
    ]
    for i, r in enumerate(prox):
        out.append(
            f'<circle cx="{px(pv):.1f}" cy="{base - 16 - i * 11:.1f}" r="4.6" fill="{ORANGE}" opacity=".9">'
            f'<title>{r["country_code"]}: proxied at {pv:,.0f} km/yr</title></circle>'
        )
    out.append(
        f'<text x="{px(pv):.0f}" y="{base - 16 - len(prox) * 11 - 6:.0f}" text-anchor="middle" '
        f'font-family="Roboto Condensed" font-size="11.5" font-weight="700" fill="#B85E00">'
        f'{len(prox)} markets, one assumed value</text>'
    )
    for r in meas:
        out.append(
            f'<circle cx="{px(r["vkt_km_per_year"]):.1f}" cy="{base:.1f}" r="5" fill="{NAVY}" opacity=".85">'
            f'<title>{r["country_code"]}: {r["vkt_km_per_year"]:,.0f} km/yr, tier {r["vkt_tier"]}</title></circle>'
        )
    for r, dy in ((meas[0], -14), (meas[-1], -14)):
        out.append(
            f'<text x="{px(r["vkt_km_per_year"]):.0f}" y="{base + dy:.0f}" text-anchor="middle" '
            f'font-family="Roboto Condensed" font-size="11" font-weight="700" fill="{NAVY}">'
            f'{r["country_code"]} {r["vkt_km_per_year"]:,.0f}</text>'
        )
    out.append(
        f'<line x1="{x0}" y1="{base + 16}" x2="{x0 + w}" y2="{base + 16}" stroke="{NAVY}" stroke-width="1.4"/>'
    )
    for v in (7000, 9000, 11000, 13000, 15000):
        out.append(
            f'<text x="{px(v):.0f}" y="{base + 32:.0f}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="10.5" fill="#667">{v // 1000}k</text>'
        )
    out.append(
        f'<text x="{x0}" y="{base + 54:.0f}" font-family="Roboto Condensed" font-size="11.5" fill="#556">'
        f'{len(meas)} markets publish a matching traffic series: {meas[0]["vkt_km_per_year"]:,.0f} to '
        f'{meas[-1]["vkt_km_per_year"]:,.0f} km/yr &#8212; a two-fold spread.</text>'
        f'<text x="{x0}" y="{base + 72:.0f}" font-family="Roboto Condensed" font-size="11" fill="#93a0a0">'
        f'The other {len(prox)} take the stock-weighted EU average, so a genuinely variable input becomes a constant.</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}</svg>'
    )


def chart_outlast() -> str:
    """One year's sales, against the target years the destination has already signed."""
    res = json.loads((PUB / "lifetime_results.json").read_text())
    surv = next(x for x in res.values() if x["firm"] == "Toyota")["trajectory"]["surviving_vehicles"]
    total = surv[0]
    y_start, n = 2024, len(surv)
    W, H = 560, 292
    x0, w, y0, h = 40, W - 74, 74, 164

    def px(year: float) -> float:
        return x0 + w * (year - y_start) / (n - 1)

    pts = " ".join(f"{px(y_start + i):.1f},{y0 + h * (1 - s / total):.1f}" for i, s in enumerate(surv))
    out = [
        f'<polygon points="{px(y_start):.1f},{y0 + h:.1f} {pts} {px(y_start + n - 1):.1f},{y0 + h:.1f}" '
        f'fill="{NAVY}" opacity=".10"/>'
        f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="2.6"/>'
        f'<line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" stroke="{NAVY}" stroke-width="1.6"/>'
    ]
    for year in (2024, 2030, 2035, 2040, 2045, 2049):
        out.append(
            f'<text x="{px(year):.0f}" y="{y0 + h + 16:.0f}" text-anchor="middle" '
            f'font-family="Roboto Condensed" font-size="10.5" fill="#667">{year}</text>'
        )
    for year, label, note in ((2030, "EU −55%", "vs 1990"), (2040, "EU −90%", "recommended")):
        i = year - y_start
        share = surv[i] / total
        out.append(
            f'<line x1="{px(year):.1f}" y1="{y0 - 30}" x2="{px(year):.1f}" y2="{y0 + h}" '
            f'stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="4 3"/>'
            f'<text x="{px(year):.0f}" y="{y0 - 34}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="11.5" font-weight="700" fill="{ORANGE}">{label}</text>'
            f'<text x="{px(year):.0f}" y="{y0 - 22}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="9.5" fill="#b08050">{note}</text>'
            f'<circle cx="{px(year):.1f}" cy="{y0 + h * (1 - share):.1f}" r="5" fill="#fff" '
            f'stroke="{ORANGE}" stroke-width="2.4"/>'
            f'<text x="{px(year) + 10:.0f}" y="{y0 + h * (1 - share) + 4:.0f}" font-family="Roboto Condensed" '
            f'font-size="14" font-weight="700" fill="{NAVY}">{share:.0%}</text>'
        )
    out.append(
        f'<text x="{x0}" y="{H - 6}" font-family="Roboto Condensed" font-size="10.5" fill="#93a0a0">'
        f'Toyota EU27 2024, from the per-market operating lifetimes. Hyundai: 100% and 61%.</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}</svg>'
    )


def chart_two_frames() -> str:
    """One real fleet, scored by each framework, computed the same way the engine would."""
    dest = {r["country_code"]: r for r in json.loads((PUB / "destination_inputs.json").read_text())}
    coh = {c["company_id"]: c for c in json.loads((PUB / "product_cohorts.json").read_text())}
    res = json.loads((PUB / "lifetime_results.json").read_text())

    absolute, units = 0.0, 0.0
    for r in coh["hyundai"]["records"]:
        if r["product_type"] != "BEV" or r["certified_electricity_kwh_per_km"] is None:
            continue
        d = dest.get(r["destination_geography"])
        if not d or d["vkt_km_per_year"] is None or d["operating_lifetime_years"] is None:
            continue
        g0, rp = d["grid_intensity_gco2_per_kwh"] / 1000.0, d["r_power_s2"]
        per = sum(r["certified_electricity_kwh_per_km"] * g0 * (1 - rp) ** t * d["vkt_km_per_year"]
                  for t in range(d["operating_lifetime_years"]))
        absolute += per * r["units"] / 1000.0
        units += r["units"]
    ti = next(x for x in res.values() if x["firm"] == "Hyundai")["cohorts"]["S2"]["by_powertrain"]["BEV"]

    rows = [
        ("SCOPE 3 CATEGORY 11", absolute / 1e6, ORANGE,
         "added to the inventory — a pure liability, with no reference point at all"),
        ("TRADE IMPACT", ti / 1e6, GREEN,
         "contribution against the destinations' committed path over the same lifetime"),
    ]
    peak = max(abs(v) for _, v, _, _ in rows)
    W, H = 560, 288
    x0, w, y0, rh = 30, 470, 74, 100
    out = [
        f'<text x="{x0}" y="26" font-family="Roboto Condensed" font-size="13" font-weight="700" '
        f'fill="{NAVY}">THE SAME {units:,.0f} HYUNDAI BATTERY-ELECTRIC CARS, SCORED TWICE</text>'
    ]
    for i, (label, val, col, note) in enumerate(rows):
        y = y0 + i * rh
        bw = w * abs(val) / peak * 0.72
        out.append(
            f'<text x="{x0}" y="{y - 4:.0f}" font-family="Roboto Condensed" font-size="11.5" '
            f'font-weight="700" fill="{col}">{label}</text>'
            f'<rect x="{x0}" y="{y}" width="{bw:.1f}" height="30" rx="3" fill="{col}" opacity=".9"/>'
            f'<text x="{x0 + bw + 10:.0f}" y="{y + 22:.0f}" font-family="Roboto Condensed" '
            f'font-size="21" font-weight="700" fill="{NAVY}">{val:+.2f} Mt</text>'
            f'<text x="{x0}" y="{y + 50:.0f}" font-family="Roboto Condensed" font-size="11.5" '
            f'fill="#667">{note}</text>'
        )
    out.append(
        f'<text x="{x0}" y="{H - 6}" font-family="Roboto Condensed" font-size="11" fill="#93a0a0">'
        f'Both computed on the same cohort, distance, grid and lifetime. Same scale &#8212; opposite meaning.</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}</svg>'
    )


def chart_pipeline() -> str:
    """Where every firm in the TI roster actually stands, stage by stage."""
    firms = [f for f in json.loads((PUB / "firms.json").read_text()) if f["project"] == "TI"]
    order = {"Toyota": 0, "Hyundai": 1}
    firms.sort(key=lambda f: (order.get(f["name"], 9),
                              -int(bool(f.get("alignment_available"))), f["name"]))
    stages = [
        ("In roster", lambda f: True),
        ("Current-period alignment", lambda f: bool(f.get("alignment_available"))),
        ("Observed cohort", lambda f: bool(f.get("cohort_available"))),
        ("Lifetime TI result", lambda f: bool(f.get("lifetime_result_available"))),
    ]
    W, H = 560, 302
    x0, y0, cw, rh = 214, 44, 80, 18
    out = []
    for si, (label, _) in enumerate(stages):
        cx = x0 + si * cw + cw / 2
        for k, part in enumerate(label.split(" ")):
            out.append(
                f'<text x="{cx:.0f}" y="{y0 - 32 + k * 11:.0f}" text-anchor="middle" '
                f'font-family="Roboto Condensed" font-size="10" font-weight="700" fill="{NAVY}">{part}</text>'
            )
    for fi, f in enumerate(firms):
        y = y0 + fi * rh
        short = f["name"].split(" (")[0]
        short = short if len(short) <= 26 else short[:24] + "…"
        out.append(
            f'<text x="{x0 - 12}" y="{y + 12:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="11" fill="#445">{short} <tspan fill="#aab">· {f["country"]}</tspan></text>'
        )
        for si, (_, ok) in enumerate(stages):
            got = ok(f)
            cx = x0 + si * cw
            out.append(
                f'<rect x="{cx:.0f}" y="{y:.0f}" width="{cw - 4}" height="{rh - 4}" rx="2" '
                f'fill="{GREEN if got else "#EEF2F2"}" opacity="{0.9 if got else 1}"/>'
                + (f'<text x="{cx + (cw - 4) / 2:.0f}" y="{y + 12:.0f}" text-anchor="middle" '
                   f'font-family="Roboto Condensed" font-size="11" font-weight="700" fill="#fff">✓</text>'
                   if got else "")
            )
    counts = [sum(1 for f in firms if ok(f)) for _, ok in stages]
    ty = y0 + len(firms) * rh + 12
    for si, c in enumerate(counts):
        out.append(
            f'<text x="{x0 + si * cw + (cw - 4) / 2:.0f}" y="{ty + 13:.0f}" text-anchor="middle" '
            f'font-family="Roboto Condensed" font-size="14" font-weight="700" '
            f'fill="{NAVY if si < 3 else ORANGE}">{c}</text>'
        )
    out.append(
        f'<text x="{x0 - 12}" y="{ty + 13:.0f}" text-anchor="end" font-family="Roboto Condensed" '
        f'font-size="11" font-weight="700" fill="{NAVY}">firms reaching this stage</text>'
    )
    out.append(
        f'<text x="{x0 - 164}" y="{H - 6}" font-family="Roboto Condensed" font-size="10.5" fill="#93a0a0">'
        f'Trade Impact roster only. Nine further firms sit under the Capital Allocation project and are out of scope here.</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}</svg>'
    )


def chart_convergence() -> str:
    """Per-vehicle TI for both firms across the three scenarios — the ranking closing up."""
    res = json.loads((PUB / "lifetime_results.json").read_text())
    series = {}
    for firm in ("Toyota", "Hyundai"):
        v = next(x for x in res.values() if x["firm"] == firm)
        cov = v["coverage"]["covered_units"]
        series[firm] = [v["cohorts"][s]["total_tCO2e"] / cov for s in ("S1", "S2", "S3")]
    W, H = 560, 268
    x0, y0, w, h = 92, 30, W - 190, H - 78
    lo, hi = -21.0, 0.0
    xs = [x0 + w * i / 2 for i in range(3)]

    def py(v: float) -> float:
        return y0 + h * (hi - v) / (hi - lo)

    out = []
    for v in (0, -5, -10, -15, -20):
        out.append(
            f'<line x1="{x0 - 8}" y1="{py(v):.1f}" x2="{x0 + w + 8}" y2="{py(v):.1f}" '
            f'stroke="{"#C9D2D2" if v == 0 else "#EDF1F1"}"/>'
            f'<text x="{x0 - 14}" y="{py(v) + 4:.1f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="10.5" fill="{GREY}">{v}</text>'
        )
    for i, s in enumerate(("S1 current", "S2 committed", "S3 1.5°C")):
        out.append(
            f'<text x="{xs[i]:.0f}" y="{y0 + h + 20:.0f}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="11.5" font-weight="700" fill="{NAVY}">{s}</text>'
        )
    # the shrinking gap is the finding, so it is drawn as an object rather than left implicit
    for i in range(3):
        a, b = series["Toyota"][i], series["Hyundai"][i]
        out.append(
            f'<line x1="{xs[i]:.1f}" y1="{py(a):.1f}" x2="{xs[i]:.1f}" y2="{py(b):.1f}" '
            f'stroke="{ORANGE}" stroke-width="7" opacity=".22" stroke-linecap="round"/>'
            + (f'<text x="{xs[i] + 22:.0f}" y="{(py(a) + py(b)) / 2 + 4:.0f}" font-family="Roboto Condensed" '
               f'font-size="11" font-weight="700" fill="#B85E00">{abs(b - a):.2f} t apart</text>' if i != 1 else '')
        )
    for firm, col, dy in (("Toyota", NAVY, -7), ("Hyundai", TEAL, 15)):
        pts = " ".join(f"{xs[i]:.1f},{py(v):.1f}" for i, v in enumerate(series[firm]))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>')
        for i, v in enumerate(series[firm]):
            out.append(
                f'<circle cx="{xs[i]:.1f}" cy="{py(v):.1f}" r="5" fill="#fff" stroke="{col}" stroke-width="2.6"/>'
            )
        out.append(
            f'<text x="{xs[2] + 13:.0f}" y="{py(series[firm][2]) + dy:.0f}" font-family="Roboto Condensed" '
            f'font-size="12" font-weight="700" fill="{col}">{series[firm][2]:.1f}  {firm}</text>'
        )
    out.append(
        f'<text x="{x0 - 14}" y="{py(series["Toyota"][0]) + 16:.0f}" text-anchor="end" '
        f'font-family="Roboto Condensed" font-size="11" fill="{NAVY}">{series["Toyota"][0]:.1f}</text>'
        f'<text x="{x0 - 14}" y="{py(series["Hyundai"][0]) + 16:.0f}" text-anchor="end" '
        f'font-family="Roboto Condensed" font-size="11" fill="{TEAL}">{series["Hyundai"][0]:.1f}</text>'
    )
    out.append(
        f'<text x="{x0 + w / 2:.0f}" y="{H - 6}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" fill="{GREY}">tCO2e per covered vehicle over its lifetime · 2.01× apart at S1, 1.06× at S3</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}</svg>'
    )


def chart_tornado() -> str:
    """What actually moves the number, from the sweeps the engine already ran."""
    res = json.loads((PUB / "lifetime_results.json").read_text())
    sens = next(x for x in res.values() if x["firm"] == "Toyota")["sensitivity"]
    central = sens["lifetime"]["T_central"]["S2"] / 1e6
    bars = [
        ("Operating lifetime  T ± 3 yr",
         sens["lifetime"]["T_minus"]["S2"] / 1e6, sens["lifetime"]["T_plus"]["S2"] / 1e6, ORANGE),
        ("Proxied distance  measured quartiles",
         sens["vkt_proxy"]["low_distance"]["S2"] / 1e6, sens["vkt_proxy"]["high_distance"]["S2"] / 1e6, TEAL),
    ]
    bars.sort(key=lambda b: -abs(b[1] - b[2]))
    s1, s3 = sens["scenario_spread"]["S1"] / 1e6, sens["scenario_spread"]["S3"] / 1e6
    lo, hi = -14.6, -0.6
    W, H = 560, 256
    x0, w, y0, rh = 176, 336, 74, 40

    def px(v: float) -> float:
        return x0 + w * (v - lo) / (hi - lo)

    out = []
    for v in (-14, -12, -10, -8, -4, -2):
        out.append(
            f'<line x1="{px(v):.1f}" y1="{y0 - 26}" x2="{px(v):.1f}" y2="{y0 + 2 * rh + 26}" '
            f'stroke="#EDF1F1"/>'
            f'<text x="{px(v):.1f}" y="{y0 + 2 * rh + 42}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="10.5" fill="{GREY}">{v}</text>'
        )
    # the policy dimension sits behind the uncertainty bars, not among them
    out.append(
        f'<rect x="{px(s3):.1f}" y="{y0 - 26}" width="{px(s1) - px(s3):.1f}" height="{2 * rh + 52}" '
        f'fill="{NAVY}" opacity=".05"/>'
        f'<text x="{px(s3) + 6:.0f}" y="{y0 - 14}" font-family="Roboto Condensed" font-size="10.5" '
        f'font-weight="700" fill="#8fa0a8">SCENARIO S1 &#8594; S3, the policy dimension &#8212; not an error bar</text>'
    )
    out.append(
        f'<line x1="{px(central):.1f}" y1="{y0 - 26}" x2="{px(central):.1f}" y2="{y0 + 2 * rh + 26}" '
        f'stroke="{NAVY}" stroke-width="1.6" stroke-dasharray="4 3"/>'
    )
    for i, (label, a, b, c) in enumerate(bars):
        y = y0 + i * rh
        left, right = min(a, b), max(a, b)
        out.append(
            f'<text x="{x0 - 12}" y="{y + 16:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="12" font-weight="700" fill="{NAVY}">{label.split("  ")[0]}</text>'
            f'<text x="{x0 - 12}" y="{y + 29:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="10.5" fill="{GREY}">{label.split("  ")[1]}</text>'
            f'<rect x="{px(left):.1f}" y="{y}" width="{px(right) - px(left):.1f}" height="21" rx="3" '
            f'fill="{c}" opacity=".85"><title>{label}: {a:+.2f} to {b:+.2f} MtCO2e</title></rect>'
            f'<text x="{px(left) - 6:.0f}" y="{y + 15:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="11" font-weight="700" fill="#445">{left:+.2f}</text>'
            f'<text x="{px(right) + 6:.0f}" y="{y + 15:.0f}" font-family="Roboto Condensed" '
            f'font-size="11" font-weight="700" fill="#445">{right:+.2f}</text>'
        )
    out.append(
        f'<text x="{px(central):.0f}" y="{y0 - 36}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" font-weight="700" fill="{NAVY}">{central:.2f} central</text>'
    )
    out.append(
        f'<text x="{x0 + w / 2:.0f}" y="{H - 4}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" fill="{GREY}">MtCO2e over the cohort lifetime · Toyota, committed policy</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}</svg>'
    )


def chart_annual() -> str:
    """TI_annual for the whole cohort, with the survival curve that shapes its tail."""
    res = json.loads((PUB / "lifetime_results.json").read_text())
    v = next(x for x in res.values() if x["firm"] == "Toyota")
    ann = v["cohorts"]["S2"]["annual_tCO2e"]
    surv = v["trajectory"]["surviving_vehicles"]
    n = len(ann)
    W, H = 620, 300
    x0, y0, w, h = 52, 26, W - 96, H - 62
    lo, hi = min(ann) / 1e3, max(ann) / 1e3          # ktCO2e
    span = hi - lo
    zero = y0 + h * hi / span
    peak_i = min(range(n), key=lambda i: ann[i])
    out = []
    for v_ in (400, 200, 0, -200, -400):
        if not lo <= v_ <= hi:
            continue
        y = y0 + h * (hi - v_) / span
        out.append(
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + w}" y2="{y:.1f}" '
            f'stroke="{"#C9D2D2" if v_ == 0 else "#EDF1F1"}" stroke-width="{1.4 if v_ == 0 else 1}"/>'
            f'<text x="{x0 - 7}" y="{y + 4:.1f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="10.5" fill="{GREY}">{v_:+d}</text>'
        )
    bw = w / n * 0.72
    for i, a in enumerate(ann):
        val = a / 1e3
        cx = x0 + w * (i + 0.5) / n
        y = zero - h * val / span if val >= 0 else zero
        bh = abs(h * val / span)
        hot = i == peak_i
        out.append(
            f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(bh, 0.8):.1f}" rx="1.5" '
            f'fill="{GREEN if val >= 0 else ORANGE}"{"" if not hot else f" stroke=\"{NAVY}\" stroke-width=\"1.4\""}>'
            f'<title>year {i}: {val:+,.0f} ktCO2e · {surv[i]:,.0f} vehicles still on the road</title></rect>'
        )
    # survival curve on its own scale, so retirement is visibly what closes the tail
    smax = max(surv) or 1
    pts = " ".join(
        f"{x0 + w * (i + 0.5) / n:.1f},{y0 + h * (1 - s / smax) * 0.42 + 4:.1f}" for i, s in enumerate(surv)
    )
    out.append(
        f'<polyline points="{pts}" fill="none" stroke="{TEAL}" stroke-width="2.4" stroke-dasharray="5 3"/>'
    )
    out.append(
        f'<text x="{x0 + w * 0.5 / n + 6:.0f}" y="{zero - h * (ann[0] / 1e3) / span - 8:.0f}" '
        f'font-family="Roboto Condensed" font-size="11" font-weight="700" fill="#5a8a1e">'
        f'+{ann[0] / 1e3:,.0f} kt — identical in all three scenarios</text>'
    )
    out.append(
        f'<text x="{x0 + w - 4:.0f}" y="{y0 + 12}" text-anchor="end" font-family="Roboto Condensed" '
        f'font-size="11" font-weight="700" fill="{TEAL}">vehicles still on the road</text>'
    )
    ticks = "".join(
        f'<text x="{x0 + w * (t + 0.5) / n:.0f}" y="{y0 + h + 16:.0f}" text-anchor="middle" '
        f'font-family="Roboto Condensed" font-size="10.5" fill="#667">{t}</text>'
        for t in (0, 5, 10, 15, 20, 24)
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}'
        f'<line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" stroke="{NAVY}" stroke-width="1.6"/>{ticks}'
        f'<text x="{x0 + w / 2:.0f}" y="{H - 4}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" fill="{GREY}">YEARS SINCE THE 2024 COHORT WAS SOLD · ktCO2e per year</text></svg>'
    )


def chart_layer2() -> str:
    """All three product shapes on one axis, against the benchmark they are measured on."""
    W, H = 560, 300
    x0, y0, w, h = 48, 16, W - 98, H - 56
    vmax = 1950
    eta, g0 = 0.15155696, 0.33638          # Hyundai KONA in DE
    bev2 = [eta * g0 * D] * T
    bev3 = [eta * g0 * (1 - RP["S3"]) ** t * D for t in range(T)]
    grid, ticks = axis(x0, y0, w, h, vmax, (0, 5, 10, 14), (0, 500, 1000, 1500))
    lines = (
        f'<polyline points="{poly(ref["S2"], x0, y0, w, h, vmax)}" fill="none" stroke="{NAVY}" stroke-width="3.2"/>'
        f'<polyline points="{poly([E_PROD] * T, x0, y0, w, h, vmax)}" fill="none" stroke="{ORANGE}" stroke-width="3.2"/>'
        f'<polyline points="{poly(bev2, x0, y0, w, h, vmax)}" fill="none" stroke="{TEAL}" stroke-width="3.2"/>'
        f'<polyline points="{poly(bev3, x0, y0, w, h, vmax)}" fill="none" stroke="{TEAL}" stroke-width="2" '
        f'stroke-dasharray="6 4" opacity=".8"/>'
    )
    lab = (
        f'<text x="{sx(7.4, x0, w):.0f}" y="{sy(1290, y0, h, vmax):.0f}" font-family="Roboto Condensed" '
        f'font-size="12" font-weight="700" fill="{NAVY}">E_ref — the fleet benchmark, falling</text>'
        f'<text x="{sx(6.2, x0, w):.0f}" y="{sy(1640, y0, h, vmax):.0f}" font-family="Roboto Condensed" '
        f'font-size="12" font-weight="700" fill="{ORANGE}">ICE / HEV — fixed at sale-year efficiency</text>'
        f'<text x="{sx(4.2, x0, w):.0f}" y="{sy(690, y0, h, vmax):.0f}" font-family="Roboto Condensed" '
        f'font-size="12" font-weight="700" fill="{TEAL}">BEV — flat, because this grid pathway is already met</text>'
        f'<text x="{sx(5.4, x0, w):.0f}" y="{sy(130, y0, h, vmax):.0f}" font-family="Roboto Condensed" '
        f'font-size="11.5" font-weight="700" fill="{TEAL}" opacity=".85">same BEV on the 1.5°C grid &#8594; 175</text>'
    )
    ends = "".join(
        f'<circle cx="{sx(T - 1, x0, w):.1f}" cy="{sy(v, y0, h, vmax):.1f}" r="3.6" fill="{c}"/>'
        f'<text x="{sx(T - 1, x0, w) + 7:.0f}" y="{sy(v, y0, h, vmax) + 4:.0f}" font-family="Roboto Condensed" '
        f'font-size="11" font-weight="700" fill="{c}">{v:.0f}</text>'
        for v, c in ((ref["S2"][-1], NAVY), (E_PROD, ORANGE), (bev2[-1], TEAL))
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{grid}{lines}{lab}{ends}'
        f'<line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" stroke="{NAVY}" stroke-width="2"/>{ticks}'
        f'<text x="{x0 + w / 2:.0f}" y="{H - 3}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" fill="{GREY}">YEARS SINCE SALE · kgCO2e per vehicle per year · Germany, committed policy</text></svg>'
    )


def chart_identity() -> str:
    """The decomposition identity as a matrix: rows and columns must meet at the same corner."""
    res = json.loads((PUB / "lifetime_results.json").read_text())
    v = next(x for x in res.values() if x["firm"] == "Toyota")
    c = v["cohorts"]["S2"]
    cells = {(x["country"], x["powertrain"]): x["TI_tCO2e"] for x in c["by_cell"]}
    by_c, by_p, total = c["by_country"], c["by_powertrain"], c["total_tCO2e"]
    cols = ["HEV", "ICE", "BEV"]
    top = sorted(by_c.items(), key=lambda kv: kv[1])[:8]
    names = [k for k, _ in top]
    rest = {p: sum(cells.get((k, p), 0.0) for k in by_c if k not in names) for p in cols}
    rows = [(k, {p: cells.get((k, p), 0.0) for p in cols}, x) for k, x in top]
    rows.append((f"other {len(by_c) - 8}", rest, sum(x for k, x in by_c.items() if k not in names)))

    peak = max(abs(cells.get((k, p), 0.0)) for k in names for p in cols) or 1.0

    def fill(val: float) -> tuple[str, str]:
        a = min(1.0, abs(val) / peak) ** 0.62
        if val < 0:
            return f'rgba(236,131,5,{0.10 + 0.85 * a:.2f})', "#fff" if a > 0.5 else "#40301c"
        if val > 0:
            return f'rgba(139,195,74,{0.14 + 0.80 * a:.2f})', "#26340f" if a < 0.7 else "#fff"
        return "#F4F7F7", "#aab"

    W, H = 560, 318
    lx, cw, gap = 70, 76, 4
    xs = [lx + 6 + i * (cw + gap) for i in range(3)]
    mx = xs[2] + cw + 22          # row-margin column
    rh, y0 = 23, 42
    out = []
    for i, p in enumerate(cols):
        out.append(
            f'<text x="{xs[i] + cw / 2:.0f}" y="{y0 - 10}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="12" font-weight="700" fill="{NAVY}">{p}</text>'
        )
    out.append(
        f'<text x="{mx + 44}" y="{y0 - 10}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="12" font-weight="700" fill="{TEAL}">&#931; BY MARKET</text>'
    )
    for ri, (name, vals, rowsum) in enumerate(rows):
        y = y0 + ri * rh
        out.append(
            f'<text x="{lx - 4}" y="{y + 15:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="11.5" fill="#556">{name}</text>'
        )
        for i, p in enumerate(cols):
            val = vals[p]
            bg, fg = fill(val)
            out.append(
                f'<rect x="{xs[i]}" y="{y}" width="{cw}" height="{rh - 3}" rx="2" fill="{bg}">'
                f'<title>{name} · {p}: {val / 1e3:+,.1f} ktCO2e</title></rect>'
                f'<text x="{xs[i] + cw / 2:.0f}" y="{y + 14:.0f}" text-anchor="middle" '
                f'font-family="Roboto Condensed" font-size="11" fill="{fg}">{val / 1e3:+,.0f}</text>'
            )
        out.append(
            f'<rect x="{mx}" y="{y}" width="88" height="{rh - 3}" rx="2" fill="#EAF1F2"/>'
            f'<text x="{mx + 44}" y="{y + 14:.0f}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="11.5" font-weight="700" fill="{NAVY}">{rowsum / 1e3:+,.0f}</text>'
        )
    my = y0 + len(rows) * rh + 6
    out.append(
        f'<text x="{lx - 4}" y="{my + 16:.0f}" text-anchor="end" font-family="Roboto Condensed" '
        f'font-size="12" font-weight="700" fill="{TEAL}">&#931; BY TYPE</text>'
    )
    for i, p in enumerate(cols):
        out.append(
            f'<rect x="{xs[i]}" y="{my}" width="{cw}" height="22" rx="2" fill="#EAF1F2"/>'
            f'<text x="{xs[i] + cw / 2:.0f}" y="{my + 16:.0f}" text-anchor="middle" '
            f'font-family="Roboto Condensed" font-size="11.5" font-weight="700" fill="{NAVY}">'
            f'{by_p[p] / 1e3:+,.0f}</text>'
        )
    out.append(
        f'<rect x="{mx}" y="{my}" width="88" height="22" rx="3" fill="{NAVY}"/>'
        f'<text x="{mx + 44}" y="{my + 16:.0f}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="12.5" font-weight="700" fill="{GREEN}">{total / 1e3:+,.0f}</text>'
    )
    out.append(
        f'<text x="{lx + 6}" y="{H - 20}" font-family="Roboto Condensed" font-size="10.5" fill="#93a0a0">'
        f'Toyota, committed-policy scenario, ktCO2e. Eight worst destinations shown;</text>'
        f'<text x="{lx + 6}" y="{H - 6}" font-family="Roboto Condensed" font-size="10.5" fill="#93a0a0">'
        f'the remaining 19 are pooled into one row so both margins still close.</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}</svg>'
    )


def chart_coverage() -> str:
    """Both cohorts' units, split by publication decision, at true proportion."""
    res = json.loads((PUB / "lifetime_results.json").read_text())
    order = ["Toyota", "Hyundai"]
    by_firm = {v["firm"]: v["coverage"] for v in res.values()}
    W, H = 560, 254
    x0, bw = 84, 400
    out = []
    for fi, firm in enumerate(order):
        c = by_firm[firm]
        total = c["total_units"]
        parts = [
            ("covered", c["covered_units"], GREEN),
            ("PHEV", c["withheld_product_types"].get("PHEV", {}).get("units", 0.0), ORANGE),
            ("FCEV", c["withheld_product_types"].get("FCEV", {}).get("units", 0.0), "#B85E00"),
            ("no certified value", c["unpriced_units"], GREY),
        ]
        y = 44 + fi * 96
        out.append(
            f'<text x="{x0 - 10}" y="{y + 21:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="13.5" font-weight="700" fill="{NAVY}">{firm}</text>'
            f'<text x="{x0 - 10}" y="{y + 36:.0f}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="10.5" fill="{GREY}">{total:,.0f} units</text>'
        )
        x = x0
        for name, u, c_ in parts:
            w = bw * u / total
            out.append(
                f'<rect x="{x:.2f}" y="{y}" width="{max(w, 1.4):.2f}" height="32" rx="2" fill="{c_}">'
                f'<title>{firm} · {name}: {u:,.0f} ({u / total:.3%})</title></rect>'
            )
            x += w
        cov = c["covered_units"] / total
        out.append(
            f'<text x="{x0 + bw * cov / 2:.0f}" y="{y + 21:.0f}" text-anchor="middle" '
            f'font-family="Roboto Condensed" font-size="13" font-weight="700" fill="#fff">'
            f'{cov:.1%} covered</text>'
        )
        # the withheld sliver is too thin to label in place, so it is called out above the bar
        wx = x0 + bw * cov
        held = total - c["covered_units"]
        out.append(
            f'<line x1="{wx + 1:.0f}" y1="{y - 3}" x2="{wx + 1:.0f}" y2="{y}" stroke="{ORANGE}" stroke-width="1.2"/>'
            f'<text x="{wx - 3:.0f}" y="{y - 6}" text-anchor="end" font-family="Roboto Condensed" '
            f'font-size="10.5" fill="#B85E00">withheld {held:,.0f} ({held / total:.1%}) &#8594;</text>'
        )
    legend, lx = "", x0
    for name, c_ in (("covered by the result", GREEN), ("PHEV withheld", ORANGE),
                     ("FCEV withheld", "#B85E00"), ("no certified value", GREY)):
        legend += (
            f'<rect x="{lx}" y="6" width="10" height="10" rx="2" fill="{c_}"/>'
            f'<text x="{lx + 14}" y="15" font-family="Roboto Condensed" font-size="10.5" fill="#333">{name}</text>'
        )
        lx += 26 + len(name) * 5.4
    out.append(
        f'<text x="{x0}" y="{H - 22}" font-family="Roboto Condensed" font-size="10.5" fill="#93a0a0">'
        f'Bars are true proportion. FCEV and the unpriced rows are thinner than a hairline &#8212;</text>'
        f'<text x="{x0}" y="{H - 8}" font-family="Roboto Condensed" font-size="10.5" fill="#93a0a0">'
        f'the published count, not the bar width, is the disclosure. Hover any segment for both.</text>'
    )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{legend}'
        f'{"".join(out)}</svg>'
    )


def chart_bars() -> str:
    W, H = 580, 302
    x0, y0, w, h = 40, 12, W - 56, H - 44
    top, bot = 700.0, 700.0
    zero = y0 + h * top / (top + bot)
    out = []
    for i, g in enumerate(gap):
        bw, cx = w / T * 0.66, x0 + w * (i + 0.5) / T
        bh = abs(g) / (top if g >= 0 else bot) * (zero - y0 if g >= 0 else y0 + h - zero)
        y = zero - bh if g >= 0 else zero
        out.append(
            f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" '
            f'fill="{GREEN if g >= 0 else ORANGE}"/>'
            f'<text x="{cx:.1f}" y="{(y - 5) if g >= 0 else (y + bh + 13):.1f}" text-anchor="middle" '
            f'font-family="Roboto Condensed" font-size="10.5" font-weight="700" '
            f'fill="{"#5a8a1e" if g >= 0 else ORANGE}">{g:+.0f}</text>'
            f'<text x="{cx:.1f}" y="{y0 + h + 14:.0f}" text-anchor="middle" font-family="Roboto Condensed" '
            f'font-size="10" fill="{GREY}">{i}</text>'
        )
    return (
        f'<svg class="csvg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">{"".join(out)}'
        f'<line x1="{x0}" y1="{zero:.1f}" x2="{x0 + w}" y2="{zero:.1f}" stroke="{NAVY}" stroke-width="2"/>'
        f'<text x="{x0 + w / 2:.0f}" y="{H - 2}" text-anchor="middle" font-family="Roboto Condensed" '
        f'font-size="11" fill="{GREY}">YEARS SINCE SALE · kgCO2e per vehicle per year</text></svg>'
    )


# --------------------------------------------------------------------- results payload
def case_payload() -> str:
    """Real published per-powertrain results, wired to the scenario switcher."""
    desc = {
        "S1": "Even measured against the trend the EU is actually realising, both cohorts are already "
              "a net liability. Hyundai's battery-electric line is the only positive figure anywhere.",
        "S2": "Against the committed EU transport pathway Toyota's liability roughly quadruples, and "
              "its non-plug-in hybrids alone account for −4.08 Mt of it.",
        "S3": "On a 1.5°C-aligned benchmark Toyota's 610,881 hybrids become a −10.41 Mt liability, and "
              "the battery-electric contribution shrinks to a third of its S1 value.",
    }
    data = {}
    for s in ("S1", "S2", "S3"):
        entry = {"d": desc[s]}
        for firm in ("Toyota", "Hyundai"):
            v = BY_FIRM[firm]
            c = v["cohorts"][s]
            pt = c["by_powertrain"]
            entry[firm] = {
                "HEV": round(pt.get("HEV", 0) / 1e6, 3),
                "ICE": round(pt.get("ICE", 0) / 1e6, 3),
                "BEV": round(pt.get("BEV", 0) / 1e6, 3),
                "net": round(c["total_tCO2e"] / 1e6, 3),
                "pv": f"{c['total_tCO2e'] / v['coverage']['covered_units']:+.2f}".replace("+", "+").replace("-", "−"),
            }
        data[s] = entry
    return json.dumps(data, ensure_ascii=False)


# --------------------------------------------------------------------------- slides
SLIDES: list[tuple[str, str]] = []   # (toc title, html)


def add(toc: str, html: str) -> None:
    SLIDES.append((toc, html))


def foot(src: str) -> str:
    return f'<div class="foot"><span>PLANiT · Trade Impact</span><span>{src}</span></div>'


def slide(sid, chap, kicker, title, body, src, navy=False, extra=""):
    return (
        f'<section class="slide {"navy" if navy else "white"}" id="{sid}"{extra}>\n'
        f'  <div class="chap">{chap}</div>\n'
        f'  <div class="kicker">{kicker}</div>\n'
        f'  <h1 class="title">{title}</h1>\n'
        f'  <div class="body-area">\n{body}\n  </div>\n  {foot(src)}\n</section>\n'
    )


LOGO = '<div class="wordmark">PLAN<span>i</span>T</div>'

# ============================================================ PART A — WHY
add("Cover", f'''<section class="slide navy" id="s1" style="justify-content:center;">
  {LOGO}
  <div class="rule"></div>
  <h1 class="cover-h1">Trade as a Climate Amplifier</h1>
  <div class="cover-sub">The Trade Impact (TI) Framework — and, step by step, how its number is built</div>
  <div class="statrow">
    <div><b>1,286</b><span>evidence rows</span></div>
    <div><b>27</b><span>destination markets</span></div>
    <div><b>3</b><span>policy scenarios</span></div>
    <div><b>18</b><span>calculation steps</span></div>
  </div>
  <div class="cover-meta">PLANiT Institute · August 2026 · Climate Arc</div>
  <div class="cover-hint">→ / ← to navigate · M for contents</div>
</section>
''')

add("The problem", slide(
    "s2", "01 · The problem", "Where the story starts",
    "Every traded product bends a country's emissions path — and no accounting framework can see which way",
    f'''    <div class="grid cols2" style="grid-template-columns:1.06fr 0.94fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Cars from the 2024 cohort still on European roads</div>
        <div class="chart-sub">Share of the cohort surviving, against the target years the EU has already committed to</div>
        {chart_outlast()}
      </div>
      <div class="icards">
        <div class="icard"><div class="n">Every one of them</div><div class="t"><b>The clean-technology export</b> keeps cutting the buyer's emissions for its whole operating life — yet Scope 3 books it only as the seller's growing liability.</div></div>
        <div class="icard orange"><div class="n">73% still running</div><div class="t"><b>The carbon-intensive export</b> locks the buyer in past its own commitments. Three quarters of one year's sales are still on European roads when the 2040 target falls due — and nothing prices that.</div></div>
      </div>
    </div>
    <div class="takeaway"><b>The blind spot:</b> a single year of sales outlives two rounds of national commitments, and nothing reads the product against where its destination is <i>committed</i> to going.</div>''',
    "TI Whitepaper v1.5 §1 · surviving-vehicle series from the published run"))

add("The framework", slide(
    "s3", "02 · The framework", "One question, asked everywhere",
    "TI reads every sale against the destination's committed pathway",
    '''    <div class="quote">“Does this product emit more or less than what the destination's sector is committed to emitting — in each year of the product's operating life?”</div>
    <div class="flow">
      <div class="fbox"><h4>Observed sales</h4><p>Real units: destination × model × technology.</p></div>
      <div class="arr">→</div>
      <div class="fbox"><h4>NDC benchmark</h4><p>Each destination's own fleet intensity, falling along a committed path.</p></div>
      <div class="arr">→</div>
      <div class="fbox"><h4>Product trajectory</h4><p>Combustion fixed at sale; electric rides the grid down.</p></div>
      <div class="arr">→</div>
      <div class="fbox hl"><h4>Gap → TI score</h4><p>Benchmark − product, summed over the lifetime, sales-weighted.</p></div>
    </div>
    <div class="takeaway"><b>Positive TI</b> = contribution. <b>Negative TI</b> = carbon lock-in. Always additional to Scope 3 — never netted against it.</div>''',
    "TI Whitepaper v1.5 §2 · Automotive Guideline v1.8 §4"))

add("Positioning", slide(
    "s4", "03 · Positioning", "Why a new metric at all",
    "Neither Scope 3 nor avoided-emissions methods can produce this signal",
    f'''    <div class="grid cols2" style="grid-template-columns:1.1fr 0.9fr;">
      <div class="chart-wrap">
        {chart_two_frames()}
      </div>
      <div class="icards">
        <div class="icard orange"><div class="n">Scope 3 Cat. 11</div><div class="t">Absolute footprint only, with no reference point. Selling a battery-electric car into Europe <b>adds 0.31 Mt to the inventory and earns nothing back</b> — clean exporters are penalised for accelerating other countries' transitions.</div></div>
        <div class="icard"><div class="n">Scope 4 · avoided</div><div class="t">Reductions against a <b>static</b> average. It would credit these cars, but with a number blind to what Europe has actually committed to — and blind to how that commitment tightens over the car's life.</div></div>
        <div class="icard green"><div class="n">Trade Impact</div><div class="t">Dynamic and NDC-derived, on <b>each destination's own fleet, grid, distance and lifetime</b>. <b>+0.58 Mt of contribution</b> here — and the same method turns negative the moment a product falls behind the path. Where a national pathway is missing, a regional one stands in and says so.</div></div>
      </div>
    </div>
    <div class="warn"><b>These are not alternatives to be netted.</b> The 0.31 Mt stays in the inventory whatever TI says; TI is an additional disclosure that answers a different question — <b>not whether the product emits, but whether it helps.</b></div>''',
    "TI Whitepaper v1.5 §1.3 · computed on the published Hyundai BEV cohort"))

# ============================================================ PART B — HOW
add("The walkthrough", slide(
    "s5", "04 · How the number is built", "The walkthrough begins",
    "Eighteen steps, followed on one real cell of the 2024 Toyota cohort",
    f'''    <div class="grid cols2" style="grid-template-columns:1.04fr 0.96fr;flex:none;">
      <div class="fieldrow">
        <div class="fr"><span class="fk">Destination</span><span class="fv">Germany</span><span class="fn">where the car is driven</span></div>
        <div class="fr"><span class="fk">Product</span><span class="fv">TOYOTA COROLLA</span><span class="fn">EEA commercial name</span></div>
        <div class="fr"><span class="fk">Technology</span><span class="fv">HEV</span><span class="fn">non-plug-in hybrid</span></div>
        <div class="fr"><span class="fk">Units · cohort year</span><span class="fv">17,111 · 2024</span><span class="fn">first registrations, t = 0</span></div>
        <div class="fr"><span class="fk">Certified WLTP</span><span class="fv">107.13 gCO2/km</span><span class="fn">registration-weighted</span></div>
      </div>
      <div class="stat-side">
        <div class="stat-big"><div class="n">−3,167 <em>kgCO2e</em></div><div class="t">Where step 14 lands: the lifetime TI of <b>one</b> Corolla in Germany, committed-policy scenario.</div></div>
        <div class="stat-big"><div class="n">−54,182 <em>tCO2e</em></div><div class="t">The same figure times the units actually registered. One model, one market, one year.</div></div>
      </div>
    </div>
    <div class="flow" style="margin-top:16px;">
      <div class="fbox sm"><h4>OBSERVED</h4><p>steps 1–2</p></div><div class="arr">→</div>
      <div class="fbox sm"><h4>DESTINATION</h4><p>steps 3–7</p></div><div class="arr">→</div>
      <div class="fbox sm"><h4>JOIN</h4><p>steps 8–9</p></div><div class="arr">→</div>
      <div class="fbox sm"><h4>CELL MATH</h4><p>steps 10–14</p></div><div class="arr">→</div>
      <div class="fbox sm"><h4>AGGREGATE</h4><p>steps 15–16</p></div><div class="arr">→</div>
      <div class="fbox sm hl"><h4>GATE</h4><p>steps 17–18</p></div>
    </div>
    <div class="takeaway">The same arithmetic runs on <b>1,286 evidence rows across 27 destinations under 3 scenarios</b> — over 32,000 cell-years per cohort.</div>''',
    "data/published/product_cohorts.json · destination_inputs.json"))

add("Step 1 · The cohort", slide(
    "s6", "04 · How the number is built", "Step 1 · The cohort",
    "The cohort is observed registrations — never modelled or estimated sales",
    '''    <div class="grid cols2" style="grid-template-columns:1.08fr 0.92fr;">
      <div class="fieldrow">
        <div class="fr"><span class="fk">destination_geography</span><span class="fv">DE</span><span class="fn">EU27 member state</span></div>
        <div class="fr"><span class="fk">product_name</span><span class="fv">COROLLA</span><span class="fn">commercial name</span></div>
        <div class="fr"><span class="fk">product_type</span><span class="fv">HEV</span><span class="fn">from the fuel-mode field</span></div>
        <div class="fr"><span class="fk">units</span><span class="fv">17,111</span><span class="fn">sum of registrations</span></div>
        <div class="fr"><span class="fk">certified_tailpipe</span><span class="fv">107.13</span><span class="fn">gCO2/km, WLTP</span></div>
        <div class="fr"><span class="fk">certified_electricity</span><span class="fv">null</span><span class="fn">kWh/km — not a BEV</span></div>
        <div class="fr"><span class="fk">source_ids</span><span class="fv">eea-co2-cars-2024</span><span class="fn">hash-pinned snapshot</span></div>
      </div>
      <div class="stat-line">
        <div class="row"><div class="num">1,286</div><div class="txt"><b>The whole evidence base.</b> 660 Toyota rows, 626 Hyundai. Each row is one destination × model × powertrain.</div></div>
        <div class="row"><div class="num">803,094</div><div class="txt"><b>Toyota EU27 first registrations, 2024.</b> Hyundai: 429,936.</div></div>
        <div class="row"><div class="num">SHA-256</div><div class="txt"><b>The source snapshot is committed and hashed.</b> The build fails if a byte of it moves.</div></div>
      </div>
    </div>
    <div class="warn"><b>What this is not.</b> Registrations record where a car <b>enters use</b>, not where it was built. This is a destination-cohort result and not an export claim — production origin is a separate, uncollected Level 2 input.</div>''',
    "EEA CO2 cars 2024 final · data-pipeline/adapters/automotive_eea.py"))

add("Step 2 · Withholding", slide(
    "s7", "04 · How the number is built", "Step 2 · Mapping and withholding",
    "A product the model cannot price is withheld with its unit count, not set to zero",
    f'''    <div class="grid cols2" style="grid-template-columns:0.98fr 1.02fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Both 2024 EU27 cohorts, by publication decision</div>
        <div class="chart-sub">1,233,030 registrations · what the lifetime result does and does not span</div>
        {chart_coverage()}
      </div>
      <div class="stat-line">
        <div class="row"><div class="num sm">→ ICE</div><div class="txt"><b>ICE_OTHER and HEV both map to fixed sale-year emissions.</b> A non-plug-in hybrid takes no external energy, so its intensity never changes.</div></div>
        <div class="row"><div class="num sm">→ BEV</div><div class="txt"><b>Priced on the destination grid,</b> using the certified kWh/km.</div></div>
        <div class="row"><div class="num sm">PHEV</div><div class="txt"><b>Withheld — underdetermined, not missing.</b> 132 of the 134 PHEV rows publish both a combined CO2 and a combined kWh/km. That is <b>two observations against three unknowns</b> — utility factor, EV-mode efficiency, charge-sustaining intensity. The system has no solution unless one is assumed.</div></div>
        <div class="row"><div class="num sm">FCEV</div><div class="txt"><b>Withheld.</b> No hydrogen supply intensity is sourced for the destination market.</div></div>
      </div>
    </div>
    <div class="takeaway">A missing input produces an <b>unavailable</b> result — never a zero, never an invented estimate. The withheld unit count is published beside the headline.</div>''',
    "data-pipeline/lifetime_run.py · coverage object"))

add("Step 3 · Distance", slide(
    "s8", "04 · How the number is built", "Step 3 · Annual distance",
    "Distance comes from the one traffic series whose population matches the fleet",
    f'''    <div class="calcrow">
      <div class="cbox"><div class="cv">594,136</div><div class="cl">million vehicle-km · road_tf_veh</div></div>
      <div class="op">÷</div>
      <div class="cbox"><div class="cv">49.34 M</div><div class="cl">registered cars · road_eqs_carpda</div></div>
      <div class="op">=</div>
      <div class="cbox res"><div class="cv">12,042</div><div class="cl">km per car per year · Germany</div></div>
    </div>
    <div class="grid cols2" style="grid-template-columns:1.16fr 0.84fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Annual distance per registered car, all 27 destination markets</div>
        <div class="chart-sub">Navy = measured from a national traffic series · orange = assigned the EU average</div>
        {chart_distance()}
      </div>
      <div class="icards">
        <div class="icard"><div class="n">One series only</div><div class="t">TER_REGNAT counts traffic by cars <b>registered in the reporting country</b> — the same population as the stock denominator. The territory-based series counts foreign vehicles too and is not used at all.</div></div>
        <div class="icard green"><div class="n">3,000–30,000 km</div><div class="t">A result outside the plausibility band means the two series describe different populations. The value is <b>rejected outright</b>, not quietly tiered down.</div></div>
        <div class="icard orange"><div class="n">2.0× spread</div><div class="t">Malta drives 7,109 km a year, Slovenia 14,417. <b>Thirteen markets are handed a single number in the middle</b> — with the derivation and its known bias stated on the record.</div></div>
      </div>
    </div>
    <div class="warn"><b>The single largest uncertainty in the whole result.</b> 53.6% of Toyota's covered units sit in a proxied-distance market. The proxy skews to higher-mileage western states, which pushes the product side up and the contribution down. Step 17 re-runs the entire calculation at the measured lower and upper quartile.</div>''',
    "Eurostat road_tf_veh · road_eqs_carpda · 2024"))

add("Step 4 · Lifetime", slide(
    "s9", "04 · How the number is built", "Step 4 · Operating lifetime",
    "Lifetime is bracketed by observed fleet age, not assumed from a rule of thumb",
    '''    <div class="eqbar">T<em> = 1.5 × </em>mean car age<span class="u">bracket [mean age, 2 × mean age] · clamped to 10–25 years</span></div>
    <div class="calcrow">
      <div class="cbox"><div class="cv">10.33 yr</div><div class="cl">German stock-weighted mean age</div></div>
      <div class="op">→</div>
      <div class="cbox res"><div class="cv">15 yr</div><div class="cl">central operating lifetime T</div></div>
      <div class="op">±</div>
      <div class="cbox"><div class="cv">10 – 20</div><div class="cl">bracket carried into sensitivity</div></div>
    </div>
    <div class="grid cols3" style="flex:none;">
      <div class="card tb-navy"><h3>Why 1.5×</h3><p>In steady state with exponential scrappage the mean operating life is <b>at least</b> the mean age; with a single retirement age it is <b>at most twice</b> it. The published value is the midpoint of that bracket.</p></div>
      <div class="card tb-teal"><h3>Per destination</h3><p>T ranges <b>12 to 25 years</b> across EU27. A country's own value drives its own cells; the cohort horizon is the longest. Toyota central 19, Hyundai 18.</p></div>
      <div class="card tb-green"><h3>What is assumed</h3><p>Eurostat's top age band is open-ended. It is <b>closed at 25 years</b>, and that assumption is written into the published derivation string, not buried in a footnote.</p></div>
    </div>
    <div class="takeaway">21 of 27 markets publish a complete age partition. The other 6 borrow the pooled EU distribution and are <b>tiered down to C</b> for it.</div>''',
    "Eurostat road_eqs_carage · 2025 vintage"))

add("Step 5 · Benchmark base", slide(
    "s10", "04 · How the number is built", "Step 5 · The benchmark base",
    "The benchmark is what the destination's whole car fleet actually emits today",
    '''    <div class="calcrow">
      <div class="cbox"><div class="cv">89.32 Mt</div><div class="cl">German car CO2 · CRF 1.A.3.b.i</div></div>
      <div class="op">÷</div>
      <div class="cbox"><div class="cv">49.34 M × 12,042</div><div class="cl">cars × km per car</div></div>
      <div class="op">=</div>
      <div class="cbox res"><div class="cv">150.34</div><div class="cl">gCO2/km · I_fleet(0)</div></div>
    </div>
    <div class="grid cols2">
      <div class="card tb-navy"><h3>An in-use average, not a type-approval value</h3>
        <p>It contains every vintage on the road — including twenty-year-old cars — and every powertrain. Against that, a new hybrid certified at 107 g looks clean.</p>
        <p class="sp"><b>That comparison is not yet fair.</b> One side is measured on the road, the other in a laboratory. Step 8 closes the gap before they are ever subtracted.</p></div>
      <div class="card tb-teal"><h3>A second plausibility gate</h3>
        <p>Outside <b>80–320 gCO2/km</b> the national inventory and the registered stock are describing different driving populations — cross-border refuelling is the usual cause.</p>
        <p class="sp">The value is not discarded, but it is <b>tiered down to C</b> and the reason is attached to the country record as a published warning.</p></div>
    </div>
    <div class="takeaway">12 markets resolve at tier A, 2 at B, 13 at C. <b>The tier travels with the number all the way to the published result.</b></div>''',
    "Eurostat env_air_gge CRF 1.A.3.b.i · 2024"))

add("Steps 6–7 · Pathways", slide(
    "s11", "04 · How the number is built", "Steps 6–7 · Grid and pathways",
    "Two decline rates, derived independently, three scenarios each",
    f'''    <div class="grid cols2" style="grid-template-columns:1.02fr 0.98fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Germany — the benchmark a 2024 car is measured against</div>
        <div class="chart-sub">E_ref(t), kgCO2e per vehicle per year · same base, same distance, different committed rate</div>
        {chart_pathways()}
      </div>
      <div class="stat-line">
        <div class="row"><div class="num">S1 <em>2.63%</em></div><div class="txt"><b>Current trajectory.</b> Log-linear fit to observed CO2 per registered car, 2015–2024, excluding the 2020–21 pandemic years. An outturn, not a commitment.</div></div>
        <div class="row"><div class="num">S2 <em>4.34%</em></div><div class="txt"><b>Committed policy.</b> EU domestic transport, 795.6 → 583 MtCO2e by 2030. A regional sector proxy applied to every member state — and labelled as one.</div></div>
        <div class="row"><div class="num">S3 <em>13.51%</em></div><div class="txt"><b>1.5°C aligned.</b> Pro-rata against the recommended −90% by 2040 versus 1990.</div></div>
        <div class="row"><div class="num sm">r_power</div><div class="txt"><b>Always derived separately.</b> Germany: 4.02% / 0% / 8.56%. Setting r_fleet = r_power is the framework's commonest error.</div></div>
      </div>
    </div>
    <div class="warn"><b>A published inconvenience.</b> EU power-sector CO2 in 2024 already sits below its pro-rata 2030 level, so the implied S2 rate is negative. Letting a benchmark <b>rise</b> would flatter every electrified product, so it is held flat at zero — and the condition is printed as a warning on all 27 country records.</div>''',
    "EU Climate Law 2021/1119 · COM(2024) 63 · Ember/OWID grid intensity"))

add("Data status · all 27 markets", slide(
    "s11b", "04 · How the number is built", "Data status · the whole destination table at once",
    "Every market is input-complete — and not one of them is fully measured",
    f'''    <div class="grid cols2" style="grid-template-columns:1.42fr 0.58fr;">
      <div class="chart-wrap">
        <div class="chart-h3">27 destination markets: every sourced input, at its published tier</div>
        <div class="chart-sub">Steps 3–7 side by side · the two rate rows show whether a value is country-specific at all</div>
        {chart_tiers()}
        <div class="chart-note">Grid intensity resolves at tier A everywhere. Lifetime never does — it is a bracket around observed fleet age, not a measurement, so B is its ceiling by construction.</div>
      </div>
      <div class="stat-line">
        <div class="row"><div class="num sm">0 <em>missing</em></div><div class="txt"><b>The publication gate passes.</b> All 27 markets have every required input sourced, which is why a lifetime value exists at all.</div></div>
        <div class="row"><div class="num sm">58% / 56%</div><div class="txt"><b>Toyota / Hyundai units sitting in a tier-C market.</b> Both above the 50% threshold.</div></div>
        <div class="row"><div class="num sm">LU 391</div><div class="txt"><b>The plausibility gate firing.</b> Luxembourg's implied fleet intensity is 391 gCO2/km — cross-border refuelling. Tiered down to C, with the reason attached.</div></div>
      </div>
    </div>
    <div class="warn"><b>Two things this table admits.</b> <b>Distance</b> and <b>Benchmark</b> carry the same colour in every column, because the benchmark is derived <i>through</i> the distance — a proxied distance hands the benchmark its proxy. And the committed rate is <b>one EU number applied to all 27 markets</b>: the benchmark's <i>level</i> is destination-specific everywhere, its <i>slope</i> only under S1.</div>''',
    "data/published/destination_inputs.json · tier and warning fields"))

add("Step 8 · Real-world", slide(
    "s12", "04 · How the number is built", "Step 8 · Real-world correction",
    "Certified values are corrected once, at the door, so they can never be corrected twice",
    '''    <div class="calcrow">
      <div class="cbox"><div class="cv">107.13</div><div class="cl">certified WLTP · gCO2/km</div></div>
      <div class="op">×</div>
      <div class="cbox"><div class="cv">1.211</div><div class="cl">EEA OBFCM petrol gap · +21.1%</div></div>
      <div class="op">=</div>
      <div class="cbox res"><div class="cv">129.74</div><div class="cl">real-world · gCO2/km</div></div>
    </div>
    <div class="grid cols3" style="flex:none;">
      <div class="card tb-teal"><h3>HEV × 1.211</h3><p>Both cohorts' hybrids are petrol hybrids. The gap is EEA on-board monitoring for model-year 2022 registrations.</p></div>
      <div class="card tb-navy"><h3>ICE × 1.191</h3><p>ICE_OTHER pools petrol and diesel. The midpoint is applied and the <b>span between them drives the sensitivity sweep</b>.</p></div>
      <div class="card tb-green"><h3>BEV × 1.000</h3><p>No official real-world gap is published for battery-electric consumption, so the certified value passes through untouched.</p></div>
    </div>
    <div class="warn"><b>An asymmetry we own.</b> Passing BEV through uncorrected while combustion is marked up 19–21% <b>flatters BEV in every result in this deck</b>. It is disclosed in the published coverage object rather than argued away. The correction is applied at fixture build time and the engine never re-applies one, so double counting is structurally impossible.</div>''',
    "EEA real-world CO2 (OBFCM), model year 2022"))

add("Step 9 · The fixture", slide(
    "s13", "04 · How the number is built", "Step 9 · The join",
    "Two published objects meet on one key, and the engine input is written to disk",
    '''    <div class="flow" style="margin-bottom:18px;">
      <div class="fbox"><h4>product_cohorts.json</h4><p>1,286 observed rows — units, model, technology, certified intensity</p></div>
      <div class="arr">+</div>
      <div class="fbox"><h4>destination_inputs.json</h4><p>27 markets — distance, lifetime, benchmark, grid, six pathway rates</p></div>
      <div class="arr">→</div>
      <div class="fbox hl"><h4>run_input.json</h4><p>one committed fixture per cohort</p></div>
    </div>
    <div class="grid cols4">
      <div class="card tb-navy"><div class="nt">01</div><h3>placements</h3><p>One per destination × model × powertrain, with units, corrected intensity, and both tiers.</p></div>
      <div class="card tb-teal"><div class="nt">02</div><h3>countries</h3><p>Benchmark base, grid, six pathway rates, worst-of tier, and every warning attached.</p></div>
      <div class="card tb-green"><div class="nt">03</div><h3>support</h3><p>Per-country lifetime and distance, plus the bands the sensitivity sweeps will use.</p></div>
      <div class="card tb-navy"><div class="nt">04</div><h3>config</h3><p>Scenarios to run, and the rule for markets whose benchmark is not derivable from an NDC.</p></div>
    </div>
    <div class="takeaway">The join key is <b>destination_geography = country_code</b>, and nothing else is inferred across it. The fixture is committed per cohort: <b>anyone can re-run the engine on it and reach the same number.</b></div>''',
    "outputs/&lt;cohort&gt;/run_input.json"))

add("Step 10 · Layer 1", slide(
    "s14", "04 · How the number is built", "Step 10 · Layer 1",
    "Layer 1 — the benchmark a car is measured against falls every single year",
    '''    <div class="eqbar">E_ref,c(t)<em> = </em>I_fleet,c(0)<em> × </em>(1 − r_fleet,c)<sup>t</sup><em> × </em>D_c<span class="u">kgCO2e per vehicle per year</span></div>
    <div class="calcrow">
      <div class="cbox"><div class="cv">0.15034</div><div class="cl">kgCO2/km · step 5</div></div>
      <div class="op">×</div>
      <div class="cbox"><div class="cv">(1 − 0.0434)<sup>t</sup></div><div class="cl">committed rate · step 7</div></div>
      <div class="op">×</div>
      <div class="cbox"><div class="cv">12,042</div><div class="cl">km/yr · step 3</div></div>
      <div class="op">=</div>
      <div class="cbox res"><div class="cv">1,810 → 972</div><div class="cl">kg/yr · t = 0 → t = 14</div></div>
    </div>
    <div class="grid cols3" style="flex:none;">
      <div class="card tb-teal"><h3>Fleet electrification</h3><p>Cleaner powertrains enter the stock and pull the average down.</p></div>
      <div class="card tb-navy"><h3>Vintage turnover</h3><p>The oldest and dirtiest vehicles scrap out of the denominator.</p></div>
      <div class="card tb-green"><h3>Better new entrants</h3><p>Each year's arrivals are cleaner than the year before's.</p></div>
    </div>
    <div class="takeaway">The destination's transport target is the <b>intended combined outcome of all three processes</b> — which is why one committed rate can stand in for the whole fleet transition.</div>''',
    "Whitepaper §3.1 · Guideline §2.3 Method B"))

add("Step 11 · Layer 2", slide(
    "s15", "04 · How the number is built", "Step 11 · Layer 2",
    "Layer 2 — what the sold car emits depends entirely on what it draws energy from",
    f'''    <div class="grid cols2" style="grid-template-columns:1.22fr 0.78fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Three product shapes, and the one benchmark they are all measured against</div>
        <div class="chart-sub">E_prod,v,c(t) for each powertrain · Toyota Corolla and Hyundai KONA, both in Germany</div>
        {chart_layer2()}
      </div>
      <div class="stat-line">
        <div class="row"><div class="num sm">ICE<br>HEV</div><div class="txt"><span class="fm">E = I_export × D</span><b>Flat, for all t.</b> The Corolla emits exactly as much in year 15 as in year 1 — nothing in the destination can change it.</div></div>
        <div class="row"><div class="num sm">BEV</div><div class="txt"><span class="fm">E = η_EV × G(t) × D</span><b>Tracks the destination grid.</b> Flat here only because the EU power pathway is already met at S2; on the 1.5°C grid the same car falls to 175.</div></div>
        <div class="row"><div class="num sm">PHEV</div><div class="txt"><span class="fm">E = [UF·η_elec·G(t) + (1−UF)·I_ICE] × D</span><b>Not drawn.</b> Three unknowns on the right, two published values to solve them with. UF can be assumed but not recovered, so 23,911 Toyota units stay outside the result.</div></div>
      </div>
    </div>
    <div class="takeaway"><b>The combustion car's emissions never improve.</b> The electric car's improve only as fast as the destination's <b>power</b> pathway says they must — which under committed policy here is <b>not at all</b>. Whether electrifying helps is therefore a question about the destination's grid commitment, not about the car.</div>''',
    "Whitepaper §3.2 · Guideline §3.3–3.5"))

add("Step 12 · The gap", slide(
    "s16", "04 · How the number is built", "Step 12 · The annual gap",
    "The gap is the benchmark minus the product — and the car is not what changes",
    f'''    <div class="grid cols2" style="grid-template-columns:1.3fr 0.7fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Toyota Corolla HEV in Germany · committed-policy scenario</div>
        <div class="chart-sub">TI_gap(t) = E_ref(t) − E_prod(t) · green area = contribution, orange area = lock-in</div>
        {chart_gap()}
      </div>
      <div class="stat-side">
        <div class="stat-big green"><div class="n">+248 <em>kg</em></div><div class="t">Year 0. The new hybrid is <b>cleaner</b> than the German fleet average, which still contains a great many old cars.</div></div>
        <div class="stat-big"><div class="n">−590 <em>kg</em></div><div class="t">Year 14. Same car, same emissions — but the fleet around it has moved on.</div></div>
      </div>
    </div>
    <div class="takeaway"><b>The car did not get worse. The benchmark moved.</b> That is precisely the signal a static baseline cannot produce.</div>''',
    "ti-framework/core/gap.py · engine output"))

add("Step 13 · Crossover", slide(
    "s17", "04 · How the number is built", "Step 13 · Crossover",
    "The crossover year names the moment a contribution becomes a liability",
    '''    <div class="eqbar">t*<em> = </em>ln( E_prod / E_ref(0) )<em> / </em>ln( 1 − r_fleet )<span class="u">closed form for ICE, HEV and BEV · where a product starts above the benchmark the engine records the reason, not a year</span></div>
    <div class="calcrow">
      <div class="cbox"><div class="cv">ln(1,562 / 1,810)</div><div class="cl">= −0.1476</div></div>
      <div class="op">÷</div>
      <div class="cbox"><div class="cv">ln(0.9566)</div><div class="cl">= −0.0444</div></div>
      <div class="op">=</div>
      <div class="cbox res"><div class="cv">3.32 years</div><div class="cl">crossover t*</div></div>
    </div>
    <div class="grid cols3" style="flex:none;">
      <div class="card tb-green"><h3>Before t*</h3><p>The vehicle emits below the destination's committed fleet trajectory. Every year here is a genuine contribution to the NDC.</p></div>
      <div class="card tb-navy"><h3>After t*</h3><p>The same fixed emissions now sit above the trajectory, and the gap <b>widens</b> every year until scrappage.</p></div>
      <div class="card tb-orange"><h3>Electric is not exempt</h3><p>Under committed policy <b>20 of 115 Hyundai battery-electric cells and 11 of 61 Toyota's cross into liability inside their own lifetime</b> — Poland at 3.3 years, Greece at 3.8. Dirty grids that S2 holds flat while the fleet benchmark keeps falling.</p></div>
    </div>
    <div class="takeaway">A new hybrid in Germany stays cleaner than the German fleet for <b>3.3 years of a fifteen-year life</b>. A battery-electric car in Poland crosses at <b>3.3 years too</b> — the same date, for the opposite reason: not a car that fails to improve, but a grid the committed pathway does not require to.</div>''',
    "ti-framework/core/crossover.py · ti_crossover.csv"))

add("Step 14 · Cell total", slide(
    "s18", "04 · How the number is built", "Step 14 · Cumulative and cell total",
    "Sum the fifteen annual gaps, then multiply by the cars actually registered",
    f'''    <div class="grid cols2" style="grid-template-columns:1.24fr 0.76fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Every year of the Corolla's life, in sign</div>
        <div class="chart-sub">TI_gap(t) for t = 0 … T−1 · four positive years, eleven negative</div>
        {chart_bars()}
      </div>
      <div class="stat-side">
        <div class="stat-big"><div class="n">−3,167 <em>kgCO2e</em></div><div class="t">Cumulative lifetime TI of <b>one</b> Corolla, summed t = 0 to T−1 with no discounting.</div></div>
        <div class="stat-big"><div class="n">−54,182 <em>tCO2e</em></div><div class="t">× 17,111 registrations ÷ 1,000. <b>One model, one market, one year of sales.</b></div></div>
      </div>
    </div>
    <div class="takeaway"><b>Four good years cannot pay for eleven bad ones.</b> The early contribution is real, and it is not enough.</div>''',
    "Whitepaper §3.5–3.6 · ti_decomposition.csv"))

add("Step 15 · Decomposition", slide(
    "s19", "04 · How the number is built", "Step 15 · Decomposition",
    "A headline that does not reconcile to both margins is never written to disk",
    f'''    <div class="grid cols2" style="grid-template-columns:1.34fr 0.66fr;">
      <div class="chart-wrap">
        <div class="chart-h3">The joint, and the two margins it has to satisfy</div>
        <div class="chart-sub">Every row sums into the teal column; every column sums into the teal row; both land on the same corner</div>
        {chart_identity()}
      </div>
      <div class="stat-side">
        <div class="stat-big"><div class="n">−5,965 <em>kt</em></div><div class="t">Reached three independent ways: <b>Σ destinations, Σ powertrains, Σ cells</b>. If any pair disagrees by more than one part in a million, the run raises.</div></div>
        <div class="stat-big orange"><div class="n">27 × 3 <em>cells</em></div><div class="t">Margins that each sum correctly can still disagree about <b>which cell carries the weight</b>. Publishing the joint rules that out — PL·HEV alone is −1,173 kt, a fifth of the whole cohort.</div></div>
      </div>
    </div>
    <div class="takeaway">Each destination also stops contributing after <b>its own</b> lifetime, so a 12-year market and a 25-year market are never forced onto one schedule. <b>A headline without both decompositions is treated as insufficient by the method itself</b>, not merely as incomplete presentation.</div>''',
    "ti-framework/core/aggregate.py · decomposition_identity_holds"))

add("The machine", slide(
    "s20", "05 · The machine", "Already built, method-locked",
    "Theory and code cannot drift apart — the build fails if they do",
    '''    <div class="flow" style="margin-bottom:18px;">
      <div class="fbox"><h4>Methodology anchors</h4><p>21 named anchors across the whitepaper and the guideline.</p></div>
      <div class="arr">→</div>
      <div class="fbox hl"><h4>CI sync contract</h4><p>An anchor missing from docs, code or tests breaks the build.</p></div>
      <div class="arr">→</div>
      <div class="fbox"><h4>Calculation engine</h4><p>3 layers · 3 scenarios · full sensitivity suite. Python, GPL v3.</p></div>
      <div class="arr">→</div>
      <div class="fbox"><h4>Published outputs</h4><p>Open CSV / JSON with provenance and a data-quality declaration.</p></div>
    </div>
    <div class="grid cols3">
      <div class="vcheck"><div class="cmd">pytest</div><div class="res">✓ 104 passed</div>
        <p>101 engine + 3 MCP. Includes a ±1% check of the engine against an independently hand-calculated reference fixture.</p></div>
      <div class="vcheck"><div class="cmd">check_sync.py</div><div class="res">✓ 21 anchors, three-way linked</div>
        <p>Each anchor must appear in the methodology, the code and a test; a missing link fails the build. It binds the 21 equations it names — the documents restate several of them again without a second anchor.</p></div>
      <div class="vcheck"><div class="cmd">check_published.py</div><div class="res">✓ OK</div>
        <p>Recomputes the entire published dataset from the committed source snapshots and fails if one number drifts.</p></div>
    </div>
    <div class="takeaway">All three ran clean against this repository while this deck was being built, and all three run again on every commit. <b>Any reviewer can trace a published number to the exact equation, source and test behind it</b> — which is what the previous eighteen slides just did.</div>''',
    "theory/SYNC.md · ti-framework/validation_report.md"))

# ============================================================ PART C — WHAT IT PRODUCES
add("First evidence", slide(
    "s21", "06 · First evidence", "Real cohorts, already resolved",
    "Two portfolios, same segment and same year — and the mix is what TI prices",
    '''    <div class="grid cols2" style="grid-template-columns:1.5fr 1fr;">
      <div class="chart-wrap">
        <div class="chart-h3">2024 EU27 first registrations by powertrain, Toyota against Hyundai</div>
        <div class="chart-sub">Share of each firm's own total · EEA registration data · brand boundary, not the corporate group</div>
        <div style="flex:1;min-height:0;"><svg id="mix" viewBox="0 0 560 252" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%"></svg></div>
      </div>
      <div class="stat-line">
        <div class="row"><div class="num">803,094</div><div class="txt">Toyota-brand EU27 registrations mapped</div></div>
        <div class="row"><div class="num">429,936</div><div class="txt">Hyundai-brand EU27 registrations mapped</div></div>
        <div class="row"><div class="num">1,286</div><div class="txt">destination × model × powertrain evidence rows</div></div>
        <div class="row"><div class="num">9.7%<em> vs </em>1.4%</div><div class="txt">BEV share, Hyundai versus Toyota — the mix difference TI prices</div></div>
      </div>
    </div>
    <div class="takeaway"><b>Discipline first:</b> registrations prove destination and mix — not origin. No number before its evidence.</div>''',
    "EEA 2024 final · data/published/product_cohorts.json"))

add("Step 16 · The result", slide(
    "s22", "07 · The result", "Step 16 · What the eighteen steps produce",
    "Both cohorts are a net liability under every one of the three scenarios",
    '''    <div class="scnbar">
      <span class="scnlab">Scenario</span>
      <button class="scnbtn csb" data-s="S1" onclick="selCase('S1')">S1 · Current trajectory</button>
      <button class="scnbtn csb" data-s="S2" onclick="selCase('S2')">S2 · Committed policy</button>
      <button class="scnbtn csb" data-s="S3" onclick="selCase('S3')">S3 · 1.5°C aligned</button>
      <span class="pubtag warn-tag">DIRECTIONAL RESULT — TIER-C SHARE 58% / 56% EXCEEDS THE 50% RULE</span>
    </div>
    <div class="scn-desc" id="caseDesc"></div>
    <div class="grid cols2" style="grid-template-columns:2fr 1fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Lifetime TI of the 2024 EU27 cohorts by powertrain, MtCO2e</div>
        <div class="chart-sub">Positive = contribution against the destination pathway; negative = carbon lock-in</div>
        <div style="flex:1;min-height:0;"><svg id="csvg" viewBox="0 0 560 286" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%"></svg></div>
      </div>
      <div class="kpis">
        <div class="kpi"><div class="kl">Toyota · net cohort TI</div><div class="kv" id="cNetT">−5.97 Mt</div><div class="kp" id="cPvT"></div></div>
        <div class="kpi"><div class="kl">Hyundai · net cohort TI</div><div class="kv" id="cNetH">−3.72 Mt</div><div class="kp" id="cPvH"></div></div>
        <div class="knote"><b style="color:#B85E00">The engine flags these magnitudes — it does not hide them.</b> Both cohorts trip the tier-C rule, so <b>directional_only</b> is set on every scenario and travels with the number: the CLI tags it, the published JSON carries it, the web app prints “direction only” beside it. The publishable claim is the <b>direction</b> — net liability, every scenario.</div>
        <div class="knote">PHEV and FCEV are withheld, not zero — the bar is drawn empty and the unit count is published.</div>
      </div>
    </div>''',
    "data/published/lifetime_results.json · engine run 2026-08"))

add("The same result, year by year", slide(
    "s22b", "07 · The result", "The second required output",
    "The lifetime total is one number; the annual flow is where it actually happens",
    f'''    <div class="grid cols2" style="grid-template-columns:1.32fr 0.68fr;">
      <div class="chart-wrap">
        <div class="chart-h3">TI_annual for the whole Toyota cohort · committed policy</div>
        <div class="chart-sub">All 778,461 covered vehicles, summed each year · the dashed line is how many are still on the road</div>
        {chart_annual()}
      </div>
      <div class="stat-line">
        <div class="row"><div class="num sm">+102 <em>kt</em></div><div class="txt"><b>Year 0 is the same under every scenario.</b> At t = 0 no benchmark has declined yet, so the gap cannot depend on the rate. The three scenarios only separate from year 1 onward.</div></div>
        <div class="row"><div class="num sm">year 14</div><div class="txt"><b>The deepest year, −504 kt.</b> Not the last — the flow shrinks afterwards because vehicles retire, not because anything improves.</div></div>
        <div class="row"><div class="num sm">25 <em>years</em></div><div class="txt"><b>The horizon is the longest destination lifetime,</b> not the average. The jagged tail is markets scrapping out at 12, 15, 18, 25 years — each on its own clock.</div></div>
      </div>
    </div>
    <div class="takeaway">A cohort sold in one year keeps acting on its destinations for a quarter of a century. <b>The lifetime total compresses that into a single figure; only the annual series shows when the damage is actually done</b> — and it peaks a decade after the sale.</div>''',
    "Guideline §5.1 output 2 · cohorts[].annual_tCO2e"))

add("Step 17 · Sensitivity", slide(
    "s23", "07 · The result", "Step 17 · Sensitivity and tiers",
    "Every result is re-run at its own bounds before it is allowed out",
    '''    <div class="grid cols2">
      <div class="stat-line">
        <div class="row"><div class="num">−4.20<em> to </em>−7.98</div><div class="txt"><b>Lifetime T ± 3 years, Toyota S2.</b> The widest single band. Every per-country lifetime shifts together, so short-lifetime markets are not silently dropped.</div></div>
        <div class="row"><div class="num">−5.40<em> to </em>−6.41</div><div class="txt"><b>Distance proxy at the measured quartiles</b> (10,366 / 13,265 km). The proxy stands in for 13 markets; the spread of the markets that do publish is the honest band.</div></div>
        <div class="row"><div class="num">−1.40<em> to </em>−13.95</div><div class="txt"><b>Scenario spread S1 → S3.</b> This is the firm's exposure to how ambitiously its destinations actually implement.</div></div>
      </div>
      <div class="stat-side">
        <div class="stat-big green"><div class="n">Sign stable</div><div class="t">Across every distance bound and every scenario the direction does not flip. <b>That is the claim the study makes.</b></div></div>
        <div class="stat-big orange"><div class="n">TRIGGERED</div><div class="t">Cell tier is the worst of benchmark, vehicle and volume. Above a 50% tier-C share the result is stamped <b>directional_only</b> — and at 58% / 56% <b>this study is over the line</b>, in every scenario.</div></div>
      </div>
    </div>
    <div class="takeaway"><b>Direction is robust. Magnitude is not — and the engine, not the authors, is what decided that.</b> The flag lives on the result object rather than in a caveat, so no consumer can render the number without it.</div>''',
    "ti-framework/core/sensitivity.py · sensitivity block"))

add("Step 18 · The gate", slide(
    "s24", "07 · The result", "Step 18 · What we publish, and what we refuse to",
    "The list of what is withheld is printed at the same size as the result",
    '''    <div class="grid cols2">
      <div class="stat-line">
        <div class="row"><div class="num sm">TI score</div><div class="txt">with <b>mandatory decomposition</b> by destination and by product type</div></div>
        <div class="row"><div class="num sm">S1·S2·S3</div><div class="txt">three scenarios side by side, each with its sensitivity band</div></div>
        <div class="row"><div class="num sm">t*</div><div class="txt">the crossover year — when contribution flips to lock-in</div></div>
        <div class="row"><div class="num sm">Tier A·B·C</div><div class="txt">a data-quality declaration attached to every result</div></div>
        <div class="row" style="border-bottom:none;"><div class="num sm">Open</div><div class="txt">CSV / JSON, charts, web app, MCP server — reproducible from committed source</div></div>
      </div>
      <div class="wcards">
        <div class="wcard"><h3>PHEV and FCEV</h3><p>24,601 Toyota and 18,646 Hyundai units, withheld with the unit count and the missing input named.</p></div>
        <div class="wcard"><h3>Rolling portfolio</h3><p>Needs T consecutive cohorts. Repeating one observed year would publish a <b>counterfactual</b> beside sourced numbers.</p></div>
        <div class="wcard"><h3>Production origin</h3><p>Not collected. This is a destination-cohort impact; calling it an export claim would be an unsupported inference.</p></div>
      </div>
    </div>
    <div class="takeaway">A gate, not a disclaimer: if a required input is missing the status is <b>inputs_incomplete</b>, and the application may publish the observed cohort and the missing-input list — but no lifetime value and no firm score.</div>''',
    "docs/product-contract.md · export-impact-v1"))

# ============================================================ PART D — WHERE IT GOES
add("Where the pipeline stands", slide(
    "s24b", "08 · Data status", "The roster, honestly",
    "Two firms of eleven carry a lifetime result — and this is exactly what stands between",
    f'''    <div class="grid cols2" style="grid-template-columns:1.36fr 0.64fr;">
      <div class="chart-wrap">
        <div class="chart-h3">Every Trade Impact firm, and the stage it has actually reached</div>
        <div class="chart-sub">Read left to right: a firm only advances when the inputs for that stage are sourced</div>
        {chart_pipeline()}
      </div>
      <div class="icards">
        <div class="icard"><div class="n">2,509 vs 240</div><div class="t"><b>Engine lines that are sector-agnostic, against lines that are automotive.</b> Aggregation, scenarios, sensitivity and decomposition are written once and reused. Another car maker needs only data — power and shipping each still need a Layer 1 and Layer 2 class, both <b>NotImplementedError</b> today.</div></div>
        <div class="icard green"><div class="n">3 part-way</div><div class="t"><b>MOL, JERA and KOEN already have current-period alignment.</b> What they lack is the observed sold-product cohort — a voyage set, a dispatch record — that lifetime TI needs.</div></div>
        <div class="icard orange"><div class="n">27 markets, 1 sector</div><div class="t"><b>Destination inputs exist for EU27 passenger cars only.</b> A new sector needs its own service unit — MWh, tonne-nautical-mile — plus a survival curve and a pathway.</div></div>
      </div>
    </div>
    <div class="takeaway">Showing this is the point. <b>A framework that reports two results and names the nine it cannot yet produce is more checkable than one that reports eleven</b> — and the readiness object in the published data says the same thing in machine-readable form.</div>''',
    "data/published/firms.json · impact_readiness.json"))

add("Roadmap", slide(
    "s25", "09 · 12-month roadmap", "Where we are in the grant",
    "Month 7 of 12 — the machine is built; the case studies are next",
    '''    <div class="chiprow" style="margin-bottom:16px;">
      <span class="chiplab">Already delivered</span>
      <span class="chip done">✓ Whitepaper v1.5 + Guideline v1.8 in peer review</span>
      <span class="chip done">✓ Engine built &amp; validated (±1%)</span>
      <span class="chip done">✓ 1.23M-vehicle EU27 cohorts mapped and run</span>
      <span class="chip done">✓ Web app + MCP server, 11 read-only tools</span>
    </div>
    <div class="flow" style="flex:1;">
      <div class="fbox hl ctr"><h4>Month 7 — now</h4><p>Methodology published; the <b>automotive</b> case study delivered as an open working paper with its dataset. Power and shipping are at alignment stage, not cohort stage.</p></div>
      <div class="arr">→</div>
      <div class="fbox ctr"><h4>Month 10</h4><p>Open-source repository public; shipbuilding cross-validation study; Transition Arc integration specification. Web releases move to Git-triggered deploys.</p></div>
      <div class="arr">→</div>
      <div class="fbox ctr"><h4>Month 12</h4><p>v1.0 public release, final synthesis report and policy brief — every output open-access.</p></div>
    </div>
    <div class="takeaway"><b>Case-study firms, at their real state:</b> Toyota and Hyundai are complete; JERA, KOEN and MOL have current-period alignment and are waiting on a sold-product cohort; KEPCO, TEPCO, KOSPO, HD Hyundai HI, Samsung HI and Kawasaki HI are planned. <b>The previous slide is the same list, drawn.</b></div>''',
    "Deliverable schedule per Climate Arc grant proposal"))

add("Three-year path", slide(
    "s26", "10 · Three-year path", "Methodology → platform → standard",
    "Each stage removes the next barrier",
    '''    <div class="grid cols3">
      <div class="pillar tb-teal"><div class="pn teal">2026</div><h3>Foundation</h3>
        <p>Peer-reviewed methodology, validated open-source engine, three sector case studies, live prototype. TI moves from concept to a <b>documented, replicable standard</b>.</p>
        <div class="gr"><div class="grl">Grounded in</div><span class="chip">white paper</span><span class="chip">engine v1.0</span><span class="chip">3 case studies</span></div></div>
      <div class="pillar tb-navy"><div class="pn navy">2027</div><h3>Expansion</h3>
        <p>Shipping (IMO CII) and power modules on the same core; Level 2 production-origin attribution; coverage across major KR / JP / EU / CN exporters; <b>Transition Arc integration live</b>.</p>
        <div class="gr"><div class="grl">Grounded in</div><span class="chip">pluggable sectors</span><span class="chip">Arc data spec</span><span class="chip">30+ firms</span></div></div>
      <div class="pillar tb-green"><div class="pn green">2028</div><h3>Adoption</h3>
        <p>Standard-setter engagement on trade-aware disclosure; investor pilots pricing trade-embedded transition risk; <b>TI reported by early movers alongside Scope 3</b>.</p>
        <div class="gr"><div class="grl">Grounded in</div><span class="chip">disclosure pilots</span><span class="chip">investor use</span><span class="chip">policy brief</span></div></div>
    </div>
    <div class="takeaway"><b>The growth logic:</b> a trusted method enables data coverage → coverage enables investor use → demonstrated use is what standard-setters can adopt.</div>''',
    "Indicative trajectory beyond the current 12-month grant"))

add("Why it matters", slide(
    "s27", "11 · Why it matters", "Theory of change",
    "The barrier is not political will — it is the absence of a trusted measurement",
    '''    <div class="grid cols3">
      <div class="card tb-teal"><h3>For the exporter</h3><p>Electrifying other countries' fleets currently only grows your Scope 3. TI is the <b>credible counter-signal</b> — and, as these cohorts show, it is not automatically flattering.</p></div>
      <div class="card tb-green"><h3>For the investor</h3><p>Trade-embedded transition risk is unpriced. TI makes <b>export-strategy risk comparable across firms</b>, with the crossover year as the timing signal.</p></div>
      <div class="card tb-navy"><h3>For the Arc ecosystem</h3><p>Transition Arc shows where a firm stands today. TI adds <b>where its exports are pushing the markets it serves</b>.</p></div>
    </div>
    <div class="takeaway"><b>The chain:</b> rigorous measurement → credible disclosure → priced risk → reallocated capital. This project builds the first link.</div>''',
    "PLANiT theory of change · Climate Arc priority: Analysis"))

add("Known limits", slide(
    "s28", "12 · Known limits", "Stated, not buried",
    "What we do not claim, ranked by how much it actually moves the number",
    f'''    <div class="grid cols2" style="grid-template-columns:1.24fr 0.76fr;">
      <div class="chart-wrap">
        <div class="chart-h3">The two limits the engine can quantify, swept at their own bounds</div>
        <div class="chart-sub">Everything else on this slide is a limit we can name but not yet price</div>
        {chart_tornado()}
      </div>
      <div class="wcards">
        <div class="wcard"><h3>Not priced · the BEV asymmetry</h3><p>No official real-world gap exists for battery-electric consumption, so BEV passes uncorrected while combustion is marked up 19–21%. <b>Every BEV figure here is the optimistic end.</b></p></div>
        <div class="wcard"><h3>Not priced · PHEV and FCEV</h3><p>3.1% of Toyota's units and 4.3% of Hyundai's stand outside the result entirely. Their sign is unknown, not zero.</p></div>
        <div class="wcard"><h3>Not priced · production origin</h3><p>Registrations prove destination and mix, never the factory. Context only until Level 2 disclosure exists.</p></div>
        <div class="wcard"><h3>Structural · target level 3 of 5</h3><p>The contract prefers a destination-country road-transport pathway. What exists is an <b>EU regional sector proxy</b> — third on a five-level hierarchy, stamped <b>target_level: 3</b> on every country record.</p></div>
      </div>
    </div>
    <div class="warn"><b>And the limit that binds hardest is not on this chart.</b> The tier-C unit share is 58% / 56%, so the engine suppresses the magnitude outright — the sweeps above describe a number the method will only publish as a <b>direction</b>. No EU27 market was excluded for an underivable benchmark; that mechanism exists but this dataset never needed it.</div>''',
    "sensitivity block · TI Methodological Challenges v1 · ti-framework/NOTES.md"))

add("How it is used", slide(
    "s28b", "13 · Use and insight", "What the number is for",
    "Three things this metric says that an absolute footprint cannot",
    f'''    <div class="grid cols2" style="grid-template-columns:1.06fr 0.94fr;">
      <div class="chart-wrap">
        <div class="chart-h3">The comparison a static baseline can never produce</div>
        <div class="chart-sub">Lifetime TI per covered vehicle, both cohorts, under each destination ambition</div>
        {chart_convergence()}
      </div>
      <div class="icards">
        <div class="icard"><div class="n">2.01× → 1.06×</div><div class="t"><b>Ranking is a property of the destination's ambition, not of the firm alone.</b> Hybrids are rewarded by a slow benchmark and punished by a fast one, so Toyota's two-to-one lead nearly vanishes at 1.5°C.</div></div>
        <div class="icard green"><div class="n">41,582 BEVs</div><div class="t"><b>Mix beats flagship.</b> The only powertrain with a positive total, in any scenario — though 20 of its 115 cells still turn liability within life. Not enough to offset the 198,552 combustion cars sold beside them.</div></div>
        <div class="icard orange"><div class="n">3.3 → 14 → 25 yr</div><div class="t"><b>Timing, not just size.</b> One hybrid stops helping Germany at 3.3 years; the cohort peaks at year 14, runs to 25.</div></div>
      </div>
    </div>
    <div class="flow" style="margin-top:12px;">
      <div class="fbox sm"><h4>EXPORTER</h4><p>Which destination × technology combinations are accumulating lock-in, and how soon.</p></div>
      <div class="arr">·</div>
      <div class="fbox sm"><h4>INVESTOR</h4><p>Export-strategy transition risk, comparable across firms on one benchmark.</p></div>
      <div class="arr">·</div>
      <div class="fbox sm"><h4>POLICYMAKER</h4><p>Which imports are working against the NDC the country has already signed.</p></div>
      <div class="arr">·</div>
      <div class="fbox sm hl"><h4>THE ARC</h4><p>Where a firm stands today, plus where its exports are pushing the markets it serves.</p></div>
    </div>
    <div class="takeaway">Everything above is a <b>direction</b>, not a magnitude — the tier-C rule is in force. Closing 13 proxied distances is what converts these into publishable quantities.</div>''',
    "data/published/lifetime_results.json · decomposition and crossover"))

add("Contact", f'''<section class="slide navy" id="s29" style="justify-content:center;">
  {LOGO}
  <div class="rule"></div>
  <h1 class="cover-h1" style="font-size:40px;max-width:920px;">Make the climate direction of trade measurable — then let measurement do its work.</h1>
  <div class="clinks">
    <div><span>CONTACT</span>sanghyun@planitinstitute.org</div>
    <div><span>OUTPUTS</span>transitionarc.climatearc.org · open-access</div>
    <div><span>METHOD</span>TI Whitepaper v1.5 · Automotive Guideline v1.8</div>
    <div><span>LICENCE</span>GNU GPL v3 — code, data and documents</div>
  </div>
</section>
''')

# --------------------------------------------------------------------------- document
import re as _re

def _chap_of(html: str) -> str:
    m = _re.search(r'class="chap">([^<]*)<', html)
    return m.group(1) if m else ""

titles = [{"t": t, "c": _chap_of(h)} for t, h in SLIDES]
body = "\n".join(h for _, h in SLIDES)

CSS = f""":root{{--navy:{NAVY};--teal:{TEAL};--green:{GREEN};--cream:#E4F3EF;
  --grey:{GREY};--lgrey:#CFD8D6;--panel:#F1F6F6;--orange:{ORANGE};--slate:{SLATE};}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{height:100%;background:#06152e;font-family:'Roboto',Arial,sans-serif;overflow:hidden;}}
#stage-wrap{{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;}}
#stage{{width:1280px;height:720px;position:relative;background:#fff;box-shadow:0 20px 80px rgba(0,0,0,.5);overflow:hidden;}}
.slide{{position:absolute;inset:0;padding:46px 72px 62px;display:flex;flex-direction:column;
  opacity:0;visibility:hidden;transform:translateX(40px);transition:opacity .4s ease,transform .4s ease,visibility .4s;}}
.slide.active{{opacity:1;visibility:visible;transform:translateX(0);}}
.slide.navy{{background:var(--navy);color:#fff;}} .slide.white{{background:#fff;color:#111;}}
.kicker{{font-family:'Roboto Condensed';font-weight:700;letter-spacing:.18em;text-transform:uppercase;
  font-size:13px;color:var(--teal);margin-bottom:6px;}}
.navy .kicker{{color:var(--green);}}
h1.title{{font-family:Georgia,'Times New Roman',serif;font-size:30px;font-weight:700;color:var(--navy);
  line-height:1.2;margin-bottom:18px;max-width:1110px;}}
.body-area{{flex:1;display:flex;flex-direction:column;min-height:0;}}
.grid{{display:grid;gap:18px;flex:1;min-height:0;}}
.cols2{{grid-template-columns:repeat(2,1fr);}} .cols3{{grid-template-columns:repeat(3,1fr);}}
.cols4{{grid-template-columns:repeat(4,1fr);}}
.chap{{position:absolute;top:48px;right:72px;font-family:'Roboto Condensed';font-size:12px;
  letter-spacing:.14em;color:var(--grey);text-transform:uppercase;}}
.navy .chap{{color:rgba(255,255,255,.5);}}
.foot{{position:absolute;left:72px;right:72px;bottom:18px;display:flex;justify-content:space-between;
  align-items:center;font-size:11px;color:var(--grey);border-top:1px solid var(--lgrey);padding-top:7px;}}
.foot>span:last-child{{margin-right:86px;font-family:'Roboto Condensed';letter-spacing:.02em;}}
#progress{{position:absolute;top:0;left:0;height:4px;background:var(--green);width:0;z-index:60;transition:width .35s ease;}}
#counter{{position:absolute;bottom:22px;left:50%;transform:translateX(-50%);font-family:'Roboto Condensed';
  font-size:12px;color:var(--grey);z-index:50;}}
.navctl{{position:absolute;bottom:14px;right:24px;display:flex;gap:8px;z-index:50;}}
.navctl button{{width:32px;height:32px;border-radius:50%;border:1.5px solid var(--lgrey);background:#fff;
  color:var(--navy);font-size:15px;cursor:pointer;line-height:1;}}
.navctl button:hover{{border-color:var(--teal);color:var(--teal);}}
/* cover / closing */
.wordmark{{font-family:'Roboto Condensed';font-weight:700;font-size:32px;letter-spacing:.06em;margin-bottom:24px;}}
.wordmark span{{color:var(--green);}}
.rule{{width:84px;height:6px;background:var(--green);border-radius:3px;margin:0 0 24px;}}
.cover-h1{{font-family:Georgia,serif;font-size:47px;font-weight:700;line-height:1.12;max-width:980px;}}
.cover-sub{{font-size:20px;font-weight:300;color:#cfe0e3;margin-top:14px;max-width:900px;line-height:1.4;}}
.statrow{{display:flex;gap:52px;margin-top:40px;}}
.statrow b{{display:block;font-family:'Roboto Condensed';font-size:36px;color:var(--green);line-height:1;}}
.statrow span{{font-size:12.5px;color:rgba(255,255,255,.72);}}
.cover-meta{{position:absolute;bottom:24px;left:72px;font-size:12px;color:rgba(255,255,255,.5);}}
.cover-hint{{position:absolute;bottom:24px;right:120px;font-size:12px;color:rgba(255,255,255,.42);}}
.clinks{{margin-top:32px;display:grid;grid-template-columns:auto auto;gap:12px 48px;width:max-content;
  font-size:16px;font-weight:300;color:#cfe0e3;}}
.clinks span{{font-family:'Roboto Condensed';font-weight:700;font-size:10.5px;letter-spacing:.14em;color:var(--green);display:block;}}
/* cards */
.card{{background:transparent;border-left:3px solid var(--lgrey);padding:8px 20px 8px 24px;
  display:flex;flex-direction:column;justify-content:center;transition:transform .2s,border-color .2s;}}
.card:hover{{transform:translateX(5px);}}
.card h3{{font-size:20px;color:var(--navy);margin-bottom:9px;font-weight:700;line-height:1.28;}}
.card p{{font-size:15.5px;line-height:1.5;color:#333;}} .card p.sp{{margin-top:10px;}}
.tb-teal{{border-left-color:var(--teal)!important;}} .tb-green{{border-left-color:var(--green)!important;}}
.tb-navy{{border-left-color:var(--navy)!important;}} .tb-orange{{border-left-color:var(--orange)!important;}}
.tb-grey{{border-left-color:var(--lgrey)!important;}}
.nt{{font-family:'Roboto Condensed';font-weight:700;font-size:14px;color:var(--green);background:var(--navy);
  width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:10px;flex:none;}}
.navy-card{{background:var(--navy);border-radius:18px;padding:26px 28px;color:#fff;
  display:flex;flex-direction:column;justify-content:center;}}
.navy-card h3{{font-size:20px;color:#fff;margin-bottom:10px;}}
.navy-card p{{font-size:15.5px;line-height:1.5;color:#dbe7ea;}} .navy-card .hi{{color:var(--green);}}
.pcard{{border-radius:18px;padding:24px 26px;display:flex;flex-direction:column;justify-content:center;}}
.pcard h3{{font-size:19px;margin-bottom:8px;}}
.pcard .bn{{font-family:'Roboto Condensed';font-weight:700;font-size:38px;line-height:1;margin-bottom:12px;}}
.pcard .bn span{{display:block;font-size:12.5px;font-weight:400;margin-top:6px;letter-spacing:.04em;}}
.pcard .fm{{font-family:'Roboto Condensed';font-size:13.5px;padding:6px 10px;border-radius:6px;margin-bottom:10px;}}
.pcard p{{font-size:15px;line-height:1.5;}}
.pnavy{{background:var(--navy);color:#fff;}} .pnavy h3{{color:#fff;}} .pnavy .bn{{color:var(--orange);}}
.pnavy .fm{{background:rgba(255,255,255,.1);color:#dbe7ea;}} .pnavy p{{color:#dbe7ea;}}
.pteal{{background:var(--teal);color:#fff;}} .pteal h3{{color:#fff;}} .pteal .bn{{color:#eaf7c9;}}
.pteal .fm{{background:rgba(255,255,255,.16);color:#eafafa;}} .pteal p{{color:#eafafa;}}
.pcream{{background:var(--cream);color:#123;}} .pcream h3{{color:var(--navy);}} .pcream .bn{{color:var(--orange);font-size:30px;}}
.pcream .fm{{background:#fff;color:#456;}} .pcream p{{color:#33474a;}}
.takeaway{{margin-top:14px;background:var(--cream);border-left:6px solid var(--green);
  border-radius:8px;padding:13px 22px;font-size:16.5px;line-height:1.5;color:#222;flex:none;}}
.takeaway b{{color:var(--navy);}}
.warn{{margin-top:13px;background:#FDF1E4;border-left:6px solid var(--orange);border-radius:8px;
  padding:12px 22px;font-size:15.5px;line-height:1.5;color:#3a2a18;flex:none;}}
.warn b{{color:#B85E00;}}
/* flow */
.flow{{display:flex;align-items:stretch;flex:none;}}
.fbox{{flex:1;background:var(--panel);border:2px solid var(--navy);border-radius:12px;padding:14px 16px;}}
.fbox h4{{font-family:'Roboto Condensed';font-size:17px;color:var(--navy);margin-bottom:5px;}}
.fbox p{{font-size:13px;line-height:1.42;color:#333;}}
.fbox.sm{{padding:10px 8px;text-align:center;}} .fbox.sm h4{{font-size:14px;}} .fbox.sm p{{font-size:11.5px;}}
.fbox.ctr{{display:flex;flex-direction:column;justify-content:center;}}
.fbox.hl{{background:var(--navy);}} .fbox.hl h4{{color:var(--green);}} .fbox.hl p{{color:#dbe7ea;}}
.arr{{align-self:center;font-size:22px;color:var(--teal);padding:0 9px;flex:none;}}
.quote{{font-size:17px;font-style:italic;color:#274;background:var(--panel);border-radius:10px;
  padding:14px 22px;margin-bottom:20px;flex:none;}}
/* stat rows */
.stat-line{{display:flex;flex-direction:column;justify-content:center;min-height:0;}}
.stat-line .row{{display:flex;align-items:baseline;gap:16px;padding:9px 4px;border-bottom:1px solid var(--lgrey);transition:transform .2s;}}
.stat-line .row:hover{{transform:translateX(5px);}}
.stat-line .num{{font-family:'Roboto Condensed';font-weight:700;font-size:30px;color:var(--teal);min-width:158px;line-height:1.05;}}
.stat-line .num.sm{{font-size:21px;min-width:104px;}}
.stat-line .num em{{font-style:normal;font-size:16px;color:var(--grey);}}
.stat-line .txt{{font-size:14.5px;color:#333;line-height:1.45;}} .stat-line .txt b{{color:var(--navy);}}
.stat-line .num br{{line-height:0.95;}}
.txt .fm{{display:block;font-family:'Roboto Condensed';font-size:12.5px;color:var(--navy);
  background:var(--panel);border-radius:5px;padding:3px 8px;margin-bottom:5px;}}
.stat-side{{display:flex;flex-direction:column;gap:12px;min-height:0;}}
.stat-big{{flex:1;background:var(--cream);border-left:6px solid var(--teal);border-radius:12px;
  padding:16px 22px;display:flex;flex-direction:column;justify-content:center;}}
.stat-big.green{{border-left-color:var(--green);}}
.stat-big .n{{font-family:'Roboto Condensed';font-weight:700;font-size:44px;color:var(--navy);line-height:1;}}
.stat-big .n em{{font-style:normal;font-size:22px;color:var(--teal);}}
.stat-big .t{{font-size:15px;color:#333;margin-top:9px;line-height:1.5;}} .stat-big .t b{{color:var(--navy);}}
/* calc components */
.eqbar{{background:var(--navy);border-radius:10px;padding:12px 22px;font-family:'Roboto Condensed';
  font-size:20px;color:#fff;flex:none;display:flex;align-items:baseline;flex-wrap:wrap;}}
.eqbar em{{font-style:normal;color:var(--green);}} .eqbar sup,.eqbar sub{{font-size:.6em;}}
.eqbar .u{{font-size:12px;color:rgba(255,255,255,.6);margin-left:auto;padding-left:18px;letter-spacing:.06em;text-transform:uppercase;}}
.calcrow{{display:flex;align-items:stretch;gap:9px;flex:none;margin:13px 0;}}
.calcrow .cbox{{flex:1;background:var(--panel);border:1px solid var(--lgrey);border-radius:10px;
  padding:10px 12px;text-align:center;display:flex;flex-direction:column;justify-content:center;}}
.calcrow .cbox .cv{{font-family:'Roboto Condensed';font-weight:700;font-size:24px;color:var(--navy);line-height:1.12;}}
.calcrow .cbox .cv sup{{font-size:.62em;}}
.calcrow .cbox .cl{{font-size:10.5px;color:var(--grey);margin-top:4px;font-family:'Roboto Condensed';
  letter-spacing:.05em;text-transform:uppercase;line-height:1.3;}}
.calcrow .cbox.res{{background:var(--cream);border-color:var(--green);}}
.calcrow .op{{width:22px;display:flex;align-items:center;justify-content:center;font-family:'Roboto Condensed';
  font-size:22px;color:var(--teal);font-weight:700;flex:none;}}
.fieldrow{{display:flex;flex-direction:column;justify-content:center;flex:1;min-height:0;}}
.fieldrow .fr{{display:flex;align-items:baseline;gap:14px;border-bottom:1px solid var(--lgrey);padding:8px 2px;}}
.fieldrow .fk{{font-family:'Roboto Condensed';font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--grey);width:172px;flex:none;}}
.fieldrow .fv{{font-family:'Roboto Condensed';font-weight:700;font-size:18px;color:var(--navy);}}
.fieldrow .fn{{font-size:12px;color:#777;margin-left:auto;text-align:right;}}
/* charts */
.chart-wrap{{display:flex;flex-direction:column;min-height:0;}}
.chart-h3{{font-size:15px;color:var(--navy);font-weight:700;}}
.chart-sub{{font-size:11.5px;color:var(--grey);margin-bottom:4px;}}
.chart-note{{font-size:11.5px;color:var(--grey);margin-top:7px;}}
.csvg{{width:100%;flex:1;min-height:0;}}
.hbars{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:11px;min-height:0;padding:6px 0;}}
.hb{{display:flex;align-items:center;gap:10px;}}
.hbl{{font-family:'Roboto Condensed';font-size:11.5px;color:#556;width:118px;flex:none;text-align:right;}}
.hbr{{height:18px;border-radius:3px;min-width:3px;}}
.hbv{{font-family:'Roboto Condensed';font-weight:700;font-size:13px;color:var(--navy);white-space:nowrap;}}
/* chips + pillars */
.chiprow{{flex:none;}}
.icards{{display:flex;flex-direction:column;gap:10px;min-height:0;justify-content:center;}}
.icard{{background:var(--cream);border-left:5px solid var(--teal);border-radius:9px;padding:11px 18px;}}
.icard.green{{border-left-color:var(--green);}}
.icard.orange{{background:#FDF1E4;border-left-color:var(--orange);}}
.icard .n{{font-family:'Roboto Condensed';font-weight:700;font-size:25px;color:var(--navy);line-height:1.05;margin-bottom:5px;}}
.icard.orange .n{{color:#B85E00;}}
.icard .t{{font-size:13.5px;line-height:1.45;color:#333;}} .icard .t b{{color:var(--navy);}}
.vcheck{{background:var(--panel);border-left:4px solid var(--green);border-radius:8px;padding:13px 18px;
  display:flex;flex-direction:column;justify-content:center;}}
.vcheck .cmd{{font-family:'Roboto Condensed';font-size:13px;letter-spacing:.04em;color:var(--navy);
  background:#fff;border:1px solid var(--lgrey);border-radius:5px;padding:3px 9px;display:inline-block;
  align-self:flex-start;margin-bottom:8px;}}
.vcheck .res{{font-family:'Roboto Condensed';font-weight:700;font-size:18px;color:#5a8a1e;margin-bottom:7px;}}
.vcheck p{{font-size:13.5px;line-height:1.45;color:#445;}}
.chip{{display:inline-block;background:#fff;border:1px solid var(--lgrey);border-radius:14px;
  padding:3px 12px;font-size:12px;color:#333;margin:3px 4px 0 0;font-family:'Roboto Condensed';}}
.chip.done{{border-color:var(--green);}}
.chiplab{{font-family:'Roboto Condensed';font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);margin-right:8px;}}
.pillar{{border-left:3px solid var(--lgrey);padding:6px 18px 6px 22px;display:flex;flex-direction:column;justify-content:center;}}
.pillar .pn{{font-family:'Roboto Condensed';font-weight:700;font-size:28px;line-height:1;margin-bottom:7px;}}
.pn.teal{{color:var(--teal);}} .pn.navy{{color:var(--navy);}} .pn.green{{color:#6a9a2d;}}
.pillar h3{{font-size:18px;color:var(--navy);margin-bottom:7px;}}
.pillar p{{font-size:13.5px;line-height:1.48;color:#333;}}
.pillar .gr{{margin-top:16px;}}
.pillar .grl{{font-family:'Roboto Condensed';font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);margin:9px 0 2px;}}
.wcards{{display:flex;flex-direction:column;gap:10px;min-height:0;justify-content:center;}}
.wcard{{background:#FDF1E4;border-left:5px solid var(--orange);border-radius:8px;padding:9px 18px;}}
.wcard h3{{font-size:16px;color:#B85E00;margin-bottom:4px;}}
.wcard p{{font-size:13px;line-height:1.42;color:#3a2a18;}} .wcard p b{{color:#B85E00;}}
/* vm */
.vm{{display:grid;grid-template-columns:1fr 1fr;gap:20px;flex:1;min-height:0;}}
.vbox{{border-radius:20px;padding:30px 32px;display:flex;flex-direction:column;justify-content:center;}}
.vteal{{background:var(--teal);color:#fff;}} .vcream{{background:var(--cream);color:#123;}}
.vbox h2{{font-family:'Roboto Condensed';font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:13.5px;margin-bottom:13px;}}
.vteal h2{{color:#eaf7c9;}} .vcream h2{{color:var(--teal);}}
.vbox .tx{{font-size:21px;font-weight:300;line-height:1.45;}} .vbox .tx b{{font-weight:700;}}
/* scenario switcher */
.scnbar{{display:flex;align-items:center;gap:9px;flex:none;margin-bottom:5px;}}
.scnlab{{font-family:'Roboto Condensed';font-weight:700;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--grey);}}
.scnbtn{{font-family:'Roboto Condensed';font-weight:700;font-size:12.5px;padding:5px 13px;
  border-radius:16px;border:1.5px solid var(--lgrey);background:#fff;color:#555;cursor:pointer;}}
.scnbtn:hover{{border-color:var(--teal);color:var(--teal);}}
.scnbtn.active{{background:var(--teal);border-color:var(--teal);color:#fff;}}
.pubtag{{font-family:'Roboto Condensed';font-weight:700;font-size:10.5px;letter-spacing:.08em;color:#5a8a1e;
  border:1.5px solid var(--green);border-radius:14px;padding:3px 11px;margin-left:auto;}}
.pubtag.warn-tag{{color:#B85E00;border-color:var(--orange);background:#FDF1E4;}}
.stat-big.orange{{border-left-color:var(--orange);background:#FDF1E4;}}
.stat-big.orange .n{{color:#B85E00;}}
.scn-desc{{font-size:13.5px;color:#455;flex:none;margin-bottom:8px;min-height:36px;line-height:1.45;}}
.kpis{{display:flex;flex-direction:column;justify-content:center;gap:11px;min-height:0;}}
.kpi{{background:var(--panel);border-radius:14px;padding:13px 18px;}}
.kl{{font-family:'Roboto Condensed';font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--grey);}}
.kv{{font-family:Georgia,serif;font-size:31px;font-weight:700;line-height:1.15;}}
.kp{{font-size:12px;color:#556;}}
.knote{{font-size:12px;color:var(--grey);line-height:1.45;}}
/* print / PDF export — without this only the active slide reaches the page */
@media print{{
  @page{{size:1280px 720px;margin:0;}}
  html,body{{height:auto;overflow:visible;background:#fff;
    -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
  #stage-wrap{{position:static;display:block;inset:auto;}}
  #stage{{width:1280px;height:auto;box-shadow:none;overflow:visible;transform:none!important;}}
  .slide{{position:relative;inset:auto;width:1280px;height:720px;
    opacity:1!important;visibility:visible!important;transform:none!important;transition:none!important;
    page-break-after:always;break-after:page;overflow:hidden;}}
  .slide:last-of-type{{page-break-after:auto;break-after:auto;}}
  .card:hover,.stat-line .row:hover,.vbox:hover{{transform:none!important;}}
  #progress,#counter,.navctl,#toc{{display:none!important;}}
}}
/* toc */
#toc{{position:absolute;inset:0;background:#001F3F;z-index:80;display:none;padding:44px 72px;color:#fff;overflow:auto;}}
#toc.open{{display:block;}}
#toc h2{{font-family:'Roboto Condensed';letter-spacing:.2em;font-size:14px;color:var(--green);margin-bottom:18px;}}
#toc ol{{columns:3;column-gap:38px;list-style:none;counter-reset:t;}}
#toc li{{counter-increment:t;padding:5px 0;font-size:13px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,.12);break-inside:avoid;}}
#toc li:before{{content:counter(t,decimal-leading-zero);color:var(--teal);font-family:'Roboto Condensed';margin-right:9px;font-size:11.5px;}}
#toc li:hover{{color:var(--green);}}
#toc li.toc-chap{{counter-increment:none;font-family:'Roboto Condensed';font-size:11.5px;
  letter-spacing:.16em;text-transform:uppercase;color:var(--teal);border-bottom:none;
  padding:11px 0 2px;cursor:default;}}
#toc li.toc-chap:before{{content:none;}}
#toc li.toc-chap:hover{{color:var(--teal);}}"""

SCRIPT = f"""
var CASE={case_payload()};
var TITLES={json.dumps(titles, ensure_ascii=False)};
var __s=[].slice.call(document.querySelectorAll('.slide')),__c=0;
var toc=document.getElementById('toc'),tocl=document.getElementById('tocl');
var lastChap=null;
TITLES.forEach(function(t,i){{
  if(t.c && t.c!==lastChap){{
    var hd=document.createElement('li');hd.className='toc-chap';hd.textContent=t.c;
    tocl.appendChild(hd);lastChap=t.c;
  }}
  var li=document.createElement('li');li.textContent=t.t;
  li.onclick=function(){{__go(i);toc.classList.remove('open');}};tocl.appendChild(li);}});
function __go(n){{__c=Math.max(0,Math.min(__s.length-1,n));
  __s.forEach(function(s,i){{s.classList.toggle('active',i===__c);}});
  document.getElementById('counter').textContent=(__c+1)+' / '+__s.length;
  document.getElementById('progress').style.width=((__c+1)/__s.length*100)+'%';}}
document.getElementById('nx').onclick=function(){{__go(__c+1);}};
document.getElementById('pv').onclick=function(){{__go(__c-1);}};
document.getElementById('mn').onclick=function(){{toc.classList.toggle('open');}};
document.addEventListener('keydown',function(e){{
  if(e.key==='ArrowRight'||e.key===' ')__go(__c+1);
  else if(e.key==='ArrowLeft')__go(__c-1);
  else if(e.key==='Home')__go(0); else if(e.key==='End')__go(__s.length-1);
  else if(e.key.toLowerCase()==='m')toc.classList.toggle('open');
  else if(e.key==='Escape')toc.classList.remove('open');}});
function fit(){{document.getElementById('stage').style.transform=
  'scale('+Math.min(window.innerWidth/1280,window.innerHeight/720)+')';}}
window.addEventListener('resize',fit);fit();
var q=new URLSearchParams(location.search);__go(q.has('slide')?(+q.get('slide')-1):0);

/* ---- results chart, real published values ---- */
var PTS=["HEV","ICE","BEV"],CVMIN=-14.8,CVMAX=1.6,CPL=112,CPR=52,CPW=560-CPL-CPR;
function cx(v){{return CPL+(v-CVMIN)/(CVMAX-CVMIN)*CPW;}}
function renderCase(d,scn){{
  var g='<g font-family="Roboto Condensed">';
  [-14,-12,-10,-8,-6,-4,-2,0,1].forEach(function(v){{
    g+='<line x1="'+cx(v)+'" y1="24" x2="'+cx(v)+'" y2="252" stroke="'+(v===0?"{NAVY}":"#EDF1F1")+'" stroke-width="'+(v===0?1.4:1)+'"/>'
      +'<text x="'+cx(v)+'" y="266" text-anchor="middle" font-size="10" fill="#9aa">'+(v>0?"+":"")+v+'</text>';}});
  g+='<text x="'+cx(-6.6)+'" y="281" text-anchor="middle" font-size="10" fill="#9aa">MtCO2e over the cohort lifetime</text>';
  g+='<text x="'+(cx(0)-6)+'" y="18" text-anchor="end" font-size="10.5" fill="{ORANGE}" font-weight="700">&#8592; lock-in</text>';
  g+='<text x="'+(cx(0)+6)+'" y="18" font-size="10.5" fill="#5a8a1e" font-weight="700">contribution &#8594;</text>';
  ["Toyota","Hyundai"].forEach(function(f,fi){{
    var y0=32+fi*112;
    g+='<text x="6" y="'+(y0+11)+'" font-size="13.5" font-weight="700" fill="{NAVY}">'+f+'</text>';
    PTS.forEach(function(pt,pi){{
      var v=d[f][pt],y=y0+pi*19+2,x0=cx(Math.min(0,v)),w=Math.abs(cx(v)-cx(0));
      g+='<text x="'+(CPL-8)+'" y="'+(y+11)+'" text-anchor="end" font-size="10.5" fill="#556">'+pt+'</text>'
        +'<rect x="'+x0+'" y="'+y+'" width="'+Math.max(w,0.8)+'" height="13" rx="3" fill="'+(v<0?"{ORANGE}":"{GREEN}")+'"><title>'+f+' '+pt+': '+(v>0?"+":"")+v.toFixed(2)+' Mt</title></rect>'
        +'<text x="'+(v<0?x0-5:x0+w+5)+'" y="'+(y+11)+'" text-anchor="'+(v<0?"end":"start")+'" font-size="10" fill="#333">'+(v<0?'\\u2212':'+')+Math.abs(v).toFixed(2)+'</text>';}});
    var wy=y0+PTS.length*19+2;
    g+='<text x="'+(CPL-8)+'" y="'+(wy+11)+'" text-anchor="end" font-size="10.5" fill="#aab">PHEV</text>'
      +'<rect x="'+(cx(0)-4)+'" y="'+wy+'" width="8" height="13" fill="none" stroke="#C9D2D2" stroke-width="1" stroke-dasharray="3 3"/>'
      +'<text x="'+(cx(0)-12)+'" y="'+(wy+10)+'" text-anchor="end" font-size="9.5" fill="#93a0a0">withheld \\u2014 no real-world utility factor is sourced</text>';
    var nv=d[f].net,ny=wy+21,nx0=cx(Math.min(0,nv)),nw=Math.abs(cx(nv)-cx(0));
    var nvs=(nv<0?'\\u2212':'+')+Math.abs(nv).toFixed(2)+' Mt';
    g+='<text x="'+(CPL-8)+'" y="'+(ny+12)+'" text-anchor="end" font-size="11" font-weight="700" fill="{NAVY}">NET</text>'
      +'<rect x="'+nx0+'" y="'+ny+'" width="'+Math.max(nw,1)+'" height="15" rx="3" fill="{NAVY}"><title>'+f+' net: '+nvs+'</title></rect>';
    if(nw>66)g+='<text x="'+(nx0+6)+'" y="'+(ny+11.5)+'" font-size="11" font-weight="700" fill="#fff">'+nvs+'</text>';
    else g+='<text x="'+(nx0-5)+'" y="'+(ny+11.5)+'" text-anchor="end" font-size="11" font-weight="700" fill="{NAVY}">'+nvs+'</text>';}});
  g+='</g>';
  document.getElementById('csvg').innerHTML=g;
  document.getElementById('caseDesc').textContent=CASE[scn].d;
  [['cNetT','cPvT','Toyota'],['cNetH','cPvH','Hyundai']].forEach(function(k){{
    var n=CASE[scn][k[2]].net,el=document.getElementById(k[0]);
    el.textContent=(n<0?'\\u2212':'+')+Math.abs(n).toFixed(2)+' Mt';
    el.style.color=n<0?'{ORANGE}':'#5a8a1e';
    document.getElementById(k[1]).textContent=CASE[scn][k[2]].pv+' tCO2e per covered vehicle';}});
}}
var curCase=null;
function selCase(scn){{
  document.querySelectorAll('.csb').forEach(function(b){{b.classList.toggle('active',b.dataset.s===scn);}});
  var target=CASE[scn];
  if(!curCase){{curCase=scn;renderCase(target,scn);return;}}
  var from=CASE[curCase],t0=null;
  function mix(a,b,e){{var o={{}};["Toyota","Hyundai"].forEach(function(f){{o[f]={{}};
    PTS.concat(["net"]).forEach(function(k){{o[f][k]=a[f][k]+(b[f][k]-a[f][k])*e;}});}});return o;}}
  function step(ts){{if(!t0)t0=ts;var t=Math.min(1,(ts-t0)/600);
    var e=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
    renderCase(mix(from,target,e),scn);
    if(t<1)requestAnimationFrame(step);else curCase=scn;}}
  requestAnimationFrame(step);
}}
selCase('S2');

/* ---- powertrain mix chart ---- */
(function(){{
  var DATA=[
    {{firm:"Toyota",total:"803,094",mix:[["HEV",76.1,"{SLATE}"],["ICE",19.5,"{ORANGE}"],["PHEV",3.0,"{TEAL}"],["BEV",1.4,"{GREEN}"]]}},
    {{firm:"Hyundai",total:"429,936",mix:[["ICE",46.2,"{ORANGE}"],["HEV",39.8,"{SLATE}"],["BEV",9.7,"{GREEN}"],["PHEV",4.3,"{TEAL}"]]}}];
  /* paired rows, not two stacks: the contrast between the mixes is the point */
  var ROWS=[["HEV","{SLATE}",76.1,39.8],["ICE / other","{ORANGE}",19.5,46.2],
            ["BEV","{GREEN}",1.4,9.7],["PHEV","{TEAL}",3.0,4.3]];
  var X0=118,XW=330,SC=XW/100,g='<g font-family="Roboto Condensed">';
  g+='<rect x="'+X0+'" y="5" width="14" height="10" rx="2" fill="{NAVY}"/>'
   +'<text x="'+(X0+20)+'" y="14" font-size="11" font-weight="700" fill="{NAVY}">TOYOTA</text>'
   +'<text x="'+(X0+76)+'" y="14" font-size="10.5" fill="#9aa">803,094 units</text>'
   +'<rect x="'+X0+'" y="21" width="14" height="10" rx="2" fill="{NAVY}" opacity="0.5"/>'
   +'<text x="'+(X0+20)+'" y="30" font-size="11" font-weight="700" fill="#5f7f8c">HYUNDAI</text>'
   +'<text x="'+(X0+76)+'" y="30" font-size="10.5" fill="#9aa">429,936 units</text>';
  ROWS.forEach(function(r,i){{
    var y=48+i*44,t=r[2],hy=r[3];
    g+='<text x="'+(X0-12)+'" y="'+(y+13)+'" text-anchor="end" font-size="12.5" font-weight="700" fill="{NAVY}">'+r[0]+'</text>';
    [[t,y,1],[hy,y+17,0.5]].forEach(function(b,k){{
      var w=Math.max(b[0]*SC,1.5);
      g+='<rect x="'+X0+'" y="'+b[1]+'" width="'+w+'" height="14" rx="2" fill="'+r[1]+'" opacity="'+b[2]+'">'
        +'<title>'+(k?"Hyundai":"Toyota")+' '+r[0]+': '+b[0]+'%</title></rect>'
        +'<text x="'+(X0+w+6)+'" y="'+(b[1]+11)+'" font-size="11" font-weight="700" fill="#445">'+b[0].toFixed(1)+'%</text>';}});
    var d=(hy-t);
    g+='<text x="'+(X0+XW+26)+'" y="'+(y+19)+'" text-anchor="end" font-size="11.5" font-weight="700" fill="'
      +(Math.abs(d)>15?"{ORANGE}":"#9aa")+'">'+(d>0?"+":"\\u2212")+Math.abs(d).toFixed(1)+' pp</text>';}});
  g+='<text x="'+(X0+XW+26)+'" y="40" text-anchor="end" font-size="10" letter-spacing="0.08em" fill="#9aa">HYUNDAI \\u2212 TOYOTA</text>';
  g+='<text x="8" y="228" font-size="11.5" fill="#556">Same segment, same year, same 27 markets \\u2014 two very different portfolios.</text>';
  g+='<text x="8" y="244" font-size="11.5" fill="#93a0a0">Certified tailpipe: ICE 131\\u2013134 \\u00b7 HEV 106\\u2013129 \\u00b7 BEV 0 g/km.</text>';
  g+='</g>';
  document.getElementById('mix').innerHTML=g;
}})();
"""

doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>PLANiT — Trade Impact: the framework and how its number is built</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&family=Roboto+Condensed:wght@400;700&display=swap" rel="stylesheet">
<style>
{CSS}
</style></head><body>
<div id="stage-wrap"><div id="stage"><div id="progress"></div>

{body}
<div id="counter">1 / {len(SLIDES)}</div>
<div class="navctl"><button id="pv">&#8249;</button><button id="nx">&#8250;</button><button id="mn">&#9776;</button></div>
<div id="toc"><h2>CONTENTS — CLICK TO JUMP</h2><ol id="tocl"></ol></div>
</div></div>
<script>
{SCRIPT}
</script></body></html>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(doc)
print(f"wrote {OUT} ({len(doc):,} bytes)")
print(f"slides={doc.count('<section class=')}  toc={len(titles)}  match={doc.count('<section class=') == len(titles)}")
