# Manual To-Do (things only you can do)

Last updated: 2026-10-02. Email-count checks are no longer needed: the sandbox runner reads per-iteration send results from the run itself. I add to this list whenever a test needs a human (looking at Teams/Outlook, asking CDO, an office visit). Tick items off as you go; nothing here blocks me from continuing with the next flow.

## A. Quick checks on your own account (about 30 minutes total)

| ☐ | Task | Where | What to look for | Flows |
|---|---|---|---|---|
| ☐ | Check the **FAILED alerts in Teams** | Teams → chat **Workflows** | Newest FAILED messages should read: original text + `Failed step: …` + `Error: …` + an "Open this run" link. No raw JSON blobs. Screenshot them or tell me what's wrong | 3, 4, 5, 6, 8, 9, 10, 12, 13, 14 (flow 1 already confirmed) |
| ☐ | **Do you know what the flow `Export Attachment - Report Duty RAW Data` is?** (in your own account, Stopped, created 2025-09-17) | It is not one of the 14: a manual button that copies every Report Duty registration's attachments into `Internship Programme/<year>/<semester>/Report Duty Attachment/…` | — |
| ☐ | Delete the **redundant sandbox flows** | Power Automate → My flows | Flow 1: older fixed copy `a56d61bd-…`. Flow 3: older fixed copy `c41580af-…`. Flows 5 and 10: several older `[SANDBOX-FIXED]` copies from re-imports (the runner always uses the newest; older ones are harmless while Off). Keep the newest `[SANDBOX-…]` of each, or delete all sandbox flows when everything is finished. I can list them with `pw.py flows` | 1, 3, 5 |
| ☐ | **Check the sandbox flow `[SANDBOX-FIXEDX] UTP/CSD/CDO Store Student List into SharePoint List` is Off** (the 2026-10-06 test run was cut off before it could be switched off) | Power Automate → My flows (your personal account) → that flow → if it says *On*, turn it Off. It only watches the sandbox folder and emails nobody, so it is harmless but wasteful. Or ask me to run `pw.py alloff` | Keeps the sandbox quiet | 14 |
| ☑ | **Reconnect Excel Online (Business)** (done 2026-10-02; flows 12 and 13 then ran with real Excel; flows 3, 4, 14 not yet) | Power Automate → Connections → Excel Online (Business) → Reconnect | Unblocks testing real Excel reads/writes in the sandbox with the generated workbooks (`testdata/`). Power BI and OneDrive also show Reconnect; not needed | 3, 4, 12, 13, 14 |
| ☐ | Tidy the sandbox library (optional, at the very end) | OneDrive → Documents → `CDO-Sandbox` | Delete the test files and the `[CLEANED]_` copies | 2, 14 |

## B. Questions to ask CDO staff (when convenient)

| ☐ | Question | Why it matters | Flows |
|---|---|---|---|
| ☐ | If the PowerApp button is clicked twice (or after a failure), should existing rows be **skipped, updated, or added again**? | Today every Excel row is added again → duplicates | 3, 4, 14 (and 5: re-emailing students) |
| ☐ | If a student list fails, should the file stay in the drop folder (current behaviour) so staff re-drop it? | After a failure the trigger won't re-fire for a file already there | 14 |
| ☐ | Should **Clear Raw Database** ask "are you sure?" before deleting everything? | One click wipes all registrations | 6 |
| ☐ | Do staff ever drop files in **subfolders** of the drop folders on purpose? | The new trigger fires for subfolders; I added a guard to keep today's behaviour | 2, 14 |
| ☐ | Should the PowerApp check the email address before calling flow 9? | Today a typo makes the send fail; the fix now reports it, but the student still gets nothing | 9 |
| ☐ | If one student on the Student List appears twice, should they get one reminder or two? | Today two (flow 10) | 10 |
| ☐ | What is normally in the `MasterList_RawData_ToBeProcess` folder when staff press the HC checking buttons, and does anything clear it between rounds? | Flows 12 and 13 process **every** file in it and email the PIC once per file; leftover files would be re-checked and appended | 7, 12, 13 |
| ☐ | Which exact things have gone wrong: the **student share folder**, the **"old database"**, the **manual email**, **Excel process-ID reading**? | These reported issues still need a real failed run's error text to pin to a flow | R1–R5 in ISSUES-BY-FLOW.md |
| ☐ | What does the **semester rollover date** look like? | Sequencing of the office work | all |

