# All Known Issues, by Flow

Last updated: 2026-10-06. One row per issue, grouped by the flow it comes from, plus the issues that span many flows. Status of each *flow* is in [FLOW-TRACKER.md](FLOW-TRACKER.md); the older backlog is [../guides/issues_backlog.md](../guides/issues_backlog.md).

**Evidence:** **Observed** = reproduced by running a sandbox copy. **Read** = read directly in the flow's exported definition (fact about the design, not yet seen failing). **Docs** = Microsoft documentation. **Reported** = from the brief or staff, not yet traced. **Fix status:** ✅ fix sandbox-tested · 🔶 fix built, partly tested · ⬜ not started · ➖ won't fix / note only.

No fix has been applied to any live flow. "Fix" below means a tested design ready for the office laptop.

---

<!-- generated:issues (python tools/docs.py; edit flows.json, not this block) -->
## Flow 1: Success Submit Email (student confirmation email)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 1.1 | If the email fails to send (bad or blank address, expired connection) the flow stops and nobody is told | **Observed** (baseline run failed silently) | ✅ Try/Catch + Teams alert + mark run Failed |
| 1.2 | The only backup uses SharePoint's SendEmail API, **retired 31 Oct 2025**, so it does nothing; and it only runs on time-out, not on failure | Read + Docs | ✅ removed |
| 1.3 | Backup path hard-codes Kamal's address as sender; breaks on names with an apostrophe | Read | ✅ removed with 1.2 |
| 1.4 | Power Automate's own failure-alert subscription is off for the flow | Read | ➖ note; moot once 1.1 is fixed |
| 1.5 | Subject uses the UTC month ("…for September Semester") | Read | ➖ cosmetic, left alone |
| 1.6 | Only export without the `[LIVE-CDO]` tag; unclear if it's switched on in production | Read | ⬜ someone with access must check |
| 1.7 | Connections expire and then fail with `Unauthorized` | **Observed** (during the sandbox import) | ⬜ admin-guide item, see cross-cutting |
| 1.8 | Alert for a blank email showed raw connector JSON | **Observed** (Teams screenshot) | ✅ fixed and re-run; message text awaits your Teams look |

