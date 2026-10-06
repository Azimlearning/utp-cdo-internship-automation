# Flow 6: Clear Raw Database

> Sandbox workflow (D-08). Fix module: `tools/fixes/f06_clear_raw_database.py`, using the shared `tools/fixes/trycatch.py`.

## Status

🔶 **Sandbox-tested; one check left for you (Teams alert wording).** 2026-10-01. This is the first **destructive** flow tested; the sandbox run only ever deleted fake rows in your own sandbox list.

## What it does

PowerApp button → RUNNING ×2 → reads every item in the Report Duty Registration list → deletes each one → runs an Office Script that resets the `SummaryTable` in the master Excel → COMPLETED ×2. A FAILED ×2 branch hangs off the COMPLETED posts.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 6.1 | **A failed run reports "Succeeded".** The summary-reset step failed *after* all rows were deleted; the run header read "Your flow ran successfully" while the generic FAILED messages fired | **Observed** | ✅ Try/Catch + Terminate |
| 6.2 | **Half-cleared state:** the delete loop runs first and cannot be undone; if the Excel reset then fails, the registrations are gone but the summary still shows old numbers. Nothing tells staff the two are out of step | **Observed** (list went 5 → 0 while the script step failed) | 🔶 the alert now names the failed step; no rollback is possible after deletes, so the admin guide must say "if this alerts, reset the SummaryTable by hand before the next semester run" |
| 6.3 | The FAILED message has no step, error or link | Read | ✅ |
| 6.4 | The Excel file, drive and Office Script are hard-coded IDs (`01QW2RL4FS4E…`, script `01HL57H3M4…`) | Read (D-03) | ⬜ issue 2 |
| 6.5 | No confirmation before deleting everything (button press → immediate delete) | Read | ⬜ suggestion: confirm step in the PowerApp |
| 6.6 | Pagination is set to 100,000 so the delete covers the whole list | Read | ➖ **not a problem**, checked |

## Test results (sandbox)

| Case | Package | Result |
|---|---|---|
| scriptfail (5 rows, script stub errors) | baseline | list **5 → 0**; run **Succeeded** with the failed script visible but the header green. Evidence `evidence/flow-06/01-…` |
| scriptfail (5 rows) | fixed | list **5 → 0** (the delete still happens, as designed); Try failed on the script → **Catch ✓ (4 actions)** → **Terminate ✓** → run **Failed**; header names the step and error. Evidence `evidence/flow-06/02-…` |
| ok (3 rows) | fixed | list **3 → 0**, run **Succeeded**, no alerts |

**Not confirmed:** Teams alert wording. **Not tested:** the real Excel Office Script (stubbed).

## Office steps

1. Back up flow 6 into `flows/` and commit.
2. Wrap `Get items` + `Apply to each` + `Run script - Reset Summary Table` in `Try - Clear database`; Catch/Terminate as in flow 3. Or import `build/prod/flow06-prod.zip` with **Update**.
3. Test with a **copy** of the list and workbook only, never the live registrations.
