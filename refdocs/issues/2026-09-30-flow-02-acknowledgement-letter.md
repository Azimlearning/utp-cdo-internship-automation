# Flow 2 — Acknowledgement Letter Email Process ("Issuance Letter Drop File")

> Per-flow review under the sandbox workflow (D-08). Package: `flows/[LIVE-CDO] UTPCSDCDO Acknowledgement Letter Email Process.zip`. Fix module: `tools/fixes/f02_acknowledgement_letter.py`. Tiers: `../guides/methodology.md`.

## Status

🔶 **Reviewed. Trigger fix built. Harness imported, not yet run.** (2026-09-30) The full flow can't run in a sandbox (Excel Office Scripts bound to production files, a Word template, two Teams approval gates), so the risky part, the trigger swap, is proven on a small harness that copies flow 2's trigger-dependent actions. The rest of the flow is left unchanged.

## What the flow does

A staff member drops the raw Excel list of confirmed placements into `…/[UTP_CSD_CDO_AppointmentLetter]/Drop File`. The flow: copies it as `[CLEANED]_<name>`; cleans it with Office Scripts (empty cells, email format, wrong semester, duplicates, unused columns); **asks for approval twice in Teams** (the raw file, then the cleaned file); then, per host-company supervisor row, fills a Word template, converts it to PDF, emails it, logs the result in an "Email Status" workbook, and archives everything. ~100 actions.

## Findings