## Flow 2: Acknowledgement Letter Email Process (appointment letters)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 2.1 | Uses the **deprecated** "When a file is created in a folder" trigger (likely cause of flaky letter drop) | Read + Docs | ✅ trigger swap built and harness-tested |
| 2.2 | The old trigger supplies content, name and path; the replacement supplies none of these, so a bare swap breaks the flow | Read | 🔶 handled: Get file content added, 3 expressions remapped |
| 2.3 | The replacement trigger also fires for files in subfolders (the old one didn't) | **Observed** | ✅ guard added and **re-tested live (T-H4b)** |
| 2.4 | The dropped Excel must match an exact format (`Course`/`Host Company` headers with a trailing space, table named `Database`); otherwise the scripts fail | Read (2023–24 admin guide) | ⬜ candidate cause of "Excel reading doesn't work" |
| 2.5 | Failures inside the cleaning scripts give only a generic FAILED message | Read | ⬜ later |
| 2.6 | Cleaned copies were named with `%20` for spaces (old trigger's encoded name) | Read; **Observed** the new name is plain | 🔶 change is cosmetic |
| 2.7 | Excel template and Office Script referenced by hard-coded IDs; replacing the template file breaks the flow silently | Read (D-03) | ⬜ issue 2 |
| 2.8 | The rest of the flow (2 Teams approvals, Word→PDF, emails) has never been run outside production | n/a | ⬜ only an office run can test it |

## Flow 3: Add HC Supervisor into MasterList (sandbox-tested 2026-09-30 and with real Excel 2026-10-06)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 3.1 | **A failed run is reported as "Succeeded"** in run history (green banner over a failed loop) | **Observed** (sample rows, and a real Excel read: missing workbook and rejected row) | ✅ Terminate(Failed) after the alert |
| 3.2 | Partial writes: row 1 saved, row 2 failed, nothing reports how far it got | **Observed** | 🔶 alert now names the failed step; rollback not attempted |
| 3.3 | FAILED message names no step, error or run link | Read | ✅ Failed step + Error + run link added |
| 3.4 | Every Excel row is written as a new item, so running it twice duplicates supervisors | Read | ⬜ needs a CDO decision (skip or update?) |
| 3.5 | The FAILED branch hangs off the last COMPLETED post, so it also fires if only that Teams *message* fails | Read | ✅ alert now keyed to the real work |
| 3.6 | Excel file, drive and table are hard-coded IDs | Read (D-03) | ⬜ issue 2 |
| 3.7 | (Bug caught during the fix) inside a loop, `result()` items have array outputs and broke the first alert expression | **Observed** | ✅ type-safe expression |

## Flow 4: Add Host Company into MasterList (sandbox-tested 2026-09-30 and with real Excel 2026-10-06)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 4.1 | Failed runs reported "Succeeded" | **Observed** (sample rows, and a real Excel read: missing workbook and rejected row) | ✅ Try/Catch + Terminate |
| 4.2 | Partial write on a mid-loop failure | **Observed** | 🔶 alert names the failed step; no rollback |
| 4.3 | No duplicate check (rerun re-adds every row) | **Observed** | ⬜ CDO decision |
| 4.4 / 4.5 | FAILED alert has no detail; fires if only the COMPLETED message fails | Read | ✅ |
| 4.6 | Hard-coded Excel file + table IDs | Read | ⬜ issue 2 |

## Flow 5: Bulk Email To Start Registration (sandbox-tested 2026-09-30)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 5.1 | Failed runs reported "Succeeded" | **Observed** | ✅ Try/Catch + Terminate |
| 5.2 | Mid-batch failure leaves already-sent emails; a re-click re-emails students | Read | 🔶 alert only; CDO decision |
| 5.3 / 5.4 | FAILED message has no detail; fires if only the COMPLETED message fails | Read | ✅ |
| 5.5 | Guideline attachment fetched by hard-coded list item ID 282 | Read | ⬜ admin-guide / issue 2 |
| 5.6 | Sends from a personal mailbox | Read | ⬜ P4 |
| 5.7 | Logo file read had no alert if missing | Read | ✅ moved inside Try |

## Flow 6: Clear Raw Database (sandbox-tested 2026-10-01)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 6.1 | Failed runs reported "Succeeded" | **Observed** | ✅ Try/Catch + Terminate |
| 6.2 | Half-cleared state (rows deleted, Excel summary not reset) | **Observed** | 🔶 alert only; manual reset note for the admin guide |
| 6.3 | FAILED alert has no detail | Read | ✅ |
| 6.4 | Hard-coded Excel file and Office Script IDs | Read | ⬜ issue 2 |
| 6.5 | No confirmation before deleting everything | Read | ⬜ PowerApp suggestion |

## Flow 7: Combine raw data (sandbox-tested 2026-10-02; Excel parts stubbed)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 7.1 | Failed runs reported "Succeeded" | **Observed** | ✅ Try/Catch + Terminate |
| 7.2 | Default-parallel loop writes rows into one Excel workbook (lost rows / locks) | Read | 🔶 concurrency 1 in the fix; untested |
| 7.3 | A student with N attachments may get N identical rows | Read | ⬜ real-data check first |
| 7.4 / 7.7 | COMPLETED and the PIC email come before the final copy to the downstream folder | Read | ✅ copy moved inside Try |
| 7.5 | FAILED alert detail only via the last step | **Observed** | ✅ |
| 7.6 | Hard-coded template path and Office Script id | Read | ⬜ issue 2 |
| 7.8 | Fixed 30 s wait instead of a check | Read | ➖ |

## Flow 8: Delete Student List (sandbox-tested 2026-10-02, real failure)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 8.1 | Failed runs reported "Succeeded" (real "Item Not Found" failure) | **Observed** | ✅ Try/Catch + Terminate |
| 8.2 | Partial delete with no report of which items | Read | 🔶 alert names the failing action |
| 8.3 | FAILED alert has no detail | Read | ✅ |
| 8.4 | Read capped at 10,000 items | Read | ➖ low risk |
| 8.5 | No confirmation before deleting the whole list | Read | ⬜ PowerApp suggestion |

## Flow 9: Email To Inform Student Updates (sandbox-tested 2026-10-02)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 9.1 | Failed email (malformed address) reported "Succeeded" | **Observed** | ✅ Try/Catch + Terminate |
| 9.2 | Address from the PowerApp field is not validated | Observed (same mechanism) | ⬜ PowerApp suggestion |
| 9.3 | FAILED alert has no detail | Read | ✅ |
| 9.4 | Student gets no Teams message when the email fails | Read | ➖ acceptable |

## Flow 10: Email for Report Duty Reminder (sandbox-tested 2026-10-02)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 10.1 | Failed send reported "Succeeded" | **Observed** | ✅ Try/Catch + Terminate |
| 10.2 | One bad address leaves a partly sent batch, no list of who was missed | **Observed** (run data: 2 sent, 1 failed in the same run) | 🔶 alert names the failing action |
| 10.3 | Duplicate Student List rows get duplicate reminders | **Observed** (run data: 2 reminders to the same address) | ⬜ duplicate policy decision |
| 10.4 | Re-click re-emails everyone still unregistered | Read | ➖ by design |
| 10.5 | Teams summary counts are loosely labelled | Read | ➖ wording |
| 10.6 | FAILED alert has no detail | Read | ✅ |

## Flow 11: Email for Student Report Duty Status (export is a duplicate of flow 4)

Not reviewed yet. Known before review: Resolved 2026-10-02: the file is flow 4 again (same flow id, identical definition). Nothing about the real flow is known except that the PowerApp's "Get Status" button runs it (admin guide p16) and that status emails go to the PIC recipients on the config item.

## Flow 12: HC Supervisor Info MasterList Checking (sandbox-tested 2026-10-02, stubbed and with real Excel; Office Scripts stubbed)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 12.1 | Failed run reported "Succeeded" (script step or a row write deep in the loops) | **Observed** (forced errors, and a real Excel failure: missing file) | ✅ Try/Catch + Terminate |
| 12.2 | Partial write with no report (2 rows written, the 3rd failed, no PIC email, run Succeeded) | **Observed** | 🔶 alert only; no rollback |
| 12.3 | Every file in the folder is processed and each gets its own PIC email (2 files → every row twice, 2 emails) | **Observed** (stubbed listing; plus an unplanned real case: a stray file with other columns failed in the loop, run still green) | ⬜ check real folder contents; decision |
| 12.4 | Classification on real Excel data (4 rows, incl. a lower-case/trailing-space duplicate): exact → Matched, other position → Partially Not Matched, unknown name → Exactly Not Matched; unchanged by the fix | **Observed** (real Excel reads and writes) | ➖ logic left alone |
| 12.5 | Scripts clear the template tables first; a later failure leaves it cleared or half-filled | Read | ➖ admin-guide note |
| 12.6 | Hard-coded template, Office Script and table ids | Read (D-03) | ⬜ issue 2 |
| 12.7 | Fixed 30 s Delay instead of a check | Read | ➖ |
| 12.8 | Input file needs a `Database` table with exact headers | Read | ⬜ same family as 2.4 |
| 12.9 | FAILED alert had no detail; for nested-loop failures it names `Apply_to_each_2` (limit of Power Automate), the run link finds the exact step | **Observed** | ✅ with that limit |
| 12.10 | Shares its workbook with flow 3: the Exactly Not Matched table it writes (`{CB10AEA9…}`) is the one flow 3 reads, so a partial run here means flow 3 imports only part of the new supervisors | Read (definitions) | ⬜ admin-guide note (X11) |

## Flow 13: Host Company Info MasterList Checking (sandbox-tested 2026-10-02, stubbed and with real Excel; Office Scripts stubbed)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 13.1 | Failed run reported "Succeeded" (script step or a row write deep in the loops) | **Observed** (forced errors, and a real Excel failure: missing file) | ✅ Try/Catch + Terminate |
| 13.2 | Partial write with no report (2 rows written, the 3rd failed, no PIC email, run Succeeded) | **Observed** | 🔶 alert only; no rollback |
| 13.3 | Every file in the folder is processed and each gets its own PIC email (2 files → every row twice, 2 emails) | **Observed** (stubbed listing; plus an unplanned real case: a stray file with other columns failed in the loop, run still green) | ⬜ check real folder contents; decision |
| 13.4 | Classification on real Excel data (4 rows, incl. a lower-case/trailing-space duplicate): identical → Matched, differing street → Partially Not Matched, unknown company → Exactly Not Matched; unchanged by the fix | **Observed** (real Excel reads and writes) | ➖ logic left alone |
| 13.5 | Shares its workbook with flow 4: the Exactly Not Matched table it writes is the one flow 4 reads, so a partial run here means flow 4 imports only part | Read | ⬜ admin-guide note (X11) |
| 13.6 | Hard-coded drive-item id, Office Script id and table GUIDs; replacing the template breaks flows 13 and 4 | Read (D-03) | ⬜ issue 2 |
| 13.7 | Scripts clear the template first; a later failure leaves it cleared or half-filled | Read | ➖ admin-guide note |
| 13.8 | Fixed 30 s Delay; input needs a `Database` table with exact headers | Read | ➖ / ⬜ like 2.4 |
| 13.9 | Runs on flow 7's last output; stale if flow 7 wasn't re-run first | Read + admin guide | ⬜ admin-guide note |
| 13.10 | FAILED alert had no detail; nested-loop failures name `Apply_to_each_2`, the run link finds the exact write | **Observed** | ✅ with that limit |

## Flow 14: Store Student List into SharePoint List (sandbox-tested 2026-09-30 and with real Excel 2026-10-06)

| ID | Issue | Evidence | Fix status |
|---|---|---|---|
| 14.1 | Uses the **deprecated** file trigger (same as flow 2) | Read + Docs | ✅ trigger swap sandbox-tested |
| 14.2 | **Loop risk:** the flow archives the processed file into `StudentList_DropFile/Archive Student List`, a *subfolder of the watched folder*. With the replacement trigger this could re-trigger on its own archived file, so the subfolder guard is mandatory | Read + Docs | ✅ guard sandbox-tested: the archive move did not re-trigger |
| 14.3 | **No failure alert at all**; a failure just stops (run history at least shows Failed) | Read | ✅ Try/Catch + Terminate sandbox-tested |
| 14.4 | The "Excel moved to Archive" message posts even if the move failed for a reason other than a file lock | Read | ⬜ note; not changed |
| 14.5 | Excel read uses the trigger's path header; the replacement's `Identifier` can't be tested without a live Excel connection | Read | ⬜ verify at the office with a real test file |
| 14.6 | Reads the whole existing list before de-duplicating by email (pagination is set to 100,000) | Read | ➖ **not a problem**, checked |
| 14.7 | **Concurrent runs create duplicate students** (3 files dropped together → 5 rows for 2 students) | **Observed** | ⬜ CDO decision (concurrency limit or write-time check) |
| 14.8 | Baseline reports failed runs as "Succeeded" (as flow 3) | **Observed** | ✅ Try/Catch + Terminate sandbox-tested |
| 14.9 | On failure the file stays in the drop folder and the trigger won't re-fire for it; staff must re-drop | **Observed** | ➖ admin-guide note |
<!-- /generated:issues -->

## Issues that span many flows

| ID | Issue | Flows | Evidence | Fix status |
|---|---|---|---|---|
| X1 | **Failed runs show as "Succeeded"** whenever the last step is a Teams FAILED message that itself succeeds | The flows with the FAILED-post pattern | **Observed on flows 3–10 and 14**; 11–13 not yet run | 🔶 Try/Catch + Terminate sandbox-tested on each of those; 11–13 to come |
| X2 | The FAILED alert says nothing about which step or why | 12 flows | Read | 🔶 same pattern as X1 |
| X3 | All 14 flows run under Kamal's account (`kamalazreel.k@utp.edu.my`); it's total, not partial | All 14 | Read | ⬜ P4 ownership migration |
| X4 | Outlook emails send from a personal mailbox, not a shared one | 7 flows that send email | Read | ⬜ P4 |
| X5 | **Connection expiry:** a lapsed connection fails with `Unauthorized`, silencing both success and failure alerts | All 14 (all use Kamal's connections) | **Observed** (on your own account) | ⬜ admin-guide item |
| X6 | Excel templates and scripts are referenced by hard-coded file/script IDs; replacing a template file breaks flows silently | 2, 3, 4, 7, 12, 13, 14 | Read (D-03) | ⬜ issue 2: in-place rule + identity guard + recovery runbook |
| X7 | Deprecated file trigger | 2, 14 | Read + Docs | 🔶 see flows 2 and 14 |
| X8 | Every flow reads the Teams recipient from one shared config item (ID 1); deleting or restructuring it breaks all alerts | All 13 with Teams | Read | ⬜ admin-guide item |
| X9 | No admin guideline exists | n/a | Confirmed absence | ⬜ M8 / P5, after the flows are stable |
| X10 | No test environment exists in the UTP tenant | n/a | Confirmed (D-07) | ✅ mitigated by the sandbox (D-08) |
| X11 | **The checking flows feed the adding flows through a shared Excel template** (12 → 3 for supervisors, 13 → 4 for host companies): the check writes the *Exactly Not Matched* table, the add flow reads it. A partial or failed check run, or a stale folder, changes what the add flow imports, and the add flows have no duplicate check | 3, 4, 12, 13 (and 7, which fills the folder the checks read) | Read (matching file and table ids in the definitions) | ⬜ admin-guide: run order 7 → 12/13 → review → 3/4 |

## Reported but not yet traced to a specific flow

| # | Reported issue | What's needed |
|---|---|---|
| R1 | "Issue with the student share folder" | Likely flows 2/14 (deprecated trigger); confirm what staff actually saw |
| R2 | "Only works for students to fill in" | Which specific admin button/flow fails outright |
| R3 | "Old database" issue | Which database, and what's wrong |
| R4 | "Email has to be manual" | Likely X1/1.1 (silent failure); confirm with staff |
| R5 | "Process ID reading Excel doesn't work" | Two candidates: X6 (stale hard-coded ID) or 2.4 (wrong Excel format); a real failed run's error text would decide |

## Sandbox-only notes (not production problems)

- Your own Excel Online, Power BI and OneDrive connections show as expired (only the Teams one was renewed).
- The browser tool caps a single wait at ~30 s and parallel calls don't queue; larger sandbox imports take 3–5 minutes.
