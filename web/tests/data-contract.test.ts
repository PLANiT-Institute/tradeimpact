import assert from "node:assert/strict";
import test from "node:test";
import { getCountryViews } from "../lib/country";
import {
  COHORT_KEYS,
  DATA_QUALITY_KEYS,
  FIRM_RESULT_KEYS,
  getCalculatorFirm,
  getContract,
  getCountries,
  getFirmResult,
  getFirms,
  getMeta,
  SCENARIOS,
} from "../lib/data";

test("published contract.json matches the TypeScript data contract", () => {
  // contract.json is generated from the Python emitter (to_json_dict); the *_KEYS
  // arrays are compile-time-bound to the TS interfaces. This is the single test
  // that fails when either side renames a field.
  const contract = getContract();
  assert.deepEqual(contract.firm_result, [...FIRM_RESULT_KEYS]);
  assert.deepEqual(contract.cohort, [...COHORT_KEYS]);
  assert.deepEqual(contract.data_quality, [...DATA_QUALITY_KEYS]);
});

test("country views use the canonical contract and exclude illustrative firms", () => {
  const views = getCountryViews();
  assert.ok(views.length > 0);
  assert.ok(views.every((view) => view.firms.every((firm) => firm.slug !== "referenceco")));

  const kr = views.find((view) => view.code === "KR");
  assert.ok(kr);
  assert.match(kr.source ?? "", /UNFCCC KR/);
  assert.ok(kr.warnings.some((warning) => warning.includes("PRORATA_IDENTITY")));
});

test("country rows preserve scenario-level directional suppression", () => {
  // The country regrouping must carry each scenario's directional_only flag
  // through unchanged from the firm report it came from.
  const rows = getCountryViews().flatMap((view) => view.firms);
  assert.ok(rows.length > 0);
  for (const row of rows) {
    const report = getFirmResult(row.slug);
    for (const scenario of SCENARIOS) {
      if (report.cohorts[scenario]) {
        assert.equal(row.directionalOnly[scenario], report.cohorts[scenario].directional_only);
      }
    }
  }
});

test("published provenance is content-addressed and coverage is explicit", () => {
  const meta = getMeta();
  assert.match(meta.engine_source_sha256, /^[a-f0-9]{64}$/);
  assert.match(meta.dataset_sha256, /^[a-f0-9]{64}$/);
  assert.equal("build_date" in meta, false);
  assert.equal("engine_git_sha" in meta, false);

  const covered = getFirms().filter((firm) => firm.coverage_ratio !== undefined);
  assert.ok(covered.length > 0);
  for (const firm of covered) {
    assert.ok(firm.coverage_ratio! > 0 && firm.coverage_ratio! < 1);
    assert.ok(firm.coverage_source);
    assert.equal(getFirmResult(firm.slug).provenance.dataset_sha256, meta.dataset_sha256);
  }
});

test("effective calculator inputs agree with the published country contract", () => {
  // No frozen engine floats: assert linkage instead — each firm's effective
  // country inputs must equal the canonical countries.json values.
  const countries = new Map(getCountries().map((country) => [country.code, country]));
  const firms = getFirms().filter((firm) => firm.runnable && !firm.illustrative);
  assert.ok(firms.length > 0);
  for (const firm of firms) {
    const inputs = getFirmResult(firm.slug).inputs?.countries as Record<
      string,
      { r_fleet: Record<string, number>; r_power: Record<string, number> }
    >;
    assert.ok(inputs);
    for (const [code, country] of Object.entries(inputs)) {
      const canonical = countries.get(code);
      assert.ok(canonical, `countries.json missing ${code}`);
      assert.deepEqual(country.r_fleet, canonical.r_fleet);
      assert.deepEqual(country.r_power, canonical.r_power);
    }
  }
});

test("support contract is published and covers every country with a vkt", () => {
  const support = getMeta().support_contract;
  assert.ok(support.lifetime_T > 0);
  assert.ok(Object.keys(support.vkt).length > 0);
  for (const country of getCountries()) {
    if (country.vkt != null) {
      assert.equal(support.vkt[country.code], country.vkt);
    }
  }
});

test("calculator defaults to a real assessment but still permits an explicit validation case", () => {
  const fallback = getCalculatorFirm();
  assert.equal(fallback.illustrative, undefined);
  assert.equal(fallback.runnable, true);
  assert.equal(getCalculatorFirm("referenceco").illustrative, true);
});
