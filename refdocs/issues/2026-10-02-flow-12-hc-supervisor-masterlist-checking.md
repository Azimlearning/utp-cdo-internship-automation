# Flow 12: HC Supervisor Info MasterList Checking

> Sandbox workflow (D-08/D-09). Fix module: `tools/fixes/f12_hc_supervisor_masterlist_checking.py`, using the shared `tools/fixes/trycatch.py`.

## Status

🔶 **Sandbox-tested twice: with Excel stubbed, then again with real Excel Online reads/writes/attachment (only the two Office Scripts stay stubbed). One check left for you (Teams alert wording); the production template/ids need an office run.** 2026-10-02.

## What it does

PowerApp button → RUNNING ×2 → two Office Script runs clear the result tables in the HC Supervisor MasterList template → lists **every file** in `MasterList_RawData_ToBeProcess` (the folder flow 7 writes into) → for each file reads its `Database` table and compares every row with the HC Supervisor SharePoint list → writes each row into the template as **Matched** / **Partially Not Matched** / **Exactly Not Matched** → waits 30 s → **for each file** emails the PIC the template → COMPLETED ×2; FAILED ×2 hangs off the COMPLETED posts.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 12.1 | **A failed run reports "Succeeded".** Script step failed, or a row write failed deep in the nested loops: COMPLETED skipped, generic FAILED posts sent, header "ran successfully" | **Observed** (scriptfail, addfail) | ✅ Try/Catch + Terminate |
| 12.2 | **Partial write with no report:** when the "new supervisor" row write failed, the exact and partial rows had already been written, no email went to the PIC, and the run still showed Succeeded | **Observed** (addfail baseline: 1 + 1 rows written, 1 failed, 0 emails) | 🔶 alert now says the run failed; no rollback |
| 12.3 | **Every file in the folder is processed, and each one triggers its own PIC email.** With 2 files every row is classified twice and the PIC gets 2 emails; old files left in the folder would be re-appended each run | **Observed** (twofiles, with the folder listing stubbed: 2 files → 2× every bucket, 2 emails) | ⬜ needs the real folder contents checked (does anything clean it?) and a decision |
| 12.4 | Classification as run on stub data: exact row → *Matched*, differing position → *Partially Not Matched*, name not in the list → *Exactly Not Matched* (1 / 1 / 1). The fix does not change it (fixed `ok` gives identical counts) | **Observed** | ➖ logic left alone |
| 12.5 | The two scripts **clear the template tables first**; any later failure leaves the template cleared or half-filled with no cleanup | Read (and `scriptfail` shows that nothing after the failed script step ran) | ➖ alert only; admin-guide note |
| 12.6 | The template, Office Script and table ids are hard-coded (file `01QW2RL4CH7R…`, script `01HL57H3NEO…`, tables `{05D719C3…}` / `{CB10AEA9…}`) | Read (D-03) | ⬜ issue 2 |
| 12.7 | Fixed 30 s `Delay` instead of checking that the writes are done | Read | ➖ |
| 12.8 | The input file must have a table named `Database` with exact header names (`HC SV Name`, `HC SV Designation/Position`, …); otherwise the read fails | Read | ⬜ same family as flow 2.4 |
| 12.9 | FAILED alert had no step/error/link; for a failure inside the nested loops it now names `Apply_to_each_2` (the per-row loop) rather than the single Excel write, because Power Automate cannot reference an action nested that deep from the Catch; the run link leads to it | **Observed** | ✅ with that limit |
| 12.10 | **This flow and flow 3 share one workbook.** Flow 12 writes the *Exactly Not Matched* table (`{CB10AEA9…}`) of `HC Supervisor MasterList Template.xlsx`; flow 3 reads that same table to create the SharePoint items, so a half-finished run here followed by flow 3 imports only part of the new supervisors | Read (definitions) | ⬜ admin-guide note; see ISSUES-BY-FLOW X11 |

## Test results (sandbox)

Counts are per loop iteration, read from the run (the five `Add_a_row_…` actions are the Excel row writes, stubbed as Composes. From the definition: `Add_a_row_into_a_table` and `_2` write **Partially Not Matched**, `_3` and `_5` write **Matched**, `_4` writes **Exactly Not Matched** into the second table).

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

Same flow, but with **real Excel Online** against generated workbooks in the sandbox OneDrive (`testdata/`): the raw file's `Database` table is read for real, all five row writes go into the real template, the template is read and attached to the PIC email for real (To/Cc forced to you). Still stubbed: the two Office Scripts (their ids belong to the account that owns the production template) and the folder listing is real.

| Scenario | Package | Run status | What happened | Result file |
|---|---|---|---|---|
| ok | baselinex | **Succeeded** | 4 rows read; the downloaded template holds `HCSupervisor` Matched 2 / Partially Not Matched 1 and `SVExactlyNotMatched` 1, i.e. one row of each kind plus the lower-case/trailing-space duplicate matched as the same supervisor; 1 email with the real attachment | `results/ok-baselinex.json` |
| ok | fixedx | **Succeeded** | identical counts and workbook contents; the fix does not change the behaviour | `results/ok-fixedx.json` |
| excelfail (raw-file path does not exist) | baselinex | **Succeeded** | `List_rows_present_in_a_table` failed for real, the FAILED Teams posts went out, **run history says Succeeded** | `results/excelfail-baselinex.json` |
| excelfail | fixedx | **Failed** (`Terminated`) | same real failure; run error `HC Supervisor MasterList Checking failed at: List_rows_present_in_a_table`; both FAILED posts carry step/error/link | `results/excelfail-fixedx.json` |

So 12.1 is now **proven with a real Excel failure**, not only with a forced error, and 12.4 with real Excel reads and writes. Finding 12.3 got a second real-world demonstration: see flow 13's `twofiles-wrongcolumns-realexcel-baselinex.json`, where a flow 12 raw file was left in the shared folder and flow 13 read it first, failed on every row, and reported "Succeeded".

**Operational note from this run (applies to the office dry run too):** after Power Automate or Excel Online touches a workbook, Excel Online holds a lock on it for about 8 minutes (HTTP 423 on delete or overwrite). Wait before replacing or clearing the files, or the next run reads stale content.

## Still stubbed / unproven

Both Office Scripts (the template tables are not cleared by a real script, so the test starts from a fresh template each run), and the run's behaviour against the *production* templates, folder contents and ids. Real in the sandbox: the HC Supervisor SharePoint list, every Condition and loop, Excel reads/writes/attachment, Teams, the PIC email (sent to you only).

## Office steps

1. Back up flow 12 into `flows/` and commit.
2. Wrap `Run script`, `Run script 2`, `Get files`, `Get items`, `Apply to each`, `Delay` and `Apply to each 4` in `Try - Check HC supervisors` (variable initialisations stay above it); Catch/Terminate as in flow 3. Or import `build/prod/flow12-prod.zip` with **Update**.
3. Test on a **copy** of the template and a folder holding exactly **one** small test file; confirm the three buckets and one PIC email. Run flow 7 first: this flow reads its output.
