# Office-Laptop Checklist

Generated 2026-10-02 by `python tools/office_pack.py` from flows.json and the issue docs. Do not edit by hand; re-run it after any fix changes.

## Before touching any flow (once per visit)

1. Sign in on the office admin laptop with the account that owns the flows. Check **Connections** for *Reconnect* first (an expired connection fails with `Unauthorized` and also silences the FAILED alerts).
2. Copy `build/office/` to the laptop (or rebuild there with `python tools/office_pack.py`). Compare each zip's sha256 with the table below.
3. **Per flow, in this order** (full detail and the stop rules: `refdocs/execution/2026-10-02-real-system-rollout.md`): export a fresh backup into `flows/` and commit it (rule 5, git is the only rollback) → Import → **Update** with the **probe** zip, re-selecting the production connections → run it once and confirm the run is **Failed**, names the Probe step and the Teams alert arrives → Import → **Update** with the **prod** zip → real test (see the rollout doc) → read the run history → re-export into `flows/` and run `python tools/compare_prod.py NN` → tick the row.
4. Never apply two flows' fixes before the first one's run history has been read (CLAUDE.md: observed, not assumed).
5. Flow 7 must run before flows 12 and 13 in any test, since they read its last output.

## Packages

| Done | # | Flow | Sandbox status | Probe package | Prod package | prod sha256 (first 16) |
|---|---|---|---|---|---|---|
| ☐ | 1 | Success Submit Email | ready | `flow01-probe.zip` | `flow01-prod.zip` | `5e68141510dcf22a` |
| ☐ | 2 | Acknowledgement Letter Email Process | **NOT READY** | — (no Try scope) | `flow02-prod.zip` | `ccd17ecf2ad80012` |
| ☐ | 3 | Add HC Supervisor into MasterList | ready | `flow03-probe.zip` | `flow03-prod.zip` | `0567070678ac55c6` |
| ☐ | 4 | Add Host Company into MasterList | ready | `flow04-probe.zip` | `flow04-prod.zip` | `d5603a9817b1e2a8` |
| ☐ | 5 | Bulk Email To Start Registration | ready | `flow05-probe.zip` | `flow05-prod.zip` | `bfcd42e94f87a2a4` |
| ☐ | 6 | Clear Raw Database | ready | `flow06-probe.zip` | `flow06-prod.zip` | `63fa0bda2d8ccf19` |
| ☐ | 7 | Combine raw data | ready | `flow07-probe.zip` | `flow07-prod.zip` | `0555c990f28daba0` |
| ☐ | 8 | Delete Student List | ready | `flow08-probe.zip` | `flow08-prod.zip` | `ea9ef64097c397b0` |
| ☐ | 9 | Email To Inform Student Updates | ready | `flow09-probe.zip` | `flow09-prod.zip` | `cb404ab0c7a5d235` |
| ☐ | 10 | Email for Report Duty Reminder | ready | `flow10-probe.zip` | `flow10-prod.zip` | `bdb5fb0c8e7ad837` |
| ☐ | 12 | HC Supervisor Info MasterList Checking | ready | `flow12-probe.zip` | `flow12-prod.zip` | `41e5d09cfe9aff8f` |
| ☐ | 13 | Host Company Info MasterList Checking | ready | `flow13-probe.zip` | `flow13-prod.zip` | `6f8485359cec36c3` |
| ☐ | 14 | Store Student List into SharePoint List | ready | `flow14-probe.zip` | `flow14-prod.zip` | `e3f6a85aff4c9d52` |

No fix built yet: 11 Email for Student Report Duty Status.

## Per-flow steps

### Flow 1: Success Submit Email (ready)

Package `build/office/flow01-prod.zip` (sha256 `5e68141510dcf22a…`), probe: `flow01-probe.zip`, [issue doc](../issues/2026-09-30-flow-01-success-submit-email.md). Still open: User glances at the 2 newest Teams alerts → **office-ready**

**Option A, by hand in the designer** (about 10 minutes, easy to audit):

1. Export a backup into `flows/` and commit (rule 5).
2. Add a **Scope** at the top named `Try - Send confirmation email`, and drag *Send an email (V2)* into it.
3. Delete *Compose - EmailBody* and *Send an HTTP request to SharePoint*.
4. Add a **Scope** after Try named `Catch - Alert CDO staff`. Under ⋯ → *Configure run after*, tick only **has failed** and **has timed out**.
5. Inside Catch, add SharePoint **Get item** (CDO site, list *Control Template*, Id `1`), then Teams **Post message in a chat or channel** (Post as *Flow bot*, Post in *Chat with Flow bot*, Recipient = dynamic `TeamsNotification1`). Copy the message text from `ALERT_HTML` in `tools/fixes/f01_success_submit_email.py`.
6. After Catch, add **Terminate** (Status *Failed*, Code `ConfirmationEmailFailed`). Under *Configure run after*, tick **is successful**, **has failed** and **has timed out**.
7. Save. Check the next real registration's run in run history.

