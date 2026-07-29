import assert from "node:assert/strict";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ScenarioCards from "../components/ScenarioCards";
import { impactDirectionWord } from "../lib/shared";

test("directional-only scenarios never render their numeric value", () => {
  const html = renderToStaticMarkup(
    <ScenarioCards
      totals={{ S1: 1234567, S2: -250 }}
      directionalOnly={{ S1: true }}
      unit="tCO2e"
    />,
  );
  assert.match(html, />Below pathway</);
  assert.doesNotMatch(html, /1,234,567/);
  assert.match(html, />250 tCO2e</);
  assert.match(html, /NDC lock-in/);
});

test("zero is rendered as NDC aligned, not a contribution", () => {
  const html = renderToStaticMarkup(<ScenarioCards totals={{ S2: 0 }} unit="tCO2e" />);
  assert.match(html, /NDC aligned/);
  assert.doesNotMatch(html, /NDC contribution/);
  assert.equal(impactDirectionWord("neutral"), "aligned");
});
