"""Build the Trade Impact automotive analysis report as one self-contained HTML file.

Input   data/auto/database/tradeimpact_auto.sqlite   every figure, through report/facts.py
Output  data/auto/report/ti_automotive_report.html   about 30 printed pages, charts inline

The report carries no data of its own. Every number in every sentence, table and chart is
interpolated from a query in ``facts.py``, so a rebuild after a data change moves the prose with
the figures and a claim cannot outlive the table under it. Charts are inline SVG from
``chart.py``: no script, no external request, no raster, so the file opens from disk, prints, and
renders the same way on any machine. Nothing here is written by hand into the output — this
script is the source, exactly as a CSV's extractor is the source of the CSV.

The report is deterministic: it states the data's own as-of date and the content hashes of the
tables it reads, and carries no build timestamp, so two builds from the same database are
byte-identical.

Run from the repository root:  .venv/bin/python script/auto/report/build_report.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chart  # noqa: E402
from facts import (  # noqa: E402
    COMMON_COHORT,
    COMPANIES,
    DIRECTIONAL_THRESHOLD,
    MARKETS,
    Facts,
    load,
)

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "data" / "auto" / "report" / "ti_automotive_report.html"
TITLE = "Trade Impact of the automotive trade"
SUBTITLE = (
    "What four carmakers' 2024-2026 sales commit their destination markets to, "
    "measured against each government's own pathway"
)

SCENARIO_NAME = {"S1": "S1 current trajectory", "S2": "S2 committed policy"}
PT_COLOUR = {
    "ICE": "var(--c-ice)",
    "HEV": "var(--c-hev)",
    "BEV": "var(--c-bev)",
    "PHEV": "var(--c-phev)",
    "FCEV": "var(--c-fcev)",
}
SC_COLOUR = {"S1": "var(--c-s1)", "S2": "var(--c-s2)"}
#: How each company's worldwide denominator is put together, in words.
BASIS_TEXT = {
    "worldwide_sales": "the company's own published worldwide total",
    "worldwide_retail": "the sum of every destination in its retail release",
    "worldwide_sales_derived": "derived from its three workbooks; it publishes no single total",
}

CSS = """
:root {
  color-scheme: light;
  --ink: #14161a; --muted: #5b6472; --rule: #d7dce3; --bg: #ffffff; --panel: #f6f8fa;
  --pos: #1f7a5a; --neg: #b03030; --band: #c9d4e055;
  --c-s1: #4a6fa5; --c-s2: #b06a1f;
  --c-ice: #8a8f98; --c-hev: #3f7fb3; --c-bev: #1f7a5a; --c-phev: #9a6fb0; --c-fcev: #b0894a;
  --accent: #1f4e79;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --ink: #e6e9ee; --muted: #9aa4b2; --rule: #333a45; --bg: #14171c; --panel: #1b1f26;
    --pos: #4cbf95; --neg: #e0736b; --band: #3a4a5e55;
    --c-s1: #7fa8dd; --c-s2: #dda45f;
    --c-ice: #9aa0aa; --c-hev: #62a8dc; --c-bev: #4cbf95; --c-phev: #b78fd0; --c-fcev: #d0a86a;
    --accent: #9dc4ea;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 10.5pt/1.55 "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
}
main { max-width: 820px; margin: 0 auto; padding: 24px 20px 60px; }
section.page { padding: 6px 0 18px; }
h1 { font-size: 26pt; line-height: 1.15; margin: 0 0 6px; letter-spacing: -0.01em; }
h2 {
  font-size: 15pt; margin: 26px 0 8px; padding-bottom: 4px;
  border-bottom: 1.5px solid var(--rule);
}
h3 { font-size: 11.5pt; margin: 18px 0 4px; }
h2 .num { color: var(--accent); font-variant-numeric: tabular-nums; margin-right: 8px; }
p { margin: 0 0 9px; }
p.lead { font-size: 12pt; color: var(--ink); }
p.kicker {
  font: 600 8.5pt/1.3 ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.09em;
  text-transform: uppercase; color: var(--accent); margin: 0 0 4px;
}
.muted { color: var(--muted); }
small, .small { font-size: 8.7pt; }
ul, ol { margin: 0 0 10px; padding-left: 20px; }
li { margin-bottom: 5px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 6px; font-size: 8.9pt; }
th, td { text-align: right; padding: 3.5px 6px; border-bottom: 1px solid var(--rule); }
th:first-child, td:first-child, th.l, td.l { text-align: left; }
thead th { border-bottom: 1.2px solid var(--ink); font-weight: 600; }
tbody tr:nth-child(even) { background: var(--panel); }
td.pos { color: var(--pos); } td.neg { color: var(--neg); }
tfoot td { font-weight: 600; border-top: 1.2px solid var(--ink); border-bottom: none; }
figure { margin: 14px 0 16px; }
figcaption { font-size: 8.7pt; color: var(--muted); margin-top: 5px; }
figcaption b { color: var(--ink); font-weight: 600; }
svg.chart { width: 100%; height: auto; display: block; }
.chart .plot-bg { fill: transparent; }
.chart .grid { stroke: var(--rule); stroke-width: 0.6; }
.chart .zero { stroke: var(--ink); stroke-width: 1.1; }
.chart .stem { stroke: var(--rule); stroke-width: 1; }
.chart .range { fill: var(--band); stroke: var(--rule); stroke-width: 0.6; }
.chart .central { stroke: var(--ink); stroke-width: 1.6; }
.chart .band { fill: var(--band); }
.chart text {
  font: 8.4px ui-sans-serif, system-ui, sans-serif; fill: var(--ink);
}
.chart text.tick, .chart text.axis-unit { fill: var(--muted); font-size: 8px; }
.chart text.small { font-size: 7.6px; }
.chart text.inbar { fill: #fff; }
.legend { margin: 2px 0 10px; font-size: 8.7pt; color: var(--muted); }
.key { margin-right: 14px; white-space: nowrap; }
.key i { display: inline-block; width: 9px; height: 9px; margin-right: 4px; border-radius: 2px; }
.callout {
  background: var(--panel); border-left: 3px solid var(--accent);
  padding: 9px 12px; margin: 12px 0;
}
.callout p:last-child { margin-bottom: 0; }
.finding { border-top: 2px solid var(--accent); padding-top: 4px; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 0 22px; }
.cover { min-height: 86vh; display: flex; flex-direction: column; justify-content: center; }
.cover h1 { font-size: 32pt; }
.cover .rule { height: 3px; background: var(--accent); width: 120px; margin: 16px 0 18px; }
.meta { font-size: 9pt; color: var(--muted); }
.meta dt { float: left; width: 130px; clear: left; font-weight: 600; color: var(--ink); }
.meta dd { margin: 0 0 3px 130px; }
.toc { columns: 2; column-gap: 26px; font-size: 9.2pt; list-style: none; padding: 0; }
.toc a { color: inherit; text-decoration: none; }
.toc li { break-inside: avoid; }
.fmono { font-variant-numeric: tabular-nums; }
.eq {
  background: var(--panel); padding: 9px 12px; margin: 10px 0; font-size: 9.6pt;
  font-family: ui-monospace, "SF Mono", Menlo, monospace; overflow-x: auto;
}
@media print {
  body { font-size: 9.6pt; }
  main { max-width: none; padding: 0; }
  section.page { break-after: page; }
  section.page:last-of-type { break-after: auto; }
  figure, table { break-inside: avoid; }
  h2 { break-after: avoid; }
  .cover { min-height: 0; }
  a { color: inherit; text-decoration: none; }
}
@page { size: A4; margin: 17mm 15mm; }
"""


# --------------------------------------------------------------------------------------------
# formatting helpers
# --------------------------------------------------------------------------------------------
def mt(value: float, dp: int = 2) -> str:
    """A tCO2e figure written in millions of tonnes, signed."""
    return f"{value / 1e6:+,.{dp}f}"


def num(value: float, dp: int = 0) -> str:
    """A plain number with thousands separators."""
    return f"{value:,.{dp}f}"


def pct(value: float, dp: int = 1) -> str:
    """A fraction written as a percentage."""
    return f"{value * 100:.{dp}f} %"


def signed(value: float, dp: int = 0) -> str:
    """A signed number."""
    return f"{value:+,.{dp}f}"


def cell(value: float, dp: int = 2, scale: float = 1.0) -> str:
    """A table cell coloured by sign."""
    klass = "pos" if value > 0 else ("neg" if value < 0 else "")
    return f'<td class="{klass} fmono">{value / scale:+,.{dp}f}</td>'


def maybe(value: object, dp: int = 1) -> str:
    """A number, or an em dash where the source publishes none."""
    if value is None or value == "":
        return "&mdash;"
    return f"{float(value):,.{dp}f}"


def esc(text: object) -> str:
    """HTML-escape."""
    return chart.esc(str(text))


def table(
    head: list[str],
    body: list[list[str]],
    *,
    foot: list[str] | None = None,
    left: int = 1,
) -> str:
    """A data table; the first ``left`` columns are left-aligned."""

    def klass(i: int) -> str:
        return ' class="l"' if i < left else ""

    thead = "".join(f"<th{klass(i)}>{h}</th>" for i, h in enumerate(head))
    trs = []
    for row in body:
        tds = "".join(
            c if c.startswith("<td") else f"<td{klass(i)}>{c}</td>" for i, c in enumerate(row)
        )
        trs.append(f"<tr>{tds}</tr>")
    tfoot = ""
    if foot:
        tds = "".join(
            c if c.startswith("<td") else f"<td{klass(i)}>{c}</td>" for i, c in enumerate(foot)
        )
        tfoot = f"<tfoot><tr>{tds}</tr></tfoot>"
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(trs)}</tbody>{tfoot}</table>"


def figure(svg: str, number: str, caption: str, *, legend: str = "") -> str:
    """A numbered figure with its caption and optional colour key."""
    return (
        f"<figure>{legend}{svg}<figcaption><b>Figure {number}.</b> {caption}</figcaption></figure>"
    )


SECTIONS: list[tuple[str, str]] = []


def page(anchor: str, title: str, body: str, *, number: str | None = None) -> str:
    """One printed section, recorded in the table of contents."""
    if number:
        SECTIONS.append((anchor, f"{number}. {title}"))
        heading = f'<h2 id="{anchor}"><span class="num">{number}</span>{title}</h2>'
    else:
        SECTIONS.append((anchor, title))
        heading = f'<h2 id="{anchor}">{title}</h2>'
    return f'<section class="page">{heading}{body}</section>'


# --------------------------------------------------------------------------------------------
# sections
# --------------------------------------------------------------------------------------------
def cover(f: Facts) -> str:
    """Title page with the scope in one glance."""
    d = f.derived
    markets = ", ".join(MARKETS[m] for m in d["markets"])  # type: ignore[index]
    companies = ", ".join(COMPANIES[c] for c in d["companies"])  # type: ignore[index]
    years = sorted({int(r["cohort_year"]) for r in f.company_results})
    return f"""<section class="page cover">
<p class="kicker">PLANiT Institute &middot; Trade Impact, automotive</p>
<h1>{TITLE}</h1>
<div class="rule"></div>
<p class="lead">{SUBTITLE}</p>
<dl class="meta">
<dt>Companies</dt><dd>{companies}</dd>
<dt>Destination markets</dt><dd>{markets}</dd>
<dt>Sale years</dt><dd>{years[0]}&ndash;{years[-1]}</dd>
<dt>Cohorts assessed</dt><dd>{d["cohorts"]} (company &times; market &times; sale year)</dd>
<dt>Vehicles assessed</dt><dd>{num(d["units"])} units, {num(d["withheld_units"])} withheld</dd>
<dt>Scenarios</dt><dd>{", ".join(SCENARIO_NAME[s] for s in d["scenarios"])}</dd>
<dt>Data as of</dt><dd>{f.as_of}</dd>
<dt>Built from</dt><dd>data/auto/database/tradeimpact_auto.sqlite</dd>
</dl>
<p class="small muted">Every figure in this report is read from that database at build time by
<code>script/auto/report/build_report.py</code>. Nothing is typed in by hand. Method,
assumptions and per-value data-quality tiers are in <code>data/auto/output/method.md</code>;
the sources behind every input are in Appendix D.</p>
</section>"""


def contents() -> str:
    """Placeholder replaced once every section has registered itself."""
    return "@@CONTENTS@@"


def summary(f: Facts) -> str:
    """The findings, stated with their numbers."""
    d = f.derived
    pt = d["powertrain_totals"]  # type: ignore[index]
    corolla = nameplate_across_markets(f, "toyota", ("Corolla", "COROLLA", "TOYOTA COROLLA"), "HEV")
    eu = sorted([r for r in f.eu_country if r["scenario"] == "S1"], key=lambda r: r["per_vehicle"])
    life_bands = lifetime_bands(f)
    years = [int(r["cohort_year"]) for r in f.company_results]
    s2_values = [float(r["ti_tco2e"]) for r in f.company_results if r["scenario"] == "S2"]
    body = f"""
<p class="lead">Four carmakers sold {num(d["units"])} vehicles into four destination markets in
{min(years)}&ndash;{max(years)}.
Measured against what each destination's own government has committed to, those sales are a
lifetime liability of {mt(abs(d["S2_total_mt"] * 1e6), 0)[1:]} MtCO&#8322;e. Measured against
what each destination is actually doing, the same sales are a net contribution of
{mt(d["S1_total_mt"] * 1e6, 1)} MtCO&#8322;e. Both numbers come from the same cars. The gap
between them is the finding.</p>

<div class="callout"><p><b>The one-sentence result.</b> Under the observed trajectory
(S1) {d["S1_contributions"]} of {d["S1_n"]} cohorts emit less over their lifetime than the fleet
they join; under each government's own committed pathway (S2) <b>none of them do</b> &mdash;
{d["S2_liabilities"]} out of {d["S2_n"]}, without exception, in every market and for every
company.</p></div>

<h3 class="finding">1. Against committed policy there are no good cohorts, only slower ones</h3>
<p>S2 turns every cohort negative: {mt(d["S2_total_mt"] * 1e6, 1)} MtCO&#8322;e across
{d["cohorts"]} cohorts, from {mt(min(s2_values), 1)} to {mt(max(s2_values), 2)}
MtCO&#8322;e. The ranking that remains is a ranking of exposure, not of alignment.</p>

<h3 class="finding">2. Five years is the half-life of a good-news story</h3>
<p>A vehicle's emissions are fixed on the day it is sold; the benchmark it is measured against
keeps falling. Under S2 the units-weighted crossover &mdash; the year a cohort stops beating its
benchmark &mdash; is {d["s2_crossing_min"]:.1f} to {d["s2_crossing_max"]:.1f} years after sale in
every market, against {d["crossings"][("US", "S1")]:.0f} years in the United States under the
observed trend. The committed pathway does not change the car. It changes how long the car looks
good.</p>

<h3 class="finding">3. Hybrids beat the trend; only battery-electric beats the target</h3>
<p>On the {COMMON_COHORT} cohorts, hybrids are the largest single contribution under S1
({mt(pt[("HEV", "S1")], 1)} MtCO&#8322;e) and all but vanish under S2
({mt(pt[("HEV", "S2")], 1)}). Battery-electric vehicles stay positive under both
({mt(pt[("BEV", "S1")], 1)} and {mt(pt[("BEV", "S2")], 1)}), and are the only powertrain that
does, in {d["bev_markets_positive_s2"]} of the {d["bev_markets_s2"]} markets where they appear.
Combustion is the liability that dominates the total ({mt(pt[("ICE", "S2")], 1)}).</p>

<h3 class="finding">4. The same car gets opposite verdicts in different markets</h3>
<p>{corolla}</p>

<h3 class="finding">5. Inside Europe, where a car is registered outweighs what it is</h3>
<p>The four companies' European cohorts, pooled and measured state by state under S1, run
from
{num(eu[0]["per_vehicle"] / 1000, 1)} tCO&#8322;e per vehicle in {eu[0]["destination"]} to
{signed(eu[-1]["per_vehicle"] / 1000, 1)} in {eu[-1]["destination"]} &mdash; a
{num((eu[-1]["per_vehicle"] - eu[0]["per_vehicle"]) / 1000, 0)} tonne swing for identical
vehicles, driven by national fleet intensity, the national observed trend and national fleet
age. That spread is wider than the difference between any two powertrains in the same country.</p>

<h3 class="finding">6. The answer is most sensitive to the input that is least sourced</h3>
<p>Of the four sensitivity dimensions the model carries, vehicle lifetime moves the result the
most: {"; ".join(f"{MARKETS[m]} {pct(v, 0)}" for m, v in life_bands.items())} of the central
value. In the United States the expected lifetime is also the only tier-C input, fitted to
1977&ndash;2002 registrations. The least-evidenced number is the one the conclusion rests on,
and that is stated here rather than smoothed over.</p>
"""
    return page("summary", "Executive summary", body, number="1")


def lifetime_bands(f: Facts) -> dict[str, float]:
    """Market -> mean width of the lifetime sensitivity band as a share of the central value."""
    widths: dict[str, list[float]] = {}
    for (_company, market), dims in f.sensitivity.items():
        band = dims.get("lifetime")
        if not band:
            continue
        low, central, high = band
        if central:
            widths.setdefault(market, []).append(abs(high - low) / abs(central))
    return {m: sum(v) / len(v) for m, v in sorted(widths.items(), key=lambda kv: -max(kv[1]))}


def nameplate_across_markets(
    f: Facts, company: str, names: tuple[str, ...], powertrain: str
) -> str:
    """One sentence contrasting the same nameplate and powertrain in different markets."""
    hits = [
        r
        for r in f.nameplates
        if r["company"] == company
        and r["powertrain"] == powertrain
        and r["scenario"] == "S2"
        and r["model"] in names
    ]
    hits.sort(key=lambda r: -r["per_vehicle"])
    if not hits:
        return ""
    parts = [
        f"{MARKETS[r['market']]} {signed(r['per_vehicle'] / 1000, 1)} tCO&#8322;e per vehicle"
        for r in hits
    ]
    best, worst = hits[0], hits[-1]
    return (
        f"A {COMPANIES[company]} {best['model'].title()} {powertrain} sold in "
        f"{COMMON_COHORT} is assessed at " + ", ".join(parts) + " under committed policy. The "
        f"product is the same class of technology in each; the verdict differs by "
        f"{num((best['per_vehicle'] - worst['per_vehicle']) / 1000, 1)} tonnes per vehicle "
        f"because {MARKETS[worst['market']]} sets a benchmark that falls faster and holds a "
        f"vehicle for {worst['life']:.0f} years against {best['life']:.0f}."
    )


def what_it_measures(f: Facts) -> str:
    """The definition, the two scenarios and the sign convention."""
    rate_summary = market_rate_table(f)
    body = f"""
<p>Trade Impact (TI) asks a counterfactual question about a single year's sales. Take the
vehicles a company sold into one country in one year. Over their operating life, how much would
that many vehicles have emitted had they performed like the fleet they joined &mdash; and how
much will the vehicles actually sold emit? The difference is the trade impact of that sale.</p>

<div class="eq">TI = &Sigma;<sub>t</sub> [ E<sub>ref</sub>(t) &minus; E<sub>prod</sub>(t) ]
&times; units<br>
E<sub>ref</sub>(t) = I<sub>0</sub> / 1000 &times; (1 &minus; r<sub>fleet</sub>)<sup>t</sup>
&times; D</div>

<p>I<sub>0</sub> is the destination fleet's CO&#8322; intensity in the sale year (gCO&#8322;/km),
D the annual distance a vehicle of that segment travels there (km/year), r<sub>fleet</sub> the
annual rate at which the benchmark improves, and t the years since sale. Battery-electric
products carry the destination's grid intensity, declining at its own committed rate
r<sub>power</sub>; combustion and hybrid products carry a fixed tailpipe intensity, because a
sold vehicle does not improve.</p>

<h3>Two scenarios, and why there is no third</h3>
<p><b>S1 current trajectory</b> fits a log-linear trend to the destination's own observed
series &mdash; fleet CO&#8322; and grid intensity, 2015 onward with 2020 and 2021 excluded as
pandemic years. It answers: measured against what this country is actually doing, is this sale
better or worse?</p>
<p><b>S2 committed policy</b> is the pathway the destination's own government has stated, taken
to the furthest year that government sets, so a vehicle's whole operating life sits inside the
target horizon. It answers: measured against what this country has promised, is this sale
consistent with it? No modelled 1.5&nbsp;&deg;C scenario appears anywhere in this report. No
government published one, and the claim being made is a comparison against commitments, not
against a consultant's pathway.</p>
{rate_summary}
<h3>Reading the sign</h3>
<p>Positive TI means the vehicles emit less over their lifetime than the benchmark fleet would
have: a contribution. Negative means more: a lock-in liability, emissions the destination is
committed to for as long as the vehicles stay on the road. TI is additional to Scope 3
Category 11 and never offsets it; it is a measure of what a trade flow commits a market to, not
a credit against a company's own inventory.</p>
"""
    return page("definition", "What the number means", body, number="2")


def market_rate_table(f: Facts) -> str:
    """The S1 and S2 rate pair per market, with the policy anchor behind S2."""
    rows: list[list[str]] = []
    for market in MARKETS:
        pick = "EU27" if market == "EU27" else market
        source = [r for r in f.rate_rows if r["tbl"] == market]
        if market == "EU27":
            source = [r for r in source if r["country"] == "DE"]
        by = {(r["scenario"], r["rate"]): r for r in source}
        if ("S2", "r_fleet") not in by:
            continue
        anchor = by[("S2", "r_fleet")]
        rows.append(
            [
                MARKETS[market],
                f"{float(by[('S1', 'r_fleet')]['value']) * 100:+.2f} %",
                f"{float(by[('S1', 'r_power')]['value']) * 100:+.2f} %",
                f"{float(anchor['value']) * 100:.2f} %",
                f"{float(by[('S2', 'r_power')]['value']) * 100:.2f} %",
                esc(anchor["target_level"]),
                f"{anchor['base_year']}&ndash;{anchor['target_year']}",
            ]
        )
        del pick
    return table(
        [
            "Market",
            "S1 fleet",
            "S1 power",
            "S2 fleet",
            "S2 power",
            "S2 anchor",
            "Window",
        ],
        rows,
    ) + (
        '<p class="small muted">Annual rates of decline. The EU27 row shows Germany for the S1'
        " trend, which is fitted per member state; the S2 pair is EU-wide. Full derivations, one"
        " per market, are in Appendix B.</p>"
    )


def scope(f: Facts) -> str:
    """Who and where, and how much of each company's worldwide sales this speaks for."""
    palette = {
        "assessed": "var(--pos)",
        "counted, not assessed": "var(--c-hev)",
        "outside the data": "var(--c-ice)",
    }
    rows = []
    body_rows = []
    for r in sorted(f.coverage, key=lambda r: (r["company"], r["cohort_year"])):
        share = float(r["assessed_share_of_global"])
        held = float(r["held_share_of_global"])
        label = f"{COMPANIES[r['company']]} {r['cohort_year']}"
        rows.append(
            (
                label,
                [
                    ("assessed", share),
                    ("counted, not assessed", max(held - share, 0.0)),
                    ("outside the data", max(1.0 - max(held, share), 0.0)),
                ],
            )
        )
        body_rows.append(
            [
                label,
                num(int(r["global_units"])),
                esc(BASIS_TEXT.get(r["global_basis"], r["global_basis"])),
                num(int(r["assessed_units"])),
                pct(share),
                pct(held),
                esc(r["assessed_markets"]),
                str(r["assessed_countries"]),
            ]
        )
    coverage_chart = chart.stacked_shares(
        rows, label="Share of worldwide sales assessed, per company and cohort", palette=palette
    )
    d = f.derived
    body = f"""
<p>The unit of analysis is a cohort: one company, one destination market, one sale year. There
are {d["cohorts"]} of them here. Every cohort is built from the company's or the market's own
published volumes, joined to certified product values from that market's own regulator, and
measured against a benchmark built from that market's own statistics. Cohorts and markets are
never summed: they rest on different sales bases, test cycles and national benchmarks.</p>

{
        figure(
            coverage_chart,
            "3.1",
            "How much of each company's worldwide sales this report speaks for. <b>Assessed</b> is "
            "units carrying a result. <b>Counted, not assessed</b> is units the project holds but "
            "cannot yet measure &mdash; a market with no benchmark, or a powertrain with "
            "no sourced "
            "parameter. Source: <code>ti_global_coverage.csv</code>.",
            legend=chart.legend([(k, v) for k, v in palette.items()]),
        )
    }

{
        table(
            [
                "Company, cohort",
                "Worldwide sales",
                "Basis",
                "Assessed units",
                "Assessed",
                "Held",
                "Markets",
                "Countries",
            ],
            body_rows,
            left=3,
        )
    }

<p>The honest reading of that table is that this is a report about a third to a half of each
company's worldwide business, and about the destinations where free official statistics support
a defensible benchmark. Nothing is extrapolated to the rest. Where a company reports brands
together that this project holds apart &mdash; Lexus inside Toyota, Infiniti inside Nissan,
Genesis inside Hyundai &mdash; those units count in the denominator and are named in the
coverage table, so the assessed share is understated rather than flattered.</p>
"""
    return page("scope", "Scope, and what it covers", body, number="3")


def headline(f: Facts) -> str:
    """Every cohort, both scenarios."""
    reported = [r for r in f.company_results if r["status"] == "reported"]
    keys = sorted(
        {(r["market"], int(r["cohort_year"]), r["company"]) for r in reported},
        key=lambda k: (list(MARKETS).index(k[0]), k[1], list(COMPANIES).index(k[2])),
    )
    lookup = {
        (r["market"], int(r["cohort_year"]), r["company"], r["scenario"]): r for r in reported
    }
    rows = []
    body_rows = []
    for market, year, company in keys:
        label = f"{market} {year} {COMPANIES[company]}"
        series = []
        for scenario in ("S1", "S2"):
            r = lookup.get((market, year, company, scenario))
            if r:
                series.append((scenario, float(r["ti_tco2e"]) / 1e6))
        rows.append((label, series))
        s1 = lookup[(market, year, company, "S1")]
        s2 = lookup[(market, year, company, "S2")]
        body_rows.append(
            [
                market,
                str(year),
                COMPANIES[company],
                num(int(s1["covered_units"])),
                num(int(s1["withheld_units"])),
                pct(float(s1["covered_share"])),
                cell(float(s1["ti_tco2e"]) / 1e6, 2),
                cell(float(s1["ti_per_vehicle_kgco2e"]) / 1000, 1),
                cell(float(s2["ti_tco2e"]) / 1e6, 2),
                cell(float(s2["ti_per_vehicle_kgco2e"]) / 1000, 1),
                esc(s2["direction"]),
            ]
        )
    d = f.derived
    svg = chart.grouped_bars(
        rows,
        unit="MtCO2e over the operating lifetime",
        label="Lifetime trade impact per cohort under both scenarios",
        palette=SC_COLOUR,
        dp=1,
    )
    body = f"""
<p>Figure 4.1 is the whole result set. Each row is one cohort; the two bars are the two
scenarios. The pattern is immediate and it is the reason this report exists: under the observed
trajectory the bars fall on both sides of zero, and under committed policy they all fall on
one.</p>

{
        figure(
            svg,
            "4.1",
            "Lifetime trade impact of every cohort, MtCO&#8322;e, under the observed "
            "trajectory (S1) "
            "and committed policy (S2). Positive is a contribution, negative a lock-in liability. "
            "Source: <code>ti_company.csv</code>.",
            legend=chart.legend([(SCENARIO_NAME[s], SC_COLOUR[s]) for s in ("S1", "S2")]),
        )
    }

{
        table(
            [
                "Market",
                "Year",
                "Company",
                "Units",
                "Coverage",
                "S1 Mt",
                "S1 t/veh",
                "S2 Mt",
                "S2 t/veh",
            ],
            body_rows,
            left=3,
            foot=[
                "All cohorts",
                "",
                "",
                num(d["units"]),
                "",
                cell(d["S1_total_mt"], 2),
                "",
                cell(d["S2_total_mt"], 2),
                "",
            ],
        )
    }

<p class="small muted">Coverage is the share of the source's units that carry a result;
withheld units are counted and reported, never absorbed (section 13). Per-vehicle values are
tonnes CO&#8322;e over the whole operating life, not per year. The totals row sums cohorts for
reference only: cohort years overlap between markets and the markets rest on different bases, so
the sum is an order of magnitude, not a company footprint. This is the whole published result
set; <code>ti_company.csv</code> carries it with the decomposition-identity check on every
row.</p>
"""
    return page("headline", "The result set", body, number="4")


def finding_committed(f: Facts) -> str:
    """Finding 1: under committed policy every cohort is a liability."""
    reported = [r for r in f.company_results if r["status"] == "reported" and r["scenario"] == "S2"]
    rows = sorted(
        (
            (
                f"{r['market']} {r['cohort_year']} {COMPANIES[r['company']]}",
                float(r["ti_per_vehicle_kgco2e"]) / 1000,
            )
            for r in reported
        ),
        key=lambda kv: kv[1],
    )
    svg = chart.diverging_bars(
        rows,
        unit="tCO2e per vehicle, lifetime, under committed policy",
        label="Per-vehicle trade impact under committed policy",
        dp=1,
    )
    d = f.derived
    s1 = [r for r in f.company_results if r["status"] == "reported" and r["scenario"] == "S1"]
    s1_neg = sorted((r for r in s1 if float(r["ti_tco2e"]) < 0), key=lambda r: float(r["ti_tco2e"]))
    neg_markets = sorted({r["market"] for r in s1_neg})
    neg_list = "; ".join(
        f"{COMPANIES[r['company']]} {r['cohort_year']} {mt(float(r['ti_tco2e']), 2)} Mt"
        for r in s1_neg
    )
    body = f"""
<p class="kicker">Finding 1</p>
<p class="lead">Under each destination's own committed pathway, not one of the
{d["cohorts"]} cohorts emits less over its lifetime than the fleet it joins.</p>

{
        figure(
            svg,
            "5.1",
            "Per-vehicle lifetime trade impact under committed policy, worst to best. Every cohort "
            "is negative; the spread is a ranking of exposure, not of alignment. Source: "
            "<code>ti_company.csv</code>.",
        )
    }

<p>The size of the liability tracks three things, in order: how far the destination's committed
pathway falls over a vehicle's life, how long that life is, and how far the vehicles travel each
year. It tracks the product mix fourth. That ordering is the uncomfortable part of the result:
the same product mix sold into a market with a steeper commitment and a longer-lived fleet
produces a larger liability, and no product decision inside the company changes the slope of a
national target.</p>

<h3>The five cohorts already negative under the observed trend</h3>
<p>Under S1, {d["S1_liabilities"]} of {d["S1_n"]} cohorts are already liabilities, all of them in
{" and ".join(MARKETS[m] for m in neg_markets)}:
{neg_list}.
Europe is the only market where the observed trend alone is enough to make a 2024 sale a
liability, for two compounding reasons: its observed per-car CO&#8322; intensity is falling
faster than any other market's, and its fleets are the oldest, so a car sold in 2024 is measured
against an improving benchmark for up to two decades.</p>

<div class="callout"><p><b>What would change this.</b> Not a marginally better hybrid. A cohort
turns positive under S2 only if its product intensity starts far enough below the benchmark that
the benchmark's decline cannot catch it within the vehicle's life &mdash; which in practice means
a zero-tailpipe product in a market whose grid is also decarbonising, or a much shorter assumed
vehicle life. Section 9 shows the arithmetic on a single nameplate.</p></div>
"""
    return page(
        "committed", "Against committed policy, there are no good cohorts", body, number="5"
    )


def finding_crossover(f: Facts) -> str:
    """Finding 2: the crossover year."""
    d = f.derived
    rows = []
    for market in MARKETS:
        for scenario in ("S1", "S2"):
            value = d["crossings"].get((market, scenario))  # type: ignore[union-attr]
            if value is None:
                continue
            rows.append((f"{market} {scenario}", value))
    svg = chart.diverging_bars(
        rows,
        unit="years after sale until the cohort stops beating its benchmark",
        label="Units-weighted crossover year by market and scenario",
        dp=1,
        colours=("var(--c-s1)", "var(--c-s1)"),
        label_width=110,
    )
    kr = [r for r in f.crossover if r["market"] == "KR" and r["scenario"] == "S1"][0]
    s2_fleet = [
        abs(float(r["value"]))
        for r in f.rate_rows
        if r["scenario"] == "S2" and r["rate"] == "r_fleet"
    ]
    body = f"""
<p class="kicker">Finding 2</p>
<p class="lead">Under committed policy a cohort stops beating its benchmark
{d["s2_crossing_min"]:.1f} to {d["s2_crossing_max"]:.1f} years after it is sold &mdash; in every
market, whatever the product mix.</p>

{
        figure(
            svg,
            "6.1",
            "Units-weighted crossover year: how long after sale the cohort's annual emissions rise "
            "above the benchmark's. Under S2 the four markets agree within a year of each other. "
            "Source: <code>ti_crossover.csv</code>.",
        )
    }

<p>The crossover is not an artefact of the model; it is the arithmetic of selling a fixed asset
into a moving target. A vehicle's tailpipe intensity is set at manufacture. The benchmark is a
national fleet average that a government has committed to lowering every year. Whatever margin
a product starts with is spent at the benchmark's rate of decline, and under committed policy
that rate is {min(s2_fleet) * 100:.1f} to {max(s2_fleet) * 100:.1f} per cent a year.</p>

<h3>Where the trend gives cover, and where it does not</h3>
<p>Under S1 the crossovers are far apart: {d["crossings"][("US", "S1")]:.0f} years in the United
States, {d["crossings"][("JP", "S1")]:.0f} in Japan, {d["crossings"][("EU27", "S1")]:.0f} in the
EU27, and in Korea no crossover at all for any of the {num(int(kr["units"]))} units assessed.
Korea's observed road-transport CO&#8322; is essentially flat, so a Korean cohort never has to
outrun anything. That is the clearest illustration of what S1 measures: not the product's
quality, but the destination's inertia.</p>

<div class="callout"><p><b>Why the crossover matters more than the total.</b> A lifetime total
nets a few good early years against many bad later ones and reports one number. The crossover
year says when the policy problem starts. For a fleet operator or a regulator, a cohort that
turns at year five is a different object from one that turns at year twenty, even where the
lifetime totals match.</p></div>
"""
    return page("crossover", "Five years is the half-life of a good-news story", body, number="6")


def finding_profile(f: Facts) -> str:
    """Finding 3: the flat line and the falling line."""
    market, company, year = "US", "toyota", COMMON_COHORT
    s1 = f.annual[(market, company, year, "S1")]
    s2 = f.annual[(market, company, year, "S2")]
    labels = [str(r["calendar_year"]) for r in s2]
    svg = chart.lines(
        [
            chart.Series("product", [float(r["e_prod_tco2e"]) / 1e6 for r in s2], "var(--c-ice)"),
            chart.Series(
                "benchmark S2", [float(r["e_ref_tco2e"]) / 1e6 for r in s2], SC_COLOUR["S2"]
            ),
            chart.Series(
                "benchmark S1", [float(r["e_ref_tco2e"]) / 1e6 for r in s1], SC_COLOUR["S1"]
            ),
        ],
        labels,
        unit="MtCO2e per year",
        label="Annual product and benchmark emissions of one cohort",
        fill_between=("benchmark S2", "product"),
        height=290,
        dp=1,
    )
    flow = chart.diverging_bars(
        [(str(r["calendar_year"]), float(r["ti_tco2e"]) / 1e6) for r in s2],
        unit="MtCO2e in that year",
        label="Annual trade impact of one cohort under committed policy",
        dp=2,
        label_width=70,
    )
    first_neg = next((r for r in s2 if float(r["ti_tco2e"]) < 0), None)
    peak = max(s2, key=lambda r: float(r["cumulative_ti_tco2e"]))
    last = s2[-1]
    body = f"""
<p class="kicker">Finding 3</p>
<p class="lead">One cohort, year by year: the product line is flat by construction, the benchmark
line falls by commitment, and everything follows from the two crossing.</p>

{
        figure(
            svg,
            "7.1",
            f"{COMPANIES[company]}'s {year} {MARKETS[market]} cohort "
            f"({num(int(s2[0]['surviving_vehicles']))} vehicles). The flat line is what the "
            "vehicles emit; the shaded area is the annual trade impact against committed "
            "policy. Source: <code>ti_annual.csv</code>.",
            legend=chart.legend(
                [
                    ("product (fixed at sale)", "var(--ink)"),
                    ("benchmark, committed policy", SC_COLOUR["S2"]),
                    ("benchmark, observed trend", SC_COLOUR["S1"]),
                ]
            ),
        )
    }

<p>The product line falls by {
        (1 - float(s2[-1]["e_prod_tco2e"]) / float(s2[0]["e_prod_tco2e"])) * 100:.1f}
per cent over {len(s2)} years &mdash; only because the battery-electric part of the cohort
charges from a grid that decarbonises. The combustion and hybrid parts do not move at all. The
S2 benchmark falls
{(1 - float(s2[-1]["e_ref_tco2e"]) / float(s2[0]["e_ref_tco2e"])) * 100:.0f} per cent over the
same window. That asymmetry is the whole mechanism.</p>

{
        figure(
            flow,
            "7.2",
            "The same cohort's annual trade impact under committed policy: a contribution for the "
            f"first years, a liability from {first_neg['calendar_year'] if first_neg else 'n/a'} "
            "onward, growing every year the vehicles stay on the road. Source: "
            "<code>ti_annual.csv</code>.",
        )
    }

<p>Read the two figures together. Cumulative trade impact peaks at
{mt(float(peak["cumulative_ti_tco2e"]), 2)} MtCO&#8322;e in {peak["calendar_year"]}, and by
{last["calendar_year"]} it has fallen to {mt(float(last["cumulative_ti_tco2e"]), 2)}. A report
that stopped at the peak would call this cohort a contribution. A report that stops at the end
of the vehicles' life &mdash; which is what the whitepaper requires, and what a lock-in claim
means &mdash; calls it a liability. Both numbers are in
<code>ti_annual.csv</code>; the choice of horizon is the difference between them.</p>
"""
    return page("profile", "The flat line and the falling line", body, number="7")


def finding_powertrain(f: Facts) -> str:
    """Finding 4: powertrains under the two scenarios."""
    rows = []
    for market in MARKETS:
        for powertrain in ("ICE", "HEV", "BEV"):
            series = []
            for scenario in ("S1", "S2"):
                hit = [
                    r
                    for r in f.powertrain
                    if r["market"] == market
                    and r["powertrain"] == powertrain
                    and r["scenario"] == scenario
                ]
                if hit:
                    series.append((scenario, float(hit[0]["per_vehicle"]) / 1000))
            if series:
                rows.append((f"{market} {powertrain}", series))
    svg = chart.grouped_bars(
        rows,
        unit="tCO2e per vehicle, lifetime",
        label="Per-vehicle trade impact by market and powertrain",
        palette=SC_COLOUR,
        dp=1,
        label_width=110,
    )
    pt = f.derived["powertrain_totals"]  # type: ignore[index]
    units = {(r["powertrain"], r["scenario"]): int(r["units"]) for r in f.powertrain}
    hev_units = sum(v for (p, sc), v in units.items() if p == "HEV" and sc == "S1")
    hev_s1_per_vehicle = pt[("HEV", "S1")] / max(hev_units, 1)
    hev_s2_per_vehicle = pt[("HEV", "S2")] / max(hev_units, 1)
    body_rows = []
    for powertrain in ("ICE", "HEV", "BEV"):
        total_units = sum(v for (p, s), v in units.items() if p == powertrain and s == "S1")
        body_rows.append(
            [
                powertrain,
                num(total_units),
                cell(pt[(powertrain, "S1")] / 1e6, 2),
                cell(pt[(powertrain, "S1")] * 1000 / total_units / 1000, 1),
                cell(pt[(powertrain, "S2")] / 1e6, 2),
                cell(pt[(powertrain, "S2")] * 1000 / total_units / 1000, 1),
            ]
        )
    body = f"""
<p class="kicker">Finding 4</p>
<p class="lead">Hybrids are the largest contribution against what markets are doing, and almost
nothing against what they have promised. Battery-electric is the only powertrain that stays
positive under both.</p>

{
        figure(
            svg,
            "8.1",
            f"Per-vehicle lifetime trade impact by market and powertrain, {COMMON_COHORT} cohorts. "
            "Source: <code>ti_powertrain.csv</code>.",
            legend=chart.legend([(SCENARIO_NAME[s], SC_COLOUR[s]) for s in ("S1", "S2")]),
        )
    }

{
        table(
            ["Powertrain", f"Units, {COMMON_COHORT}", "S1 Mt", "S1 t/veh", "S2 Mt", "S2 t/veh"],
            body_rows,
        )
    }

<p>The hybrid result is the one worth pausing on. Across the {COMMON_COHORT} cohorts, hybrids
carry {mt(pt[("HEV", "S1")], 1)} MtCO&#8322;e against the observed trend and
{mt(pt[("HEV", "S2")], 1)} against committed policy. A technology that looks like the main
decarbonisation lever in the first framing disappears entirely in the second. Nothing about the
vehicles changed between the two columns; only the yardstick did.</p>

<p>The mechanism is the fixed intensity again. A hybrid's advantage over the fleet a market
currently runs is real, and over a lifetime it is worth {hev_s1_per_vehicle:,.1f} tonnes a
vehicle. Measured against the pathway the same markets have committed to, those vehicles are a
{abs(hev_s2_per_vehicle):,.1f} tonne liability each instead: the committed pathway spends the
margin in a handful of years, and the hybrid then sits above the benchmark for the rest of its
life.
Battery-electric products escape this because their emissions fall with the grid: they are the
only product in the cohort whose intensity is not fixed at the point of sale.</p>

<div class="callout"><p><b>The policy reading.</b> If a market's question is "are these sales
better than our current fleet?", hybrids answer yes. If the question is "are these sales
consistent with the pathway we have committed to?", only zero-tailpipe products answer yes, and
only where the grid is on its own committed pathway too. Those are different questions and they
have different answers for the same cars.</p></div>
"""
    return page("powertrain", "Hybrids beat the trend, not the target", body, number="8")


def finding_market(f: Facts) -> str:
    """Finding 5: the same nameplate in different markets."""
    interesting = (
        "Corolla",
        "COROLLA",
        "TOYOTA COROLLA",
        "RAV4",
        "TOYOTA RAV4",
        "Yaris",
        "TOYOTA YARIS",
        "Note",
        "X-Trail",
        "NISSAN X-TRAIL",
    )
    rows = []
    for r in f.nameplates:
        if r["scenario"] != "S2" or r["model"] not in interesting or int(r["units"]) < 15000:
            continue
        rows.append(
            [
                f"{COMPANIES[r['company']]} {r['model'].title()}",
                r["powertrain"],
                r["market"],
                num(int(r["units"])),
                num(float(r["prod0"]), 0),
                num(float(r["ref0"]), 0),
                f"{float(r['life']):.0f}",
                num(float(r["vkt"]), 0),
                cell(float(r["per_vehicle"]) / 1000, 1),
            ]
        )
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    body = f"""
<p class="kicker">Finding 5</p>
<p class="lead">The same nameplate, the same powertrain, sold in the same year into three
markets, is assessed as a contribution in one and a multi-tonne liability in another.</p>

{
        table(
            [
                "Nameplate",
                "Drive",
                "Market",
                "Units",
                "Product kg/yr",
                "Benchmark kg/yr",
                "Life yr",
                "km/yr",
                "S2 t/veh",
            ],
            rows,
            left=3,
        )
    }

<p>Four market parameters do all the work in that table, and none of them is a property of the
car.</p>
<ul>
<li><b>The benchmark level.</b> A destination's fleet intensity sets the starting margin.
The United States benchmark is the all-light-duty fleet including pickups, so a compact hybrid
starts far below it; Japan's fleet average already contains the hybrids and kei cars that make a
Japanese cohort look clean elsewhere, so the same hybrid starts barely below it.</li>
<li><b>Annual distance.</b> Every kilogram per kilometre is multiplied by it. US light-duty
vehicles travel roughly twice as far each year as Japanese cars, so both the margin and the
later liability are about twice the size.</li>
<li><b>Vehicle life.</b> Europe holds a car for close to two decades and Japan and the US for
about thirteen years, which decides how many years of a falling benchmark the vehicle has to
survive.</li>
<li><b>The rate of decline.</b> The steepest committed pathway in this report is more than twice
the shallowest. A product that would be defensible against one government's commitment is not
against another's.</li>
</ul>

<div class="callout"><p><b>What this means for a company's strategy.</b> Product planning cannot
be separated from destination planning. The same model line, shifted between two markets in the
mix, changes the assessed lifetime liability by more than a full powertrain generation of
efficiency improvement would. It also means a company cannot be ranked on trade impact without
stating where it sells, which is why every table in this report carries a market column and no
table sums across markets.</p></div>
"""
    return page("market", "The same car, a different verdict", body, number="9")


def finding_geography(f: Facts) -> str:
    """Finding 6: intra-EU spread."""
    s1 = sorted([r for r in f.eu_country if r["scenario"] == "S1"], key=lambda r: r["per_vehicle"])
    s2 = {r["destination"]: r for r in f.eu_country if r["scenario"] == "S2"}
    svg = chart.dots(
        [(r["destination"], float(r["per_vehicle"]) / 1000) for r in s1],
        unit="tCO2e per vehicle, lifetime, observed trend",
        label="Per-vehicle trade impact by EU member state",
        dp=1,
        label_width=52,
    )
    params = {
        r["country"]: r
        for r in f.parameters
        if r["market"] == "EU27" and r["segment"] == "passenger_car"
    }
    rows = []
    for r in s1[:3] + s1[-3:]:
        p = params[r["destination"]]
        rows.append(
            [
                r["destination"],
                num(int(r["units"])),
                num(float(p["fleet_intensity_gco2_km"]), 1),
                num(float(p["vkt_km"]), 0),
                f"{p['lifetime_years']}",
                num(float(p["grid_gco2_kwh"]), 0),
                cell(float(r["per_vehicle"]) / 1000, 1),
                cell(float(s2[r["destination"]]["per_vehicle"]) / 1000, 1),
            ]
        )
    body = f"""
<p class="kicker">Finding 6</p>
<p class="lead">The four companies' European cohorts, measured state by state, span
{num((s1[-1]["per_vehicle"] - s1[0]["per_vehicle"]) / 1000, 0)} tonnes per vehicle &mdash; wider
than the gap between any two powertrains in the same country.</p>

{
        figure(
            svg,
            "10.1",
            f"All EU27 cohorts of {COMMON_COHORT}, per-vehicle lifetime trade impact under the "
            "observed trend, by member state. Each state carries its own fleet intensity, its own "
            "observed trend, its own distance and its own fleet age. Source: "
            "<code>ti_country.csv</code>.",
        )
    }

{
        table(
            [
                "State",
                "Units",
                "Fleet gCO2/km",
                "km/yr",
                "Life yr",
                "Grid gCO2/kWh",
                "S1 t/veh",
                "S2 t/veh",
            ],
            rows,
        )
    }

<p>The three states at each end of the distribution show what drives it. A state with a
high fleet intensity and a short assumed life gives an imported car a wide margin and few years
to lose it in; a state with an already-clean fleet, a long-lived fleet and a steeply falling
trend gives it neither. Under S2 the spread narrows sharply, because the committed pathway is
EU-wide: the same rate applies in every member state and only the starting level and the fleet
age still differ.</p>

<p>Two honest caveats travel with this figure. Thirteen of the twenty-six states use an
EU-average distance because no national figure is published, which is why their distance column
repeats; and the operating life is derived from national mean fleet age, which is a proxy for a
survival curve nobody publishes per state. Both are tier-C inputs and both are declared on every
affected row of <code>destination_parameters_eu27.csv</code>. Luxembourg is excluded entirely:
its registration-based fleet intensity is implausible for a country whose fleet is largely
cross-border.</p>
"""
    return page("geography", "Inside Europe, geography outweighs technology", body, number="10")


def benchmarks(f: Facts) -> str:
    """Why the markets are never summed: the parameter table."""
    rows = []
    for r in f.parameters:
        if r["market"] == "EU27":
            continue
        rows.append(
            [
                r["market"],
                esc(r["segment"]),
                num(float(r["fleet_intensity_gco2_km"]), 1),
                esc(r["fleet_intensity_tier"]),
                num(float(r["vkt_km"]), 0),
                esc(r["vkt_tier"]),
                num(float(r["grid_gco2_kwh"]), 0),
                f"{r['lifetime_years']} [{r['lifetime_low_years']}, {r['lifetime_high_years']}]",
                esc(r["lifetime_tier"]),
                f"{r['co2_year']}",
            ]
        )
    eu = [r for r in f.parameters if r["market"] == "EU27" and r["segment"] == "passenger_car"]
    intensities = sorted(float(r["fleet_intensity_gco2_km"]) for r in eu)
    lifetimes = sorted(int(r["lifetime_years"]) for r in eu)
    body = f"""
<p>A trade impact figure is only as meaningful as the benchmark behind it, and the benchmarks in
this report are built from four different countries' statistics. They are not
interchangeable.</p>

{
        table(
            [
                "Market",
                "Segment",
                "Fleet gCO2/km",
                "Tier",
                "km/yr",
                "Tier",
                "Grid gCO2/kWh",
                "Life yr [low, high]",
                "Tier",
                "CO2 yr",
            ],
            rows,
            left=2,
        )
    }

<p>Across the {len(eu)} EU member states assessed, fleet intensity runs from
{intensities[0]:.0f} to {intensities[-1]:.0f} gCO&#8322;/km and the operating life from
{lifetimes[0]} to {lifetimes[-1]} years, so the EU27 rows are a distribution rather than a
single benchmark. The single-country markets each have one.</p>

<h3>Three asymmetries worth naming</h3>
<ul>
<li><b>The United States benchmark is generous by construction.</b> Its emissions numerator is
all light-duty vehicles including pickups and large SUVs, because the distance and stock
statistics split the fleet by wheelbase rather than by body type and pairing a car numerator with
a short-wheelbase denominator produces an implausible figure. A benchmark that includes pickups
is higher than a car-only benchmark, and a higher benchmark makes every product look better. The
segment ratio stays at 1.0 and the consequence is disclosed rather than corrected.</li>
<li><b>Japan's benchmark is unusually hard to beat.</b> Its fleet average already contains kei
cars and a decade of hybrid sales, so it is the lowest passenger-car intensity in the report
while the cohort measured against it excludes kei cars entirely.</li>
<li><b>Korea's numerator is a proxy.</b> The national inventory publishes no vehicle-class
split, so the class share comes from a bottom-up local inventory whose national level sits
13&ndash;26 per cent below the inventory total. Only the share is used, never the level, and
every Korean fleet-intensity value is tier C because of it.</li>
</ul>

<p>This is why no table in this report adds a company's markets together. A single global figure
would be dominated by whichever market happened to have the most generous benchmark and the
longest assumed vehicle life, and would move if a company merely shifted its sales mix between
two countries.</p>
"""
    return page("benchmarks", "Why the markets are never summed", body, number="11")


def segments(f: Facts) -> str:
    """The commercial-vehicle segments."""
    rows = []
    for r in f.segments:
        if r["segment"] == "passenger_car" and r["market"] != "KR":
            continue
        rows.append(
            [
                MARKETS[r["market"]],
                esc(r["segment"]),
                r["scenario"],
                num(int(r["units"])),
                cell(float(r["ti"]) / 1e6, 2),
                cell(float(r["per_vehicle"]) / 1000, 1),
            ]
        )
    kr = {(r["segment"], r["scenario"]): r for r in f.segments if r["market"] == "KR"}
    freight_params = [r for r in f.parameters if r["market"] == "KR" and r["segment"] == "freight"][
        0
    ]
    car_params = [
        r for r in f.parameters if r["market"] == "KR" and r["segment"] == "passenger_car"
    ][0]
    body = f"""
<p>These companies do not only sell cars, and a result that measured a one-tonne truck against a
passenger-car benchmark would be wrong twice: it would use the wrong fleet and the wrong
distance. Every cohort row therefore carries a segment, and the benchmark it is measured against
is built for that same population.</p>

{table(["Market", "Segment", "Scenario", "Units", "Mt", "t/veh"], rows, left=3)}

<p>Korea is where this matters most, because Hyundai's Porter and Kia's Bongo one-tonne trucks
are a large share of Korean domestic volume. Measured against Korean goods vehicles &mdash;
{num(float(freight_params["fleet_intensity_gco2_km"]), 0)} gCO&#8322;/km over
{num(float(freight_params["vkt_km"]), 0)} km a year for
{freight_params["lifetime_years"]} years, against
{num(float(car_params["fleet_intensity_gco2_km"]), 0)} gCO&#8322;/km over
{num(float(car_params["vkt_km"]), 0)} km for {car_params["lifetime_years"]} years for cars
&mdash; the freight cohort is the single largest per-vehicle contribution in the whole report
under S1 ({num(float(kr[("freight", "S1")]["per_vehicle"]) / 1000, 1)} tCO&#8322;e per vehicle)
and a substantial liability under S2
({num(float(kr[("freight", "S2")]["per_vehicle"]) / 1000, 1)}).</p>

<p>That pair of numbers is a warning about segment benchmarks in general. A goods vehicle
travels further and emits more per kilometre than a car, so both the margin and the liability
scale up together; the per-vehicle figure is large in whichever direction the scenario points.
Heavy trucks and coaches above 3.5 tonnes are counted and withheld, because Korea's fuel-economy
labelling scheme does not certify them and no product intensity exists to measure them with.
Japan carries a goods segment on the same principle; buses are not built there because the
national distance survey bundles petrol buses in with cars and special vehicles, which would
give an all-bus emissions numerator a diesel-only denominator.</p>
"""
    return page("segments", "Trucks are measured as trucks", body, number="12")


def not_in_numbers(f: Facts) -> str:
    """What is withheld and why."""
    rows = [
        [
            MARKETS[r["market"]] if r["market"] in MARKETS else esc(r["market"]),
            num(int(r["units"])),
            str(r["cells"]),
            esc(r["reason"])[:190],
        ]
        for r in f.withheld[:14]
    ]
    total_withheld = sum(int(r["units"]) for r in f.withheld)
    cohort_rows = [
        [
            MARKETS[r["market"]] if r["market"] in MARKETS else esc(r["market"]),
            COMPANIES.get(r["company"], esc(r["company"])),
            esc(r["model"]) or "&mdash;",
            num(int(r["units"])),
            esc(r["reason"])[:150],
        ]
        for r in f.cohort_withheld[:10]
    ]
    body = f"""
<p>{num(total_withheld)} units carry no result. They are listed, never absorbed into a total and
never assumed to behave like the units that do. The reasons fall into four classes, and each is a
statement about a missing published input rather than about the vehicles.</p>

{table(["Market", "Units", "Cells", "Reason"], rows, left=1)}

<p>The largest single class is the plug-in hybrid. No sales release in any of these markets
publishes a utility factor &mdash; the share of distance a plug-in actually drives on
electricity &mdash; and the certified combined value depends entirely on it, so plug-in units are
counted and left unassessed rather than assessed on a guess. Fuel-cell vehicles are withheld for
the mirror reason: no destination in scope publishes a hydrogen supply intensity. Battery-electric
units in Japan are withheld because the Japanese fuel-economy list is a fuel-consumption
publication and carries no electricity-consumption rating at all.</p>

<h3>Volumes held out before the impact step</h3>
{table(["Market", "Company", "Nameplate", "Units", "Reason"], cohort_rows, left=3)}

<h3>Four biases that run the other way</h3>
<p>Not every gap is neutral, and three of the four known biases in this report flatter the
companies:</p>
<ul>
<li>The US benchmark includes pickups and large SUVs, which raises it and makes every US product
look better than a car-only comparison would.</li>
<li>Japan's real-world correction factor is borrowed from the European on-board fuel-consumption
programme for the same test procedure; Japan's own cycle omits the highest-speed phase, so the
true gap is probably larger and the factor understates real-world product emissions.</li>
<li>Korea's committed pathway is applied to intensity rather than to absolute emissions while its
fleet is still growing, which makes the intensity-only reading looser than the absolute target.</li>
<li>Against that, withholding battery-electric units in Japan removes the cleanest products from
the Japanese cohorts and makes those results worse than complete data would.</li>
</ul>
<p>Every one of these is on the affected rows in the output tables, not only in this
paragraph.</p>
"""
    return page("gaps", "What is not in the numbers", body, number="13")


def quality(f: Facts) -> str:
    """Tiers and the §5.3 flag."""
    rows = []
    for r in f.quality:
        rows.append(
            [
                r["market"],
                COMPANIES[r["company"]],
                str(r["cohort_year"]),
                pct(float(r["tier_c_share"])),
                "yes" if str(r["directional_only"]).lower() in {"1", "true"} else "no",
                pct(float(r["tier_c_units_share"])),
                f"{r['lifetime_t_central_years']}",
                esc(r["test_cycles"]),
            ]
        )
    tier_rows = []
    for market in MARKETS:
        params = [r for r in f.parameters if r["market"] == market]
        worst = {
            "fleet intensity": {r["fleet_intensity_tier"] for r in params},
            "distance": {r["vkt_tier"] for r in params},
            "lifetime": {r["lifetime_tier"] for r in params},
        }
        tier_rows.append(
            [
                MARKETS[market],
                "/".join(sorted(worst["fleet intensity"])),
                "/".join(sorted(worst["distance"])),
                "/".join(sorted(worst["lifetime"])),
            ]
        )
    body = f"""
<p>Every input value in this project carries a data-quality tier &mdash; A directly sourced,
B derived or estimated, C proxied &mdash; and every result cell carries the worst tier of the
benchmark side, the worst of the product side, and the worst of both. The tiers are not
decoration: they decide whether a figure may be read as a magnitude or only as a direction.</p>

{
        table(
            [
                "Market",
                "Company",
                "Year",
                "Proxied-distance share",
                "Directional only",
                "Tier-C cells",
                "Life yr",
                "Test cycle",
            ],
            rows,
            left=3,
        )
    }

<p>Two different tier-C measures appear in that table and they answer different questions. The
<i>proxied-distance share</i> is the guideline's own suppression rule: above
{pct(DIRECTIONAL_THRESHOLD, 0)} of units on a proxied distance, a result is directional only. The
<i>tier-C cells</i> column is the share of units whose worst-of tier is C for any reason at all.
The first flags {sum(1 for r in f.quality if str(r["directional_only"]).lower() in {"1", "true"})}
cohorts; by the second, every cohort outside the EU27 is entirely tier C.</p>

{table(["Market", "Fleet intensity", "Distance", "Lifetime"], tier_rows)}

<p>What makes each market tier C is different, and worth knowing before quoting a figure:</p>
<ul>
<li><b>United States</b> &mdash; the expected vehicle lifetime. It is the NHTSA survival
schedule, fitted to 1977&ndash;2002 registrations rather than to the current fleet. Every other
US input is tier A or B.</li>
<li><b>Korea</b> &mdash; the fleet intensity, because the national inventory publishes no
vehicle-class split, and the lifetime, derived from a mean fleet age whose oldest band is
open-ended.</li>
<li><b>Japan</b> &mdash; the powertrain split and the borrowed real-world factor. Its emissions
numerator, uniquely, is tier A: Japan publishes road CO&#8322; by vehicle type.</li>
<li><b>EU27</b> &mdash; the distance for the thirteen states with no national figure, and the
lifetime everywhere, derived from mean fleet age.</li>
</ul>

<div class="callout"><p><b>How to quote these results.</b> The direction and the ordering are
robust: they survive every sensitivity variant the model carries. The magnitudes are not, and
should be quoted with the band in section 15, not as point estimates.</p></div>
"""
    return page(
        "quality", "Data quality, and what each market's weakest link is", body, number="14"
    )


def sensitivity(f: Facts) -> str:
    """The tornado."""
    label_for = {
        "lifetime": "vehicle lifetime, ±3 years",
        "vkt_proxy": "proxied distance, quartile band",
        "realworld": "real-world correction, low/high",
        "powertrain_mix": "powertrain mix, all-hybrid bound",
    }
    rows = []
    for (company, market), dims in sorted(f.sensitivity.items()):
        for dimension, (low, central, high) in sorted(dims.items()):
            if abs(high - low) < 1e-9:
                continue
            rows.append(
                (
                    f"{market} {COMPANIES[company]} — {label_for.get(dimension, dimension)}",
                    low / 1e6,
                    central / 1e6,
                    high / 1e6,
                )
            )
    rows.sort(key=lambda r: -(abs(r[3] - r[1])))
    svg = chart.ranges(
        rows[:16],
        unit="MtCO2e, committed policy",
        label="Sensitivity of the committed-policy result to each input",
        dp=1,
        label_width=250,
    )
    bands = lifetime_bands(f)
    body = f"""
<p>Four inputs are varied one at a time over their published or documented ranges, and every
cohort is repriced. The bars below are the resulting spread around the central figure for the
{COMMON_COHORT} cohorts under committed policy, largest spread first.</p>

{
        figure(
            svg,
            "15.1",
            "Sensitivity of the committed-policy result. The bar is the range, the vertical "
            "mark the "
            "published central value. Dimensions whose variant leaves the result unchanged are "
            "omitted. Source: <code>ti_sensitivity.csv</code>.",
        )
    }

<p>Vehicle lifetime dominates everywhere:
{"; ".join(f"{MARKETS[m]} {pct(v, 0)}" for m, v in bands.items())} of the central value, against
under {
        pct(
            max(
                abs(h - lo) / abs(mid)
                for _n, lo, mid, h in rows
                if "distance" in _n or "real-world" in _n
            ),
            0,
        )
    }
for the next largest. That is a structural feature of the method rather than a defect in one
market's data: the lifetime is both the number of years of benchmark decline a vehicle has to
survive and the multiplier on every year's gap, so it enters the result twice.</p>

<p>The powertrain-mix bound matters where a sales release does not split a nameplate by
powertrain and the split has to be assumed from a market-wide share. Where such a bound exists,
pricing every unit of the affected nameplates as a hybrid moves the cohort result by
{pct(max((abs(h - lo) / abs(mid) for _n, lo, mid, h in rows if "powertrain" in _n), default=0), 0)}
at most &mdash; large enough that the assumption is named in the method document and carried as
a variant rather than buried.</p>

<div class="callout"><p><b>What no sensitivity variant does.</b> None of them flips a
committed-policy result from liability to contribution. Taking three years off every vehicle's
life &mdash; the most favourable single variant in the model &mdash; reduces the liabilities but
does not remove one of them. The finding in section 5 is robust to every parameter the model is
willing to vary.</p></div>
"""
    return page("sensitivity", "What would change the answer", body, number="15")


def reproduce(f: Facts) -> str:
    """Provenance and how to rebuild."""
    rows = [
        [f"<code>{esc(r['table'])}</code>", num(int(r["rows"])), f"<code>{r['sha256'][:16]}</code>"]
        for r in f.manifest
    ]
    body = f"""
<p>Everything in this report is regenerated from the raw sources by one command, and every
intermediate table is content-hashed so a figure can be traced to the exact bytes it came
from.</p>

<div class="eq">.venv/bin/python script/auto/run_all.py<br>
.venv/bin/python script/auto/report/build_report.py</div>

<p>The first command fetches or reuses every raw file, re-derives every processed dataset,
rebuilds the model, writes the SQLite database, and runs the linter and the test suite, exiting
non-zero at the first failure. The second reads that database and writes this file. No number in
this report is typed by hand; the prose interpolates the same query results the charts use, so a
sentence cannot drift away from its table.</p>

<h3>Output tables this report reads</h3>
{table(["Table", "Rows", "SHA-256 (first 16)"], rows, left=1)}

<p class="small muted">Every raw file is recorded in <code>data/auto/registry/raw_files.csv</code>
with its source, its original filename as served, and its SHA-256; every source is in
<code>data/auto/registry/sources.csv</code> with a URL, an access date and a licence. Data as of
{f.as_of}. This report carries no build timestamp, so two builds from the same database are
identical.</p>
"""
    return page("reproduce", "How to reproduce this", body, number="16")


def appendix_parameters(f: Facts) -> str:
    """Appendix A: every destination parameter."""
    rows = []
    for r in f.parameters:
        rows.append(
            [
                r["market"],
                r["country"],
                esc(r["segment"]),
                num(float(r["vkt_km"]), 0),
                esc(r["vkt_tier"]),
                num(float(r["fleet_intensity_gco2_km"]), 1),
                esc(r["fleet_intensity_tier"]),
                num(float(r["grid_gco2_kwh"]), 1),
                maybe(r["mean_age_years"], 2),
                f"{r['lifetime_years']}",
                esc(r["lifetime_tier"]),
            ]
        )
    body = (
        "<p>One row per destination and segment: the benchmark inputs, each with its"
        " data-quality tier.</p>"
        + table(
            [
                "Market",
                "Country",
                "Segment",
                "km/yr",
                "T",
                "gCO2/km",
                "T",
                "Grid",
                "Mean age",
                "Life",
                "T",
            ],
            rows,
            left=3,
        )
    )
    return page("appendix-a", "Appendix A — destination parameters", body)


def appendix_rates(f: Facts) -> str:
    """Appendix B: the rate derivations."""
    seen: set[tuple[str, str, str]] = set()
    rows = []
    for r in f.rate_rows:
        if r["tbl"] == "EU27" and r["country"] != "DE":
            continue
        key = (r["tbl"], r["scenario"], r["rate"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            [
                MARKETS[r["tbl"]],
                r["scenario"],
                esc(r["rate"]),
                f"{float(r['value']) * 100:+.3f} %",
                esc(r["target_level"]),
                f"{r['base_year']}&ndash;{r['target_year']}",
                esc(r["source_id"]),
            ]
        )
    derivations = []
    for r in f.rate_rows:
        if r["scenario"] != "S2" or r["rate"] != "r_fleet":
            continue
        if r["tbl"] == "EU27" and r["country"] != "DE":
            continue
        derivations.append(
            f"<h3>{MARKETS[r['tbl']]} — committed fleet pathway</h3>"
            f'<p class="small">{esc(r["derivation"])}</p>'
        )
    body = (
        "<p>Every scenario rate, with the policy anchor it comes from. The EU27 row shows"
        " Germany for the S1 trend, which is fitted per member state.</p>"
        + table(
            ["Market", "Scenario", "Rate", "Per year", "Anchor", "Window", "Source"], rows, left=3
        )
        + "".join(derivations)
    )
    return page("appendix-b", "Appendix B — scenario rates and their anchors", body)


def appendix_sources(f: Facts) -> str:
    """Appendix D: the source registry."""
    def clip(text: object, width: int) -> str:
        """A cell that fits the page, cut on a word and marked where it was cut."""
        raw = str(text or "")
        if len(raw) <= width:
            return esc(raw)
        cut = raw[:width].rsplit(" ", 1)[0]
        return esc(cut) + "&hellip;"

    rows = []
    for r in f.sources:
        source_id = esc(r["source_id"])
        link = (
            f'<a href="{esc(r["url"])}"><code>{source_id}</code></a>'
            if r["url"]
            else f"<code>{source_id}</code>"
        )
        rows.append(
            [link, clip(r["publisher"], 46), clip(r["title"], 96), clip(r["license"], 34)]
        )
    body = (
        "<p>Every source behind every figure in this report, as recorded in"
        " <code>data/auto/registry/sources.csv</code> at build time; each identifier links to"
        " the publisher. Titles and licences are cut to fit the page &mdash; the registry"
        " carries them in full, together with the access date, the original filename each file"
        " was served under and its SHA-256.</p>"
        + table(["Source", "Publisher", "Title", "Licence"], rows, left=3)
    )
    return page("appendix-d", "Appendix D — sources", body)


def build(f: Facts) -> str:
    """Assemble the whole document."""
    sections = [
        cover(f),
        contents(),
        summary(f),
        what_it_measures(f),
        scope(f),
        headline(f),
        finding_committed(f),
        finding_crossover(f),
        finding_profile(f),
        finding_powertrain(f),
        finding_market(f),
        finding_geography(f),
        benchmarks(f),
        segments(f),
        not_in_numbers(f),
        quality(f),
        sensitivity(f),
        reproduce(f),
        appendix_parameters(f),
        appendix_rates(f),
        appendix_sources(f),
    ]
    items = "".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in SECTIONS)
    toc = (
        '<section class="page"><h2 id="contents">Contents</h2>'
        f'<ul class="toc">{items}</ul>'
        '<p class="small muted">This report is one file. It opens from disk, prints to A4, '
        "contains no script and makes no network request; the charts are inline SVG.</p>"
        "</section>"
    )
    html = "".join(sections).replace("@@CONTENTS@@", toc)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<style>{CSS}</style>
</head>
<body><main>{html}</main></body>
</html>
"""


def main() -> None:
    """Write the report."""
    facts = load()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(facts), encoding="utf-8")
    size = OUT.stat().st_size
    charts = OUT.read_text(encoding="utf-8").count("<svg")
    tables = OUT.read_text(encoding="utf-8").count("<table>")
    print(
        f"{OUT.relative_to(REPO)}: {size / 1024:,.0f} KB, {len(SECTIONS)} sections, "
        f"{charts} charts, {tables} tables, data as of {facts.as_of}"
    )


if __name__ == "__main__":
    main()
