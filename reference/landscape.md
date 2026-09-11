# Where the Trade Impact framework sits

TI takes a product sold into a country, models what it emits over its operating life, subtracts
what that country's own sector trajectory implies for the same service, and reports the
difference in tonnes with a sign. Every part of that sentence exists somewhere in the published
literature. The combination does not. This note says which parts come from where, what each
neighbour would say about TI, and what the register's own contents demand that TI change.

Keys in `backticks` are rows in [`references.csv`](references.csv).

## Three questions, not one

Every framework in the register answers one of three questions, and most of the confusion around
TI comes from readers assuming it answers a different one than it does.

| question | what it produces | families |
|---|---|---|
| What was emitted, and whose books does it go in? | an absolute quantity, no comparison | `scope3`, `disclosure_standard`, `attribution_finance`, `embodied_trade`, `committed_emissions` |
| How far is this from where it should be? | a distance from a pathway | `alignment` |
| What difference did it make? | a difference against a counterfactual | `avoided_emissions`, `counterfactual`, `grid_baseline` |

The remaining families are context rather than method. `export_impact` and `power_attribution`
are the studies that ask TI's question of the same assets without computing TI's quantity,
`transport_benchmark` holds the evidence base for the automotive parameters, `policy_instrument`
the rules that already cross a border, `critique` the attacks on the whole counterfactual family,
and `data_source` the two references the benchmark itself is read from.

TI is the only entry in the register that sits in two rows at once. It computes a **distance from
a pathway**, which is an alignment metric, and reports it **in tonnes with a causal sign**, which
is the output convention of an impact metric. That hybrid is the framework's contribution and the
source of every serious objection to it.

The comparison worth keeping in mind is `pacta_investors_methodology`. PACTA does asset-level,
ownership-attributed, scenario-benchmarked analysis - structurally the same pipeline as TI - and
its designers deliberately stop before converting the deviation into tonnes, reporting a
technology-mix deviation instead. TI takes the extra step. Nothing in the register makes that
step illegitimate, and nothing in the register makes it free.

## The families

### `scope3` — the absolute inventory of sold products

`ghgp_scope3_standard` fixes what Category 11 is: the total expected lifetime emissions of the
products sold in the reporting year, booked in that year, with no reference to any alternative.
`ghgp_scope3_technical_guidance` gives the arithmetic and requires the lifetime and use-profile
assumptions to be disclosed. `cdp_scope3_relevance` makes the category mandatory-relevant for
automotive while offering no sector-specific method, and `ifrs_s2` is where a listed company
publishes the result.

TI's product term is this calculation. The benchmark term is what Category 11 does not have, and
§9.5 of the standard is explicit about where that puts TI — verified verbatim in the 2011 PDF:

> Any estimates of avoided emissions must be reported separately from a company's scope 1,
> scope 2, and scope 3 emissions, rather than included or deducted from the scope 3 inventory.

TI is therefore beside Category 11 and never inside it. The whitepaper already says this; the
standard is the reason it must keep saying it on the face of every table.

### `attribution_finance` — dividing one asset's emissions among the parties behind it

`pcaf_financed_emissions` is the discipline TI's role columns will be measured against. It folds
each financier's share into an attribution factor, multiplies it through, and the factors across
all financiers of one asset sum to no more than one. `pcaf_facilitated_emissions` extends this to
institutions that arrange rather than hold, with a weighting to reflect the difference — the one
place in the standards world that already says an arranging role is not an owning role.

TI breaks with this on purpose: the share stays outside the number, the same unit appears under
every role that touched it, and the roles do not sum. That is defensible as a design — it is what
lets a reader choose the weighting later — but it is only defensible if the methodology states a
**prohibition on aggregation** rather than a footnote, because summing TI across seven roles
multiplies one plant's physics by seven.

### `alignment` — how far a company is from a pathway

`sbti_sectoral_decarbonization` is the canonical form: converge a company's intensity onto a
sector pathway. `sbti_corporate_net_zero_v2`, `sbti_automotive_standard_draft`,
`tpi_automotive_carbon_performance`, `pacta_investors_methodology`, `pacta_changing_gear` and
`wba_automotive_benchmark` are instances of it. `iigcc_cumulative_benchmark_divergence` is the
closest cousin to TI's integration over time: it sums the divergence from a benchmark across
years rather than reading it once at a target date.