## C. Tests that need the office laptop / real production files (no rush)

| ☐ | Task | Why | Flows |
|---|---|---|---|
| ☐ | **Request the real "Email for Student Report Duty Status" flow export from your supervisor** (the flow behind the PowerApp "Get Status" button). Export → Package (.zip) from Power Automate, saved into `flows/` replacing `[LIVE-CDO] UTPCSDCDO Email for Student Report Duty Status.zip`, which is only a copy of flow 4 | The repo has no definition of this flow | 11 |
| ☐ | **Ask Kamal (or whoever co-owns it) to export the PowerApp(s)**: Power Apps → Apps → *SIIP Report Duty Form* (and *IPBAS*, also Kamal's: check which one is the admin interface) → Export package (.zip), and ideally the app's source download. Put the zip(s) in a new `powerapp/` folder in the repo | Your account can only *run* the app (Edit and Export package are greyed out), so its formulas can't be read from here. With it I can check which flow each button calls with which inputs, how the app handles a flow that ends Failed, and which flow is "Get Status" | 11, all PowerApp-triggered flows |
| ☐ | Run each fixed flow once on a **small real test workbook** in the CDO test window, staff aware | The sandbox replaces the Excel read/Office Script/Word template; only a real run proves those parts | 2, 3, 4, 5, 6, 14 |
| ☐ | Test flow 2's **approvals, scripts, letter PDFs and emails** end to end | Never run outside production | 2 |
| ☐ | Back up each live flow into `flows/` **before** changing it, then apply the fix (rebuild by hand or import `build/prod/flowNN-prod.zip` with **Update**) | Rule 5: git is the only rollback | all |
| ☐ | Flows 12 and 13: run each fixed flow on a **copy** of its MasterList template with a folder holding exactly **one** small test file; confirm the three buckets (Matched / Partially / Exactly Not Matched) and a single PIC email. Run flow 7 first (they read its output) | The sandbox stubs the workbook, scripts and folder listing | 12, 13 |
| ☐ | Flow 7: run on a **copy** of the workbook with 2–3 students; confirm all rows present, no "file locked" errors (concurrency fix), and whether a student with several attachments gets one row or several (7.3) | The sandbox stubs every Excel step | 7 |
| ☐ | Check the **flow 7 report email** `[SIIP Student Report Duty] Combined RawData` arrived in your inbox (fixed "ok" run) | Confirms the email step | 7 |
| ☐ | Never point a bulk-email test at real students: temporarily set the Student List/CC to your own address | Flow 5 emails real students | 5 |

## D. Decisions I need from you (when ready)

| ☐ | Decision | Options |
|---|---|---|
| ☐ | Commit the work to git? (nothing is committed yet; `flows/`, `refdocs/`, `tools/` are all untracked) | Yes, one commit now / commit per flow / wait |
| ☐ | Anything to keep when you delete sandbox flows? | Evidence screenshots and docs are already in the repo |

## E. Before the real-system rollout (see the rollout plan and execution doc)

| ☐ | Item | Why |
|---|---|---|
| ☐ | **Pick the visit and a quiet window**, and tell CDO staff tests will run | The probe step makes any real form submission / file drop during it fail (flows 1, 14) |
| ☐ | **Find out who receives the Teams alerts** (config item id 1: `TeamsNotification1/2`) and ask them to watch Teams during the visit | An alert nobody sees is not an alert; this also settles the "alert wording" check |
| ☐ | Confirm **Python is available on the office laptop** (or plan to run `compare_prod.py` at home after exporting) | Step P9 of the procedure |
| ☐ | Generate flow 2's test file only when you are ready: `python tools/testdata.py --staff-email <you> --semester "<current semester>"` | It emails supervisors (only you) and starts real approvals |
| ☐ | Decide the **rollover date** if you learn it (PRD Open Question #1) | Sets when class R flows get their first genuine run |
