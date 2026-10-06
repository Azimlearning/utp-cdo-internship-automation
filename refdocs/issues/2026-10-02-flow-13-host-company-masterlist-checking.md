# Flow 13: Host Company Info MasterList Checking

> Sandbox workflow (D-08/D-09). Fix module: `tools/fixes/f13_host_company_masterlist_checking.py`, a sibling of flow 12 (`f12_…`); same Try/Catch + Terminate wrapper. Read [flow 12's doc](2026-10-02-flow-12-hc-supervisor-masterlist-checking.md) for the shared description and the nested-loop alert limit.

## Status

🔶 **Sandbox-tested twice: with Excel stubbed, then again with real Excel Online reads/writes/attachment (only the two Office Scripts stay stubbed). One check left for you (Teams alert wording); the production template/ids need an office run.** 2026-10-02. Same design and the same results as flow 12.

## What it does

Same as flow 12 with host-company fields: two Office Script runs clear the Host Company MasterList template's result tables → every file in `MasterList_RawData_ToBeProcess` is read (`Database` table) → each row is compared with the Host Company SharePoint list (type of host, placement, organisation and industry type, street, city, postcode, state) → written to the template as Matched / Partially Not Matched / Exactly Not Matched → 30 s wait → each file triggers a PIC email with the template → COMPLETED ×2; FAILED ×2.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 13.1 | **A failed run reports "Succeeded"** (script step failed, or a row write failed deep in the nested loops) | **Observed** (scriptfail, addfail) | ✅ Try/Catch + Terminate |
| 13.2 | **Partial write with no report:** the exact and partial rows were written, the new-company row failed, the PIC got no email, the run showed Succeeded | **Observed** (addfail baseline) | 🔶 alert only; no rollback |
| 13.3 | **Every file in the folder is processed and emailed separately** (2 files → every row classified twice, 2 PIC emails) | **Observed** (twofiles, folder listing stubbed) | ⬜ check real folder contents; decision |
| 13.4 | Classification on stub data: identical row → Matched, differing street → Partially Not Matched, unknown company → Exactly Not Matched (1 / 1 / 1); unchanged by the fix | **Observed** | ➖ logic left alone |
| 13.5 | **This flow and flow 4 share one workbook.** Flow 13 writes the *Exactly Not Matched* table (`{08F6F0A2…}`) of `Host Company MasterList Template.xlsx` (file `01QW2RL4GFFA…`); flow 4 reads that same table to create the SharePoint items. So a half-finished run of this flow followed by flow 4 imports only part of the new companies | Read (definitions) | ⬜ ordering/admin-guide note; see ISSUES-BY-FLOW X11 |
| 13.6 | Hard-coded drive-item id, Office Script id and table GUIDs; replacing the template file breaks both flows 13 and 4 silently | Read (D-03) | ⬜ issue 2 |
| 13.7 | Scripts clear the template first; a later failure leaves it cleared or half-filled | Read | ➖ admin-guide note |
| 13.8 | Fixed 30 s `Delay`; input needs a `Database` table with exact headers (`Host Company ` with a trailing space, `HC City / Town`, …) | Read | ➖ / ⬜ same family as flow 2.4 |
| 13.9 | The checks run on whatever is in the folder, i.e. flow 7's last output; running them without re-running flow 7 first uses stale data | Read + admin guide | ⬜ admin-guide note |
| 13.10 | FAILED alert had no detail; for a failure inside the nested loops it names `Apply_to_each_2` (the per-row loop), the run link finds the exact write | **Observed** | ✅ with that limit |

## Test results (sandbox)

Counts per loop iteration from the run. `Add_a_row_into_a_table` and `_2` write **Partially Not Matched**, `_3` and `_5` write **Matched**, `_4` writes **Exactly Not Matched** (the second table).

| Scenario | Package | Run status | Failed actions | Counts | Matches expectation | Result file |
|---|---|---|---|---|---|---|
| addfail | baseline | **Succeeded** | Add_a_row_into_a_table_4: Unable to process template language expressions in action 'Add_a_row_into_a_tabl | Add_a_row_into_a_table Succeeded=1, Skipped=1; Add_a_row_into_a_table_2 Skipped=3; Add_a_row_into_a_table_3 Succeeded=1, Skipped=1; Add_a_row_into_a_table_4 Failed=1, Skipped=2; Add_a_row_into_a_table_5 Skipped=3; Send_an_email_(V2)  | ✅ | `results/addfail-baseline.json` |
| addfail | fixed | **Failed** | Add_a_row_into_a_table_4: Unable to process template language expressions in action 'Add_a_row_into_a_tabl | Add_a_row_into_a_table Succeeded=1, Skipped=1; Add_a_row_into_a_table_2 Skipped=3; Add_a_row_into_a_table_3 Succeeded=1, Skipped=1; Add_a_row_into_a_table_4 Failed=1, Skipped=2; Add_a_row_into_a_table_5 Skipped=3; Send_an_email_(V2)  | ✅ | `results/addfail-fixed.json` |
| ok | baseline | **Succeeded** | — | Add_a_row_into_a_table Succeeded=1, Skipped=1; Add_a_row_into_a_table_2 Skipped=3; Add_a_row_into_a_table_3 Succeeded=1, Skipped=1; Add_a_row_into_a_table_4 Succeeded=1, Skipped=2; Add_a_row_into_a_table_5 Skipped=3; Send_an_email_(V2) Succeeded=1 | ✅ | `results/ok-baseline.json` |
| ok | fixed | **Succeeded** | — | Add_a_row_into_a_table Succeeded=1, Skipped=1; Add_a_row_into_a_table_2 Skipped=3; Add_a_row_into_a_table_3 Succeeded=1, Skipped=1; Add_a_row_into_a_table_4 Succeeded=1, Skipped=2; Add_a_row_into_a_table_5 Skipped=3; Send_an_email_(V2) Succeeded=1 | ✅ | `results/ok-fixed.json` |
| readfail | fixed | **Failed** | Get_items | Add_a_row_into_a_table ; Add_a_row_into_a_table_2 ; Add_a_row_into_a_table_3 ; Add_a_row_into_a_table_4 ; Add_a_row_into_a_table_5  | ✅ | `results/readfail-fixed.json` |
| scriptfail | baseline | **Succeeded** | Run_script: Unable to process template language expressions in action 'Run_script' inputs at | Add_a_row_into_a_table ; Add_a_row_into_a_table_2 ; Add_a_row_into_a_table_3 ; Add_a_row_into_a_table_4 ; Add_a_row_into_a_table_5 ; Send_an_email_(V2)  | ✅ | `results/scriptfail-baseline.json` |
| scriptfail | fixed | **Failed** | Run_script: Unable to process template language expressions in action 'Run_script' inputs at | Add_a_row_into_a_table ; Add_a_row_into_a_table_2 ; Add_a_row_into_a_table_3 ; Add_a_row_into_a_table_4 ; Add_a_row_into_a_table_5 ; Send_an_email_(V2)  | ✅ | `results/scriptfail-fixed.json` |
| twofiles | baseline | **Succeeded** | — | Add_a_row_into_a_table Succeeded=2, Skipped=2; Add_a_row_into_a_table_2 Skipped=6; Add_a_row_into_a_table_3 Succeeded=2, Skipped=2; Add_a_row_into_a_table_4 Succeeded=2, Skipped=4; Add_a_row_into_a_table_5 Skipped=6; Send_an_email_(V2) Succeeded=2 | ✅ | `results/twofiles-baseline.json` |
| twofiles | fixed | **Succeeded** | — | Add_a_row_into_a_table Succeeded=2, Skipped=2; Add_a_row_into_a_table_2 Skipped=6; Add_a_row_into_a_table_3 Succeeded=2, Skipped=2; Add_a_row_into_a_table_4 Succeeded=2, Skipped=4; Add_a_row_into_a_table_5 Skipped=6; Send_an_email_(V2) Succeeded=2 | ✅ | `results/twofiles-fixed.json` |

## Real-Excel sandbox run (`baselinex` / `fixedx`, 2026-10-02)

Same method as [flow 12](2026-10-02-flow-12-hc-supervisor-masterlist-checking.md): real Excel Online reads the generated raw workbook (`Database` table) and writes the generated Host Company template, which is attached to the PIC email for real (To/Cc forced to you). Only the two Office Scripts are stubbed.

| Scenario | Package | Run status | What happened | Result file |
|---|---|---|---|---|
| ok | baselinex | **Succeeded** | Downloaded template: `HostCompany` Matched 2 / Partially Not Matched 1, `ExactlyNotMatched` 1; 1 email with the real attachment | `results/ok-baselinex.json` |
| ok | fixedx | **Succeeded** | identical | `results/ok-fixedx.json` |
| excelfail (raw-file path does not exist) | baselinex | **Succeeded** | `List_rows_present_in_a_table` failed for real, FAILED Teams posts sent, **run history says Succeeded** | `results/excelfail-baselinex.json` |
| excelfail | fixedx | **Failed** (`Terminated`) | run error `Host Company MasterList Checking failed at: List_rows_present_in_a_table`; both FAILED posts sent | `results/excelfail-fixedx.json` |
| *unplanned* two files, wrong columns | baselinex | **Succeeded** | A leftover flow 12 raw file (HC Supervisor columns) was still in the shared folder because Excel Online had it locked, so the runner could not delete it. Flow 13 read it first: `trim()` failed on all 4 rows of that file (`Filter_array_-_Host_company_name`), the FAILED Teams posts went out (seen in Teams at 19:58), and **run history still said Succeeded**. The second, correct file was processed normally | `results/twofiles-wrongcolumns-realexcel-baselinex.json` |

The unplanned run is a good picture of finding 13.3 (every file in the folder is processed): a stray file with different columns does not stop the flow, it fails inside the loop, and without the fix the run still shows green. The test runner now refuses to start a run if it cannot empty the folder (`prepareFiles` in `tools/sandbox/commands.js`).

**What the real-Excel runs show about the Teams alerts:** the baseline sends *RUNNING ×2* then *FAILED ×2* (the screenshot you sent); the fixed flow sends the same posts but now they carry the failed step, the error and the run link, and run history says Failed.

## Still stubbed / unproven

Both Office Scripts, and everything against the production templates, folder and ids. Real in the sandbox: the Host Company SharePoint list, every Condition and loop, Excel reads/writes/attachment, Teams, the PIC email (to you only).

## Office steps

1. Back up flow 13 into `flows/` and commit.
2. Wrap `Run script`, `Run script 2`, `Get files`, `Get items`, `Apply to each`, `Delay` and `Apply to each 4` in `Try - Check host companies` (variable initialisations stay above it); Catch/Terminate as in flow 3. Or import `build/prod/flow13-prod.zip` with **Update**.
3. Test on a **copy** of the Host Company template and a folder holding exactly **one** small test file; confirm the three buckets and one PIC email. Run flow 7 first.
