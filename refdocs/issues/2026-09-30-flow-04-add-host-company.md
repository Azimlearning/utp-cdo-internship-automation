# Flow 4: Add Host Company into MasterList

> Sandbox workflow (D-08). Fix module: `tools/fixes/f04_add_host_company.py` (reuses flow 3's Try/Catch + Terminate). Detail of the pattern: `2026-09-30-flow-03-add-hc-supervisor.md`.

## Status

🔶 **Sandbox-tested, one check left for you (Teams alert wording).** 2026-09-30. Same sandbox method as flow 3: the Excel read is replaced by sample rows (it can't run without the production workbook), everything else is the real flow.

## What it does

PowerApp button → looks up the shared Teams config → RUNNING ×2 → reads the confirmed host-company table from the master-list Excel → for each row creates an item in the **Host Company** SharePoint list → COMPLETED ×2; a FAILED ×2 branch hangs off the last COMPLETED post. Structurally identical to flow 3 (same action names).

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 4.1 | **Failed runs are reported "Succeeded"** | **Observed** (baseline: all 3 runs Succeeded, incl. a failing loop and a failing read) | ✅ Try/Catch + Terminate |
| 4.2 | Partial write: a run that fails on row 2 has already saved row 1, with no report of how far it got | **Observed** (baseline list held 3 rows after `ok` + `rowfail`, "Test Company 1" twice) | 🔶 alert now names the failed step; no rollback |
| 4.3 | **No duplicate check**: rerunning writes every Excel row again (visible as "Test Company 1" saved twice) | **Observed** | ⬜ needs a CDO decision (skip or update?) |
| 4.4 | FAILED message names no step/error/link | Read | ✅ |
| 4.5 | FAILED branch also fires if only the COMPLETED Teams *message* fails | Read | ✅ alert now keyed to the real work |
| 4.6 | Excel file id and table id are hard-coded (`01QW2RL4GFFA…`, `{08F6F0A2-…}`) | Read (D-03) | ⬜ issue 2 |

## Test results

| Case | Package | Result |
|---|---|---|
| ok | baseline | Succeeded, 2 rows |
| rowfail (2nd row too long to save) | baseline | **Succeeded** (false green) + row 1 saved |
| readfail (read step errors) | baseline | **Succeeded** (false green) |
| ok | fixed | Succeeded |
| rowfail | fixed | Try failed on `Create_item` (iteration 1 of 2) → **Catch ✓ (4 actions)** → **Terminate ✓** → run **Failed**. Screenshot `evidence/flow-04/01-…` |
| readfail | fixed | run **Failed** (Catch not opened separately; identical path to flow 3, where it was checked) |

**Not confirmed:** wording of the two FAILED alerts in Teams (only that the Teams actions in Catch were green).

### Real-Excel sandbox run (2026-10-06)

Same method as [flow 3](2026-09-30-flow-03-add-hc-supervisor.md#real-excel-sandbox-run-baselinex--fixedx-2026-10-06): real Excel read of a generated workbook (`Rows_for_Flow4_*.xlsx`, table `Rows`); items go to the sandbox Host Company list. `ok`: both packages create 2 items. `readfail` (missing workbook): baselinex **Succeeded** (false success), fixedx **Failed** at `List_rows_present_in_a_table`. `rowfail` (2nd company name 300 characters): both write 1 item and fail on the 2nd; baselinex stays **Succeeded**, fixedx **Failed** at `Create_item`. All six in `evidence/flow-04/results/`. **Still not tested:** the production workbook, ids and table GUID (office).

## Office steps (when convenient; no deadline pressure)

1. Back up flow 4 into `flows/` and commit.
2. Follow the flow 3 office steps (wrap `List rows` + `Apply to each` in a Try scope; Catch with two Filter arrays and the two FAILED posts plus detail block; Terminate Failed), or import `build/prod/flow04-prod.zip` with **Update** and re-select connections.
3. Test with a one-row Excel table in the CDO test window.
