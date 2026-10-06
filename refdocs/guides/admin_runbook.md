# Running the Internship Report Duty System: Admin Runbook

> **DRAFT, 2026-10-02.** Module M8 of the project. Written for CDO staff who are not technical. Not final until someone who did not write it has followed it through a full semester rollover (P5), and until the fixes described in §4 have been applied to the real system. Items marked **⚠ confirm** are things we expect but have not yet seen on the real system. `[to fill: …]` marks facts only CDO knows.
> Background and evidence for every statement: `refdocs/updates/ISSUES-BY-FLOW.md`. The original 2023–24 guide is `refdocs/context-2023-2024-admin-user-guide.pdf`.

## 1. What the system is

A PowerApp (the admin screen with buttons) starts small automatic programs called **flows**. The flows read and write the SharePoint lists and Excel files on the CDO team site and send emails and Teams messages. Every flow tells you what it is doing in Teams (the chat called **Workflows**): *RUNNING*, then *COMPLETED* or *FAILED*.

**If something looks wrong and this runbook does not cover it, contact:** `[to fill: name, email, phone of the technical contact]`.

## 2. The semester at a glance

Buttons are named as in the original guide. Page numbers are the 2023–24 guide's. **⚠ confirm** the exact order against the guide at the first dry run.

| Step | Button / action | What it does | Take care |
|---|---|---|---|
| 1 | **Clear Raw Data** (p3) | Deletes every registration and resets the summary sheet | Destructive. The flow itself asks no "are you sure?" (**⚠ confirm** whether the app does). Run *Get Raw Data* (step 7) first if you need the old data |
| 2 | **Control Template** → Update (p4) | Edit the one settings record: current semester, PIC emails, Teams recipients, registration cut-off date | Edit it **in place**; never delete and recreate it |
| 3 | **Delete All Student** (p6) | Deletes the whole Student List | Destructive; the flow asks no confirmation (**⚠ confirm** the app) |
| 4 | **Add and drop Student List** (p5–7) | Drop the Excel student list into the drop folder | Drop it **directly in the folder, not in a sub-folder**; see §5 |
| 5 | **Send email to all student** (p8–10) | Emails every student the registration invitation | Press **once**. A second press emails everyone again |
| 6 | Students fill in the form (p17) | Each student gets a confirmation email | — |
| 7 | **Get Raw Data** (p11) | Combines the registrations into the working workbook | Needed before any checking in step 9 |
| 8 | **Email Reminder** (p14), **Inform Student** (p12–13), **Get Status** (p16) | Reminds students who have not registered, emails one student, reports status to the PIC | Reminder emails **every** student still unregistered each time you press it; a student listed twice gets two |
| 9 | **HC MasterList Checking** (p18): Host Company and HC Supervisor | Compares the registrations with the company and supervisor lists and fills the check workbook | **Run Get Raw Data first** (§5). Make sure only **one** file is in the check folder |
| 10 | **Add company / supervisor into MasterList** (p21–22) | Adds the new entries from the check workbook to the SharePoint lists | Press **once** per check; a second press adds duplicates |
| 11 | **Issuance Letter Drop File** (p25–30) | Drop the raw Excel to start appointment letters; approve twice in Teams | The Excel must have exact column names (§5) |

## 3. What the Teams messages mean

- **RUNNING**: the flow started. **COMPLETED**: it finished its work. Nothing to do.
- **FAILED**: it did not finish. Do not press the button again straight away: some flows have already done part of their work and pressing again can repeat it (emails, rows). Go to §6.
- **⚠ confirm (after the fixes are applied):** a FAILED message also says **Failed step** (which part broke), **Error** (the reason), and has an **Open this run** link. The flow's run history now shows **Failed** in red. *Before the fixes a failed run could show "Succeeded" even when it had failed, so run history alone could not be trusted.*

## 4. What changes once the fixes are in the real system

- A failure is no longer silent or disguised as a success: you get the FAILED message with the reason and a link, and run history says Failed.
- Nothing about how you use the buttons changes. **⚠ confirm:** what the PowerApp shows on screen when a flow fails has not been observed yet.
- The fixes **report** problems; they do not repair them. A half-finished run still needs a person to decide what to do (§6).

## 5. Rules that keep the system working

