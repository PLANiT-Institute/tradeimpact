import assert from "node:assert/strict";
import test from "node:test";
import {
  COHORT_KEYS,
  DATA_QUALITY_KEYS,
  FIRM_RESULT_KEYS,
  getCompanyMetrics,
  getContract,
  getDestinationPathways,
  getImpactReadiness,
  getMeta,
  getProductCohorts,
  getSources,
} from "../lib/data";

test("internal engine result schema remains pinned", () => {
  const contract = getContract();
  assert.deepEqual(contract.firm_result, [...FIRM_RESULT_KEYS]);
  assert.deepEqual(contract.cohort, [...COHORT_KEYS]);
  assert.deepEqual(contract.data_quality, [...DATA_QUALITY_KEYS]);
});

test("Toyota product cohort reconciles by destination, product, and powertrain", () => {
  const cohorts = getProductCohorts();
  assert.equal(cohorts.length, 2);
  const cohort = cohorts.find((row) => row.company_id === "toyota");
  assert.ok(cohort);
  assert.equal(cohort.contract_version, "export-impact-v1");
  assert.equal(cohort.cohort_id, "toyota-eu27-passenger-cars-2024");
  assert.equal(cohort.coverage.reported_units, 803_094);
  assert.equal(cohort.records.length, 660);
  assert.equal(
    cohort.records.reduce((sum, row) => sum + row.units, 0),
    cohort.coverage.reported_units,
  );
  assert.equal(new Set(cohort.records.map((row) => row.destination_geography)).size, 27);
  assert.equal(new Set(cohort.records.map((row) => row.product_name)).size, 72);
  assert.deepEqual(
    [...new Set(cohort.records.map((row) => row.product_type))].sort(),
    ["BEV", "FCEV", "HEV", "ICE_OTHER", "PHEV"],
  );
  assert.equal(cohort.origin_mapping_status, "not_collected");
  assert.match(cohort.origin_mapping_note, /do not.*prove|not.*produced/i);
});

test("Hyundai cohort is comparable on the same EEA boundary", () => {
  const cohort = getProductCohorts().find((row) => row.company_id === "hyundai");
  assert.ok(cohort);
  assert.equal(cohort.cohort_id, "hyundai-eu27-passenger-cars-2024");
  assert.equal(cohort.coverage.reported_units, 429_936);
  assert.equal(cohort.records.length, 626);
  assert.equal(new Set(cohort.records.map((row) => row.destination_geography)).size, 27);
  assert.equal(new Set(cohort.records.map((row) => row.product_name)).size, 67);
  assert.equal(cohort.origin_mapping_status, "not_collected");
  assert.equal(cohort.origin_context?.comparability, "context_only_not_cohort_mapping");
  assert.match(cohort.origin_context?.notes ?? "", /does not map individual registrations/i);
});

test("zero-tailpipe classification stays distinct from lifetime GHG", () => {
  const cohort = getProductCohorts()[0];
  const byType = Object.fromEntries(
    ["BEV", "FCEV", "PHEV", "HEV", "ICE_OTHER"].map((type) => [
      type,
      cohort.records
        .filter((row) => row.product_type === type)
        .reduce((sum, row) => sum + row.units, 0),
    ]),
  );
  assert.equal(byType.BEV, 10_882);
  assert.equal(byType.FCEV, 690);
  assert.equal(byType.PHEV, 23_911);
  assert.equal(byType.HEV, 610_881);
  assert.equal(byType.ICE_OTHER, 156_730);
  assert.equal(byType.BEV + byType.FCEV, 11_572);

  const bev = cohort.records.find(
    (row) => row.product_type === "BEV" && row.certified_electricity_kwh_per_km != null,
  );
  assert.ok(bev);
  assert.equal(bev.destination_inventory_sector, "power");
  const hev = cohort.records.find((row) => row.product_type === "HEV");
  assert.ok(hev);
  assert.equal(hev.destination_inventory_sector, "road_transport");
});

test("arbitrary fixed-distance load is absent", () => {
  const serialized = JSON.stringify({
    metrics: getCompanyMetrics(),
    cohorts: getProductCohorts(),
  });
  assert.ok(!serialized.includes("normalized_tailpipe_co2_load"));
  assert.ok(!serialized.includes("cohort-1000km"));
});

test("destination pathways preserve proxy hierarchy", () => {
  const pathways = getDestinationPathways();
  assert.equal(pathways.length, 2);
  const sector = pathways.find((row) => row.comparison_role === "sector_proxy");
  const ndc = pathways.find((row) => row.comparison_role === "fallback_context");
  assert.ok(sector);
  assert.ok(ndc);
  assert.equal(sector.policy_level, "regional_sector_pathway");
  assert.equal(sector.calculation_status, "proxy_requires_disclosure");
  assert.ok(Math.abs((sector.annual_reduction_rate ?? 0) - 0.04344369190911768) < 1e-12);
  assert.equal(ndc.policy_level, "ndc");
  assert.equal(ndc.reduction_min, 0.6625);
  assert.equal(ndc.reduction_max, 0.725);
  assert.equal(ndc.calculation_status, "not_directly_usable");
});

test("readiness gate blocks unsourced lifetime results", () => {
  const readiness = getImpactReadiness()[0];
  assert.equal(readiness.status, "inputs_incomplete");
  assert.equal(readiness.publication_decision, "withhold_lifetime_ti");
  assert.equal(readiness.missing_required_inputs.length, 9);
  assert.match(readiness.publication_reason, /unsourced assumptions/i);

  const meta = getMeta();
  assert.equal(meta.impact_contract.version, "export-impact-v1");
  assert.equal(meta.impact_contract.product_cohorts, 2);
  assert.equal(meta.impact_contract.cohort_records, 1_286);
  assert.equal(meta.impact_contract.published_lifetime_results, 0);
  assert.match(meta.engine_source_sha256, /^[a-f0-9]{64}$/);
  assert.match(meta.dataset_sha256, /^[a-f0-9]{64}$/);
});

test("cohort and pathway records cite published sources", () => {
  const sourceIds = new Set(getSources().map((source) => source.source_id));
  for (const cohort of getProductCohorts()) {
    for (const sourceId of cohort.source_ids) assert.ok(sourceIds.has(sourceId));
    for (const sourceId of cohort.origin_context?.source_ids ?? []) {
      assert.ok(sourceIds.has(sourceId));
    }
    for (const row of cohort.records) {
      assert.ok(row.source_ids.length > 0);
      for (const sourceId of row.source_ids) assert.ok(sourceIds.has(sourceId));
    }
  }
  for (const pathway of getDestinationPathways()) {
    assert.ok(pathway.source_ids.length > 0);
    for (const sourceId of pathway.source_ids) assert.ok(sourceIds.has(sourceId));
  }
});
