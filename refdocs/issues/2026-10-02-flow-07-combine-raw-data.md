# Flow 7: Combine raw data

> Sandbox workflow (D-08). Fix module: `tools/fixes/f07_combine_raw_data.py`, using the shared `tools/fixes/trycatch.py`.

## Status

🔶 **Sandbox-tested for the failure handling; the Excel parts and the concurrency fix are NOT testable in the sandbox.** 2026-10-02. Needs a real run at the office for the Excel steps (MANUAL-TODO C).

## What it does

PowerApp button → RUNNING ×2 → copies the `FinalizedHeader.xlsx` template into a new RawData workbook → for every student in the Student List, looks up their registrations and adds rows to the workbook with six different **Add a row** actions in nested loops (one per attachment, "Other" or not) → waits 30 s → runs an Office Script on the workbook → emails the PIC (to/cc from the config item) with the file → COMPLETED ×2 → copies the file into `MasterList_RawData_ToBeProcess` (the file flows 12 and 13 read). FAILED ×2 only hangs off that last copy step.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 7.1 | **A failed run reports "Succeeded".** Sandbox baseline: the Office Script step failed, the email and COMPLETED were skipped, the generic FAILED messages fired, header "Your flow ran successfully" | **Observed** | ✅ Try/Catch + Terminate |
| 7.2 | **The per-student loop writes rows into one workbook with default parallelism** (up to 20 iterations at once). Parallel Excel writes to one file are a classic cause of lost rows and "file locked" errors, and a plausible cause of the reported Excel problems | Read (no concurrency setting) | 🔶 set to **1 at a time** in the fix. **Untested** (Excel is stubbed in the sandbox); expect slower runs but safer data |
| 7.3 | **Possible duplicate rows:** the loop over a registration's attachments (`Apply_to_each_2`) writes `items('Apply_to_each')` (the registration), not the attachment, so a student with N attachments can get N identical rows | Read (expression) | ⬜ **needs a real-data check** before changing: confirm whether staff expect one row per attachment |
| 7.4 | The COMPLETED messages were posted *before* the final copy to `MasterList_RawData_ToBeProcess`; if the copy failed, staff had already been told "COMPLETED" | Read | ✅ copy moved inside Try; COMPLETED now means everything finished. (Behaviour change: COMPLETED arrives a little later) |
| 7.5 | The FAILED message fires only if the final copy fails/is skipped; a failure in any earlier step still produced the generic message only because the copy was skipped | Read; **Observed** | ✅ detail added (step, error, run link) |
| 7.6 | The Excel template path (`…/Template/FinalizedHeader.xlsx`) and the Office Script id are hard-coded | Read (D-03) | ⬜ issue 2 |
| 7.7 | The PIC email goes out before the file is archived; a failure at the copy step leaves the PIC with a file the downstream flows (12, 13) never received | Read | ✅ same as 7.4: copy and email are now in one Try; a failure alerts and marks the run Failed |
| 7.8 | The 30 s `Delay` is a fixed wait for Excel to settle, not a check | Read | ➖ note only |

## Test results (sandbox)

| Case | Package | Result |
|---|---|---|
| scriptfail | baseline | Script step failed; email/COMPLETED skipped; generic FAILED posts sent; run **Succeeded**. Evidence `evidence/flow-07/01-…` |
| scriptfail | fixed | Try failed at `Run script` → **Catch ✓ (4 actions)** → **Terminate ✓** → run **Failed**; email, COMPLETED and the duplicate copy skipped. Evidence `evidence/flow-07/02-…` |
| ok | fixed | Run **Succeeded** (email sent to your inbox; files created in `CDO-Sandbox/F7`) |

**Stubbed in the sandbox (so unproven):** the template read, all six Excel add-row actions, and the Office Script. Files were real SharePoint files created by the real `Create file` actions.

## Not confirmed / for you

Teams alert wording; the report email arriving in your inbox (subject `[SIIP Student Report Duty] Combined RawData`).

## Office steps

1. Back up flow 7 into `flows/` and commit.
2. Wrap everything from the template-copy scope to the final duplicate copy in `Try - Combine raw data`; set the per-student loop's concurrency to 1; Catch/Terminate as in flow 3. Or import `build/prod/flow07-prod.zip` with **Update**.
3. Run once on a **copy** of the workbook with 2–3 students and check: all rows present, no "file locked" errors, and (for 7.3) whether students with several attachments get duplicate rows.