**Option B, import:** `python tools/build.py 1 prod` → Import → *Update* on the existing flow → select the production connections (Teams is new to this flow).

### Flow 2: Acknowledgement Letter Email Process (**NOT READY**)

Package `build/office/flow02-prod.zip` (sha256 `ccd17ecf2ad80012…`), probe: — (no Try scope), [issue doc](../issues/2026-09-30-flow-02-acknowledgement-letter.md). Still open: Confirm with CDO that staff never use subfolders; office test last (needs its own mini-plan)

1. Export a fresh backup of flow 2 into `flows/` and commit (rule 5).
2. In Studio: delete the old trigger, add *When a file is created (properties only)* (library *Documents*, folder = the Drop File folder), add the *IsFolder* trigger condition, add *Get file content* first, and remap the three expressions per the table above. Or import `build/prod/flow02-prod.zip` with **Update** and re-select connections.
3. Drop a real small test workbook and follow it through both approval cards. **Do this only in the CDO test window with staff aware**, since real approvals and real emails will fire.

### Flow 3: Add HC Supervisor into MasterList (ready)

Package `build/office/flow03-prod.zip` (sha256 `0567070678ac55c6…`), probe: `flow03-probe.zip`, [issue doc](../issues/2026-09-30-flow-03-add-hc-supervisor.md). Still open: User checks the FAILED alerts in Teams → **office-ready**

1. Export a fresh backup of flow 3 into `flows/` and commit (rule 5).
2. In Studio (or import `build/prod/flow03-prod.zip` with **Update** and re-select connections):
   a. Select `List rows present in a table` **and** `Apply to each` → *Add to a scope* → name it `Try - Add HC Supervisors`.
   b. Point the two COMPLETED posts' *Configure run after* at that scope (**is successful** only).
   c. Add a scope `Catch - Alert CDO staff` after it (*Configure run after*: **has failed**, **has timed out**). Inside: two **Filter array** actions (from `result('Apply_to_each')` and `result('Try - Add HC Supervisors')`, condition `status equals Failed`), then move the two existing FAILED posts inside it and append the detail block. The exact expressions are in `f03_add_hc_supervisor.py` (`DETAIL_HTML`, `_msg`).
   d. Add **Terminate** (Failed) after Catch (run after: succeeded, failed, timed out).
3. **Test on real data** only in the CDO test window with staff aware; a real run writes real supervisors. A safe first test: run it with an Excel table that has 1 valid row. (Nothing forces a failure safely on real data; the sandbox has covered the failure paths.)

### Flow 4: Add Host Company into MasterList (ready)

Package `build/office/flow04-prod.zip` (sha256 `d5603a9817b1e2a8…`), probe: `flow04-probe.zip`, [issue doc](../issues/2026-09-30-flow-04-add-host-company.md). Still open: User checks Teams alert wording; duplicate policy decision

1. Back up flow 4 into `flows/` and commit.
2. Follow the flow 3 office steps (wrap `List rows` + `Apply to each` in a Try scope; Catch with two Filter arrays and the two FAILED posts plus detail block; Terminate Failed), or import `build/prod/flow04-prod.zip` with **Update** and re-select connections.
3. Test with a one-row Excel table in the CDO test window.

### Flow 5: Bulk Email To Start Registration (ready)

Package `build/office/flow05-prod.zip` (sha256 `bfcd42e94f87a2a4…`), probe: `flow05-probe.zip`, [issue doc](../issues/2026-09-30-flow-05-bulk-email-start-registration.md). Still open: Teams alert wording (email count settled by run data: 2 per ok run)

1. Back up flow 5 into `flows/` and commit.
2. Build the fix on the real flow: move the logo read into the Try scope (init `imageStr` empty at top level, fill it inside Try with Set variable), wrap logo + three attachment scopes + `Get items` + `Apply to each` in `Try - Send bulk emails`, then Catch/Terminate as in flow 3. Or import `build/prod/flow05-prod.zip` with **Update**.
3. **Test only with the CC/BCC list temporarily set to your own address**, never to the live student list, before the real send.

### Flow 6: Clear Raw Database (ready)

Package `build/office/flow06-prod.zip` (sha256 `63fa0bda2d8ccf19…`), probe: `flow06-probe.zip`, [issue doc](../issues/2026-10-01-flow-06-clear-raw-database.md). Still open: Teams alert wording; admin-guide note on manual SummaryTable reset

1. Back up flow 6 into `flows/` and commit.
2. Wrap `Get items` + `Apply to each` + `Run script - Reset Summary Table` in `Try - Clear database`; Catch/Terminate as in flow 3. Or import `build/prod/flow06-prod.zip` with **Update**.
3. Test with a **copy** of the list and workbook only, never the live registrations.

### Flow 7: Combine raw data (ready)

Package `build/office/flow07-prod.zip` (sha256 `0555c990f28daba0…`), probe: `flow07-probe.zip`, [issue doc](../issues/2026-10-02-flow-07-combine-raw-data.md). Still open: Office test with a real workbook; check duplicate-row question 7.3

