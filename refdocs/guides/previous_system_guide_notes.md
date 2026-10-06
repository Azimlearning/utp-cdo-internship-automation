# Previous System Guide — Notes & Cross-Reference

> Structured notes on `refdocs/context-2023-2024-admin-user-guide.pdf` — the original "CDO User Guide: UTP/CSD/CDO Automated Internship Report Duty System" (covers 30 Oct 2023 – 11 Jun 2024), written by **Chew Jing Ye** (`jingyechew110@gmail.com`), the CDO intern who appears to have built/documented this system before the current owner (`kamalazreel.k@utp.edu.my`) took it over. This is the same handoff pattern this project is now going through — read it as "what the previous intern wanted the next admin to know," which is exactly this project's Module M8 deliverable, one cycle earlier.
>
> This doc is notes, not a replacement — read the original PDF for the full screenshots when something here is unclear. Kept per the founding-context-documents rule: paraphrase loses detail.

Last updated: 2026-09-16

---

## What this resolved

**PRD Open Question #4 — "Standard approvals" step in the Acknowledgement Letter flow — RESOLVED, not ASSUMED anymore.**

Pages 25–29 of the guide show it's a deliberate, two-stage human-approval gate, not a legacy leftover:
1. Admin drops a Raw Data Excel file into "Issuance Letter Drop File" (this is the flow's deprecated trigger, issue 3).
2. Teams posts "RUNNING", then an **Approval card appears in Teams**: "[CLEANING PROCESS]: Excel File Approval" — admin reviews the *dropped* file and clicks Approve/Reject. Reject → re-upload.
3. On Approve, the flow cleans the data, Teams posts "CLEANING... RUNNING" → "COMPLETED", then a **second approval card**: "[Appointment Letter]: Excel File Approval" — admin reviews the *cleaned* file. Reject → contact the CDO's technical support contact (was Chew Jing Ye; now presumably whoever holds this project) for help. Approve → proceed.
4. Only after both approvals does the flow send letters and email a final "Email Status" + "Summary Table" report, with an "Insufficient Data" sheet for records whose status is `Failed` (example shown: `Failed] Wrong Semester`) — these get manually fixed and re-dropped to retry.

**Action:** update `refdocs/changelog/DECISIONS.md`'s assumptions list (remove this ASSUMED item) and `refdocs/guides/flow_inventory.md`'s row for the Acknowledgement Letter flow — done in this session, see below.

## What this enriches (issue 1 — Teams notifications)

The shared config item (`id: 1`) that every flow reads via `Get_item` (see `refdocs/issues/2026-09-16-01-no-failure-notifications.md`) is the **"Control Template"** the admin edits each semester (pages 4, 31). Its fields, per the guide's screenshot:

| Field | Purpose |
|---|---|
| Current Semester | e.g. "May 2024" — drives which semester's data the whole system treats as "current" |
| PIC Approval Teams | The Teams recipient(s) for the *approval* cards in the Acknowledgement Letter flow — likely a different field from `TeamsNotification1`, worth confirming which flow reads which field |
| PIC Email To / PIC Email CC | Where status/report emails (Combine raw data, Get Status, MasterList Checking reports) go |
| Teams Notification 1 | The running/processing/success (and, once issue 1 lands, failure) Teams recipient |
| Registration cut-off date | Feeds the student-facing deadline text in the registration email |

This is a well-designed pattern already — one durable record, edited in place each semester (never replaced), which is exactly the discipline D-03 wants applied to the Excel master-list templates too. **Recommendation for the admin guideline (M8):** document "Control Template" as the semester-rollover model to copy, precisely because it already avoids the hard-coded-ID trap.

## What this confirms about issue 2 ("process ID reading Excel doesn't work")

Page 25 shows a strict, undocumented-elsewhere format requirement for any Excel file dropped to trigger the Issuance Letter flow:
- "Course" and "Host Company" columns must have **exactly one trailing space** in their header name
- every other column header must have **no** leading/trailing space
- the table must be named exactly `Database`

This is a **second, independent source of fragility** for issue 2, separate from the hard-coded drive-item/script ID — a dropped file with a header that's off by one space, or a table named anything but `Database`, will fail the Office Script silently or with an opaque error. Given the brief's exact phrasing was "process ID reading Excel doesn't work," both explanations remain plausible (drive-item ID going stale, or a format mismatch like this) — **this needs a decision from whoever reports the symptom next: was it a hard failure with no output, or a wrong/garbled output?** The two symptoms point to different root causes and both are now documented as candidates.

**Action:** added as a refinement to backlog item 2 below.

## What this confirms about workflow ordering (not yet in the backlog — adding now)

Page 18: *"Make sure you had get latest 'Get Raw Data'!!! Because it will use the Raw Data last processed."* — the HC/Host Company MasterList Checking flows (#12, #13) operate on a **snapshot** produced by the "Combine raw data" flow (#7, the "Get Raw Data" button), not live data. If an admin runs MasterList Checking without first re-running Get Raw Data, the check silently runs against stale data. This is a real operational footgun, independent of any of the confirmed bugs — worth a line in the admin guideline (M8) and worth considering whether the flow should warn (or block) if Get Raw Data hasn't run recently enough.

## Full function → flow cross-reference

Confirms `guides/flow_inventory.md`'s mapping is accurate. One clarification: "Get Raw Data" (button) = **Combine raw data** (flow #7) — the button and flow names differ, worth noting so nobody goes looking for a flow literally named "Get Raw Data."

| Guide section (page) | PowerApp button | Flow(s) triggered |
|---|---|---|
| Clear raw data (p3) | "Clear Raw Data" | Clear Raw Database |
| Update control template (p4) | "Control Template" → Update | *(no flow — direct SharePoint item update)* |
| Store new semester's students (p5–7) | "Add and drop Student List" (drag-drop) | Store Student List into SharePoint List (⚠️ deprecated trigger, issue 3) |
| Delete current student list (p6) | "Delete All Student" | Delete Student List from SharePoint List |
| Send registration-start email (p8–10) | "Send email to all student" | Bulk Email To Start Registration |
| Get raw data (p11) | "Get Raw Data" | Combine raw data |
| Edit/Delete/Inform student (p12–13) | "Edit" / "Delete" / "Inform Student" | Email To Inform Student Updates (for Inform); Edit/Delete appear to be direct SharePoint operations |
| Email reminder (p14) | "Email Reminder" | Email for Report Duty Reminder |
| Delete specific student (p15) | "Delete Specific Student" | *(likely direct SharePoint operation, not a listed flow — worth confirming)* |
| Get status (p16) | "Get Status" | Email for Student Report Duty Status |
| Fill report duty form (p17) | *(student-facing, not admin)* | Success Submit Email (on submit) |
| Cross-check MasterList (p18) | "HC MasterList Checking" | Host Company Info MasterList Checking / HC Supervisor Info MasterList Checking |
| Update student info from checked MasterList (p19–20) | "Update student info" | *(likely direct — updates Raw Data from the checked Excel; flow unclear, worth confirming)* |
| Add new company/supervisor (p21–22) | "Add company into MasterList" | Add Host Company into MasterList / Add HC Supervisor into MasterList |
| Update/Delete company data (p23–24) | "Edit" / "Delete Specific Company" | *(likely direct SharePoint operations)* |
| Issue letter (p25–30) | Drag-drop into "Issuance Letter Drop File" | Acknowledgement Letter Email Process (⚠️ deprecated trigger, issue 3; two-stage approval, confirmed above) |

Rows marked "likely direct" need a 30-second check in Studio next time someone's there — the guide doesn't show a Teams "RUNNING/COMPLETED" notification for them, which is how the other rows were matched to a specific flow.

## Open item this raises

Add to `refdocs/guides/issues_backlog.md`: is the current admin still Kamal, or was there an intermediate handoff from Chew Jing Ye to Kamal that's undocumented? (The PowerApp screenshots throughout the guide show "Welcome Admin, Kamal Azreel B Kamarudin" — so Kamal was already the operating admin as of this guide's writing, Oct 2023–Jun 2024; Chew Jing Ye was the builder/support contact, not the admin user. This matches — not contradicts — everything else in this project: Kamal has been the account of record for over two years.)