1. **Never delete or replace the Excel template files** (the MasterList templates, the FinalizedHeader file). The flows find each file by a hidden internal number, not by its name. A re-uploaded file with the same name is a different file, and every flow that uses it breaks without an obvious error. Clear the contents **in place** instead.
2. **Do not put files in sub-folders** of a drop folder. The flows only look at files directly in the folder.
3. **Order matters:** *Get Raw Data* → *MasterList Checking* → review → *Add into MasterList*. The checking buttons use the **last** raw-data snapshot, not live data, and the Add buttons use what the checking step wrote.
4. **One file at a time** in the folder the checking buttons read (`MasterList_RawData_ToBeProcess`). With two files, every row is processed twice and the PIC gets two emails. Move old files aside, do not delete them.
5. **Press a button once and wait** for COMPLETED or FAILED. Adding, emailing and reminding are not safe to repeat.
6. **Dropped student and letter Excel files** must have a table named exactly `Database` (student list: `StudentList`), and column names exactly as in the guide, including the **one trailing space** in `Course ` and `Host Company `. A column off by one space makes the file fail.
7. **Do not edit the flows** in Power Automate. If a flow needs changing, ask the technical contact.

## 6. If a FAILED message arrives

1. Open the **Open this run** link (or Power Automate → My flows → the flow → the failed run) and read **Failed step** and **Error**.
2. Typical causes and what to do:

| What the error looks like | Probably | Do |
|---|---|---|
| `Unauthorized` or "connection" | A connection expired (see §7) | Reconnect it, then run the step again |
| "not a valid email" / email address | A student's or supervisor's email address is blank or malformed | Fix the address in the list, run again. **Emails to other students may already have gone out** |
| Mentions a file, folder, table or "not found" | Wrong file name, wrong table name, file missing or moved | Check the file and the rules in §5 |
| "locked" | Someone has the Excel file open | Close it, run again |
| Anything else | — | Send the link to the technical contact. Do not press the button again |

3. **Before running again**, check what was already done: the Student List, the registration list, the Excel result sheets, the PIC's inbox.
4. If unsure, stop and ask. A repeated email or row is harder to undo than a short delay.

## 7. Checks that prevent surprises

| When | Check | How |
|---|---|---|
| Start of each semester | Connections still connected | Power Automate → Connections: none should say **Reconnect**. An expired connection stops flows and also silences their alerts |
| Start of each semester | Control Template is right | Current semester, PIC emails, Teams recipients, cut-off date |
| Start of each semester | Someone is watching the alerts | The Teams recipients in the Control Template are current staff who read the **Workflows** chat |
| When staff change | Flow ownership | All flows currently run under one person's account and connections `[to fill: new owner after the ownership migration]`. If that person leaves, flows stop |
| Before a big step | Backup | Before Clear Raw Data or Delete All Student: run Get Raw Data and keep the workbook; export the Student List to Excel |

## 8. Known quirks (so they do not surprise you)

- Adding the same company/supervisor twice **creates duplicates**; the system does not check. `[to fill: CDO's decision: skip, update, or add again]`
- A student listed twice on the Student List receives two reminders.
- A failed student-list file stays in the drop folder; it will not start again by itself, so drop it again after fixing it.
- After a failed run some work may already be done (emails sent, rows written). The FAILED message tells you where it stopped, not what to undo.
- The Combine/Check steps wait a fixed time rather than checking for completion; on a very large workbook that may not be enough `[⚠ confirm on real data]`.

## 9. Glossary

**Flow**: an automatic program started by a button or by a file/record arriving. **Run history**: the list of times a flow ran and whether each succeeded. **PIC**: the staff member(s) who receive the report emails. **Control Template**: the single settings record every flow reads. **Template (Excel)**: the master workbook a flow fills in; cleared in place, never replaced. **Connection**: the saved sign-in a flow uses for SharePoint, Outlook, Teams or Excel.

## 10. Still to do before this is final

- Fill every `[to fill: …]` with CDO.
- Confirm the §2 order and all **⚠ confirm** items at the rollover dry run (P5), with someone who did not write this following it unaided.
- Add screenshots of the real buttons and Teams messages (the original guide has the old ones).
- Update §4–§8 after the fixes are applied and the first real runs are read.
