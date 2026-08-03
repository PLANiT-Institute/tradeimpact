# Evidence and logic audit

Audit date: 2026-08-03 · Public contract: `alignment-v2`

This audit evaluates whether the current public company snapshots are source-backed, whether the
sources are sufficiently independent for the claim made, and whether each calculation preserves
the source boundary. It is not a claim that every desired company-market comparison is available.

## Audit conclusion

| Pilot | Published observation | Target treatment | Assessment |
|---|---|---|---|
| Toyota · EU27 · 2024 | 803,094 EEA registrations; 803,042 with WLTP; 107.073 gCO2/km | EU 2025 and 2030 new-car fleet values are direct pathway comparators | Source-backed and reproducible for a Toyota-brand EU27 portfolio snapshot; not manufacturer compliance and not lifetime GHG |
| JERA · Japan · FY2024 | 242 TWh net sending-end generation; 520 kgCO2e/MWh | Japan 2030 use-end factor and 2040 national mix ranges are context only | Company observations are independently assured; no company target gap is logically available |
| KOEN · Korea · 2024 | 39,660 GWh reported generation; 30,606,585 tCO2e Scope 1; 103,752 tCO2e Scope 2 | Korea 2030 transition-sector emissions and 2030/2038 carbon-free shares are context only | Company totals are source-backed but not independently assured in the reviewed web table; missing gross/net basis and row-total discrepancies block intensity and target-gap calculations |
| MOL · Global fleet · FY2024 | 10.95 gCO2e/ton-mile lifecycle EEOI; 783 vessels | IMO 2030 carbon-intensity, absolute-GHG, and zero/near-zero-energy ambitions are context only | The company metric is independently assured, but its FY2019 Standard Method anchor, WtW boundary, and company fleet aggregation do not match IMO's 2008 international-shipping average CO2 target |

The public dataset contains no vehicle-lifetime greenhouse-gas estimate, reconstructed company
history, inferred fleet mix, avoided-emissions claim, or universal cross-sector score.

## Toyota evidence chain

