# Flow 3 — Add HC Supervisor into MasterList

> Per-flow review under the sandbox workflow (D-08). Package: `flows/[LIVE-CDO] UTPCSDCDO Add HC Supervisor into MasterList.zip`. Fix module: `tools/fixes/f03_add_hc_supervisor.py`. Tiers: `../guides/methodology.md`.

## Status

🔶 **Sandbox-tested; one check left for you (the alert text in Teams).** 2026-09-30. The Excel read can't run in a sandbox (bound to production file IDs), so the sandbox copies swap **only that one action** for a `Compose` of sample rows and use a list-item trigger. Everything else (the Teams config lookup, the RUNNING/COMPLETED/FAILED posts, the `Create_item` writes) is the real flow.

## What the flow does

Started from the PowerApp button. Looks up the shared Teams config item → posts "RUNNING" ×2 → reads the confirmed-supervisor table from the master-list Excel → for each row, creates an item in the **HC Supervisor** SharePoint list → posts "COMPLETED" ×2. A "FAILED" ×2 branch hangs off the last COMPLETED post. (×2 because it messages both `TeamsNotification1` and `TeamsNotification2`.)

## Findings

| # | Finding | Tier | Impact |
|---|---|---|---|
| 3.1 | **A failed run is reported as "Succeeded" in run history.** Sandbox baseline, "rowfail" scenario: `Apply to each` failed, the COMPLETED posts were skipped, and Power Automate's banner still read **"Your flow ran successfully."** All three baseline runs (including both failure scenarios) showed **Succeeded**. | **T3 → observed** | Anyone (or any monitoring) that reads run history sees green while the work failed. Because the same "FAILED-post at the end" pattern is used in **12 flows**, this very likely applies to all of them. Evidence: `evidence/flow-03/01-baseline-run-says-succeeded.png` |
| 3.2 | **Partial writes.** "rowfail": row 1 was written to the HC Supervisor list, row 2 failed, and nothing rolls back or reports how far it got. | **T3 → observed** | A retry (staff re-clicking the button) writes row 1 **again**, since nothing checks for duplicates (3.4). |
| 3.3 | The FAILED message says only "…process is FAILED!": no step, no reason, no run link. | T1 | Staff must open Power Automate and hunt for the failed run. |
| 3.4 | The flow always writes every Excel row as a new item (`Create_item`, no lookup/upsert). | T1 | Running it twice on the same table duplicates supervisors. Not changed here (behaviour change); flagged. |
| 3.5 | The FAILED branch hangs off the **last COMPLETED post** (`Failed/Skipped/TimedOut`), so it would also fire if only the COMPLETED Teams *message* failed, while the data was written fine. | T1 | Misleading "FAILED" for a successful process. Fixed by keying the alert to the real work instead. |
| 3.6 | The Excel file, drive and table are hard-coded IDs (`01QW2RL4CH7R…`, table `{CB10AEA9-…}`). | T1 | The D-03 / issue 2 fragility. **Not touched here.** |

## Fix

```
Get item → RUNNING ×2 (unchanged)
Try – Add HC Supervisors  (Scope)
    List rows present in a table (Excel)     ← unchanged
    Apply to each → Create item              ← unchanged
COMPLETED ×2       runs only if Try succeeded
Catch – Alert CDO staff  (Scope, runs if Try Failed/TimedOut)
    Filter array – failed in loop            ← result('Apply_to_each') where status = Failed
    Filter array – failed at top level       ← result('Try') where status = Failed
    FAILED post (TeamsNotification1)         ← existing text + Failed step + Error + Open this run
    FAILED post (TeamsNotification2)         ← same
Terminate – Failed  (AddHCSupervisorFailed)  ← so run history says Failed
```

The original message text and the two-recipient pattern are kept; only the detail and the run status change. `python tools/build.py 3 prod` builds it against the real flow (manual PowerApp trigger and Excel reference untouched).

## Sandbox test results — 2026-09-30

Sandbox pieces (your OneDrive site): list `CDO Sandbox - HC Supervisor` (same four internal column names as production), list `CDO Sandbox - Flow Run Trigger` (item title = scenario), sandbox flows `[SANDBOX-BASELINE]` `53b089b5-…` and `[SANDBOX-FIXED]` `f4a4cb93-…`. Scenarios: **ok** (2 good rows), **rowfail** (2nd row has a 300-char name; the column allows 255), **readfail** (the read step itself errors).

