# data/

Copies of the project input workbooks (the data contract the loaders read):

- `TI_Data_Workbook_v0.1.xlsx` — the integrated data-collection template. Mostly empty
  ("TO COLLECT"); load with `ti_framework.io.workbook.load_workbook_inputs`.
- `TI_CaseStudy_Reference_DB_v0.1.xlsx` — seed reference values (real Ember-2024 grid
  intensities, NDC headline targets, economy-wide rates); load with `load_reference_db`.

These are templates: the engine runs on partial data and marks every uncollected input as
missing rather than fabricating a default. For a fully-runnable case see
`../fixtures/reference_case.json`.

Inspect:
```
ti run --workbook data/TI_Data_Workbook_v0.1.xlsx
```