1. The [EEA CO2 monitoring dataset](https://co2cars.apps.eea.europa.eu/) supplies final 2024
   Toyota-brand new passenger-car registration records.
2. The adapter aggregates observed registrations and computes the WLTP-weighted average only for
   records with a reported WLTP value. Coverage remains explicit: 52 registrations are unmatched.
3. [Regulation (EU) 2019/631](https://eur-lex.europa.eu/eli/reg/2019/631/2025-07-09/eng)
   supplies the EU-wide 2025 and 2030 new-car fleet pathway values.
4. The platform reports distance to that fleet pathway. It does not label the result Toyota's
   manufacturer-specific legal target or compliance status.

The observation is regulatory data and the target is adopted law. The aggregation is
project-derived but reproducible and content-addressed. Remaining limitations are the
brand-versus-manufacturer-group boundary, certified tailpipe CO2 rather than lifecycle GHG, and
the absence of directly comparable country-specific targets for the 27 market rows.

## JERA evidence chain

1. [JERA Environmental Data](https://www.jera.co.jp/en/sustainability/data/e) reports FY2024
   domestic-group net generation and generation emissions intensity, with joint ventures included
   proportionately.
2. [SOCOTEC Certification Japan's independent assurance report](https://www.jera.co.jp/static/files/sustainability/pdf/JERA_Independent_Assurance_Report_20250930.pdf)
   confirms 242 billion kWh and 0.520 kgCO2e/kWh on the same stated boundary.
3. The adapter applies transparent unit conversions to 242,000,000 MWh and 520 kgCO2e/MWh. It
   does not recompute intensity from a differently rounded or differently bounded emissions total.
4. Japan's [Seventh Strategic Energy Plan](https://www.meti.go.jp/english/press/2025/0218_001.html)
   provides the FY2040 national renewable and thermal generation ranges. The METI FY2030 review
   response provides a national electricity factor at the point of use.
5. These policy values remain `context_only`: JERA's generator boundary is not the whole national
   system, and sending-end generation is not electricity at the point of use.

The company observation is company-reported but independently assured. The policy context is
official primary evidence. This supports publishing the observations and context, but not a
numeric JERA alignment margin.

## KOEN evidence chain

1. The [KOEN ESG Data Center](https://www.koenergy.kr/kosep/hw/fr/st/sthw41/main.do?menuCd=FN060101)
   reports 2024 generation and Scope 1/2 emissions for headquarters and five Korean plants.
2. The adapter converts only 39,660 GWh to 39,660,000 MWh. It retains KOEN's reported Scope 1
   and Scope 2 totals and does not replace them with sums of the displayed plant rows.
3. The Scope 1 plant rows sum to 30,608,585 tCO2e, 2,000 above the reported total. The Scope 2
   rows sum to 104,021 tCO2e, 269 above the reported total. Both discrepancies are published in
   derivation and source notes.
4. The page does not identify reported generation as gross or net, and no independent assurance
   statement was identified for this web table. A generation emissions intensity is therefore
   not calculated.
5. Korea's [Eleventh Basic Plan for Long-Term Electricity Supply and Demand](https://www.motir.go.kr/kor/article/ATCLc01b2801b/70083/view)
   supplies the adopted national context: 145.9 MtCO2e transition-sector emissions in 2030 and
   carbon-free generation shares of 53.0% in 2030 and 70.7% in 2038.
6. These values remain `context_only`: they describe the national system and are not allocated to
   KOEN. The plan also notes that the post-2030 national emissions pathway had not yet been set.

The company values are primary company reporting, not independent observations. The Korean plan
is official primary policy evidence. That evidence is sufficient to publish reported facts,
source quality, and national context, but not to claim a KOEN intensity or alignment margin.

## MOL evidence chain

1. [MOL Environmental Data](https://www.mol.co.jp/en/sustainability/data/pdf/environmental/data.pdf)
   reports FY2024 energy efficiency operational indicator (EEOI) of 10.95 gCO2e/ton-mile for MOL
   and major ocean-going vessels operated by group subsidiaries in Japan and overseas.
2. [ClassNK's independent assurance statement](https://www.mol.co.jp/en/sustainability/data/pdf/environmental/assurance-statement.pdf)
   confirms the value, lifecycle-GHG boundary, Standard Method, and FY2024 period. Its
   [appendix](https://www.mol.co.jp/en/sustainability/data/pdf/environmental/appendix.pdf) records
   783 applicable vessels and the transport-work denominator.
3. The adapter retains the source's `ton-mile` unit and current FY2024 observation. It does not
   convert the result to tonne-nautical-mile, reconstruct a trend, or attribute the fleet average
   to an individual customer.
4. The [2023 IMO GHG Strategy](https://www.imo.org/en/ourwork/environment/pages/2023-imo-strategy-on-reduction-of-ghg-emissions-from-ships.aspx)
   supplies 2030 ambitions for carbon intensity, absolute GHG, and zero/near-zero-GHG energy.
5. All three remain `context_only`: the carbon-intensity ambition is an international-shipping
   average CO2 measure against 2008, whereas MOL reports company-fleet lifecycle GHG under a
   Standard Method anchored to FY2019. The other IMO ambitions use different numerators.

MOL's observation is company-reported and independently assured, and the IMO strategy is official
primary evidence. This supports a traceable operating-efficiency snapshot and policy context, but
not a numeric MOL-to-IMO gap or compliance verdict.

## Excluded conflicting or incomplete values

- JERA's current environmental webpage displays a Scope 1 value that differs from the assurance
  appendix and is not marked as externally assured. The public adapter does not publish it.
- A JERA Integrated Report 2025 generation graphic contains a total that does not reconcile with
  its displayed fuel components and the financial table. The public adapter does not publish that
  total or infer a fuel mix from the graphic.
- JERA does not disclose renewable generation MWh on the same assured domestic-group boundary.
  The platform therefore leaves company renewable and thermal shares unavailable.
- KOEN's displayed 2024 Scope 1 and Scope 2 plant rows do not reconcile to the reported totals.
  The platform retains the reported totals, exposes the differences, and does not silently
  recompute them.
- KOEN does not state whether 39,660 GWh is gross or net generation on the ESG data page. The
  platform therefore leaves generation emissions intensity unavailable even though division is
  mathematically possible.
- MOL states that customer allocation makes the published fleet EEOI unsuitable for calculating
  a particular customer's GHG emissions. The platform preserves that caveat and publishes no
  customer-level attribution.
- MOL's current EEOI and IMO's carbon-intensity ambition do not share a baseline year, emissions
  boundary, or aggregation population. The platform therefore does not manufacture a target
  level from the percentage ambition or substitute headquarters/flag-state policy for voyage and
  international-shipping jurisdiction.
- Country pathway rates in `countries.json` remain sector context; they are not silently converted
  into company activity targets.
- The Japanese policy URLs and extracted values are recorded and the adapter snapshot is
  content-addressed, but the source servers block unattended PDF downloads. The raw policy PDFs
  are therefore not vendored or byte-hashed; they need a fresh document review when the policy
  source changes.

## Calculation and publication controls

- Direct arithmetic requires matching sector, metric definition, applicable geography, and unit.
- Contextual values and ranges never enter the alignment-margin function.
- Every company metric carries source IDs, derivation, evidence class, scope, and mapped/reported
  activity coverage.
- Source snapshots, adapters, engine files, workbook, and the complete published dataset are
  content-addressed in `meta.json`.
- The dataset build rejects missing sources, non-HTTPS source links, unregistered company metrics,
  unit mismatches, invalid coverage, partial or inverted contextual ranges, and invalid target
  relations.
- Web and MCP clients read the same published JSON and use the same Python query/comparison service.

## Remaining verification backlog

1. The second power company and geography gate is now met by JERA/Japan and KOEN/Korea, but the
   power method is not yet `supported`: neither pilot has a directly comparable company-policy
   benchmark, and KOEN lacks a verified generation denominator.
2. Obtain plant- or technology-level generation on a consistent company boundary to reveal
   portfolio composition instead of relying on a company average.
3. Source a generator-boundary policy target or an exact policy-defined clean-generation measure
   before calculating a JERA or KOEN target distance.
4. Add a second shipping company and reproducible voyage- or route-level transport work before
   promoting shipping beyond `pilot`; retain IMO context as non-arithmetic until a like-for-like
   company metric and baseline are available.
5. Extend the same acceptance gates to steel and petrochemicals; do not reuse automotive, power,
   or shipping denominators across sectors.
