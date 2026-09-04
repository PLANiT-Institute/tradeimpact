"""Build the single-file HTML dashboard over the automotive SQLite database.

Reads ``data/auto/tradeimpact_auto.sqlite``, base64-embeds the whole database file into a
self-contained HTML page and writes ``data/auto/dashboard.html``. The bytes are gzipped before
they are base64-encoded (the database is mostly text and compresses about six-fold) and the
page inflates them with the browser's native ``DecompressionStream``. It then opens them with
sql.js (WebAssembly, loaded from a version-pinned CDN) and offers four views: lineage, pivot,
browse and free-text read-only SQL.

The ``tables`` manifest, the ``columns`` dictionary, the source registry and the raw-file
provenance are also embedded as JSON, so the navigation, the lineage flow and the source links
render immediately and still render when the CDN is unreachable.

The build is deterministic: nothing time-dependent is written, every query is ordered and every
JSON object is emitted with sorted keys. Stdlib only.

Run from the repository root:  .venv/bin/python script/auto/model/build_dashboard.py
"""

from __future__ import annotations

import base64
import gzip
import json
import sqlite3
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DB = REPO / "data" / "auto" / "tradeimpact_auto.sqlite"
OUT = REPO / "data" / "auto" / "dashboard.html"

#: sql.js pinned on cdnjs; ``locateFile`` resolves sql-wasm.wasm inside the same directory.
SQLJS_VERSION = "1.10.3"
SQLJS_DIR = f"https://cdnjs.cloudflare.com/ajax/libs/sql.js/{SQLJS_VERSION}/"
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
    ("3 reference", ("destination_parameters", "reference_trajectories")),
    ("4 impact", ("ti_by_model", "ti_annual", "ti_withheld")),
    ("4b crossover and sensitivity", ("ti_crossover", "ti_sensitivity")),
    ("5 aggregates and data quality", ("ti_country", "ti_powertrain", "ti_company", "ti_data")),
)

#: The pivot the "Results" navigation entry lands on: results by vehicle model and powertrain
#: (the company roll-up is one click away in the same pivot by removing the row fields).
DEFAULT_PIVOT = {
    "agg": "sum",
    "cols": "scenario",
    "rows": ["company", "powertrain", "model"],
    "table": "ti_by_model_eu27",
    "vals": ["ti_tco2e"],
}


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trade Impact - automotive database</title>
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
</style>
</head>
<body>
<header class="topbar">
  <h1>Trade Impact <span class="sub">automotive database</span></h1>
  <div class="status" id="status">loading the SQL engine</div>
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
<script type="application/json" id="manifest">__MANIFEST__</script>
<script type="application/octet-stream" id="dbb64">__DB_B64__</script>
<script
  src="__SQLJS_SRC__"
  integrity="__SQLJS_SRI__"
  crossorigin="anonymous"
  referrerpolicy="no-referrer"
  onerror="window.__sqljsFailed = true;"></script>
