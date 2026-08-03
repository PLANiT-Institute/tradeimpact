import assert from "node:assert/strict";
import test from "node:test";
import { getCountryViews } from "../lib/country";
import {
  COHORT_KEYS,
  DATA_QUALITY_KEYS,
  FIRM_RESULT_KEYS,
  getContract,
  getBenchmarks,
  getCompanyMetrics,
  getCountries,
  getFirms,
  getMeta,
  getSectors,
  getSources,
} from "../lib/data";

test("published contract.json matches the TypeScript data contract", () => {
  const contract = getContract();
  assert.deepEqual(contract.firm_result, [...FIRM_RESULT_KEYS]);
  assert.deepEqual(contract.cohort, [...COHORT_KEYS]);
  assert.deepEqual(contract.data_quality, [...DATA_QUALITY_KEYS]);
  assert.ok(!contract.firm_result.includes("by_year"));
});

test("all source-backed countries remain visible without company reports", () => {
  const views = getCountryViews();
  assert.equal(views.length, 11);
  assert.ok(views.every((view) => view.firms.length === 0));

  const kr = views.find((view) => view.code === "KR");
  assert.ok(kr);
  assert.match(kr.source ?? "", /UNFCCC.*KR/);
  assert.ok(!kr.warnings.some((warning) => warning.includes("PRORATA_IDENTITY")));

  const au = views.find((view) => view.code === "AU");
  assert.ok(au);
  assert.ok(au.warnings.some((warning) => warning.includes("PRORATA_IDENTITY")));
});

test("vehicle-fleet estimates are absent from the public country contract", () => {
  for (const country of getCountries()) {
    assert.equal("fleet_intensity_base" in country, false);
    assert.equal("vkt" in country, false);
  }
});

test("Toyota, JERA, KOEN, and MOL share one sector-neutral evidence contract", () => {
  const sectors = getSectors();
  const metrics = getCompanyMetrics();
  const benchmarks = getBenchmarks();
  const sources = getSources();

  assert.deepEqual(
    sectors.map((sector) => sector.sector_id),
    ["automotive", "power", "shipping", "steel", "petrochemicals"],
  );
  assert.equal(metrics.length, 202);
  assert.equal(benchmarks.length, 11);
  assert.equal(sources.length, 13);

  const euIntensity = metrics.find(
    (metric) =>
      metric.company_id === "toyota" &&
      metric.geography === "EU27" &&
      metric.metric_id === "new_vehicle_tailpipe_intensity",
  );
  assert.ok(euIntensity);
  assert.ok(Math.abs(euIntensity.value - 107.07329255505938) < 1e-12);
  assert.equal(euIntensity.coverage.mapped_activity, 803_042);
  assert.equal(euIntensity.coverage.reported_activity, 803_094);
  const direct = benchmarks.filter((row) => row.comparison_mode === "direct");
  const contextual = benchmarks.filter((row) => row.comparison_mode === "contextual");
  assert.deepEqual(direct.map((row) => row.target_year), [2025, 2030]);
  assert.equal(contextual.length, 9);
  assert.ok(contextual.every((row) => row.relation === "context_only"));

  const jeraIntensity = metrics.find(
    (metric) =>
      metric.company_id === "jera" &&
      metric.geography === "JP" &&
      metric.metric_id === "generation_emissions_intensity",
  );
  assert.ok(jeraIntensity);
  assert.equal(jeraIntensity.value, 520);
  assert.equal(jeraIntensity.coverage.reported_activity, 242_000_000);

  const koenMetrics = metrics.filter((metric) => metric.company_id === "koen");
  assert.deepEqual(
    koenMetrics.map((metric) => metric.metric_id).sort(),
    ["reported_generation", "scope1_emissions", "scope2_emissions"],
  );
  assert.ok(!koenMetrics.some((metric) => metric.metric_id === "generation_emissions_intensity"));

  const automotiveSerialized = JSON.stringify(
    metrics.filter((metric) => metric.sector === "automotive"),
  ).toLowerCase();
  assert.ok(!automotiveSerialized.includes("lifetime"));
  assert.ok(!automotiveSerialized.includes("vkt"));
  assert.ok(!automotiveSerialized.includes("tco2"));
  assert.deepEqual(
    koenMetrics.filter((metric) => metric.metric_id.endsWith("_emissions")).map((metric) => metric.unit),
    ["tCO2e", "tCO2e"],
  );

  const molEeoi = metrics.find(
    (metric) => metric.company_id === "mitsui" && metric.metric_id === "shipping_eeoi",
  );
  assert.ok(molEeoi);
  assert.equal(molEeoi.value, 10.95);
  assert.equal(molEeoi.unit, "gCO2e/ton-mile");
  assert.equal(molEeoi.coverage.reported_activity, 783);
});

test("no company assessment is runnable until the evidence gate is met", () => {
  const firms = getFirms();
  assert.ok(firms.length > 0);
  assert.ok(firms.every((firm) => !firm.runnable));
  assert.ok(firms.every((firm) => !firm.illustrative));
  const toyota = firms.find((item) => item.slug === "toyota");
  assert.ok(toyota);
  assert.equal(toyota.alignment_available, true);
  assert.match(toyota.note ?? "", /alignment snapshot available.*legacy lifetime/s);

  const hyundai = firms.find((item) => item.slug === "hyundai");
  assert.ok(hyundai);
  assert.equal(hyundai.alignment_available, false);
  assert.match(hyundai.note ?? "", /Estimated vehicle mix.*removed/);

  const jera = firms.find((item) => item.slug === "jera");
  assert.ok(jera);
  assert.equal(jera.alignment_available, true);
  assert.match(jera.note ?? "", /context only.*boundaries do not match/s);

  const koen = firms.find((item) => item.slug === "koen");
  assert.ok(koen);
  assert.equal(koen.alignment_available, true);
  assert.match(koen.note ?? "", /plant-total reconciliation.*prevent/s);

  const mol = firms.find((item) => item.slug === "mitsui");
  assert.ok(mol);
  assert.equal(mol.name, "Mitsui O.S.K. Lines (MOL)");
  assert.equal(mol.alignment_available, true);
  assert.match(mol.note ?? "", /IMO 2030 ambitions are context only/s);
});

test("published provenance is content-addressed and unsourced support stays null", () => {
  const meta = getMeta();
  assert.match(meta.engine_source_sha256, /^[a-f0-9]{64}$/);
  assert.match(meta.dataset_sha256, /^[a-f0-9]{64}$/);
  assert.equal(meta.alignment_contract.company_metrics, 202);
  assert.equal(meta.alignment_contract.direct_benchmarks, 2);
  assert.equal(meta.alignment_contract.contextual_benchmarks, 9);
  assert.equal(Object.keys(meta.alignment_inputs_sha256).length, 8);
  assert.equal("build_date" in meta, false);
  assert.equal("engine_git_sha" in meta, false);
  assert.equal(meta.support_contract.lifetime_T, null);
  assert.equal(meta.support_contract.lifetime_sens, null);
  assert.equal(meta.support_contract.uf_band, null);
  assert.equal(meta.support_contract.realworld_range, null);
  assert.deepEqual(meta.support_contract.vkt, {});
  assert.ok(
    meta.collection_status.missing_inputs.includes("Registration_Vcv: no volume units collected"),
  );
});
