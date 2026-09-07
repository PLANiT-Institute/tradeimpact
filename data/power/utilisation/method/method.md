# utilisation — how hard each destination runs each fuel

## What this dataset is

One capacity factor per destination and fuel, implied by the capacity and generation that country
publishes. It answers the weakest question in the model: how much a unit with no published
capacity factor actually generates.

The August 2026 Global Integrated Power tracker publishes no unit-level capacity factor, and a
single global default per technology is a statement about a technology rather than about the
place. Global Energy Monitor itself moved to country-level factors for its lifetime CO2
estimates, computed from its own capacity data and Ember generation; this dataset does the same
arithmetic from one published source that carries both series.

## Source

Ember, **Yearly Electricity Data** (full release, long format), CC BY 4.0 —
<https://ember-energy.org/data/yearly-electricity-data/>. The same publisher's carbon-intensity
series is already the grid benchmark ([`grid`](../../grid/method/method.md)).

The published file is ~49 MB and almost all of it is aggregates, shares and per-capita series this
model never reads, so `raw/ember/ember_yearly_fuel.csv` is a **filtered subset**: `Category` in
{Capacity, Electricity generation}, `Subcategory` = Fuel, `Area type` = "Country or economy".
`raw/ember/index.csv` records the download URL, the original file's bytes and SHA-256, the filter
expression itself and the subset's own SHA-256, so a reader can reproduce the subset from the URL
and check that nothing in the kept rows was altered.

## Method

$$ CF_{c,f,y} = \frac{G_{c,f,y}\,[\mathrm{TWh}] \times 10^{6}}
                     {P_{c,f,y}\,[\mathrm{GW}] \times 10^{3} \times 8760} $$

ASCII: `cf = generation_twh * 1e6 / (capacity_gw * 1e3 * 8760)`

- The latest year with both figures is the central value; the low and high are that country and
  fuel's range over the last five usable years, and they are what the sensitivity varies.
- A pair is used only where the capacity is at least 0.05 GW and the result lands in (0, 1]. A
  small fleet, or a capacity series that lags a new plant, produces a factor above one; those are
  dropped rather than clipped.
- `method/fuel_map.csv` maps Ember's fuel names onto this model's `fuel_type`. Ember publishes no
  oil line, so **`Other Fossil` stands in for oil** — that row is marked `proxy_fuel = yes` and is
  tier C rather than tier B. Hydro includes pumped storage in some countries, which lowers the
  implied factor there.
- What this factor is **not**: it is the destination's whole fleet for that fuel, of every vintage
  and size, not this unit. A new ultra-supercritical unit in a country whose coal fleet is old and
  lightly used will be understated, and the reverse overstated. It replaces a global default with
  a national one; it does not replace a plant's own load factor.

## Output

`processed/capacity_factors_country.csv` — country (alpha-2), iso3, fuel_type, year, capacity_gw,
generation_twh, capacity_factor, cf_low, cf_high, years_used, proxy_fuel, source_id, note.

823 country x fuel rows for 195 countries (2026-09-07 run). 552 of the 558 assessed units take
their destination's factor; 6 fall back on the class default in
[`projects`](../../projects/method/method.md).

## Scripts

| step | script |
|---|---|
| fetch | `script/power/utilisation/fetch_ember_yearly.py` |
| extract | `script/power/utilisation/extract_capacity_factors.py` |