<script>
(function () {
'use strict';

const M = JSON.parse(document.getElementById('manifest').textContent);
const TBL = new Map(M.tables.map((t) => [t.table, t]));
const COLS = M.columns;
const CDN_DIR = '__SQLJS_DIR__';
const SEP = String.fromCharCode(1);
const VIEWS = [
  {id: 'lineage', label: 'Lineage'},
  {id: 'results', label: 'Results'},
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

let DB = null;
let dbError = null;
let shellKey = '';
let debounce = null;

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
  return COLS[table] || [];
}

function isNumeric(table, column) {
  const c = colsOf(table).filter((x) => x.column === column)[0];
  return !!c && (c.sqlite_type === 'INTEGER' || c.sqlite_type === 'REAL');
}

function defaultPivot(table) {
  const d = M.default;
  if (table === d.table) {
    return {rows: d.rows.slice(), cols: d.cols, vals: d.vals.slice(), agg: d.agg,
      filters: [], sort: null};
  }
  const cs = colsOf(table);
  const dims = cs.filter((c) => c.sqlite_type === 'TEXT').map((c) => c.column);
  const nums = cs.filter((c) => c.sqlite_type !== 'TEXT').map((c) => c.column);
  return {rows: dims.slice(0, 1), cols: '', vals: nums.slice(0, 1), agg: 'sum',
    filters: [], sort: null};
}

const state = {
  view: 'lineage',
  table: M.default.table,
  pivot: defaultPivot(M.default.table),
  browse: {page: 0, sort: null, dir: 'asc', q: ''},
  sql: {text: 'SELECT company, powertrain, model, scenario,\n'
        + '       SUM(units) AS units, SUM(ti_tco2e) AS ti_tco2e\n'
        + '  FROM ti_by_model_eu27\n GROUP BY 1, 2, 3, 4\n ORDER BY 1, 2, 3, 4'},
  tsv: ''
};

function errBox(msg) {
  return '<div class="err">' + esc(msg) + '</div>';
}

function engineBox() {
  const why = dbError || 'The SQL engine has not finished loading.';
  return errBox(why + ' The lineage view still works from the embedded manifest.');
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

function setStatus() {
  const el = document.getElementById('status');
  const mb = (M.db_bytes / 1e6).toFixed(2) + ' MB';
  const gz = (M.gz_bytes / 1e6).toFixed(2) + ' MB';
  if (dbError) {
    el.className = 'status bad';
    el.textContent = 'SQL engine unavailable - lineage only (' + gz + ' embedded)';
    return;
  }
  el.className = 'status';
  el.textContent = DB
    ? 'sql.js ' + M.sqljs_version + ' - ' + M.tables.length + ' tables - ' + mb +
      ' database, ' + gz + ' embedded'
    : 'loading the SQL engine';
}

function renderNav() {
  document.getElementById('nav').innerHTML = VIEWS.map((v) => {
    const on = v.id === state.view;
    return '<button class="navlink" data-view="' + v.id + '"' +
      (on ? ' aria-current="page"' : '') + '>' + esc(v.label) + '</button>';
  }).join('');
}

function renderLegend() {
  const items = M.stages.concat(['registry']);
  document.getElementById('legend').innerHTML = items
    .map((s) => '<li><span class="chip chip-' + s + '">' + esc(s) + '</span></li>')
    .join('');
}

function renderDbMeta() {
  const rows = M.tables.reduce((a, t) => a + (t.rows || 0), 0);
  const cols = Object.keys(COLS).reduce((a, k) => a + COLS[k].length, 0);
  const parts = [
    ['tables', fmtInt(M.tables.length)],
    ['rows', fmtInt(rows)],
    ['columns', fmtInt(cols)],
    ['sources', fmtInt(M.sources.length)],
    ['size', (M.db_bytes / 1e6).toFixed(2) + ' MB']
  ];
  document.getElementById('dbmeta').innerHTML = parts
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
  for (const d of M.datasets) {
    h += '<section class="card"><h2>' + esc(d.dataset) + '</h2>';
    const anyStage = M.stages.some((s) => d.stages[s].length);
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
      M.stages.forEach((s, i) => {
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

/* ---------- table selector and column panel ---------- */

function tableSelect() {
  let h = '<select id="tablesel" aria-label="Table">';
  const seen = [];
  for (const t of M.tables) {
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
    '<p class="muted">One SELECT or WITH statement against the embedded database. ' +
    'Nothing is written back: the database in the page is a copy held in memory.</p>' +
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

/* ---------- routing and rendering ---------- */

function render() {
  const key = state.view + '|' + state.table;
  if (key !== shellKey) {
    shellKey = key;
    if (state.view === 'pivot') renderPivotShell();
    else if (state.view === 'browse') renderBrowseShell();
    else if (state.view === 'sql') renderSqlShell();
    else renderLineage();
  }
  if (state.view === 'pivot') renderPivotOut();
  else if (state.view === 'browse') renderBrowseOut();
  else if (state.view === 'sql') renderSqlOut();
  renderNav();
}

function applyHash() {
  const raw = (location.hash || '#/lineage').replace(/^#\/?/, '');
  const parts = raw.split('/');
  const view = parts[0] || 'lineage';
  const table = parts[1] ? decodeURIComponent(parts[1]) : null;
  if (view === 'results') {
    state.table = M.default.table;
    state.pivot = defaultPivot(M.default.table);
    state.view = 'pivot';
    shellKey = '';
    go('#/pivot/' + encodeURIComponent(M.default.table));
    return;
  }
  if (['lineage', 'pivot', 'browse', 'sql'].indexOf(view) < 0) {
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
  if (v === 'results') go('#/results');
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

window.addEventListener('hashchange', applyHash);

/* ---------- boot ---------- */

/* The database is embedded gzipped; the browser inflates it natively. */
function dbBytes() {
  const b64 = document.getElementById('dbb64').textContent.trim();
  const bin = atob(b64);
  const packed = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) packed[i] = bin.charCodeAt(i);
  if (typeof DecompressionStream !== 'function') {
    return Promise.reject(new Error('this browser has no DecompressionStream (gzip)'));
  }
  const stream = new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Response(stream).arrayBuffer().then((buf) => new Uint8Array(buf));
}

function boot() {
  if (window.__sqljsFailed || typeof window.initSqlJs !== 'function') {
    dbError = 'sql.js ' + M.sqljs_version + ' could not be loaded from cdnjs (no network?).';
    setStatus();
    render();
    return;
  }
  Promise.all([window.initSqlJs({locateFile: (f) => CDN_DIR + f}), dbBytes()]).then((r) => {
    DB = new r[0].Database(r[1]);
    setStatus();
    render();
  }).catch((e) => {
    dbError = 'The SQL engine failed to start: ' + e.message;
    setStatus();
    render();
  });
}

renderLegend();
renderDbMeta();
setStatus();
applyHash();
boot();
})();
</script>
</body>
</html>
"""


def has_table(conn: sqlite3.Connection, name: str) -> bool:
    """Return True when ``name`` exists as a table in the database.

    Args:
        conn: Open connection to the automotive database.
        name: Table name to look for.

    Returns:
        True if a table of that name exists.
    """
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def read_tables(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Read the ``tables`` manifest, ordered by stage then dataset then table name.

    Args:
        conn: Open connection to the automotive database.

    Returns:
        One dictionary per table with keys table, dataset, kind, source_path, rows, sha256.
    """
    order = "CASE kind WHEN 'raw' THEN 0 WHEN 'method' THEN 1 WHEN 'processed' THEN 2 "
    order += "WHEN 'output' THEN 3 ELSE 4 END"
    rows = conn.execute(
        f'SELECT "table", dataset, kind, source_path, rows, sha256 FROM "tables" '
        f'ORDER BY {order}, dataset, "table"'
    ).fetchall()
    return [
        {
            "table": r[0],
            "dataset": r[1],
            "kind": r[2],
            "source_path": r[3],
            "rows": r[4],
            "sha256": r[5] or "",
        }
        for r in rows
    ]


def derive_columns(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    """Describe one table's columns from PRAGMA table_info plus per-column counts.

    Used only when the ``columns`` dictionary table is absent; it reproduces the same fields.

    Args:
        conn: Open connection to the automotive database.
        table: Table to describe.

    Returns:
        One dictionary per column with keys column, sqlite_type, non_null, distinct, example.
    """
    out: list[dict[str, Any]] = []
    for _cid, col, ctype, *_rest in conn.execute(f'PRAGMA table_info("{table}")'):
        non_null, distinct, example = conn.execute(
            f'SELECT COUNT("{col}"), COUNT(DISTINCT "{col}"), '
            f'(SELECT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL LIMIT 1) FROM "{table}"'
        ).fetchone()
        out.append(
            {
                "column": col,
                "sqlite_type": ctype,
                "non_null": non_null,
                "distinct": distinct,
                "example": None if example is None else str(example)[:80],
            }
        )
    return out


def read_columns(conn: sqlite3.Connection, tables: list[dict[str, Any]]) -> dict[str, list[dict]]:
    """Read the ``columns`` dictionary, falling back to PRAGMA when the table is absent.

    The dictionary table names its distinct-count column ``distinct_values`` in the current
    builder and ``distinct`` in earlier ones; both are accepted and normalised to ``distinct``.
    Column order follows the physical table order (PRAGMA table_info), not the dictionary's.

    Args:
        conn: Open connection to the automotive database.
        tables: The manifest rows, used for the table list and their physical column order.

    Returns:
        Mapping of table name to its ordered list of column descriptions.
    """
    stored: dict[str, dict[str, dict[str, Any]]] = {}
    if has_table(conn, "columns"):
        names = [r[1] for r in conn.execute('PRAGMA table_info("columns")')]
        distinct_col = "distinct_values" if "distinct_values" in names else "distinct"
        sql = f'SELECT "table", "column", sqlite_type, non_null, "{distinct_col}", example '
        sql += 'FROM "columns"'
        for tname, col, ctype, non_null, distinct, example in conn.execute(sql):
            stored.setdefault(tname, {})[col] = {
                "column": col,
                "sqlite_type": ctype,
                "non_null": non_null,
                "distinct": distinct,
                "example": None if example is None else str(example)[:80],
            }

    out: dict[str, list[dict[str, Any]]] = {}
    for entry in tables:
        name = entry["table"]
        physical = [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')]
        if name in stored and all(c in stored[name] for c in physical):
            out[name] = [stored[name][c] for c in physical]
        else:
            out[name] = derive_columns(conn, name)
    return out


def read_sources(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Read the source registry ordered by source_id.

    Args:
        conn: Open connection to the automotive database.

    Returns:
        One dictionary per source with the registry's eight fields; empty when the table is
        absent, so a partially built database still produces a page.
    """
    if not has_table(conn, "sources"):
        return []
    rows = conn.execute(
        "SELECT source_id, publisher, title, url, how_obtained, accessed_date, license, used_by "
        'FROM "sources" ORDER BY source_id'
    ).fetchall()
    keys = (
        "source_id",
        "publisher",
        "title",
        "url",
        "how_obtained",
        "accessed_date",
        "license",
        "used_by",
    )
    return [dict(zip(keys, r, strict=True)) for r in rows]


def read_raw_files(
    conn: sqlite3.Connection, sources: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Read raw-file provenance per dataset with each file's sources resolved.

    ``raw_files.source_id`` holds one or more ids separated by semicolons; each is looked up in
    the source registry so the lineage view can render publisher, title, link and licence
    without a join at view time.

    Args:
        conn: Open connection to the automotive database.
        sources: The source registry as returned by :func:`read_sources`.

    Returns:
        Mapping of dataset name to its ordered list of raw-file descriptions; empty when the
        table is absent.
    """
    by_id = {s["source_id"]: s for s in sources}
    out: dict[str, list[dict[str, Any]]] = {}
    if not has_table(conn, "raw_files"):
        return out
    rows = conn.execute(
        'SELECT dataset, file, source_id, original_name, sha256, note FROM "raw_files" '
        "ORDER BY dataset, file"
    ).fetchall()
    for dataset, file, source_id, original_name, sha256, note in rows:
        ids = [s.strip() for s in (source_id or "").split(";") if s.strip()]
        resolved = [
            by_id.get(i, {"source_id": i, "publisher": "", "title": "", "url": ""}) for i in ids
        ]
        out.setdefault(dataset, []).append(
            {
                "file": file,
                "original_name": original_name or "",
                "sha256": (sha256 or "")[:12],
                "note": note or "",
                "sources": resolved,
            }
        )
    return out


def build_datasets(
    tables: list[dict[str, Any]], raw_files: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Group the manifest into per-dataset lineage cards.

    Each card carries the tables present at every stage, the raw files behind the dataset and,
    for the model dataset, the whitepaper step order 3 -> 4 -> 4b -> 5 over the output tables.

    Args:
        tables: The manifest rows.
        raw_files: Raw-file provenance keyed by dataset.

    Returns:
        One dictionary per dataset in :data:`DATASET_ORDER`, unknown datasets appended sorted.
    """
    names = sorted({t["dataset"] for t in tables} | set(raw_files))
    ordered = [d for d in DATASET_ORDER if d in names]
    ordered += [d for d in names if d not in DATASET_ORDER]

    cards: list[dict[str, Any]] = []
    for dataset in ordered:
        mine = [t for t in tables if t["dataset"] == dataset]
        stages = {stage: [t["table"] for t in mine if t["kind"] == stage] for stage in STAGES}
        registry = [t["table"] for t in mine if t["kind"] == "registry"]
        outputs = list(stages["output"])
        steps: list[dict[str, Any]] = []
        if dataset == "model" and outputs:
            taken: set[str] = set()
            for label, prefixes in MODEL_STEPS:
                hit = [t for p in prefixes for t in outputs if t.startswith(p)]
                taken |= set(hit)
                if hit:
                    steps.append({"label": label, "tables": hit})
            rest = [t for t in outputs if t not in taken]
            if rest:
                steps.append({"label": "other", "tables": rest})
        cards.append(
            {
                "dataset": dataset,
                "stages": stages,
                "registry": registry,
                "steps": steps,
                "raw_files": raw_files.get(dataset, []),
            }
        )
    return cards


def build_manifest(conn: sqlite3.Connection, db_bytes: int, gz_bytes: int) -> dict[str, Any]:
    """Assemble everything the page needs before the WASM engine is available.

    Args:
        conn: Open connection to the automotive database.
        db_bytes: Size of the database file, embedded for the status line.
        gz_bytes: Size of the gzipped database, embedded for the status line.

    Returns:
        The manifest dictionary that is serialised into the page as JSON.
    """
    tables = read_tables(conn)
    sources = read_sources(conn)
    return {
        "columns": read_columns(conn, tables),
        "datasets": build_datasets(tables, read_raw_files(conn, sources)),
        "db_bytes": db_bytes,
        "gz_bytes": gz_bytes,
        "default": DEFAULT_PIVOT,
        "sources": sources,
        "sqljs_version": SQLJS_VERSION,
        "stages": list(STAGES),
        "tables": tables,
    }


def render(manifest: dict[str, Any], db_b64: str) -> str:
    """Fill the HTML template with the manifest JSON and the base64 database.

    ``<`` is escaped as ``\\u003c`` in the JSON so the embedded blob can never close the script
    element early; the base64 alphabet cannot contain ``<`` at all.

    Args:
        manifest: The manifest dictionary.
        db_b64: The gzipped database file, base64-encoded.

    Returns:
        The complete HTML document.
    """
    blob = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    blob = blob.replace("<", "\\u003c")
    html = TEMPLATE
    html = html.replace("__SQLJS_SRC__", SQLJS_DIR + "sql-wasm.js")
    html = html.replace("__SQLJS_SRI__", SQLJS_SRI)
    html = html.replace("__SQLJS_DIR__", SQLJS_DIR)
    html = html.replace("__MANIFEST__", blob)
    html = html.replace("__DB_B64__", db_b64)
    return html


def main() -> None:
    """Read the database, embed it and write data/auto/dashboard.html."""
    if not DB.exists():
        raise SystemExit(f"database not found: {DB}")
    raw = DB.read_bytes()
    # mtime=0 keeps the gzip header, and so the whole page, byte-identical between runs.
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        if not has_table(conn, "tables"):
            raise SystemExit(f"{DB} has no 'tables' manifest: run build_database.py first")
        manifest = build_manifest(conn, len(raw), len(packed))
    finally:
        conn.close()
    if not manifest["tables"]:
        raise SystemExit(f"{DB} lists no tables: is build_database.py still running?")
    html = render(manifest, base64.b64encode(packed).decode("ascii"))
    OUT.write_text(html, encoding="utf-8")
    n_tables = len(manifest["tables"])
    n_cols = sum(len(v) for v in manifest["columns"].values())
    print(
        f"{DB.relative_to(REPO)}: {len(raw) / 1e6:.2f} MB, {n_tables} tables, {n_cols} columns; "
        f"gzipped to {len(packed) / 1e6:.2f} MB"
    )
    print(f"{OUT.relative_to(REPO)}: {OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
