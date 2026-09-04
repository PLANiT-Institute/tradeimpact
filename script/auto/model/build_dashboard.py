"""Write the HTML dashboard that reads the automotive SQLite database at view time.

The page carries no data. It writes ``data/auto/database/dashboard.html``, which loads sql.js
(WebAssembly, from a version-pinned CDN with subresource integrity), fetches the sibling file
``tradeimpact_auto.sqlite`` relative to itself and reads everything else — the ``tables``
manifest, the ``columns`` dictionary, the source registry and the raw-file provenance — out of
that database with SQL once it is open. Six views: lineage, results, results by year, pivot,
browse and free-text read-only SQL.

The relative fetch needs the directory to be served over HTTP:

    .venv/bin/python script/auto/serve_dashboard.py   ->  http://127.0.0.1:8765/database/dashboard.html

Opened from ``file://`` the browser refuses to read the sibling file, so the page then shows an
"Open the database" panel with a file picker and a drag-and-drop zone instead.

The only data embedded in the page are constants: the sql.js URL and hash, the two pivot
presets, the pipeline stage order, the dataset order and the model step list. The build is
therefore deterministic and independent of the database contents; it only checks that the
database exists and carries a ``tables`` manifest. Stdlib only.

Run from the repository root:  .venv/bin/python script/auto/model/build_dashboard.py
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DB = REPO / "data" / "auto" / "database" / "tradeimpact_auto.sqlite"
OUT = REPO / "data" / "auto" / "database" / "dashboard.html"

#: How the page tells the reader to serve its own directory; matches serve_dashboard.py.
SERVE_PORT = 8765
SERVE_CMD = ".venv/bin/python script/auto/serve_dashboard.py"
SERVE_URL = f"then open http://127.0.0.1:{SERVE_PORT}/{OUT.parent.name}/{OUT.name}"
#: Where a page opened from disk looks for a running server before offering the reader.
SERVED_DB = f"http://127.0.0.1:{SERVE_PORT}/{OUT.parent.name}/{DB.name}"

#: sql.js pinned on cdnjs; ``locateFile`` resolves sql-wasm.wasm inside the same directory.
SQLJS_VERSION = "1.10.3"
SQLJS_DIR = f"https://cdnjs.cloudflare.com/ajax/libs/sql.js/{SQLJS_VERSION}/"
D3_SRC = "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"
D3_SRI = "sha384-CjloA8y00+1SDAUkjs099PVfnY2KmDC2BZnws9kh8D/lX1s46w6EPhpXdqMfjK6i"
TOPOJSON_SRC = "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"
TOPOJSON_SRI = "sha384-9dCJK6nh7skY14HrcvlLYlFga9/MehJjL9ONWRflmiXNRuf8p2jiF4Y5PR881PTq"
SQLJS_SRI = (
    "sha512-+6Q7hv5pGUBXOuHWw8OdQx3ac7DzM3oJhYqz7SHDku0yl9EBd"
    "MqegoPed4GsHRoNF/VQYK2LTYewAIEBrEf/3w=="
)

#: Pipeline stage order; ``registry`` is the provenance pair and sits outside the flow.
STAGES = ("raw", "method", "processed", "output")

#: Dataset (data type) display order in the lineage view.
DATASET_ORDER = (
    "sales",
    "vehicle_technology",
    "vehicle_usage",
    "country_emissions",
    "emission_targets",
    "model",
    "auto",
)

#: Model step order (whitepaper steps 3, 4, 4b, 5), matched on output table-name prefixes.
MODEL_STEPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("3a cohorts", ("cohorts",)),
    ("3 reference", ("destination_parameters", "reference_trajectories")),
    (
        "4 impact",
        ("ti_by_model", "ti_annual_by_model", "ti_annual", "ti_withheld", "ti_exclusions"),
    ),
    ("4b crossover and sensitivity", ("ti_crossover", "ti_sensitivity")),
    (
        "5 aggregates and data quality",
        (
            "ti_country",
            "ti_powertrain",
            "ti_company",
            "ti_data",
            "ti_coverage",
            "ti_source",
        ),
    ),
)

#: The pivot the "Results" navigation entry lands on: results by vehicle model and powertrain
#: (the company roll-up is one click away in the same pivot by removing the row fields).
DEFAULT_PIVOT = {
    "agg": "sum",
    "cols": "scenario",
    "rows": ["market", "company", "powertrain", "model"],
    "table": "ti_by_model",
    "vals": ["ti_tco2e"],
}

#: The pivot the "Results by year" navigation entry lands on: the same cells, one column per
#: calendar year of the operating life (filter on scenario to read one pathway at a time).
YEARLY_PIVOT = {
    "agg": "sum",
    "cols": "calendar_year",
    "rows": ["market", "company", "powertrain", "model"],
    "table": "ti_annual_by_model",
    "vals": ["ti_tco2e"],
    "filters": [["scenario", "=", "S1"]],
}


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trade Impact - automotive database</title>
<link rel="icon" href="data:,">
<style>
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --panel: #f4f6f8;
  --panel2: #e9edf2;
  --border: #d3d9e0;
  --text: #131820;
  --muted: #5b6673;
  --accent: #10459b;
  --accent-bg: #e5edfa;
  --neg: #a3162f;
  --raw-fg: #7a4a00; --raw-bg: #fbeed7; --raw-br: #dfb877;
  --method-fg: #513a9c; --method-bg: #ebe6fa; --method-br: #b3a4e6;
  --processed-fg: #0c6147; --processed-bg: #d9efe6; --processed-br: #79c3aa;
  --output-fg: #8d1f3c; --output-bg: #fbe0e7; --output-br: #de95aa;
  --registry-fg: #414e5d; --registry-bg: #e6eaee; --registry-br: #a8b2be;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --r: 4px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #12161c;
    --panel: #1a2028;
    --panel2: #222a34;
    --border: #333d4a;
    --text: #e4e9ef;
    --muted: #97a3b2;
    --accent: #7fb0ff;
    --accent-bg: #1c2b45;
    --neg: #ff8b9c;
    --raw-fg: #e8bf7c; --raw-bg: #35291356; --raw-br: #6b5222;
    --method-fg: #bda9f5; --method-bg: #26204056; --method-br: #4c3f7d;
    --processed-fg: #6fd0b0; --processed-bg: #10322956; --processed-br: #2c6b58;
    --output-fg: #f095ab; --output-bg: #3a1c2556; --output-br: #7a3348;
    --registry-fg: #b3bdc9; --registry-bg: #23292f56; --registry-br: #4a5561;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  font-size: 14px;
  line-height: 1.45;
}
a { color: var(--accent); }
h1, h2, h3 { margin: 0 0 6px; line-height: 1.25; }
h1 { font-size: 15px; font-weight: 650; }
h2 { font-size: 13px; font-weight: 650; }
h3 { font-size: 11px; font-weight: 650; text-transform: uppercase; letter-spacing: .06em; }
p { margin: 0 0 8px; }
.mono { font-family: var(--mono); }
.muted { color: var(--muted); }
.topbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  align-items: baseline;
  justify-content: space-between;
  padding: 8px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
}
.topbar .sub { color: var(--muted); font-weight: 400; }
.status { font-size: 12px; color: var(--muted); font-family: var(--mono); }
.status.bad { color: var(--neg); }
.shell {
  display: grid;
  grid-template-columns: 208px minmax(0, 1fr);
  gap: 14px;
  padding: 12px 14px 40px;
  align-items: start;
}
.side { position: sticky; top: 10px; display: flex; flex-direction: column; gap: 14px; }
.navgroup { display: flex; flex-direction: column; gap: 4px; }
.navlink {
  text-align: left;
  font: inherit;
  font-size: 13px;
  padding: 5px 9px;
  border: 1px solid transparent;
  border-radius: var(--r);
  background: none;
  color: var(--text);
  cursor: pointer;
}
.navlink:hover { background: var(--panel); }
.navlink[aria-current="page"] {
  background: var(--accent-bg);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.legend { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px; }
.dl { margin: 0; font-size: 12px; color: var(--muted); }
.dl div { display: flex; justify-content: space-between; gap: 8px; }
.dl dt { color: var(--muted); }
.dl dd { margin: 0; font-family: var(--mono); }
.card {
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--panel);
  padding: 10px 12px;
  margin: 0 0 12px;
}
.thead {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 12px;
  padding: 6px 10px;
  margin: 0 0 12px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--panel2);
  font-size: 12px;
}
.thead strong { font-family: var(--mono); font-size: 13px; }
.thead .meta { color: var(--muted); }
.chip {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 5px;
  max-width: 100%;
  min-width: 0;
  overflow-wrap: anywhere;
  text-align: left;
  font: inherit;
  font-size: 12px;
  font-family: var(--mono);
  padding: 2px 7px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--panel2);
  color: var(--text);
  cursor: default;
}
button.chip { cursor: pointer; }
button.chip:hover { border-color: var(--accent); }
.chip .n { color: inherit; opacity: .7; font-size: 11px; }
.chip-raw { background: var(--raw-bg); color: var(--raw-fg); border-color: var(--raw-br); }
.chip-method {
  background: var(--method-bg);
  color: var(--method-fg);
  border-color: var(--method-br);
}
.chip-processed {
  background: var(--processed-bg);
  color: var(--processed-fg);
  border-color: var(--processed-br);
}
.chip-output {
  background: var(--output-bg);
  color: var(--output-fg);
  border-color: var(--output-br);
}
.chip-registry {
  background: var(--registry-bg);
  color: var(--registry-fg);
  border-color: var(--registry-br);
}
.flow { display: flex; flex-wrap: wrap; gap: 6px; align-items: stretch; margin: 6px 0 10px; }
.stage {
  flex: 1 1 168px;
  min-width: 150px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--bg);
  padding: 6px 8px;
}
.stage h3 { color: var(--muted); }
.stage-raw h3 { color: var(--raw-fg); }
.stage-method h3 { color: var(--method-fg); }
.stage-processed h3 { color: var(--processed-fg); }
.stage-output h3 { color: var(--output-fg); }
.stage .chips { display: flex; flex-wrap: wrap; gap: 4px; }
.arrow { align-self: center; color: var(--muted); font-size: 15px; }
.scroll {
  overflow: auto;
  max-height: 64vh;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--bg);
}
.scroll.sm { max-height: 210px; margin-bottom: 8px; }
.scroll.wide { max-height: 330px; overflow-x: hidden; }
table.data { border-collapse: separate; border-spacing: 0; font-size: 12.5px; width: max-content; }
table.data th, table.data td {
  padding: 3px 9px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  white-space: nowrap;
  vertical-align: top;
}
table.data thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--panel2);
  border-bottom: 1px solid var(--border);
  font-weight: 650;
}
table.data thead tr:nth-child(2) th { top: 25px; }
table.data tbody tr:hover td { background: var(--panel); }
table.data td.num, table.data th.num { text-align: right; font-family: var(--mono); }
table.data td.neg { color: var(--neg); }
table.data tr.total td, table.data tr.total th {
  background: var(--panel2);
  font-weight: 650;
  border-top: 2px solid var(--border);
}
table.data td.dim, table.data th.dim { font-family: var(--mono); }
table.data th.total, table.data td.total { border-left: 2px solid var(--border); }
th.sortable { cursor: pointer; }
th.sortable:hover { color: var(--accent); }
th .dir { color: var(--accent); }
.pickers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(168px, 1fr));
  gap: 10px;
  margin: 8px 0;
}
.picker { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.picker label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--muted);
}
select, input[type="text"], textarea, button {
  font: inherit;
  font-size: 13px;
  color: var(--text);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 4px 6px;
  max-width: 100%;
}
select[multiple] { font-family: var(--mono); font-size: 12px; padding: 2px; }
textarea { font-family: var(--mono); width: 100%; min-height: 96px; resize: vertical; }
button { cursor: pointer; background: var(--panel2); }
button:hover { border-color: var(--accent); }
button.primary { background: var(--accent-bg); border-color: var(--accent); color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0; }
.filterrow { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 5px; }
.sqlbox {
  font-family: var(--mono);
  font-size: 12px;
  white-space: pre;
  overflow-x: auto;
  padding: 7px 9px;
  margin: 0;
  border: 1px solid var(--border);
  border-radius: var(--r);
  background: var(--panel2);
  color: var(--text);
}
.err {
  padding: 8px 10px;
  border: 1px solid var(--neg);
  border-radius: var(--r);
  color: var(--neg);
  background: var(--bg);
  font-size: 13px;
}
.note { font-size: 12px; color: var(--muted); margin-top: 6px; }
.empty { padding: 14px; color: var(--muted); }
.opener { max-width: 720px; }
.opener .sqlbox { white-space: pre-wrap; overflow-wrap: anywhere; }
.drop {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 16px 14px;
  margin-top: 8px;
  border: 2px dashed var(--border);
  border-radius: var(--r);
  background: var(--bg);
}
.drop.over { border-color: var(--accent); background: var(--accent-bg); }
.drop label { font-size: 12px; color: var(--muted); }
table.srctable { font-size: 12px; width: 100%; table-layout: fixed; }
table.srctable th, table.srctable td { white-space: normal; overflow-wrap: anywhere; }
table.srctable th:nth-child(1), table.srctable td:nth-child(1) { width: 15%; }
table.srctable th:nth-child(2), table.srctable td:nth-child(2) { width: 14%; }
table.srctable th:nth-child(3), table.srctable td:nth-child(3) { width: 23%; }
table.srctable th:nth-child(4), table.srctable td:nth-child(4) { width: 17%; }
table.srctable th:nth-child(5), table.srctable td:nth-child(5) { width: 10%; }
table.srctable th:nth-child(6), table.srctable td:nth-child(6) { width: 8%; }
table.srctable th:nth-child(7), table.srctable td:nth-child(7) { width: 13%; }
.wrapcell { white-space: normal; max-width: 420px; }
@media (max-width: 900px) {
  .shell { grid-template-columns: minmax(0, 1fr); }
  .side { position: static; }
  .navgroup { flex-direction: row; flex-wrap: wrap; }
}
.map .ctl { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: end; margin-bottom: 10px; }
.map .ctl label { display: flex; flex-direction: column; gap: 2px; font-size: 12px; color:
var(--muted); }
.map svg { width: 100%; height: auto; display: block; background: var(--panel); border-radius:
8px; }
.map path.country { stroke: var(--bg); stroke-width: 0.4; cursor: pointer; }
.map path.country.selected { stroke: var(--text); stroke-width: 1.2; }
.map .legend { display: flex; flex-wrap: wrap; gap: 6px 12px; font-size: 12px; margin: 8px 0;
align-items: center; }
.map .swatch { display: inline-block; width: 14px; height: 14px; border-radius: 3px;
vertical-align: -2px; margin-right: 4px; }
.map .tip {
  position: fixed; pointer-events: none; z-index: 5; display: none;
  background: var(--bg); color: var(--text); border: 1px solid var(--border);
  padding: 6px 8px; border-radius: 6px; font-size: 12px; max-width: 320px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}
.tier { display: inline-block; padding: 0 6px; border-radius: 10px; font-size: 11px;
font-weight: 600; }
.tier-A { background: #cfe8d6; color: #14532d; }
.tier-B { background: #fde7b6; color: #7c4a03; }
.tier-C { background: #f8cfcf; color: #7f1d1d; }
</style>
</head>
<body>
<header class="topbar">
  <h1>Trade Impact <span class="sub">automotive database</span></h1>
  <div class="status" id="status">starting</div>
</header>
<div class="shell">
  <nav class="side" aria-label="Views">
    <div class="navgroup" id="nav"></div>
    <div class="navgroup">
      <h2>Stages</h2>
      <ul class="legend" id="legend"></ul>
    </div>
    <div class="navgroup">
      <h2>Database</h2>
      <dl class="dl" id="dbmeta"></dl>
    </div>
  </nav>
  <main id="main" tabindex="-1"></main>
</div>
<script
  src="__SQLJS_SRC__"
  integrity="__SQLJS_SRI__"
  crossorigin="anonymous"
  referrerpolicy="no-referrer"
  onerror="window.__sqljsFailed = true;"></script>
<script src="__D3_SRC__" integrity="__D3_SRI__" crossorigin="anonymous"
  referrerpolicy="no-referrer" onerror="window.__d3Failed = true;"></script>
<script src="__TOPOJSON_SRC__" integrity="__TOPOJSON_SRI__" crossorigin="anonymous"
  referrerpolicy="no-referrer" onerror="window.__d3Failed = true;"></script>
<script>
(function () {
'use strict';

/* Constants written by the builder; every other value on this page is read from the
   database at view time. */
const CDN_DIR = '__SQLJS_DIR__';
const SQLJS_VERSION = '__SQLJS_VERSION__';
const DB_FILE = '__DB_FILE__';
const SERVE_CMD = '__SERVE_CMD__';
const SERVE_PORT = __SERVE_PORT__;
const SERVE_URL = '__SERVE_URL__';
const SERVED_DB = '__SERVED_DB__';
const DEFAULT_PIVOT = __DEFAULT_PIVOT__;
const YEARLY_PIVOT = __YEARLY_PIVOT__;
const STAGES = __STAGES__;
const DATASET_ORDER = __DATASET_ORDER__;
const MODEL_STEPS = __MODEL_STEPS__;

const SEP = String.fromCharCode(1);
/* Views that render the pivot: the two presets keep their own address and their own place in
   the navigation, so clicking one lands there rather than on Pivot. */
const PIVOT_VIEWS = {pivot: 1, results: 1, results_year: 1};
const PRESET_VIEWS = {results: 'DEFAULT', results_year: 'YEARLY'};

const VIEWS = [
  {id: 'lineage', label: 'Lineage'},
  {id: 'results', label: 'Results'},
  {id: 'results_year', label: 'Results by year'},
  {id: 'map', label: 'Map'},
  {id: 'pivot', label: 'Pivot'},
  {id: 'browse', label: 'Browse'},
  {id: 'sql', label: 'SQL'}
];
const AGGS = ['sum', 'mean', 'min', 'max', 'count'];
const AGG_SQL = {sum: 'SUM', mean: 'AVG', min: 'MIN', max: 'MAX', count: 'COUNT'};
const OPS = ['=', '!=', '<', '<=', '>', '>=', 'contains', 'starts with', 'is null', 'is not null'];
const NO_VALUE_OPS = {'is null': 1, 'is not null': 1};
const PAGE = 100;
const BLOCKED = /\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum)\b/i;

let SQL = null;
let DB = null;
let dbError = null;
let ready = false;
let shellKey = '';
let debounce = null;
let TBL = new Map();

/* Everything the chrome needs, read out of the database once it is open. */
const meta = {file: '', bytes: 0, tables: [], columns: {}, sources: [], datasets: []};

/* ---------- shared helpers ---------- */

const ESCAPES = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'};

function esc(v) {
  if (v === null || v === undefined) return '';
  return String(v).replace(/[&<>"']/g, (c) => ESCAPES[c]);
}

const NF = new Intl.NumberFormat('en-US', {maximumFractionDigits: 4});
const NF0 = new Intl.NumberFormat('en-US', {maximumFractionDigits: 0});

function fmtNum(v) {
  if (v === null || v === undefined) return '';
  return NF.format(v);
}

function fmtInt(v) {
  if (v === null || v === undefined) return '';
  return typeof v === 'number' ? NF0.format(v) : String(v);
}

function fmtCell(v) {
  if (v === null || v === undefined) return '';
  return typeof v === 'number' ? fmtNum(v) : String(v);
}

/* A column whose name mentions a year holds a label, so it keeps no group separator. */
function fmtIn(v, column) {
  if (v === null || v === undefined) return '';
  if (typeof v !== 'number') return String(v);
  return /year/i.test(String(column || '')) ? String(v) : fmtNum(v);
}

function qq(id) {
  return '"' + String(id).replace(/"/g, '""') + '"';
}

function lit(v) {
  return "'" + String(v).replace(/'/g, "''") + "'";
}

function colsOf(table) {
  return meta.columns[table] || [];
}

function isNumeric(table, column) {
  const c = colsOf(table).filter((x) => x.column === column)[0];
  return !!c && (c.sqlite_type === 'INTEGER' || c.sqlite_type === 'REAL');
}

function presetFor(table) {
  return [DEFAULT_PIVOT, YEARLY_PIVOT].find((d) => d && d.table === table) || null;
}

function defaultPivot(table) {
  const d = presetFor(table);
  if (d) {
    const filters = (d.filters || []).map((f) => ({col: f[0], op: f[1], val: String(f[2])}));
    return {rows: d.rows.slice(), cols: d.cols, vals: d.vals.slice(), agg: d.agg,
      filters: filters, sort: null};
  }
  const cs = colsOf(table);
  const dims = cs.filter((c) => c.sqlite_type === 'TEXT').map((c) => c.column);
  const nums = cs.filter((c) => c.sqlite_type !== 'TEXT').map((c) => c.column);
  return {rows: dims.slice(0, 1), cols: '', vals: nums.slice(0, 1), agg: 'sum',
    filters: [], sort: null};
}

const state = {
  view: 'lineage',
  table: DEFAULT_PIVOT.table,
  pivot: defaultPivot(DEFAULT_PIVOT.table),
  browse: {page: 0, sort: null, dir: 'asc', q: ''},
  map: {metric: 'coverage_units', company: '', year: '', scenario: 'S1', selected: ''},
  sql: {text: 'SELECT market, company, powertrain, model, scenario,\n'
        + '       SUM(units) AS units, SUM(ti_tco2e) AS ti_tco2e\n'
        + '  FROM ti_by_model\n GROUP BY 1, 2, 3, 4, 5\n ORDER BY 1, 2, 3, 4, 5'},
  tsv: ''
};

function errBox(msg) {
  return '<div class="err">' + esc(msg) + '</div>';
}

function engineBox() {
  return errBox(dbError || 'No database is loaded yet.');
}

function query(sql) {
  if (!DB) throw new Error(dbError || 'SQL engine not ready');
  const r = DB.exec(sql);
  if (!r.length) return {columns: [], values: []};
  return {columns: r[0].columns, values: r[0].values};
}

function opt(value, label, on) {
  return '<option value="' + esc(value) + '"' + (on ? ' selected' : '') + '>' +
    esc(label) + '</option>';
}

function selected(el) {
  return Array.prototype.slice.call(el.selectedOptions).map((o) => o.value);
}

/* ---------- chrome ---------- */

function fmtMB(bytes) {
  return (bytes / 1e6).toFixed(2) + ' MB';
}

/* Pass text to show a transient message; with no argument the line is derived from state. */
function setStatus(text, bad) {
  const el = document.getElementById('status');
  if (text) {
    el.className = 'status' + (bad ? ' bad' : '');
    el.textContent = text;
    return;
  }
  if (!ready) {
    el.className = 'status' + (dbError ? ' bad' : '');
    el.textContent = dbError ? 'no database loaded' : 'waiting for the database';
    return;
  }
  el.className = 'status';
  el.textContent = meta.file + ' - ' + fmtMB(meta.bytes) + ' - ' +
    fmtInt(meta.tables.length) + ' tables - sql.js ' + SQLJS_VERSION;
}

function renderNav() {
  document.getElementById('nav').innerHTML = ready
    ? VIEWS.map((v) => {
      const on = v.id === state.view;
      return '<button class="navlink" data-view="' + v.id + '"' +
        (on ? ' aria-current="page"' : '') + '>' + esc(v.label) + '</button>';
    }).join('')
    : '<p class="muted">The views appear once the database is open.</p>';
}

function renderLegend() {
  document.getElementById('legend').innerHTML = STAGES.concat(['registry'])
    .map((s) => '<li><span class="chip chip-' + s + '">' + esc(s) + '</span></li>')
    .join('');
}

function renderDbMeta() {
  const el = document.getElementById('dbmeta');
  if (!ready) {
    el.innerHTML = '<div><dt>file</dt><dd>not loaded</dd></div>';
    return;
  }
  const rows = meta.tables.reduce((a, t) => a + (t.rows || 0), 0);
  const cols = Object.keys(meta.columns).reduce((a, k) => a + meta.columns[k].length, 0);
  const parts = [
    ['file', meta.file],
    ['tables', fmtInt(meta.tables.length)],
    ['rows', fmtInt(rows)],
    ['columns', fmtInt(cols)],
    ['sources', fmtInt(meta.sources.length)],
    ['size', fmtMB(meta.bytes)]
  ];
  el.innerHTML = parts
    .map((p) => '<div><dt>' + esc(p[0]) + '</dt><dd>' + esc(p[1]) + '</dd></div>')
    .join('');
}

function tableHeadHtml() {
  const t = TBL.get(state.table);
  if (!t) return '';
  return '<div class="thead">' +
    '<span class="chip chip-' + esc(t.kind) + '">' + esc(t.kind) + '</span>' +
    '<strong>' + esc(t.table) + '</strong>' +
    '<span class="meta">dataset ' + esc(t.dataset) + '</span>' +
    '<span class="meta">' + fmtInt(t.rows) + ' rows</span>' +
    '<span class="meta mono">' + esc(t.source_path) + '</span>' +
    '<span class="meta mono">sha256 ' + esc(t.sha256.slice(0, 12)) + '</span>' +
    '</div>';
}

/* ---------- lineage ---------- */

function chip(table) {
  const t = TBL.get(table);
  if (!t) return '';
  return '<button class="chip chip-' + esc(t.kind) + '" data-act="open" data-table="' +
    esc(t.table) + '" title="open in the pivot">' + esc(t.table) +
    ' <span class="n">' + fmtInt(t.rows) + '</span></button>';
}

function stageBox(label, tables, kind) {
  const body = tables.length
    ? tables.map(chip).join('')
    : '<span class="muted">no table at this stage</span>';
  return '<div class="stage stage-' + esc(kind) + '"><h3>' + esc(label) + '</h3>' +
    '<div class="chips">' + body + '</div></div>';
}

function sourceCell(sources) {
  if (!sources.length) return '<span class="muted">not recorded</span>';
  return sources.map((s) => {
    const name = esc(s.publisher || s.source_id);
    const title = s.title ? ' - ' + esc(s.title) : '';
    const link = s.url
      ? '<a href="' + esc(s.url) + '" rel="noreferrer noopener" target="_blank">' + name + '</a>'
      : name;
    return '<div>' + link + title + '</div>';
  }).join('');
}

function rawFilesTable(files) {
  if (!files.length) return '';
  let h = '<h3>raw files and sources</h3>' +
    '<div class="scroll wide"><table class="data srctable"><thead><tr>' +
    '<th scope="col">file</th><th scope="col">original name</th><th scope="col">source</th>' +
    '<th scope="col">how obtained</th><th scope="col">licence</th><th scope="col">sha256</th>' +
    '<th scope="col">note</th></tr></thead><tbody>';
  for (const f of files) {
    const s0 = f.sources[0] || {};
    h += '<tr>' +
      '<td class="dim">' + esc(f.file) + '</td>' +
      '<td class="wrapcell">' + esc(f.original_name) + '</td>' +
      '<td class="wrapcell">' + sourceCell(f.sources) + '</td>' +
      '<td class="wrapcell">' + esc(s0.how_obtained || '') + '</td>' +
      '<td class="wrapcell">' + esc(s0.license || '') + '</td>' +
      '<td class="dim">' + esc(f.sha256) + '</td>' +
      '<td class="wrapcell">' + esc(f.note) + '</td>' +
      '</tr>';
  }
  return h + '</tbody></table></div>';
}

function renderLineage() {
  let h = '<p class="muted">Every table in the deliverable, by data type and pipeline stage. ' +
    'A chip opens that table in the pivot.</p>';
  for (const d of meta.datasets) {
    h += '<section class="card"><h2>' + esc(d.dataset) + '</h2>';
    const anyStage = STAGES.some((s) => d.stages[s].length);
    if (d.steps.length) {
      h += '<div class="flow">';
      d.steps.forEach((s, i) => {
        if (i) h += '<div class="arrow" aria-hidden="true">-&gt;</div>';
        h += stageBox(s.label, s.tables, 'output');
      });
      h += '</div>';
    } else if (d.registry.length && !anyStage) {
      h += '<div class="flow">' + stageBox('registry', d.registry, 'registry') + '</div>';
    } else {
      h += '<div class="flow">';
      STAGES.forEach((s, i) => {
        if (i) h += '<div class="arrow" aria-hidden="true">-&gt;</div>';
        h += stageBox(s, d.stages[s], s);
      });
      h += '</div>';
    }
    h += rawFilesTable(d.raw_files);
    h += '</section>';
  }
  document.getElementById('main').innerHTML = tableHeadHtml() + h;
}

/* ---------- map view: one value per country, read from the database ---------- */

let GEO = null;
let geoError = null;
let CODES = null;

const TIER_COLOR = {A: '#2e7d4f', B: '#d68a00', C: '#c62828'};
const STATUS_COLOR = {
  priced: '#2e7d4f', withheld: '#d68a00', no_benchmark: '#8d99ae',
  plant_side_only: '#6c757d', region_unpriced: '#adb5bd', destination_unknown: '#adb5bd'
};
const COV = ' FROM ti_coverage WHERE destination_level = "country"';

/* Every metric is a SQL query returning (destination, value); the WHERE clauses come from
   the map filters. No value is embedded in the page. */
const MAP_METRICS = [
  {id: 'coverage_units', label: 'sales units in the sales files', kind: 'seq', unit: 'vehicles',
   sql: (f) => 'SELECT destination, SUM(units)' + COV + f.company + f.year + ' GROUP BY 1'},
  {id: 'priced_units', label: 'units carrying a result', kind: 'seq', unit: 'vehicles',
   sql: (f) => 'SELECT destination, SUM(priced_units)' + COV + f.company + f.year +
     ' GROUP BY 1'},
  {id: 'priced_share', label: 'share of units priced', kind: 'seq', unit: 'fraction',
   sql: (f) => 'SELECT destination, SUM(priced_units) * 1.0 / SUM(units)' + COV + f.company +
     f.year + ' GROUP BY 1'},
  {id: 'coverage_status', label: 'coverage status', kind: 'cat', palette: STATUS_COLOR,
   sql: (f) => 'SELECT destination, MIN(status)' + COV + f.company + f.year + ' GROUP BY 1'},
  {id: 'ti_tco2e', label: 'lifetime TI (tCO2e), scenario', kind: 'div', unit: 'tCO2e',
   sql: (f) => 'SELECT destination, SUM(ti_tco2e) FROM ti_country WHERE scenario = ' +
     lit(f.scenarioVal) + f.company + f.year + ' GROUP BY 1'},
  {id: 'ti_per_vehicle', label: 'TI per vehicle (kgCO2e), scenario', kind: 'div',
   unit: 'kgCO2e per vehicle',
   sql: (f) => 'SELECT destination, SUM(ti_tco2e) * 1000.0 / SUM(units) FROM ti_country ' +
     'WHERE scenario = ' + lit(f.scenarioVal) + f.company + f.year + ' GROUP BY 1'},
  {id: 'fleet_intensity', label: 'benchmark fleet intensity (gCO2/km)', kind: 'seq',
   unit: 'gCO2/km', params: 'fleet_intensity_gco2_km'},
  {id: 'vkt', label: 'benchmark distance (km per car-year)', kind: 'seq', unit: 'km/yr',
   params: 'vkt_km'},
  {id: 'grid', label: 'grid intensity (gCO2/kWh)', kind: 'seq', unit: 'gCO2/kWh',
   params: 'grid_gco2_kwh'},
  {id: 'lifetime', label: 'operating lifetime T (years)', kind: 'seq', unit: 'years',
   params: 'lifetime_years'},
  {id: 'tier_vkt', label: 'tier: distance', kind: 'cat', palette: TIER_COLOR,
   params: 'vkt_tier'},
  {id: 'tier_fleet', label: 'tier: fleet intensity', kind: 'cat', palette: TIER_COLOR,
   params: 'fleet_intensity_tier'},
  {id: 'tier_grid', label: 'tier: grid', kind: 'cat', palette: TIER_COLOR, params: 'grid_tier'},
  {id: 'tier_lifetime', label: 'tier: lifetime', kind: 'cat', palette: TIER_COLOR,
   params: 'lifetime_tier'},
  {id: 'tier_cell', label: 'tier: worst input behind the result', kind: 'cat',
   palette: TIER_COLOR,
   sql: (f) => 'SELECT destination, CASE WHEN SUM(CASE WHEN tier = "C" THEN units ELSE 0 END)' +
     ' > 0 THEN "C" WHEN SUM(CASE WHEN tier = "B" THEN units ELSE 0 END) > 0 THEN "B" ' +
     'ELSE "A" END FROM ti_by_model WHERE scenario = ' + lit(f.scenarioVal) + f.company +
     f.year + ' GROUP BY 1'}
];

function paramTables() {
  return meta.tables.filter((t) => /^destination_parameters_/.test(t.table))
    .map((t) => t.table);
}

function paramsUnionSql(column) {
  const tables = paramTables();
  if (!tables.length) return null;
  return tables.map((t) => 'SELECT country AS destination, ' + qq(column) + ' AS v FROM ' +
    qq(t)).join(' UNION ALL ');
}

function mapFilters() {
  const m = state.map;
  return {
    company: m.company ? ' AND company = ' + lit(m.company) : '',
    year: m.year ? ' AND cohort_year = ' + lit(m.year) : '',
    scenarioVal: m.scenario || 'S1'
  };
}

/* The geometry is a row in the database (table map_geometry), so the map works wherever the
   database does - including a page opened straight from disk. */
function loadGeometry(done) {
  if (GEO || geoError) { done(); return; }
  if (window.__d3Failed || typeof d3 === 'undefined' || typeof topojson === 'undefined') {
    geoError = 'd3 or topojson could not be loaded from cdnjs - is this machine offline?';
    done();
    return;
  }
  if (!TBL.has('map_geometry')) {
    geoError = 'this database carries no map_geometry table - rebuild it with ' +
      'script/auto/model/build_database.py';
    done();
    return;
  }
  try {
    GEO = JSON.parse(query('SELECT topojson FROM map_geometry LIMIT 1').values[0][0]);
  } catch (e) {
    geoError = 'the map_geometry row could not be parsed: ' + (e.message || e);
  }
  done();
}

function loadCodes() {
  if (CODES) return CODES;
  CODES = new Map();
  if (!TBL.has('country_codes')) return CODES;
  for (const r of query('SELECT iso_numeric, alpha2, name FROM country_codes').values) {
    CODES.set(String(r[0]).padStart(3, '0'), {alpha2: r[1], name: r[2]});
  }
  return CODES;
}

function distinctList(sql) {
  return TBL.has('ti_coverage') ? query(sql).values.map((r) => String(r[0])) : [];
}

function renderMapShell() {
  const m = state.map;
  const companies = distinctList('SELECT DISTINCT company FROM ti_coverage ORDER BY 1');
  const years = distinctList('SELECT DISTINCT cohort_year FROM ti_coverage ORDER BY 1');
  const sel = (id, label, options) =>
    '<label>' + label + '<select id="' + id + '">' + options + '</select></label>';
  let h = '<section class="card map"><h2>Map</h2>' +
    '<p class="muted">One value per destination country, read from the database at view ' +
    'time. Hover for the value; click a country for every row and tier flag behind it.</p>' +
    '<div class="ctl">' +
    sel('map-metric', 'metric',
      MAP_METRICS.map((x) => opt(x.id, x.label, x.id === m.metric)).join('')) +
    sel('map-company', 'company', opt('', 'all companies', !m.company) +
      companies.map((c) => opt(c, c, c === m.company)).join('')) +
    sel('map-year', 'cohort year', opt('', 'all years', !m.year) +
      years.map((y) => opt(y, y, y === m.year)).join('')) +
    sel('map-scenario', 'scenario',
      ['S1', 'S2', 'S3'].map((sc) => opt(sc, sc, sc === m.scenario)).join('')) +
    '</div><div id="map-legend" class="legend"></div><div id="map-out"></div>' +
    '<div id="map-tip" class="tip"></div><div id="map-detail"></div></section>';
  document.getElementById('main').innerHTML = tableHeadHtml() + h;
  for (const id of ['map-metric', 'map-company', 'map-year', 'map-scenario']) {
    document.getElementById(id).addEventListener('change', (e) => {
      state.map[id.slice(4)] = e.target.value;
      renderMapOut();
    });
  }
}

function metricValues(metric) {
  const f = mapFilters();
  let sql;
  if (metric.params) {
    const inner = paramsUnionSql(metric.params);
    if (!inner) return new Map();
    sql = 'SELECT destination, v FROM (' + inner + ') WHERE v IS NOT NULL';
  } else {
    sql = metric.sql(f);
  }
  const out = new Map();
  for (const r of query(sql).values) {
    if (r[0] != null && r[1] != null) out.set(String(r[0]), r[1]);
  }
  return out;
}

function mapColor(metric, nums) {
  if (metric.kind === 'cat') return (v) => metric.palette[v] || '#adb5bd';
  if (metric.kind === 'div') {
    const amp = Math.max(1e-9, ...nums.map((v) => Math.abs(v)));
    return d3.scaleSequential([-amp, amp], d3.interpolateRdBu);
  }
  return d3.scaleSequential([Math.min(0, ...nums), Math.max(1e-9, ...nums)],
    d3.interpolateBlues);
}

function renderMapOut() {
  const out = document.getElementById('map-out');
  if (!out) return;
  loadGeometry(() => {
    if (geoError) { out.innerHTML = errBox(geoError); return; }
    const metric = MAP_METRICS.find((x) => x.id === state.map.metric) || MAP_METRICS[0];
    let values;
    try {
      values = metricValues(metric);
    } catch (e) {
      out.innerHTML = errBox(String(e.message || e));
      return;
    }
    const codes = loadCodes();
    const features = topojson.feature(GEO, GEO.objects.countries).features;
    const width = 960, height = 500;
    const projection = d3.geoNaturalEarth1().fitSize([width, height], {type: 'Sphere'});
    const path = d3.geoPath(projection);
    const nums = [...values.values()].filter((v) => typeof v === 'number');
    const color = mapColor(metric, nums);
    let svg = '<svg viewBox="0 0 ' + width + ' ' + height + '" role="img" ' +
      'aria-label="world map"><path d="' + path({type: 'Sphere'}) +
      '" fill="var(--panel)" stroke="var(--border)"/>';
    for (const ft of features) {
      const code = codes.get(String(ft.id).padStart(3, '0'));
      const a2 = code ? code.alpha2 : '';
      const v = a2 && values.has(a2) ? values.get(a2) : null;
      const fill = v === null ? 'var(--border)' : color(v);
      const sel = a2 && a2 === state.map.selected ? ' selected' : '';
      svg += '<path class="country' + sel + '" data-a2="' + esc(a2) + '" data-name="' +
        esc(ft.properties.name) + '" data-v="' + (v === null ? '' : esc(String(v))) +
        '" d="' + path(ft) + '" fill="' + fill + '"/>';
    }
    out.innerHTML = svg + '</svg>';
    renderMapLegend(metric, color, nums);
    renderMapDetail();
    const tip = document.getElementById('map-tip');
    out.querySelectorAll('path.country').forEach((el) => {
      el.addEventListener('mousemove', (e) => {
        const v = el.getAttribute('data-v');
        const a2 = el.getAttribute('data-a2');
        const shown = v === '' ? 'no value in the database'
          : (metric.kind === 'cat' ? v
            : fmtNum(Number(v)) + (metric.unit ? ' ' + metric.unit : ''));
        tip.textContent = el.getAttribute('data-name') + (a2 ? ' (' + a2 + ')' : '') +
          ': ' + shown;
        placeTip(tip, e.clientX, e.clientY);
      });
      el.addEventListener('mouseleave', () => { tip.style.display = 'none'; });
      el.addEventListener('click', () => {
        state.map.selected = el.getAttribute('data-a2');
        renderMapOut();
      });
    });
  });
}

/* Keep the hover chip inside the window: it sits right of the cursor until that would run
   past the edge, then flips to the left, and the same vertically. */
function placeTip(tip, x, y) {
  const gap = 12;
  tip.style.display = 'block';
  tip.style.left = '0px';
  tip.style.top = '0px';
  const w = tip.offsetWidth;
  const h = tip.offsetHeight;
  const right = Math.min(x + gap, window.innerWidth - w - 4);
  const left = x - gap - w;
  tip.style.left = Math.max(4, x + gap + w > window.innerWidth && left > 4 ? left : right) + 'px';
  const below = Math.min(y + gap, window.innerHeight - h - 4);
  const above = y - gap - h;
  tip.style.top = Math.max(4, y + gap + h > window.innerHeight && above > 4 ? above : below) + 'px';
}

function swatch(colour, label) {
  return '<span><span class="swatch" style="background:' + colour + '"></span>' + label +
    '</span>';
}

function renderMapLegend(metric, color, nums) {
  const el = document.getElementById('map-legend');
  if (metric.kind === 'cat') {
    el.innerHTML = Object.keys(metric.palette).map((k) => swatch(metric.palette[k], esc(k)))
      .join('') + swatch('var(--border)', 'no value');
    return;
  }
  if (!nums.length) {
    el.innerHTML = '<span class="muted">no values for this selection</span>';
    return;
  }
  const amp = Math.max(...nums.map((v) => Math.abs(v)));
  const lo = metric.kind === 'div' ? -amp : Math.min(0, ...nums);
  const hi = metric.kind === 'div' ? amp : Math.max(...nums);
  const stops = [0, 0.25, 0.5, 0.75, 1].map((q) => lo + q * (hi - lo));
  el.innerHTML = stops.map((v) => swatch(color(v), fmtNum(v))).join('') +
    ' <span class="muted">' + esc(metric.unit || '') +
    (metric.kind === 'div' ? ' (red = liability, blue = contribution)' : '') + '</span>' +
    swatch('var(--border)', 'no value');
}

function tierChip(t) {
  return t ? '<span class="tier tier-' + esc(t) + '">' + esc(t) + '</span>' : '';
}

function smallTable(r, tiers) {
  let h = '<div class="scroll sm"><table class="data"><thead><tr>' +
    r.columns.map((c) => '<th scope="col">' + esc(c) + '</th>').join('') +
    '</tr></thead><tbody>';
  for (const row of r.values) {
    h += '<tr>' + row.map((v, i) => '<td>' +
      (tiers && /tier/.test(r.columns[i]) ? tierChip(v) : fmtCell(v)) + '</td>').join('') +
      '</tr>';
  }
  return h + '</tbody></table></div>';
}

function renderMapDetail() {
  const el = document.getElementById('map-detail');
  const a2 = state.map.selected;
  if (!a2) {
    el.innerHTML = '<p class="muted">Click a country to list its coverage rows, benchmark ' +
      'parameters and tier flags.</p>';
    return;
  }
  let h = '<h3>' + esc(a2) + '</h3>';
  const f = mapFilters();
  if (TBL.has('ti_coverage')) {
    const r = query('SELECT company, cohort_year, period, basis, units, priced_units, ' +
      'withheld_units, status, note FROM ti_coverage WHERE destination = ' + lit(a2) +
      f.company + f.year + ' ORDER BY 1, 2');
    h += '<h4>coverage</h4>' + smallTable(r);
  }
  for (const t of paramTables()) {
    const r = query('SELECT * FROM ' + qq(t) + ' WHERE country = ' + lit(a2));
    if (!r.values.length) continue;
    h += '<h4>' + esc(t) + '</h4><table class="data"><tbody>';
    r.columns.forEach((c, i) => {
      const v = r.values[0][i];
      h += '<tr><th scope="row">' + esc(c) + '</th><td>' +
        (/_tier$/.test(c) ? tierChip(v) : fmtCell(v)) + '</td></tr>';
    });
    h += '</tbody></table>';
  }
  if (TBL.has('ti_country')) {
    const r = query('SELECT company, cohort_year, scenario, units, ti_tco2e, ' +
      'ti_per_vehicle_kgco2e, direction FROM ti_country WHERE destination = ' + lit(a2) +
      f.company + f.year + ' ORDER BY 1, 2, 3');
    if (r.values.length) h += '<h4>results (ti_country)</h4>' + smallTable(r);
  }
  if (TBL.has('ti_by_model')) {
    const r = query('SELECT tier, layer1_tier, layer2_tier, SUM(units) AS units FROM ' +
      'ti_by_model WHERE destination = ' + lit(a2) + ' AND scenario = ' + lit(f.scenarioVal) +
      f.company + f.year + ' GROUP BY 1, 2, 3 ORDER BY 1');
    if (r.values.length) {
      h += '<h4>units by tier of the worst input (' + esc(f.scenarioVal) + ')</h4>' +
        smallTable(r, true);
    }
  }
  el.innerHTML = h;
}

/* ---------- table selector and column panel ---------- */

function tableSelect() {
  let h = '<select id="tablesel" aria-label="Table">';
  const seen = [];
  for (const t of meta.tables) {
    const key = t.kind + ' / ' + t.dataset;
    if (seen.indexOf(key) < 0) {
      if (seen.length) h += '</optgroup>';
      seen.push(key);
      h += '<optgroup label="' + esc(key) + '">';
    }
    h += opt(t.table, t.table + '  (' + fmtInt(t.rows) + ')', t.table === state.table);
  }
  return h + (seen.length ? '</optgroup>' : '') + '</select>';
}

function columnPanel() {
  let h = '<h3>columns</h3><div class="scroll sm"><table class="data"><thead><tr>' +
    '<th scope="col">column</th><th scope="col">type</th>' +
    '<th scope="col" class="num">non-null</th><th scope="col" class="num">distinct</th>' +
    '<th scope="col">example</th></tr></thead><tbody>';
  for (const c of colsOf(state.table)) {
    h += '<tr><td class="dim">' + esc(c.column) + '</td>' +
      '<td>' + esc(c.sqlite_type) + '</td>' +
      '<td class="num">' + fmtInt(c.non_null) + '</td>' +
      '<td class="num">' + fmtInt(c.distinct) + '</td>' +
      '<td class="wrapcell">' + esc(c.example) + '</td></tr>';
  }
  return h + '</tbody></table></div>';
}

/* ---------- pivot ---------- */

function filterSql(f) {
  const c = qq(f.col);
  if (f.op === 'is null') return c + ' IS NULL';
  if (f.op === 'is not null') return c + ' IS NOT NULL';
  if (f.op === 'contains') return 'CAST(' + c + ' AS TEXT) LIKE ' + lit('%' + f.val + '%');
  if (f.op === 'starts with') return 'CAST(' + c + ' AS TEXT) LIKE ' + lit(f.val + '%');
  const numeric = f.val !== '' && isFinite(Number(f.val));
  const op = f.op === '!=' ? '<>' : f.op;
  return c + ' ' + op + ' ' + (numeric ? Number(f.val) : lit(f.val));
}

function activeFilters() {
  return state.pivot.filters.filter((f) => f.col && (NO_VALUE_OPS[f.op] || f.val !== ''));
}

function pivotSpec() {
  const p = state.pivot;
  const fn = AGG_SQL[p.agg] || 'SUM';
  const dims = p.rows.slice();
  if (p.cols) dims.push(p.cols);
  const sel = dims.map(qq);
  const vals = [];
  if (p.vals.length) {
    for (const v of p.vals) {
      sel.push(fn + '(' + qq(v) + ') AS ' + qq(p.agg + '_' + v));
      vals.push({col: v, label: v + ' (' + p.agg + ')'});
    }
  } else {
    sel.push('COUNT(*) AS ' + qq('rows'));
    vals.push({col: null, label: 'rows (count)'});
  }
  let sql = 'SELECT ' + sel.join(',\n       ') + '\n  FROM ' + qq(state.table);
  const w = activeFilters().map(filterSql);
  if (w.length) sql += '\n WHERE ' + w.join('\n   AND ');
  if (dims.length) {
    sql += '\n GROUP BY ' + dims.map(qq).join(', ');
    sql += '\n ORDER BY ' + dims.map(qq).join(', ');
  }
  return {sql: sql, dims: dims, vals: vals};
}

function combine(list, agg) {
  const nums = list.filter((x) => typeof x === 'number' && isFinite(x));
  if (!nums.length) return null;
  if (agg === 'min') return Math.min.apply(null, nums);
  if (agg === 'max') return Math.max.apply(null, nums);
  const total = nums.reduce((a, b) => a + b, 0);
  return agg === 'mean' ? total / nums.length : total;
}

function cmpVals(a, b) {
  if (a === null || a === undefined) return b === null || b === undefined ? 0 : -1;
  if (b === null || b === undefined) return 1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a) < String(b) ? -1 : String(a) > String(b) ? 1 : 0;
}

function numCell(v, extra, column) {
  const cls = 'num' + (typeof v === 'number' && v < 0 ? ' neg' : '') + (extra ? ' ' + extra : '');
  return '<td class="' + cls + '">' + esc(fmtIn(v, column)) + '</td>';
}

function sortTh(key, label, cls, span) {
  const s = state.pivot.sort;
  const on = s && s.key === key;
  const mark = on
    ? ' <span class="dir" aria-hidden="true">' + (s.dir === 'desc' ? 'v' : '^') + '</span>'
    : '';
  const aria = on ? (s.dir === 'desc' ? 'descending' : 'ascending') : 'none';
  return '<th scope="col"' + (span > 1 ? ' rowspan="' + span + '"' : '') +
    ' class="sortable ' + (cls || '') + '" aria-sort="' + aria +
    '" data-sort="' + esc(key) + '">' + esc(label) + mark + '</th>';
}

function renderPivotOut() {
  const out = document.getElementById('pivot-out');
  const spec = pivotSpec();
  document.getElementById('pivot-sql').textContent = spec.sql;
  if (!DB) {
    out.innerHTML = engineBox();
    return;
  }
  let res;
  try {
    res = query(spec.sql);
  } catch (e) {
    out.innerHTML = errBox('SQL error: ' + e.message);
    return;
  }
  const p = state.pivot;
  const nrow = p.rows.length;
  const nval = spec.vals.length;
  const base = nrow + (p.cols ? 1 : 0);
  const rows = [];
  const rowIdx = new Map();
  const colKeys = [];
  const colSeen = new Set();
  const cells = new Map();
  for (const r of res.values) {
    const dimVals = p.rows.map((c, i) => r[i]);
    const rk = JSON.stringify(dimVals);
    if (!rowIdx.has(rk)) {
      rowIdx.set(rk, rows.length);
      rows.push({key: rk, vals: dimVals});
    }
    const ck = p.cols ? (r[nrow] === null ? '(null)' : String(r[nrow])) : '';
    if (!colSeen.has(ck)) {
      colSeen.add(ck);
      colKeys.push(ck);
    }
    for (let v = 0; v < nval; v++) cells.set(rk + SEP + ck + SEP + v, r[base + v]);
  }
  if (p.cols) colKeys.sort();
  if (!rows.length) {
    out.innerHTML = '<div class="empty">No rows match the filters.</div>';
    state.tsv = '';
    return;
  }

  const cell = (rk, ck, v) => {
    const x = cells.get(rk + SEP + ck + SEP + v);
    return x === undefined ? null : x;
  };
  const rowAll = (rk, v) => combine(colKeys.map((ck) => cell(rk, ck, v)), p.agg);

  if (p.sort) {
    const s = p.sort;
    const dir = s.dir === 'desc' ? -1 : 1;
    const keyOf = (row) => {
      if (s.key.charAt(0) === 'd') return row.vals[Number(s.key.slice(2))];
      const bits = s.key.slice(2).split('|');
      const v = Number(bits[1]);
      return bits[0] === 'a' ? rowAll(row.key, v) : cell(row.key, colKeys[Number(bits[0])], v);
    };
    rows.sort((a, b) => cmpVals(keyOf(a), keyOf(b)) * dir);
  }

  const showAll = !!p.cols;
  const span = p.cols ? 2 : 1;
  let head = '<thead><tr>';
  p.rows.forEach((c, i) => {
    head += sortTh('d:' + i, c, 'dim', span);
  });
  if (p.cols) {
    for (let ci = 0; ci < colKeys.length; ci++) {
      head += '<th scope="colgroup" class="num" colspan="' + nval + '">' +
        esc(colKeys[ci]) + '</th>';
    }
    head += '<th scope="colgroup" class="num total" colspan="' + nval + '">all</th></tr><tr>';
    for (let ci = 0; ci < colKeys.length; ci++) {
      for (let v = 0; v < nval; v++) head += sortTh('v:' + ci + '|' + v, spec.vals[v].label, 'num');
    }
    for (let v = 0; v < nval; v++) head += sortTh('v:a|' + v, spec.vals[v].label, 'num total');
  } else {
    for (let v = 0; v < nval; v++) head += sortTh('v:0|' + v, spec.vals[v].label, 'num');
  }
  head += '</tr></thead>';

  const tsv = [];
  const headLine = p.rows.slice();
  if (p.cols) {
    for (const ck of colKeys) for (const v of spec.vals) headLine.push(ck + ' / ' + v.label);
    for (const v of spec.vals) headLine.push('all / ' + v.label);
  } else {
    for (const v of spec.vals) headLine.push(v.label);
  }
  tsv.push(headLine);

  const keys = p.cols ? colKeys : [''];
  let body = '<tbody>';
  for (const row of rows) {
    const line = row.vals.map((x) => (x === null ? '' : String(x)));
    body += '<tr>' + row.vals
      .map((x, i) => '<td class="dim">' + esc(fmtIn(x, p.rows[i])) + '</td>').join('');
    for (const ck of keys) {
      for (let v = 0; v < nval; v++) {
        const x = cell(row.key, ck, v);
        body += numCell(x, null, spec.vals[v].col);
        line.push(x === null ? '' : String(x));
      }
    }
    if (showAll) {
      for (let v = 0; v < nval; v++) {
        const x = rowAll(row.key, v);
        body += numCell(x, 'total', spec.vals[v].col);
        line.push(x === null ? '' : String(x));
      }
    }
    body += '</tr>';
    tsv.push(line);
  }

  const label = p.agg === 'mean' ? 'all (mean of shown)' : 'all (' + p.agg + ')';
  let foot = '<tr class="total"><th scope="row" class="dim"' +
    (nrow > 1 ? ' colspan="' + nrow + '"' : '') + '>' + esc(label) + '</th>';
  const totalLine = [label];
  for (let i = 1; i < nrow; i++) totalLine.push('');
  for (const ck of keys) {
    for (let v = 0; v < nval; v++) {
      const x = combine(rows.map((r) => cell(r.key, ck, v)), p.agg);
      foot += numCell(x, null, spec.vals[v].col);
      totalLine.push(x === null ? '' : String(x));
    }
  }
  if (showAll) {
    for (let v = 0; v < nval; v++) {
      const x = combine(rows.map((r) => rowAll(r.key, v)), p.agg);
      foot += numCell(x, 'total', spec.vals[v].col);
      totalLine.push(x === null ? '' : String(x));
    }
  }
  foot += '</tr>';
  tsv.push(totalLine);
  state.tsv = tsv.map((l) => l.join('\t')).join('\n');

  out.innerHTML = '<div class="scroll"><table class="data">' + head + body + foot +
    '</tbody></table></div>' +
    '<p class="note">' + fmtInt(rows.length) + ' row groups' +
    (p.cols ? ', ' + fmtInt(colKeys.length) + ' column groups' : '') +
    '. The all row and column re-apply the aggregation to the cells shown, so under mean they ' +
    'are the unweighted mean of those cells. Click a header to sort.</p>';
}

function renderFilters() {
  const cs = colsOf(state.table);
  const box = document.getElementById('filters');
  if (!state.pivot.filters.length) {
    box.innerHTML = '<p class="muted">No filter: every row of the table is aggregated.</p>';
    return;
  }
  box.innerHTML = state.pivot.filters.map((f, i) => {
    const colSel = '<select data-f="col" data-i="' + i + '" aria-label="Filter column">' +
      cs.map((c) => opt(c.column, c.column, c.column === f.col)).join('') + '</select>';
    const opSel = '<select data-f="op" data-i="' + i + '" aria-label="Filter operator">' +
      OPS.map((o) => opt(o, o, o === f.op)).join('') + '</select>';
    const val = '<input type="text" data-f="val" data-i="' + i + '" value="' + esc(f.val) +
      '" aria-label="Filter value"' + (NO_VALUE_OPS[f.op] ? ' disabled' : '') + '>';
    return '<div class="filterrow">' + colSel + opSel + val +
      '<button data-act="rmfilter" data-i="' + i + '">remove</button></div>';
  }).join('');
}

function renderPivotShell() {
  const cs = colsOf(state.table);
  const nums = cs.filter((c) => isNumeric(state.table, c.column));
  const p = state.pivot;
  const rowSel = '<select id="p-rows" multiple size="6" aria-label="Row fields">' +
    cs.map((c) => opt(c.column, c.column, p.rows.indexOf(c.column) >= 0)).join('') + '</select>';
  const colSel = '<select id="p-cols" aria-label="Column field">' +
    opt('', '(none)', !p.cols) +
    cs.map((c) => opt(c.column, c.column, c.column === p.cols)).join('') + '</select>';
  const valSel = '<select id="p-vals" multiple size="6" aria-label="Value fields">' +
    nums.map((c) => opt(c.column, c.column, p.vals.indexOf(c.column) >= 0)).join('') + '</select>';
  const aggSel = '<select id="p-agg" aria-label="Aggregation">' +
    AGGS.map((a) => opt(a, a, a === p.agg)).join('') + '</select>';
  document.getElementById('main').innerHTML = tableHeadHtml() +
    '<section class="card"><h2>Table</h2>' + tableSelect() + columnPanel() + '</section>' +
    '<section class="card"><h2>Pivot</h2><div class="pickers">' +
    '<div class="picker"><label for="p-rows">Rows</label>' + rowSel + '</div>' +
    '<div class="picker"><label for="p-cols">Columns</label>' + colSel + '</div>' +
    '<div class="picker"><label for="p-vals">Values (numeric)</label>' + valSel + '</div>' +
    '<div class="picker"><label for="p-agg">Aggregation</label>' + aggSel + '</div>' +
    '</div>' +
    '<h3>filters (all must hold)</h3><div id="filters"></div>' +
    '<div class="row"><button data-act="addfilter">add filter</button>' +
    '<button data-act="clearfilters">clear filters</button>' +
    '<button data-act="copytsv" class="primary">Copy as TSV</button>' +
    '<span class="muted" id="copymsg" role="status"></span></div>' +
    '<h3>generated SQL</h3><pre class="sqlbox" id="pivot-sql" tabindex="0"></pre>' +
    '</section><div id="pivot-out"></div>';
  renderFilters();
}

/* ---------- browse ---------- */

function browseSpec() {
  const b = state.browse;
  const names = colsOf(state.table).map((c) => c.column);
  let where = '';
  if (b.q) {
    const like = lit('%' + b.q + '%');
    where = '\n WHERE ' + names.map((c) => 'CAST(' + qq(c) + ' AS TEXT) LIKE ' + like)
      .join('\n    OR ');
  }
  let sql = 'SELECT *\n  FROM ' + qq(state.table) + where;
  if (b.sort) sql += '\n ORDER BY ' + qq(b.sort) + (b.dir === 'desc' ? ' DESC' : ' ASC');
  sql += '\n LIMIT ' + PAGE + ' OFFSET ' + b.page * PAGE;
  return {sql: sql, count: 'SELECT COUNT(*) FROM ' + qq(state.table) + where};
}

function renderBrowseOut() {
  const out = document.getElementById('browse-out');
  const spec = browseSpec();
  document.getElementById('browse-sql').textContent = spec.sql;
  if (!DB) {
    out.innerHTML = engineBox();
    return;
  }
  let res;
  let total;
  try {
    total = query(spec.count).values[0][0];
    res = query(spec.sql);
  } catch (e) {
    out.innerHTML = errBox('SQL error: ' + e.message);
    return;
  }
  const b = state.browse;
  const pages = Math.max(1, Math.ceil(total / PAGE));
  if (!res.values.length) {
    out.innerHTML = '<div class="empty">No rows match the filter.</div>';
    state.tsv = '';
    return;
  }
  let head = '<thead><tr>';
  for (const c of res.columns) {
    const on = b.sort === c;
    const aria = on ? (b.dir === 'desc' ? 'descending' : 'ascending') : 'none';
    const mark = on
      ? ' <span class="dir" aria-hidden="true">' + (b.dir === 'desc' ? 'v' : '^') + '</span>'
      : '';
    head += '<th scope="col" class="sortable" aria-sort="' + aria + '" data-bsort="' +
      esc(c) + '">' + esc(c) + mark + '</th>';
  }
  head += '</tr></thead>';
  let body = '<tbody>';
  const tsv = [res.columns.slice()];
  for (const r of res.values) {
    body += '<tr>' + r.map((x, i) => (typeof x === 'number'
      ? numCell(x, null, res.columns[i])
      : '<td>' + esc(fmtCell(x)) + '</td>')).join('') + '</tr>';
    tsv.push(r.map((x) => (x === null ? '' : String(x))));
  }
  state.tsv = tsv.map((l) => l.join('\t')).join('\n');
  const from = b.page * PAGE + 1;
  const to = b.page * PAGE + res.values.length;
  out.innerHTML = '<div class="scroll"><table class="data">' + head + body +
    '</tbody></table></div>' +
    '<div class="row"><button data-act="prev"' + (b.page ? '' : ' disabled') +
    '>previous</button>' +
    '<button data-act="next"' + (b.page + 1 < pages ? '' : ' disabled') + '>next</button>' +
    '<span class="muted">rows ' + fmtInt(from) + '-' + fmtInt(to) + ' of ' + fmtInt(total) +
    ', page ' + fmtInt(b.page + 1) + ' of ' + fmtInt(pages) + '</span></div>';
}

function renderBrowseShell() {
  document.getElementById('main').innerHTML = tableHeadHtml() +
    '<section class="card"><h2>Table</h2>' + tableSelect() +
    '<div class="row"><label for="b-q">Quick filter</label>' +
    '<input type="text" id="b-q" value="' + esc(state.browse.q) +
    '" placeholder="text in any column">' +
    '<button data-act="copytsv" class="primary">Copy as TSV</button>' +
    '<span class="muted" id="copymsg" role="status"></span></div>' +
    '<h3>generated SQL</h3><pre class="sqlbox" id="browse-sql" tabindex="0"></pre>' +
    '</section><div id="browse-out"></div>';
}

/* ---------- free SQL ---------- */

function cleanSql(text) {
  return text.trim().replace(/;+\s*$/, '');
}

function checkSql(text) {
  const t = cleanSql(text);
  if (!t) return 'Enter a SELECT or WITH statement.';
  if (t.indexOf(';') >= 0) return 'Only one statement is allowed.';
  if (!/^(select|with)\b/i.test(t)) return 'Only SELECT and WITH statements are allowed.';
  if (BLOCKED.test(t)) return 'This viewer is read-only: write statements are rejected.';
  return null;
}

function renderSqlOut() {
  const out = document.getElementById('sql-out');
  const bad = checkSql(state.sql.text);
  if (bad) {
    out.innerHTML = errBox(bad);
    return;
  }
  if (!DB) {
    out.innerHTML = engineBox();
    return;
  }
  let res;
  try {
    res = query(cleanSql(state.sql.text));
  } catch (e) {
    out.innerHTML = errBox('SQL error: ' + e.message);
    return;
  }
  if (!res.columns.length) {
    out.innerHTML = '<div class="empty">The statement returned no result set.</div>';
    return;
  }
  const shown = res.values.slice(0, 1000);
  let h = '<div class="scroll"><table class="data"><thead><tr>' +
    res.columns.map((c) => '<th scope="col">' + esc(c) + '</th>').join('') +
    '</tr></thead><tbody>';
  const tsv = [res.columns.slice()];
  for (const r of shown) {
    h += '<tr>' + r.map((x, i) => (typeof x === 'number'
      ? numCell(x, null, res.columns[i])
      : '<td>' + esc(fmtCell(x)) + '</td>')).join('') + '</tr>';
    tsv.push(r.map((x) => (x === null ? '' : String(x))));
  }
  state.tsv = tsv.map((l) => l.join('\t')).join('\n');
  h += '</tbody></table></div><p class="note">' + fmtInt(res.values.length) + ' rows' +
    (res.values.length > shown.length ? ', first ' + fmtInt(shown.length) + ' shown' : '') +
    '.</p>';
  out.innerHTML = h;
}

function renderSqlShell() {
  document.getElementById('main').innerHTML = tableHeadHtml() +
    '<section class="card"><h2>Read-only SQL</h2>' +
    '<p class="muted">One SELECT or WITH statement against the loaded database. ' +
    'Nothing is written back: the page holds a copy in memory.</p>' +
    '<label for="sql-text" class="muted">statement</label>' +
    '<textarea id="sql-text" spellcheck="false">' + esc(state.sql.text) + '</textarea>' +
    '<div class="row"><button data-act="runsql" class="primary">Run</button>' +
    '<button data-act="copytsv">Copy as TSV</button>' +
    '<span class="muted" id="copymsg" role="status"></span></div></section>' +
    '<div id="sql-out"></div>';
}

/* ---------- clipboard ---------- */

function copyTsv() {
  const msg = document.getElementById('copymsg');
  const text = state.tsv || '';
  const say = (s) => {
    if (msg) msg.textContent = s;
  };
  if (!text) {
    say('nothing to copy');
    return;
  }
  const done = () => say('copied ' + fmtInt(text.length) + ' characters');
  const fallback = () => {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try {
      ok = document.execCommand('copy');
    } catch (e) {
      ok = false;
    }
    document.body.removeChild(ta);
    if (ok) done();
    else say('the browser blocked the clipboard');
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, fallback);
  } else {
    fallback();
  }
}

/* ---------- metadata, read out of the database with SQL ---------- */

function rowsOf(sql) {
  return query(sql).values;
}

function tableNames() {
  return rowsOf("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    .map((r) => String(r[0]));
}

function pragmaColumns(table) {
  return rowsOf('PRAGMA table_info(' + qq(table) + ')')
    .map((r) => ({column: String(r[1]), sqlite_type: String(r[2] === null ? '' : r[2])}));
}

function text(v) {
  return v === null || v === undefined ? '' : String(v);
}

function readTables() {
  const order = "CASE kind WHEN 'raw' THEN 0 WHEN 'method' THEN 1 WHEN 'processed' THEN 2" +
    " WHEN 'output' THEN 3 ELSE 4 END";
  return rowsOf('SELECT "table", dataset, kind, source_path, rows, sha256 FROM "tables"' +
    ' ORDER BY ' + order + ', dataset, "table"')
    .map((r) => ({
      table: text(r[0]),
      dataset: text(r[1]),
      kind: text(r[2]),
      source_path: text(r[3]),
      rows: r[4],
      sha256: text(r[5])
    }));
}

/* Fallback when the columns dictionary is missing a table: one pass per column. */
function deriveColumns(table) {
  const t = qq(table);
  return pragmaColumns(table).map((c) => {
    const q = qq(c.column);
    const r = rowsOf('SELECT COUNT(' + q + '), COUNT(DISTINCT ' + q + '), (SELECT ' + q +
      ' FROM ' + t + ' WHERE ' + q + ' IS NOT NULL LIMIT 1) FROM ' + t)[0] || [0, 0, null];
    return {column: c.column, sqlite_type: c.sqlite_type, non_null: r[0], distinct: r[1],
      example: text(r[2]).slice(0, 80)};
  });
}

/* The dictionary names its distinct count distinct_values in the current builder and distinct
   in earlier ones; both are accepted. Column order follows the physical table order. */
function readColumns(tables, names) {
  const stored = new Map();
  if (names.indexOf('columns') >= 0) {
    const own = pragmaColumns('columns').map((c) => c.column);
    const dcol = own.indexOf('distinct_values') >= 0 ? 'distinct_values' : 'distinct';
    for (const r of rowsOf('SELECT "table", "column", sqlite_type, non_null, ' + qq(dcol) +
        ', example FROM "columns"')) {
      const key = text(r[0]);
      if (!stored.has(key)) stored.set(key, new Map());
      stored.get(key).set(text(r[1]), {column: text(r[1]), sqlite_type: text(r[2]),
        non_null: r[3], distinct: r[4], example: text(r[5]).slice(0, 80)});
    }
  }
  const out = {};
  for (const t of tables) {
    const physical = pragmaColumns(t.table).map((c) => c.column);
    const have = stored.get(t.table);
    out[t.table] = have && physical.every((c) => have.has(c))
      ? physical.map((c) => have.get(c))
      : deriveColumns(t.table);
  }
  return out;
}

const SOURCE_KEYS = ['source_id', 'publisher', 'title', 'url', 'how_obtained', 'accessed_date',
  'license', 'used_by'];

function readSources(names) {
  if (names.indexOf('sources') < 0) return [];
  return rowsOf('SELECT ' + SOURCE_KEYS.map(qq).join(', ') +
    ' FROM "sources" ORDER BY source_id').map((r) => {
    const o = {};
    SOURCE_KEYS.forEach((k, i) => {
      o[k] = text(r[i]);
    });
    return o;
  });
}

/* raw_files.source_id holds one or more ids separated by semicolons; each is resolved against
   the registry so the lineage view can render publisher, title, link and licence. */
function readRawFiles(names, sources) {
  const out = {};
  if (names.indexOf('raw_files') < 0) return out;
  const byId = new Map(sources.map((s) => [s.source_id, s]));
  for (const r of rowsOf('SELECT dataset, file, source_id, original_name, sha256, note ' +
      'FROM "raw_files" ORDER BY dataset, file')) {
    const dataset = text(r[0]);
    const ids = text(r[2]).split(';').map((s) => s.trim()).filter((s) => s);
    if (!out[dataset]) out[dataset] = [];
    out[dataset].push({
      file: text(r[1]),
      original_name: text(r[3]),
      sha256: text(r[4]).slice(0, 12),
      note: text(r[5]),
      sources: ids.map((i) => byId.get(i) || {source_id: i, publisher: '', title: '', url: ''})
    });
  }
  return out;
}

function buildDatasets(tables, rawFiles) {
  const seen = new Set(tables.map((t) => t.dataset));
  Object.keys(rawFiles).forEach((d) => seen.add(d));
  const names = Array.from(seen).sort();
  const ordered = DATASET_ORDER.filter((d) => names.indexOf(d) >= 0)
    .concat(names.filter((d) => DATASET_ORDER.indexOf(d) < 0));
  return ordered.map((dataset) => {
    const mine = tables.filter((t) => t.dataset === dataset);
    const stages = {};
    for (const s of STAGES) stages[s] = mine.filter((t) => t.kind === s).map((t) => t.table);
    const outputs = stages.output.slice();
    const steps = [];
    if (dataset === 'model' && outputs.length) {
      const taken = new Set();
      for (const step of MODEL_STEPS) {
        const hit = [];
        for (const p of step[1]) {
          for (const t of outputs) if (t.indexOf(p) === 0) hit.push(t);
        }
        hit.forEach((t) => taken.add(t));
        if (hit.length) steps.push({label: step[0], tables: hit});
      }
      const rest = outputs.filter((t) => !taken.has(t));
      if (rest.length) steps.push({label: 'other', tables: rest});
    }
    return {
      dataset: dataset,
      stages: stages,
      registry: mine.filter((t) => t.kind === 'registry').map((t) => t.table),
      steps: steps,
      raw_files: rawFiles[dataset] || []
    };
  });
}

function loadMeta() {
  const names = tableNames();
  if (names.indexOf('tables') < 0) {
    throw new Error('this database has no "tables" manifest: build_database.py writes it');
  }
  meta.tables = readTables();
  if (!meta.tables.length) throw new Error('the "tables" manifest is empty');
  meta.columns = readColumns(meta.tables, names);
  meta.sources = readSources(names);
  meta.datasets = buildDatasets(meta.tables, readRawFiles(names, meta.sources));
  TBL = new Map(meta.tables.map((t) => [t.table, t]));
}

/* ---------- the open-database panel ---------- */

function renderOpener() {
  const onDisk = location.protocol === 'file:';
  const picker = '<div class="drop" id="drop">' +
    '<label for="dbfile">Database file</label>' +
    '<input type="file" id="dbfile" accept=".sqlite,.db">' +
    '<span class="muted">or drag <span class="mono">' + esc(DB_FILE) +
    '</span> onto this box</span></div>';
  const served = '<p>Run this once and the page connects itself from then on - from the ' +
    'server address, and from this file too, with no clicking:</p>' +
    '<pre class="sqlbox" tabindex="0">' + esc(SERVE_CMD) + ' --open</pre>';
  document.getElementById('main').innerHTML =
    '<section class="card opener"><h2>Open the database</h2>' +
    (dbError && !onDisk ? errBox(dbError) : '') +
    '<p>This page holds no data of its own; it reads <span class="mono">' + esc(DB_FILE) +
    '</span>.</p>' + (onDisk ? served : '') +
    '<p class="muted">Or open the file yourself, once, right now - it never leaves your ' +
    'machine:</p>' + picker +
    (onDisk ? '<p class="muted">A page opened from disk may not read a file beside it on its ' +
      'own. Every browser blocks that; the server above is the way around it.</p>' : '') +
    '</section>';
}

/* ---------- routing and rendering ---------- */

function render() {
  if (!ready) {
    renderOpener();
    return;
  }
  const key = state.view + '|' + state.table;
  if (key !== shellKey) {
    shellKey = key;
    if (PIVOT_VIEWS[state.view]) renderPivotShell();
    else if (state.view === 'browse') renderBrowseShell();
    else if (state.view === 'sql') renderSqlShell();
    else if (state.view === 'map') renderMapShell();
    else renderLineage();
  }
  if (PIVOT_VIEWS[state.view]) renderPivotOut();
  else if (state.view === 'browse') renderBrowseOut();
  else if (state.view === 'sql') renderSqlOut();
  else if (state.view === 'map') renderMapOut();
  renderNav();
}

function applyHash() {
  if (!ready) {
    renderOpener();
    return;
  }
  const raw = (location.hash || '#/lineage').replace(/^#\/?/, '');
  const parts = raw.split('/');
  const view = parts[0] || 'lineage';
  const table = parts[1] ? decodeURIComponent(parts[1]) : null;
  if (PRESET_VIEWS[view]) {
    const preset = view === 'results' ? DEFAULT_PIVOT : YEARLY_PIVOT;
    if (state.view !== view) {  /* arriving: lay the preset out; staying: keep any tweaks */
      state.table = preset.table;
      state.pivot = defaultPivot(preset.table);
      state.view = view;
      shellKey = '';
    }
    render();
    return;
  }
  if (['lineage', 'map', 'pivot', 'browse', 'sql'].indexOf(view) < 0) {
    go('#/lineage');
    return;
  }
  state.view = view;
  if (table && TBL.has(table) && table !== state.table) {
    state.table = table;
    state.pivot = defaultPivot(table);
    state.browse = {page: 0, sort: null, dir: 'asc', q: ''};
    shellKey = '';
  }
  render();
}

function go(hash) {
  if (location.hash === hash) applyHash();
  else location.hash = hash;
}

function openTable(name) {
  state.view = 'pivot';
  go('#/pivot/' + encodeURIComponent(name));
}

/* ---------- events, delegated ---------- */

const main = document.getElementById('main');

document.getElementById('nav').addEventListener('click', (e) => {
  const b = e.target.closest('[data-view]');
  if (!b) return;
  const v = b.getAttribute('data-view');
  if (v === 'results' || v === 'results_year') go('#/' + v);
  else if (v === 'pivot' || v === 'browse') go('#/' + v + '/' + encodeURIComponent(state.table));
  else go('#/' + v);
});

main.addEventListener('click', (e) => {
  const el = e.target.closest('[data-act], [data-sort], [data-bsort]');
  if (!el) return;
  const act = el.getAttribute('data-act');
  if (act === 'open') {
    openTable(el.getAttribute('data-table'));
    return;
  }
  if (act === 'addfilter') {
    const first = colsOf(state.table)[0];
    state.pivot.filters.push({col: first ? first.column : '', op: '=', val: ''});
    renderFilters();
    return;
  }
  if (act === 'rmfilter') {
    state.pivot.filters.splice(Number(el.getAttribute('data-i')), 1);
    renderFilters();
    renderPivotOut();
    return;
  }
  if (act === 'clearfilters') {
    state.pivot.filters = [];
    renderFilters();
    renderPivotOut();
    return;
  }
  if (act === 'copytsv') {
    copyTsv();
    return;
  }
  if (act === 'runsql') {
    const ta = document.getElementById('sql-text');
    if (ta) state.sql.text = ta.value;
    renderSqlOut();
    return;
  }
  if (act === 'prev') {
    state.browse.page = Math.max(0, state.browse.page - 1);
    renderBrowseOut();
    return;
  }
  if (act === 'next') {
    state.browse.page += 1;
    renderBrowseOut();
    return;
  }
  const sortKey = el.getAttribute('data-sort');
  if (sortKey) {
    const s = state.pivot.sort;
    const desc = s && s.key === sortKey && s.dir === 'asc';
    state.pivot.sort = {key: sortKey, dir: desc ? 'desc' : 'asc'};
    renderPivotOut();
    return;
  }
  const bsort = el.getAttribute('data-bsort');
  if (bsort) {
    const b = state.browse;
    b.dir = b.sort === bsort && b.dir === 'asc' ? 'desc' : 'asc';
    b.sort = bsort;
    b.page = 0;
    renderBrowseOut();
  }
});

main.addEventListener('change', (e) => {
  const t = e.target;
  if (t.id === 'dbfile') {
    if (t.files && t.files.length) openFile(t.files[0]);
    return;
  }
  if (t.id === 'tablesel') {
    if (state.view === 'browse') go('#/browse/' + encodeURIComponent(t.value));
    else openTable(t.value);
    return;
  }
  if (t.id === 'p-rows') {
    state.pivot.rows = selected(t);
    state.pivot.sort = null;
  }
  if (t.id === 'p-cols') {
    state.pivot.cols = t.value;
    state.pivot.sort = null;
  }
  if (t.id === 'p-vals') {
    state.pivot.vals = selected(t);
    state.pivot.sort = null;
  }
  if (t.id === 'p-agg') state.pivot.agg = t.value;
  if (['p-rows', 'p-cols', 'p-vals', 'p-agg'].indexOf(t.id) >= 0) {
    renderPivotOut();
    return;
  }
  const f = t.getAttribute('data-f');
  if (f) {
    const i = Number(t.getAttribute('data-i'));
    state.pivot.filters[i][f] = t.value;
    if (f === 'op') renderFilters();
    renderPivotOut();
  }
});

main.addEventListener('input', (e) => {
  const t = e.target;
  if (t.id === 'sql-text') {
    state.sql.text = t.value;
    return;
  }
  const isQuick = t.id === 'b-q';
  const isVal = t.getAttribute('data-f') === 'val';
  if (!isQuick && !isVal) return;
  if (isQuick) {
    state.browse.q = t.value;
    state.browse.page = 0;
  } else {
    state.pivot.filters[Number(t.getAttribute('data-i'))].val = t.value;
  }
  clearTimeout(debounce);
  debounce = setTimeout(() => {
    if (isQuick) renderBrowseOut();
    else renderPivotOut();
  }, 250);
});

/* Drag and drop onto the open-database panel. */
function dropZone(e) {
  return e.target && e.target.closest ? e.target.closest('#drop') : null;
}

main.addEventListener('dragover', (e) => {
  const z = dropZone(e);
  if (!z) return;
  e.preventDefault();
  z.classList.add('over');
});

main.addEventListener('dragleave', (e) => {
  const z = dropZone(e);
  if (z) z.classList.remove('over');
});

main.addEventListener('drop', (e) => {
  const z = dropZone(e);
  if (!z) return;
  e.preventDefault();
  z.classList.remove('over');
  const f = e.dataTransfer && e.dataTransfer.files[0];
  if (f) openFile(f);
});

/* A file dropped beside the zone would otherwise navigate the tab away from the page. */
window.addEventListener('dragover', (e) => {
  if (!ready) e.preventDefault();
});

window.addEventListener('drop', (e) => {
  if (!ready) e.preventDefault();
});

window.addEventListener('hashchange', applyHash);

/* ---------- boot: load the engine, then the sibling database ---------- */

function engineReady() {
  if (SQL) return Promise.resolve(SQL);
  if (window.__sqljsFailed || typeof window.initSqlJs !== 'function') {
    return Promise.reject(new Error('sql.js ' + SQLJS_VERSION +
      ' could not be loaded from cdnjs - is this machine offline?'));
  }
  return window.initSqlJs({locateFile: (f) => CDN_DIR + f}).then((m) => {
    SQL = m;
    return m;
  });
}

function failOpen(message) {
  DB = null;
  ready = false;
  dbError = message;
  setStatus();
  renderNav();
  renderDbMeta();
  renderOpener();
}

/* Open an ArrayBuffer as the database, read its metadata and hand over to the views. */
function openBytes(buffer, name) {
  return engineReady().then((sql) => {
    const db = new sql.Database(new Uint8Array(buffer));
    db.exec('SELECT 1');
    DB = db;
    dbError = null;
    ready = true;
    meta.file = name;
    meta.bytes = buffer.byteLength;
    try {
      loadMeta();
    } catch (e) {
      db.close();
      throw e;
    }
    state.table = TBL.has(DEFAULT_PIVOT.table) ? DEFAULT_PIVOT.table : meta.tables[0].table;
    state.pivot = defaultPivot(state.table);
    state.browse = {page: 0, sort: null, dir: 'asc', q: ''};
    shellKey = '';
    setStatus();
    renderDbMeta();
    renderNav();
    applyHash();
  });
}

function openFile(file) {
  setStatus('reading ' + file.name);
  file.arrayBuffer()
    .then((buf) => openBytes(buf, file.name))
    .catch((e) => failOpen('Could not open ' + file.name + ': ' + e.message));
}

function boot() {
  renderLegend();
  renderDbMeta();
  renderNav();
  renderOpener();
  if (location.protocol === 'file:') {
    /* A page opened from disk may not read the file beside it, but it may read the loopback
       server if one is running - so try that before asking the reader for anything. */
    setStatus('looking for a local server');
    const stop = new AbortController();
    const timer = setTimeout(() => stop.abort(), 2000);
    fetch(SERVED_DB, {cache: 'no-store', signal: stop.signal})
      .then((res) => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.arrayBuffer();
      })
      .then((buf) => { clearTimeout(timer); return openBytes(buf, DB_FILE); })
      .catch(() => {
        clearTimeout(timer);
        failOpen('This page was opened from the file system, where the browser blocks reading ' +
          DB_FILE + ' next to it, and no local server answered on port ' + SERVE_PORT + '.');
      });
    return;
  }
  setStatus('loading ' + DB_FILE);
  fetch(DB_FILE, {cache: 'no-store'})
    .then((res) => {
      if (!res.ok) throw new Error('HTTP ' + res.status + ' ' + res.statusText);
      return res.arrayBuffer();
    })
    .then((buf) => openBytes(buf, DB_FILE))
    .catch((e) => failOpen('Could not load ' + DB_FILE + ' from this directory: ' + e.message));
}

boot();
})();
</script>
</body>
</html>
"""


