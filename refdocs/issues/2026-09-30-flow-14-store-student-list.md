# Flow 14: Store Student List into SharePoint List

> Sandbox workflow (D-08). Fix module: `tools/fixes/f14_store_student_list.py`. Reuses flow 2's trigger swap and flow 3's Try/Catch. Tiers: `../guides/methodology.md`.

## Status

🔶 **Sandbox-tested; two things still need real conditions.** (2026-09-30) The Excel read can't run in a sandbox, so the sandbox copies replace only that action with sample rows chosen by the dropped file's name (`ok` / `rowfail` / `readfail`). Everything else is the real flow.

## What it does

Staff drop the raw student-list Excel into `…/[UTP_CSD_CDO_AppointmentLetter]/StudentList_DropFile`. The flow reads the existing Student List (SharePoint) into an email array, reads the table `StudentList` from the dropped file, creates a list item for each row whose email isn't already there, posts COMPLETED ×2, then moves the file to `StudentList_DropFile/Archive Student List` (retrying while the file is locked) and posts MOVED ×2.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 14.1 | Deprecated trigger (as flow 2) | Read + Docs | ✅ swapped; no Get file content needed (the flow only uses the path) |
| 14.2 | The archive folder is a **subfolder of the watched folder**. The replacement trigger watches subfolders, so unguarded it could re-trigger on its own archived file | Read + Docs | ✅ direct-child guard (`…last(split(Path,'StudentList_DropFile/'))=''`). **Observed:** 3 files dropped and archived → exactly 3 runs, no self-trigger |
| 14.3 | No failure alert at all | Read | ✅ Try/Catch + Terminate. **Observed** below |
| 14.4 | On a failure the file stays in `StudentList_DropFile` (the archive step is skipped) | **Observed** | 🔶 arguably good (staff can retry), but the trigger will **not** re-fire for a file already there; staff must re-drop it. Note for the admin guide |
| 14.5 | **Concurrent runs create duplicate students.** Three files dropped together each read the list before the others wrote, leaving 5 rows for 2 students | **Observed** (baseline) | ⬜ not changed. Fix would be a concurrency limit of 1 on the trigger or a duplicate check at write time; CDO decision |
| 14.6 | Baseline reports failed runs as **Succeeded** (same as flow 3) | **Observed** (all 3 baseline runs Succeeded) | ✅ Terminate(Failed) |
| 14.7 | The COMPLETED message is skipped on a failure, but the MOVED message would still claim success only if the move ran; unchanged | Read | ➖ |

## Test results (sandbox, 2026-09-30)

| Case | Package | Result |
|---|---|---|
| ok (2 good rows) | baseline ×3 concurrent | 3 Succeeded, but **duplicates** (14.5) |
| readfail, rowfail | baseline | both **Succeeded** (14.6) |
| ok | fixed | Succeeded; 2 students written; file archived; no extra run from the archive move |
| readfail (read step errors) | fixed | Try failed → **Catch ✓** → **Terminate ✓** → run **Failed**; archive skipped; file stays in Drop. Screenshot `evidence/flow-14/01-…` |
| rowfail (a row that can't be saved) | fixed | Try failed in the loop → **Catch ✓ (4 actions)** → **Terminate ✓** → run **Failed**; archive skipped. Screenshot `evidence/flow-14/02-…` |

Note: my first rowfail attempt was invalid (its bad row shared an email with an existing student and was skipped as a duplicate); redone after removing that student.

**Not confirmed:** the FAILED alert **wording in Teams** (I read only that the Teams actions inside Catch were green). Please look at the newest alerts in the Workflows chat; expect "STORING process is FAILED" plus Failed step / Error / run link.

## Real-Excel sandbox run (2026-10-06)

A real workbook (`testdata/StudentList_TEST.xlsx`: table `StudentList`, 8 rows) was dropped into the sandbox watch folder and read by the **real Excel connector** (sandbox OneDrive). The fixed copy reads it through the trigger's **`{Identifier}`**; the baseline through the old path header.

| Scenario | Package | Run status | What happened | Result file |
|---|---|---|---|---|
| ok | fixedx | **Succeeded** | `{Identifier}` works as the Excel `file` value. 8 rows → **6 items** (rows 3 and 7 skipped as duplicate emails, row 8 with no email created); file archived; no re-trigger from the archive move; run took ~7 minutes | `results/ok-fixedx.json` |
| ok | baselinex | **Succeeded** | identical: 6 items, archived, ~6.5 minutes | `results/ok-baselinex.json` |

**Observed: each run took 6–7 minutes** (start 06:09:19 → end 06:16:33 for fixedx; 06:18:14 → 06:24:42 for baselinex), with `Do_until_-_Archive_Excel_File`, `Delay`, `Set_variable` and `Move_file` all Succeeded and the file ending up in `Archive Student List`. Excel Online keeps a read workbook locked for about 8 minutes (seen on flows 12/13), which is consistent with the archive loop (`Move_file`, retry every 60 s while "locked") waiting out a genuine lock. I did not read the individual loop iterations, so that explanation is likely but not confirmed; either way the file is archived successfully and the run is slow, not broken.

| readfail (valid workbook, but its table is not called `StudentList`) | baselinex | **Failed** (`ActionFailed`) | `List_rows_present_in_a_table_2` failed (`NotFound`); **no FAILED alert at all** (both FAILED posts Skipped, the flow has none); the file stays stuck in the Drop folder | `results/readfail-baselinex.json` |
| readfail | fixedx | **Failed** (`Terminated`) | failed in 12 seconds: "Store Student List failed at: List_rows_present_in_a_table_2"; Catch ran, both FAILED Teams posts sent; file stays in Drop (not archived) | `results/readfail-fixedx.json` (collected from run history: the runner was cut off and the flow, left On, picked the file up by itself) |

So for flow 14 the fix turns a **silent failure** (run red in history, nobody told) into an alert with step, error and link. An earlier attempt with a *corrupt* (non-Excel) file showed that the baseline can take **26 minutes** to fail (the connector retries); a wrong table name fails in seconds. The `rowfail` real-Excel case was not repeated (it is covered by the stubbed run above).

## Not tested (needs the real flow)

- The production workbook, drive and library (the `{Identifier}` mechanism itself is now proven on a OneDrive-backed library; the CDO team site is a SharePoint library with a different drive, so the first production drop should be a small file).
- A real-Excel `rowfail` (only the stubbed one was run).

## Office steps

1. Back up flow 14 into `flows/` and commit.
2. Apply flow 2's trigger steps (properties-only trigger, IsFolder + direct-child conditions with leaf `StudentList_DropFile`), then flow 3's Try/Catch wrap around the four read/write actions, the Catch filters + two FAILED posts, and Terminate. Or import `build/prod/flow14-prod.zip` with **Update** and re-select connections.
3. Test with one real small workbook; confirm it stores and archives once, with no second run.
