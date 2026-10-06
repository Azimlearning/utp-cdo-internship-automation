# Flow Inventory — CDO Internship Automation

> Ground truth extracted directly from the 14 exported flow packages in `flows/` (each is a Power Automate `.zip` containing `manifest.json` + `Microsoft.Flow/flows/<guid>/definition.json`). Read this before touching any flow — it's the map. If a flow's actual behavior in Power Automate Studio ever disagrees with a row here, trust Studio and fix this file (CLAUDE.md rule 4).
>
> **Confidence note:** everything in this file is Tier 1 (structural fact — read directly from the exported JSON, as certain as reading source code). Where a row states *why* something breaks in production, that's a Tier 3 causal hypothesis, not yet confirmed against a live run. See `guides/methodology.md` for what each tier means and hasn't been checked yet.

Last verified: 2026-09-16, by extracting all 14 `.zip` files and reading `manifest.json` + `definition.json` for each.

**All 14 flows' connections are currently authenticated as `kamalazreel.k@utp.edu.my`.** See [`../changelog/DECISIONS.md`](../changelog/DECISIONS.md) D-01 / D-07.

---

## The 14 flows

| # | File (in `flows/`) | Flow display name | Trigger | Connectors | Purpose |
|---|---|---|---|---|---|
| 1 | `UTPCSDCDO Success Submit Email.zip` | UTP/CSD/CDO Success Submit Email | SharePoint "When an item is created" (polling, 1 min) — **no `[LIVE-CDO]` prefix, unlike all others; publish status unconfirmed, see Open Question** | SharePoint, Outlook | Confirmation email to the student after their SharePoint list item is created |
| 2 | `[LIVE-CDO] ... Acknowledgement Letter Email Process.zip` | Acknowledgement Letter Email Process (UI: "Issuance Letter Drop File") | ⚠️ **"When a file is created in a folder (deprecated)"** on `/Shared Documents/Power Automate Documents/[UTP_CSD_CDO_AppointmentLetter]/Drop File` | SharePoint, Excel Online (Business), Word Online (Business), Standard approvals, Outlook, Teams | Generates the personalized appointment/acknowledgement letter (Word→PDF) and emails it to the host company supervisor. **Confirmed two-stage human approval gate** (not a leftover): Teams approval card on the raw dropped file, then a second Teams approval card on the cleaned file, before letters send. Requires the dropped Excel to match an exact format (`Course`/`Host Company` headers with one trailing space, all others with none, table named `Database`) — a second candidate root cause for "process ID reading Excel doesn't work" alongside the hard-coded IDs. Full detail: `previous_system_guide_notes.md` |
| 3 | `[LIVE-CDO] ... Add HC Supervisor into MasterList.zip` | Add HC Supervisor into MasterList | PowerApp (manual, `PowerAppV2`) | SharePoint, Excel Online (Business), Teams | Adds a confirmed HC (host company) supervisor record into the Excel master list |
| 4 | `[LIVE-CDO] ... Add Host Company into MasterList.zip` | Add Host Company into MasterList | PowerApp (manual) | SharePoint, Excel Online (Business), Teams | Adds a confirmed host company record into the Excel master list |
| 5 | `[LIVE-CDO] ... Bulk Email To Start Registration for Current Semester Internship Student.zip` | Bulk Email To Start Registration for Current Semester Internship Student | PowerApp (manual) | SharePoint, Outlook, Teams | The "send to all students" report-duty kickoff email button |
| 6 | `[LIVE-CDO] ... Clear Raw Database.zip` | Clear Raw Database | PowerApp (manual) | SharePoint, Excel Online (Business), Teams | Clears the raw/staging Excel data — part of the semester reset procedure |
| 7 | `[LIVE-CDO] ... Combine raw data.zip` | Combine raw data (UI button: **"Get Raw Data"**) | PowerApp (manual) | SharePoint, Excel Online (Business), Outlook, Teams | Combines raw submitted data into the finalized dataset; references `FinalizedHeader.xlsx` by hard-coded path. **Ordering dependency confirmed:** flows #12/#13 (MasterList Checking) operate on *this flow's last output*, not live data — must be re-run before a fresh MasterList check, or the check silently runs stale |
| 8 | `[LIVE-CDO] ... Delete Student List from SharePoint List.zip` | Delete Student List from SharePoint List | PowerApp (manual) | SharePoint, Teams | Clears the SharePoint student list — semester rollover step |
| 9 | `[LIVE-CDO] ... Email To Inform Student Updates.zip` | Email To Inform Student Updates | PowerApp (manual) | SharePoint, Outlook, Teams | Notifies a student their record was updated |
| 10 | `[LIVE-CDO] ... Email for Report Duty Reminder.zip` | Email for Report Duty Reminder | PowerApp (manual) | SharePoint, Outlook, Teams | The "remind students who haven't filled the report duty form" button |
| 11 | `[LIVE-CDO] ... Email for Student Report Duty Status.zip` | ⚠️ **Mis-export (resolved 2026-10-02):** this file is flow 4 again (same flow id `a66117f3…`, byte-identical definition, exported 9 minutes before flow 4). The real "Get Status" flow's definition is **not in the repo** | PowerApp (manual) | unknown | The admin guide (p16) says the PowerApp "Get Status" button runs this flow. Needs a fresh export of the *real* flow before it can be reviewed (MANUAL-TODO) |
| 12 | `[LIVE-CDO] ... HC Supervisor Info MasterList Checking.zip` | HC Supervisor Info MasterList Checking | PowerApp (manual) | SharePoint, Excel Online (Business), Outlook, Teams | New-vs-partial-match detection for HC supervisor records against the master list (array variables bucket rows; Teams reports counts) |
| 13 | `[LIVE-CDO] ... Host Company Info MasterList Checking.zip` | Host Company Info MasterList Checking | PowerApp (manual) | SharePoint, Excel Online (Business), Outlook, Teams | Same new-vs-partial-match logic for host companies. Uses `RunScriptProd` (Office Script) against `Host Company MasterList Template.xlsx`, referenced by a **hard-coded SharePoint drive-item ID** (`01QW2RL4GFFAT2NQYTXFEZ45YLOE4VKNIH`) and a **hard-coded Office Script ID**. This is the clearest confirmed instance of the "process ID reading Excel doesn't work" failure mode — see [`../changelog/DECISIONS.md`](../changelog/DECISIONS.md) D-03 |
| 14 | `[LIVE-CDO] ... Store Student List into SharePoint List.zip` | Store Student List into SharePoint List | ⚠️ **"When a file is created in a folder (deprecated)"** on `/Shared Documents/Power Automate Documents/UTP_CSD_CDO_Report Duty Process/StudentList_DropFile` | SharePoint, Excel Online (Business), Teams | Takes a dropped student-list file and writes it into the SharePoint student list |