#: Any ``__NAME__`` token left in the rendered page is an unfilled placeholder.
PLACEHOLDER = re.compile(r"__[A-Z0-9_]+__")


def js(value: Any) -> str:
    """Serialise a build-time constant as a JavaScript literal.

    Keys are sorted and ``<`` is escaped, so the literal is deterministic between runs and can
    never close the surrounding ``<script>`` element early.

    Args:
        value: Any JSON-serialisable constant.

    Returns:
        The JSON text to paste into the page.
    """
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return blob.replace("<", "\\u003c")


def render() -> str:
    """Fill the template with the build-time constants.

    Returns:
        The complete HTML document.

    Raises:
        SystemExit: If a placeholder is left unfilled.
    """
    substitutions = {
        "__SQLJS_SRC__": SQLJS_DIR + "sql-wasm.js",
        "__SQLJS_SRI__": SQLJS_SRI,
        "__SQLJS_DIR__": SQLJS_DIR,
        "__SQLJS_VERSION__": SQLJS_VERSION,
        "__D3_SRC__": D3_SRC,
        "__D3_SRI__": D3_SRI,
        "__TOPOJSON_SRC__": TOPOJSON_SRC,
        "__TOPOJSON_SRI__": TOPOJSON_SRI,
        "__DB_FILE__": DB.name,
        "__SERVE_CMD__": SERVE_CMD,
        "__SERVE_PORT__": str(SERVE_PORT),
        "__SERVE_URL__": SERVE_URL,
        "__SERVED_DB__": SERVED_DB,
        "__DEFAULT_PIVOT__": js(DEFAULT_PIVOT),
        "__YEARLY_PIVOT__": js(YEARLY_PIVOT),
        "__STAGES__": js(list(STAGES)),
        "__DATASET_ORDER__": js(list(DATASET_ORDER)),
        "__MODEL_STEPS__": js([[label, list(prefixes)] for label, prefixes in MODEL_STEPS]),
    }
    html = TEMPLATE
    for token, value in substitutions.items():
        html = html.replace(token, value)
    left = PLACEHOLDER.search(html)
    if left is not None:
        raise SystemExit(f"unfilled placeholder in the template: {left.group(0)}")
    return html