`gfanz_portfolio_alignment` is the family's own record of the problem TI inherits: two
defensible methods score the same company differently, and the divergence survived a convergence
effort. The limit that matters most for TI is that a divergence metric is **not meaningful to
aggregate** - a point `brander_attributional_consequential` makes from the accounting side and
`pcaf_financed_emissions` builds its whole architecture around.
`eu_climate_benchmarks_regulation` is the precedent for one of these metrics being written into
law, and for what it costs: the regulator had to hard-code the trajectory because the private
methods would not agree on one.

One line in `sbti_corporate_net_zero_v2` bears directly on TI's negative arm, verified verbatim
in the June 2026 PDF:

> For the avoidance of doubt, product-level avoided emissions associated with the use of sold
> products are not eligible for recognition under this program.

A client cannot carry a negative TI toward a validated target. That is not a flaw in TI, but it
settles what TI is for: it is an analytical and policy instrument, not a disclosure a company
can bank.

### `avoided_emissions` — the counterfactual claim TI's negative arm resembles

`wri_comparative_emissions_impacts` is the house treatment of product-minus-reference and the
one that refuses the term Scope 4. `wbcsd_avoided_emissions_v2` is the text a corporate claim is
now judged against, with eligibility gates and an allocation step. `itu_l1480` is the only
formally approved standards-body method in the family, and the one that requires **rebound** to
be addressed. `carbone4_nzi_pillar_b` keeps induced and avoided emissions in separate pillars
that are never netted — the sharpest structural objection to TI's single signed number.
`project_frame_methodology` and `mission_innovation_aef` handle the investor and the innovation
cases, `iea_global_ev_outlook` is the same-distance construction applied to vehicles at global
scale, and `jlca_japan_avoided_guidelines_v2` is the Japanese guidance that already varies the
reference by country and region — the closest existing precedent for TI's destination-specific
framing, in one of the two home countries TI scores.

`gronman_carbon_handprint` performs TI's subtraction with the customer's alternative as the
baseline; `bylahally_credit_allocation` divides the resulting credit among actors, which is what
TI declines to do; `de_giovanni_scope4` and `bowman_pacer_framework` are the current wave of
frameworks TI will be shelved beside.

### `counterfactual` — the formal machinery TI is actually running

`ghgp_project_protocol` is the closest formal analogue to TI's benchmark. Its performance-standard
route derives a benchmark from the population of baseline candidates at a **stated stringency
level**, chosen and justified by the analyst. TI's observed-trend scenario is a performance
standard whose stringency is the fitted mean, which by construction roughly half of everything
beats. `ghgp_policy_action_standard` is where a policy path becomes a baseline, with the
documentation and sensitivity duties that come with it — TI inverts its use, taking a policy path
as the counterfactual for a private product rather than as the reference for the policy.

`brander_attributional_consequential` is the cleanest statement of the distinction TI depends on,
and `plevin_attributional_misleads` the sharpest warning about averages standing in for margins.
`wang_grounded_emissions_consequences` states the inventory-versus-consequence gap TI is built in.

`ghgp_ami_white_paper` is the live development that matters most. The GHG Protocol's Actions and
Market Instruments work proposes a fourth reporting statement — a **GHG impact statement** on a
consequential basis, separate from the inventory, covering the production and sale of products.
That is TI's home if TI has one. The statement is currently drawn around avoided, reduced and
removed outcomes, all one-signed; TI's positive arm, emissions *added* above a benchmark, is a
sub-category nobody has drawn. The white paper lists those boundaries as an open question, which
is an invitation.

### `grid_baseline` — the destination benchmark, already in operation

This is the family the register was worth building for, because TI's benchmark is not new and
the framework has been writing as though it were.

`cdm_tool07_grid_emission_factor` has standardised the emission factor of displaced grid
electricity for two decades, as an operating margin weighted with a build margin. TI's power
benchmark is the same object with a different construction, and TI has not yet said whether its
trajectory is closer to an operating margin or a build margin. They are different counterfactuals
and a reviewer from that world will ask.

`ifi_ghg_accounting_renewables` is closer still: the multilateral banks compute a project's gross
emissions and then its emissions **net of a country-specific grid baseline**, using a shared
default factor for every country. That is TI's identity, term for term, already operating. The
four differences are the whole of TI's contribution — the baseline there is a static
appraisal-year factor rather than a trajectory evaluated in every year of the asset's life, the
figure is annual rather than lifetime, it is produced by one institution for its own portfolio
rather than across every firm holding a role, and there is no role decomposition.