| # | Finding | Tier | Impact |
|---|---|---|---|
| 2.1 | Trigger is `OnNewFile` "When a file is created in a folder **(deprecated)**". | T1 | Microsoft marks it deprecated; a likely cause of the reported flaky drop-folder behaviour (T3 until observed). Also the only reason flow 2 needs its `body` / header outputs (see 2.2). |
| 2.2 | The old trigger supplies three things downstream: file **content** (`triggerOutputs()['body']`, used by `Create_file_-_DuplicateDatabaseFile`), file **name** (`headers/x-ms-file-name-encoded`, used to name the `[CLEANED]_` copy) and file **path** (`headers/x-ms-file-path-encoded`, used by `Get_file_metadata_using_path` and by `Move_file_-_Excel_File`). The replacement trigger returns none of these in that shape. | T1 | A trigger swap alone would break the flow. The fix must add `Get file content` and remap three expressions. |
| 2.3 | The replacement trigger also fires for **folders and files in subfolders**; the old one ignored subfolder files ([Microsoft Learn](https://learn.microsoft.com/en-us/sharepoint/dev/business-apps/power-automate/sharepoint-connector-actions-triggers), [Peter Klapwijk](https://www.inthecloud247.com/logic-apps-replace-deprecated-when-a-file-is-created-in-a-folder-trigger/)). | T2 | Flow 2 writes its own output to the **parent** folder and `Archive Folder/…`, never inside `Drop File`, so there's **no self-trigger loop** (T1, checked all Create/Move actions). A trigger condition skips folders. Whether files in subfolders of `Drop File` should be ignored is decided by the harness test (T-H4). |
| 2.4 | If the dropped Excel isn't in the exact format (`Course` / `Host Company` headers with one trailing space, all others none, table named `Database`) the Office Scripts fail. | T1 (from the 2023–24 admin guide) | Second candidate cause of "process ID reading Excel doesn't work". **Not touched by this fix.** |
| 2.5 | Existing failure handling is partial: `Post_message_10` runs if the final condition fails/skips, and the two send-email posts run on `Failed/Skipped/TimedOut`. A failure *inside* the cleaning scripts is reported only as the generic FAILED message. | T1 | Improving alert detail for this flow is a later, separate step (see "Not in scope"). |
| 2.6 | The old trigger's name header is **URL-encoded**, so `[CLEANED]_<name>` files were named with `%20` for spaces. The new fix uses the plain name. | T1 (expression) / T3 (real effect) | Cosmetic change: cleaned copies get normal names. Nothing downstream depends on the name. Called out so nobody is surprised. |

## Fix (trigger swap only)

```
old: When a file is created in a folder (deprecated) ── OnNewFile, folder = …/Drop File

new: When a file is created (properties only) ── GetOnNewFileItems, library = CDO Documents, folder = …/Drop File
       condition: skip if IsFolder
     Get file content – Dropped file  (id = trigger {Identifier})           ← new, runs first
     Scope – Create new folder and files now also waits for it

remaps:  body                       → body('Get_file_content_-_Dropped_file')
         x-ms-file-name-encoded     → {FilenameWithExtension}
         x-ms-file-path-encoded     → {FullPath}     (Get_file_metadata_using_path)
                                    → {Identifier}   (Move_file_-_Excel_File)
```

Everything else in the flow is unchanged. `python tools/build.py 2 prod` builds it (31 top-level actions, no old trigger references left).

**Open detail:** the exact `folderPath` format the new trigger wants, and whether `{FullPath}` is accepted by `GetFileMetadataByPath` without a leading slash, are confirmed by the harness run, then `DROP_FOLDER` in the fix module is set to match.

## Harness tests (sandbox library `CDO-Sandbox/Drop File`; fake workbook)

The harness = same trigger + same `Get file content` + the same three consumers (`Get_file_metadata_using_path`, `Create_file_-_DuplicateDatabaseFile`, `Move_file_-_Excel_File`) + a Compose that records what the trigger returned.

| # | Case | Expected |
|---|---|---|
| T-H1 | Drop a small `.xlsx` in `Drop File` | Harness fires within ~2 min; `[CLEANED]_<name>` appears in `CDO-Sandbox`; file moved to `Archive`; Compose shows `SameSize: true` |
| T-H2 | Drop a file with **spaces and an apostrophe** in the name | Same as H1; copy's name is the plain name |
| T-H3 | Create a **folder** inside `Drop File` | Harness does **not** run (IsFolder condition) |
| T-H4 | Drop a file inside a **subfolder** of `Drop File` | Documents the behaviour difference: new trigger fires (old one wouldn't). Decide: keep, or add a path condition |
| T-H5 | Drop a ~3 MB file | Fires **once**; content copy is complete (`SameSize`) — checks for the "fires before upload completes" risk |

## Sandbox test results — 2026-09-30 (harness, first version)

**Result:** The trigger swap **works** for a single file, names with spaces/apostrophes/parentheses, and a 3 MB file. A folder produced no run. A file in a subfolder **did** fire (the behaviour difference), so a subfolder guard was added afterwards. The guard was **re-tested on 2026-10-02 (T-H4b below): it works**.

Harness `[SANDBOX-HARNESS] flow 02 trigger swap` (`b078f132-…`), fixed-copy folders in your OneDrive site `Documents/CDO-Sandbox/{Drop File,Archive}`. Test files are random bytes named `.xlsx` (the harness only copies and moves them, it never opens them). Turned Off afterwards.

| # | Case | Observed (checked in the library and in run history) | Pass? |
|---|---|---|---|
| T-H1 | small file | Run Succeeded. `[CLEANED]_H1 Placement List.xlsx` created, 20000 B = original (`SameSize: true`). Original moved to `Archive` (Drop File emptied) | ✅ |
| T-H2 | name with spaces, apostrophe, parentheses | `[CLEANED]_H2 Nur'Aina Host Co (v2) list.xlsx`: **plain** name (old trigger's header would have produced `%20`, finding 2.6). Moved to Archive | ✅ |
| T-H3 | folder created in `Drop File` | No run and no `[CLEANED]_Sub` file | ✅ *(the folder is either filtered by the `IsFolder` condition or not reported by the trigger; not separable here)* |
| T-H4 | file inside `Drop File/Sub` | **Fired**; copy made; original moved out of `Sub` to Archive | ⚠️ Behaviour differs from the old trigger. Guard added (below) |
| T-H5 | 3 MB file | **Exactly one** run/copy; 3,145,728 B = original; no partial-content problem | ✅ |

**What the trigger actually returned** (run output): `FullPath` = `Documents/CDO-Sandbox/Drop File/H1 Placement List.xlsx` (no leading slash, library name first); `Path` = `Documents/CDO-Sandbox/Drop File/` (trailing slash); `Identifier` = `Documents%252fCDO-Sandbox%252fDrop%2bFile%252fH1%2bPlacement%2bList.xlsx`; `IsFolder` = `false`. `GetFileMetadataByPath` accepted `FullPath`, and `MoveFileAsync` accepted `Identifier`. The trigger's Folder field takes `/<library>/<folder path>` (`/Documents/CDO-Sandbox/Drop File`), the same style as flow 2's `CreateFile` folder paths, so `DROP_FOLDER` (`/Shared Documents/Power Automate Documents/[UTP_CSD_CDO_AppointmentLetter]/Drop File`) is in the right shape. The designer shows the library as its GUID; that display quirk does not stop the flow running.

**Subfolder guard added** to the trigger conditions: `@equals(last(split(triggerBody()?['{Path}'], 'Drop File/')), '')`. The logic was checked offline against the real `Path` values (direct child fires; `…/Drop File/Sub/` doesn't; the production-style path fires). It doesn't depend on the library's display name.

**Still to do before the office:**
1. **Re-run T-H1 + T-H4 with the guard** (re-import `build/harness/flow02-harness.zip`, drop one file directly and one in a subfolder). Expect direct → runs, subfolder → no run. *T-H4b.*
2. Decide whether staff ever drop files in subfolders of `Drop File` on purpose. If yes, remove the guard.
3. The **rest of flow 2 (approvals, scripts, Word/PDF, emails) is still untested** and can only be verified by a real run in the CDO test window.

**Housekeeping:** the harness copy is Off. The sandbox library holds 4 `[CLEANED]_` copies and 4 archived test files; delete `Documents/CDO-Sandbox` contents when done.

### T-H4b: subfolder guard re-test, 2026-10-02 (`pw.py filetest 02 guard`)

Re-imported the harness with the guard condition (`@equals(last(split(triggerBody()?['{Path}'], 'Drop File/')), '')`), cleared the folders, switched it on, waited for its first poll, then uploaded two files over SharePoint REST: `G1 direct file.xlsx` into `Drop File` and `G2 in subfolder.xlsx` into `Drop File/Sub`, and waited ~150 s more (several polling cycles) before reading the result.

| Check | Observed | Pass? |
|---|---|---|
| Runs | **exactly 1**, Succeeded | ✅ |
| `G1 direct file.xlsx` | processed: `[CLEANED]_G1 direct file.xlsx` created, original moved to `Archive` | ✅ |
| `G2 in subfolder.xlsx` | **not processed**: still in `Drop File/Sub`, no copy | ✅ |

So the guard works as a live trigger condition: direct children fire, subfolder files don't (parity with the old trigger). Result: `evidence/flow-02/results/guard-harness.json`. Still true: the rest of flow 2 (approvals, scripts, letters) is untested until an office run; the question whether staff ever use subfolders on purpose is still for CDO (MANUAL-TODO B).

## Not in scope of this fix (later, separately)

- Clearer failure alerts for the cleaning scripts (2.5).
- The hard-coded Excel/Office Script IDs (issue 2 / D-03) and the Excel format guard (2.4).
- Flow 14 (Store Student List) has the same deprecated trigger; the same swap applies, and it uses the path with `List_rows_present_in_a_table_2` (Excel). It will be planned after flow 2's harness passes.

## Office steps (after the harness passes)

1. Export a fresh backup of flow 2 into `flows/` and commit (rule 5).
2. In Studio: delete the old trigger, add *When a file is created (properties only)* (library *Documents*, folder = the Drop File folder), add the *IsFolder* trigger condition, add *Get file content* first, and remap the three expressions per the table above. Or import `build/prod/flow02-prod.zip` with **Update** and re-select connections.
3. Drop a real small test workbook and follow it through both approval cards. **Do this only in the CDO test window with staff aware**, since real approvals and real emails will fire.