def manifest_rows(db: Path) -> int:
    """Count the rows of the database's ``tables`` manifest.

    The page reads that manifest itself; the build only checks it is there, so a page is never
    written against a database the viewer cannot navigate.

    Args:
        db: Path to the automotive SQLite database.

    Returns:
        Number of rows in the ``tables`` manifest.

    Raises:
        SystemExit: If the database has no ``tables`` manifest or the manifest is empty.
    """
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tables'"
        ).fetchone()
        if present is None:
            raise SystemExit(f"{db} has no 'tables' manifest: run build_database.py first")
        rows: int = conn.execute('SELECT COUNT(*) FROM "tables"').fetchone()[0]
    finally:
        conn.close()
    if not rows:
        raise SystemExit(f"{db} lists no tables: is build_database.py still running?")
    return rows


def main() -> None:
    """Write data/auto/database/dashboard.html, the reader for the sibling SQLite database.

    Raises:
        SystemExit: If the database is missing or carries no ``tables`` manifest.
    """
    if not DB.exists():
        raise SystemExit(f"database not found: {DB}")
    rows = manifest_rows(DB)
    OUT.write_text(render(), encoding="utf-8")
    print(
        f"{DB.relative_to(REPO)}: {DB.stat().st_size / 1e6:.2f} MB, {rows} tables "
        "(read by the page at view time, not embedded)"
    )
    print(f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1024:.0f} KB")
    print(f"serve it with: {SERVE_CMD}  ->  {SERVE_URL}")


if __name__ == "__main__":
    main()