`mdb_paris_alignment_direct_investment` is the only operating instrument that tests a
cross-border project against the **destination's own NDC**, which is TI's second scenario. It is
a qualitative screen, its first test is deliberately weak, and it carries the disclaimer TI
should copy: the judgement is of the operation, and is not a judgment or endorsement of the
country's NDC. `ebrd_paris_alignment_methodology` shows how one bank drafts it.

### `committed_emissions` — the lifetime sum

`tong_committed_emissions`, `davis_future_co2` and `pfeiffer_committed_power` compute what
existing and planned assets will emit over their remaining lives, against a carbon budget and
with no attribution. `davis_socolow_commitment_accounting` proposes booking that commitment by
vintage, which is TI's convention. `cui_coal_plant_lifetimes` is the best-sourced basis for the
operating life that dominates any such sum, and `seto_carbon_lock_in` with
`erickson_assessing_carbon_lock_in` supply the vocabulary — and the limit, since physical
commitment is one of three lock-in channels and TI measures only that one.

### `embodied_trade` — the family TI is confused with

`davis_caldeira_consumption_based`, `oecd_co2_embodied_trade`, `steininger_consumption_based` and
`afionis_consumption_based_future` reallocate the emissions released *making* a traded good from
the producer to the consumer. The global total is unchanged, no counterfactual is involved, and
the result can never be negative. TI models the emissions an exported machine causes *in use*,
years later, in the destination, and subtracts a benchmark. The two do not overlap and cannot be
added. Stating that early saves an economist the trouble of assuming TI is a multi-regional
input-output study and dismissing it as a bad one.

### `export_impact` — the export question, asked by others

`newman_used_vehicle_exports` is the closest published precedent for TI's automotive framing:
exported vehicles scored per kilometre against a fleet-average counterfactual, with export framed
as offshoring a liability. It uses the **exporting** country's fleet as the reference where TI
uses the destination's, its benchmark is static, and it starts where TI stops — at the second
transfer. The two cover complementary halves of one vehicle's life, and TI should say so.
`unep_used_vehicles_2020`, `unep_used_vehicles_2024` and `kim_used_vehicles_co2` carry the flows
and the exporter-side accounting question.

`guo_overseas_coal_emissions` is the closest cousin on the power side: 908 overseas coal plants,
emissions attributed to the investor country and projected over their lives. It attributes to
countries rather than to named firms by role, uses one investment share rather than parallel role
columns, and projects against unchanged policy rather than the destination's own path.
`carbon_majors` is the ancestor of firm-level attribution, `kuhne_carbon_bombs` the same unit of
analysis one step up the supply chain, `climate_analytics_australia_footprint` the same political
argument for an exported consumable rather than an exported machine, and
`kong_gallagher_overseas_coal` the political economy of the object TI measures.

### `power_attribution` — who was on the deal

`sfoc_coal_insurers` names the insurers behind KEPCO's overseas coal projects — Nghi Son 2,
Jawa 9 and 10, Vung Ang 2, the same units in TI's result set — from documents obtained through
the Korean National Assembly. It is the closest precedent for TI's cover role and it attributes
underwriting capacity, never a tonne. `oci_public_finance_energy_database` is the transaction
record behind the lender roles, with no emissions layer at all, and
`censkowsky_export_finance_shift` is the peer-reviewed treatment of export-credit energy deals
that stops one step short of the emissions those deals enabled.

There is no published method that computes the emissions an export credit agency enables. That is
an opening, and the framework should claim it plainly.

### `transport_benchmark` and the rest

The road-transport rows — `icct_real_world_co2_2026`, `icct_lab_to_road_international`,
`icct_global_lca_cars_2021`, `icct_global_automaker_rating`, `ec_obfcm_first_report`,
`te_phev_gap_2025`, `te_ev_progress_2026`, `greenpeace_auto_environmental_guide`,
`influencemap_auto_climate`, `lu_vehicle_survivability` — are the evidence base for TI's
automotive parameters rather than competing frameworks. Their bearing on TI's open choices is set
out in the next section.

### `policy_instrument` — what already crosses the border