**Correction (2026-09-16):** this table was originally mislabeled "13 flows" throughout the doc set — there are genuinely **14** exported `.zip` files (recount, verified via `ls flows/*.zip | wc -l`), all 14 listed above. Row 11's file/display-name mismatch is a separate, still-open question — whether it's a truly distinct 14th flow or a mis-exported duplicate of row 4 needs a Studio check — but it does not change the file count: there are 14 zip files regardless of how that question resolves.

---

## Confirmed working / already-built (don't rebuild these)

- **New-vs-partial-match company/supervisor checking** — flows #12 and #13 already bucket records into new / exact-match / partial-match using array variables and report counts. This is the logic described in the brief ("how many new companies, how many partial match"). It exists; if it's misbehaving, debug it, don't redesign it from scratch.
- **Teams "processing" notifications** — `PostMessageToConversation` (Teams) appears in 12 of the 14 flows. The "show notifications in Teams: running/processing/success" requirement is already implemented for the success case. The recipient isn't hard-coded per flow: every flow reads it dynamically from a shared SharePoint config list item (`id: 1`, table `be7f2b53-cc4e-42b1-a043-a7d6a849ba42`) via an early `Get_item` action, field `TeamsNotification1` (`TeamsNotification2` for "Combine raw data" only) — see `env_setup.md` and `refdocs/issues/2026-09-16-01-no-failure-notifications.md` for the full analysis.

## Confirmed gaps (design targets for the fix phases)

- **Failure alerts: partial, not absent** (corrected 2026-09-30; the earlier "none anywhere" claim was wrong). 12 of 14 flows end with a Teams "…process is FAILED!" post whose `runAfter` is `Failed/Skipped/TimedOut` on the final success post, so any failure after the config `Get_item` triggers it. Gaps: flow #1 (Success Submit Email) has no Teams at all, and its only backup runs on `TimedOut` via the SharePoint SendEmail API that was retired 2025-10-31; flow #14 has no alert (only a `Set_variable` branch); in the other 12 the alert names no step or error, can't fire if `Get_item` fails, and may leave the run marked Succeeded (T3, being checked in the sandbox).
- **All 14 exports were made by `fakhrul_22012087@utp.edu.my` on 2026-09-09** (each `manifest.json` → `details`). Exporting requires owner/co-owner rights, so that account likely has, or had, edit access to the real flows.
- **Deprecated trigger** in flows #2 and #14 (see table above).
- **Hard-coded Excel drive-item ID + Office Script ID** pattern, confirmed in flow #13 and structurally present (same `path`-based Excel reference pattern) in flows #2, #7, #12, #14. Every Excel-touching flow references its template file by a fixed identity, not by a resolvable path lookup at runtime.

## Open questions this inventory surfaced

`ASSUMED:` items — confirm before building anything load-bearing on them. Canonical list: [`../cdo-internship-automation-PRD.md`](../cdo-internship-automation-PRD.md) §8.

1. Is `UTPCSDCDO Success Submit Email` (no `[LIVE-CDO]` prefix) actually published/live, or a draft/deprecated copy?
2. Is the file/display-name mismatch on row 11 a re-export mistake, or does Power Automate actually have a flow titled "Add Host Company into MasterList" duplicated under the "Email for Student Report Duty Status" export name?
3. Is "Standard approvals" in flow #2 still an intentional step in the appointment-letter process, or a legacy leftover no one uses anymore?

## Not one of the 14: `Export Attachment - Report Duty RAW Data` (found 2026-10-02)

In the personal account's own flow list (default environment), state **Stopped**, created 2025-09-17, last modified 2026-09-09. Trigger: a manual button with two text inputs (year and semester). It reads the Report Duty Registration list, and for each item gets its attachments and creates them as files under `/Shared Documents/Internship Programme/<year> <semester>/Report Duty Attachment/<item field_1>`. SharePoint connector only. It is **not part of the exported 14** and no sandbox work covers it; whether it is still used is unknown (MANUAL-TODO). Read through the flow API, definition only, no run history.