| # | Package | Scenario | Expected | Observed | Pass? |
|---|---|---|---|---|---|
| B1 | baseline | ok | Succeeded, 2 rows | Succeeded; 2 rows | ✅ |
| B2 | baseline | rowfail | (what does it report?) | **Run status Succeeded**; `Apply to each` failed, COMPLETED skipped; **row 1 written** | ❌ **finding 3.1 + 3.2 confirmed** |
| B3 | baseline | readfail | (what does it report?) | **Run status Succeeded** | ❌ finding 3.1 confirmed |
| F1 | fixed | ok | Succeeded, no alerts | Run **Succeeded** | ✅ |
| F2 | fixed (v1) | readfail | Catch runs, run Failed | Try failed on the read; loop + COMPLETED **skipped**; **Catch ✓** (reading the skipped loop's `result()` caused **no error**); Terminate ✓; banner names the exact step/error; run **Failed** | ✅ |
| F3 | fixed (v1) | rowfail | Catch alerts | ❌ **Bug:** both FAILED Teams posts **failed** inside Catch: `…['outputs']?['body'] … Array elements can only be selected using an integer index`. For a loop, each iteration's `outputs` is an *array*, and `?` does not protect against the wrong type | 🐞 found, fixed |
| F3b | fixed (**v2**) | rowfail | Catch alerts | Try failed on `Create_item` (row 2, "1 of 2" iterations) → **Catch ✓ (3 s, 4 actions)** → Terminate ✓ → run **Failed**; COMPLETED skipped. Evidence `02-fixed-rowfail-catch-ok.png` | ✅ |
| F2b | fixed (v2) | readfail | same as F2 | Run **Failed** (Catch not opened separately; the v2 change only alters the message expression) | ⚠️ run status only |

The v2 fix: the error text is read from `error.message` first, and `outputs.body.*` only when `outputs` is a JSON object (`startsWith(string(outputs), '{')`).

**Not yet confirmed (needs your eyes on Teams):** that the two FAILED alerts read well. Expected text: the original message + `Failed step: Create_item` + `Error: The API operation 'PostItem' requires the property 'item/HCSupervisorName' to be a string of maximum length '255' but is of length '300'.` + an "Open this run" link. **Please screenshot the newest FAILED alerts** (they'll be near the bottom of the *Workflows* chat, from ~07:12 AM for both rowfail and readfail).

## Real-Excel sandbox run (`baselinex` / `fixedx`, 2026-10-06)

Same flow, but the table read is **real Excel Online** against a generated workbook in the sandbox OneDrive (`testdata/Rows_for_Flow3_*.xlsx`, table `Rows`, the columns this flow reads); only the trigger is swapped. Created items land in the sandbox supervisor list.

| Scenario | Package | Run status | What happened | Result file |
|---|---|---|---|---|
| ok (2 rows) | baselinex | **Succeeded** | 2 items created | `results/ok-baselinex.json` |
| ok | fixedx | **Succeeded** | 2 items created (identical) | `results/ok-fixedx.json` |
| readfail (workbook does not exist) | baselinex | **Succeeded** | `List_rows_present_in_a_table` failed (`NotFound`), FAILED posts sent, **run history green** | `results/readfail-baselinex.json` |
| readfail | fixedx | **Failed** (`Terminated`) | "Add HC Supervisor failed at: List_rows_present_in_a_table"; 0 items | `results/readfail-fixedx.json` |
| rowfail (2nd row's name is 300 characters) | baselinex | **Succeeded** | 1 item created, `Create_item` failed on row 2 ("maximum length '255' but is of length '300'"), **partial write, run green** | `results/rowfail-baselinex.json` |
| rowfail | fixedx | **Failed** (`Terminated`) | same partial write (1 item), but run Failed naming `Create_item` | `results/rowfail-fixedx.json` |

So finding 1 is now proven with a real Excel read as well as with sample rows. The read of a missing file takes about 4 minutes to fail (the connector retries) before the run starts to report.

## Sandbox-only differences (so the sandbox result isn't over-read)

- The Excel read is a `Compose` of sample rows and the trigger is a list-item trigger. The **real** Excel action, and its failure modes (file moved, table renamed, script/permission errors), are **not** exercised. Catch is action-type-agnostic (`result('Try')`), so a real Excel failure should land in the top-level filter. That's a reasoned expectation, not a test.
- `Create_item` sets `Title` in the sandbox only, since the sandbox list's Title is required by the connector schema. Production doesn't set it.

## Not in scope / later

- 3.4 duplicates: a real fix needs a business decision (skip existing? update?). Raise with CDO.
- 3.6 Excel IDs: issue 2.
- **The same Try/Catch pattern applies to the other 11 flows with the same FAILED-post pattern.** This flow is the template (see FLOW-TRACKER cross-cutting).

## Office steps (after the Teams check)

1. Export a fresh backup of flow 3 into `flows/` and commit (rule 5).
2. In Studio (or import `build/prod/flow03-prod.zip` with **Update** and re-select connections):
   a. Select `List rows present in a table` **and** `Apply to each` → *Add to a scope* → name it `Try - Add HC Supervisors`.
   b. Point the two COMPLETED posts' *Configure run after* at that scope (**is successful** only).
   c. Add a scope `Catch - Alert CDO staff` after it (*Configure run after*: **has failed**, **has timed out**). Inside: two **Filter array** actions (from `result('Apply_to_each')` and `result('Try - Add HC Supervisors')`, condition `status equals Failed`), then move the two existing FAILED posts inside it and append the detail block. The exact expressions are in `f03_add_hc_supervisor.py` (`DETAIL_HTML`, `_msg`).
   d. Add **Terminate** (Failed) after Catch (run after: succeeded, failed, timed out).
3. **Test on real data** only in the CDO test window with staff aware; a real run writes real supervisors. A safe first test: run it with an Excel table that has 1 valid row. (Nothing forces a failure safely on real data; the sandbox has covered the failure paths.)