`ipcc_2006_national_territory` decides whose inventory an exported product's emissions land in,
and corrects a loose assumption: road-transport emissions follow the **fuel sale**, not the
vehicle. `paris_agreement` governs what may be claimed — an avoided tonne inside a destination is
that country's unless it authorises a transfer, so a TI contribution is a measurement and never a
claim on anyone's target. `cbam_regulation` reaches across the border for emissions embedded in
imports, the mirror image of TI's question. `oecd_arrangement_eu_transposition` is the export
credit rulebook Japan and Korea sit in: it gates support on the technology, never on the
destination's trajectory, which is the gap between what the multilateral banks require of
themselves and what the export credit agencies require of themselves.
`glasgow_statement_cetp` closes the forward pipeline TI measures, which is why TI's value is
retrospective.

## Has anyone already computed TI?

Not as specified. TI's claim is the conjunction of four properties, and no published work holds
all four.

| | destination benchmark | lifetime sum | per unit | per firm by role |
|---|---|---|---|---|
| `guo_overseas_coal_emissions` | no, unchanged policy | yes | yes | investor country only |
| `ifi_ghg_accounting_renewables` | yes, but static | no, annual | yes | one institution's own book |
| `cdm_tool07_grid_emission_factor` | yes, historical margin | crediting period | yes | no |
| `pfeiffer_committed_power` | no, carbon budget | yes | yes | no |
| `pcaf_financed_emissions` | no, gross | no, annual | yes | financial roles, collapsed |
| `sfoc_coal_insurers` | no | no | yes | yes, and on TI's own projects |
| `newman_used_vehicle_exports` | exporter's fleet | per kilometre | per vehicle | no |
| **Trade Impact** | yes, and moving | yes | yes | yes, un-collapsed |

The novelty is the combination, and the honest way to present it is this table rather than a
claim of originality for any single element.

One practical consequence for the power case: the figures in circulation for these plants are
**gross** lifetime tonnages from advocacy material. Because TI is a difference against a grid
that is far from clean, TI's number for the same plant must come out materially smaller. That is
an expected result, not an error, and publishing the gross and the net side by side for the named
units is the way to keep the comparison legible.

## What the register demands of TI

Six changes, each anchored in a document above. They are listed in the order a reviewer will
reach them.

1. **State the stringency of the observed-trend benchmark, or renounce the causal reading.**
   A fitted mean is not a counterfactual; roughly half of everything sold beats it.
   `ghgp_project_protocol` requires a stated stringency level for exactly this reason and
   `plevin_attributional_misleads` is the same objection from the assessment side.

2. **Never publish one netted number.** `ghgp_scope3_standard` §9.5 forbids deduction from the
   inventory, `carbone4_nzi_pillar_b` keeps the arms in separate pillars, and
   `sbti_corporate_net_zero_v2` refuses product-level avoided emissions recognition outright.
   Report the added and the avoided arms as two labelled quantities with the non-netting rule on
   the face of the table.

3. **Make the prohibition on aggregating roles part of the method, not a footnote.**
   `pcaf_financed_emissions` exists to prevent the multiplication TI's design permits, and
   `pcaf_facilitated_emissions` is the precedent for treating roles differently. Borrowing the
   shape while declining the discipline is the objection that will stick.

4. **Publish a benchmark vintage and a recalculation policy.** An NDC update restates every
   historical TI figure for that destination without anything the firm did changing.
   `ghgp_policy_action_standard` requires baseline assumptions and sensitivity to be documented,
   and `okeeffe_brander_comparison` is the evidence that method choice, not physics, drives the
   headline. Put the NDC submission and date on every row and report the two scenarios as a range.

5. **Say which margin the power benchmark is.** `cdm_tool07_grid_emission_factor` distinguishes
   the operating margin from the build margin because they answer different questions. TI's
   trajectory is currently neither, explicitly.

6. **Fix the vehicle lifetime and the distance schedule.** TI takes the operating life from the
   destination's mean fleet age and holds annual distance flat. A mean age is a property of a
   stock, and half a cohort outlives it, so the sum truncates near the midpoint — in the years
   where the gap against a declining benchmark is widest. `lu_vehicle_survivability` is the
   ancestor of the survival-and-mileage schedule, `icct_global_lca_cars_2021` states an
   eighteen-year life with distance decaying about five per cent a year, and
   `sbti_automotive_standard_draft` publishes a full twenty-point decay schedule. The automotive
   guideline already defines a survival function and then does not use it.

Points 1 to 5 are about what TI may claim. Point 6 changes the numbers.