1. Back up flow 7 into `flows/` and commit.
2. Wrap everything from the template-copy scope to the final duplicate copy in `Try - Combine raw data`; set the per-student loop's concurrency to 1; Catch/Terminate as in flow 3. Or import `build/prod/flow07-prod.zip` with **Update**.
3. Run once on a **copy** of the workbook with 2–3 students and check: all rows present, no "file locked" errors, and (for 7.3) whether students with several attachments get duplicate rows.

### Flow 8: Delete Student List (ready)

Package `build/office/flow08-prod.zip` (sha256 `ea9ef64097c397b0…`), probe: `flow08-probe.zip`, [issue doc](../issues/2026-10-02-flow-08-delete-student-list.md). Still open: Teams alert wording

1. Back up flow 8 into `flows/` and commit.
2. Wrap `Get items` + `Apply to each` in `Try - Delete student list`; Catch/Terminate as in flow 3. Or import `build/prod/flow08-prod.zip` with **Update**.
3. Test on a **copy** of the Student List first.

### Flow 9: Email To Inform Student Updates (ready)

Package `build/office/flow09-prod.zip` (sha256 `cb404ab0c7a5d235…`), probe: `flow09-probe.zip`, [issue doc](../issues/2026-10-02-flow-09-email-inform-student-updates.md). Still open: Teams alert wording

1. Back up flow 9 into `flows/` and commit.
2. Wrap `Send an email (V2)` + `Post message in a chat or channel 2` in `Try - Email student`; Catch/Terminate as in flow 3. Or import `build/prod/flow09-prod.zip` with **Update**.
3. Test once with a PowerApp email addressed to a staff member's own mailbox.

### Flow 10: Email for Report Duty Reminder (ready)

Package `build/office/flow10-prod.zip` (sha256 `bdb5fb0c8e7ad837…`), probe: `flow10-probe.zip`, [issue doc](../issues/2026-10-02-flow-10-email-report-duty-reminder.md). Still open: Teams alert wording

1. Back up flow 10 into `flows/` and commit.
2. Wrap `Get items`, `Get items 2`, `Apply to each 3` and `Apply to each` in `Try - Send reminders`; Catch/Terminate as in flow 3. Or import `build/prod/flow10-prod.zip` with **Update**.
3. Test with the Student List pointed at a **copy** containing only staff addresses.

### Flow 12: HC Supervisor Info MasterList Checking (ready)

Package `build/office/flow12-prod.zip` (sha256 `41e5d09cfe9aff8f…`), probe: `flow12-probe.zip`, [issue doc](../issues/2026-10-02-flow-12-hc-supervisor-masterlist-checking.md). Still open: Teams alert wording; office test with a real workbook and a one-file folder; decide what happens to old files in the folder

1. Back up flow 12 into `flows/` and commit.
2. Wrap `Run script`, `Run script 2`, `Get files`, `Get items`, `Apply to each`, `Delay` and `Apply to each 4` in `Try - Check HC supervisors` (variable initialisations stay above it); Catch/Terminate as in flow 3. Or import `build/prod/flow12-prod.zip` with **Update**.
3. Test on a **copy** of the template and a folder holding exactly **one** small test file; confirm the three buckets and one PIC email. Run flow 7 first: this flow reads its output.

### Flow 13: Host Company Info MasterList Checking (ready)

Package `build/office/flow13-prod.zip` (sha256 `6f8485359cec36c3…`), probe: `flow13-probe.zip`, [issue doc](../issues/2026-10-02-flow-13-host-company-masterlist-checking.md). Still open: Teams alert wording; office test with a real workbook and a one-file folder

1. Back up flow 13 into `flows/` and commit.
2. Wrap `Run script`, `Run script 2`, `Get files`, `Get items`, `Apply to each`, `Delay` and `Apply to each 4` in `Try - Check host companies` (variable initialisations stay above it); Catch/Terminate as in flow 3. Or import `build/prod/flow13-prod.zip` with **Update**.
3. Test on a **copy** of the Host Company template and a folder holding exactly **one** small test file; confirm the three buckets and one PIC email. Run flow 7 first.

### Flow 14: Store Student List into SharePoint List (ready)

Package `build/office/flow14-prod.zip` (sha256 `e3f6a85aff4c9d52…`), probe: `flow14-probe.zip`, [issue doc](../issues/2026-09-30-flow-14-store-student-list.md). Still open: User checks the Teams alert wording; real-Excel `{Identifier}` test at the office; decide on the concurrent-duplicates fix

1. Back up flow 14 into `flows/` and commit.
2. Apply flow 2's trigger steps (properties-only trigger, IsFolder + direct-child conditions with leaf `StudentList_DropFile`), then flow 3's Try/Catch wrap around the four read/write actions, the Catch filters + two FAILED posts, and Terminate. Or import `build/prod/flow14-prod.zip` with **Update** and re-select connections.
3. Test with one real small workbook; confirm it stores and archives once, with no second run.
