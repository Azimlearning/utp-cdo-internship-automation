# Environment Setup — UTP CDO Internship Automation

> **This project has no API keys or secrets to manage.** All authentication is Microsoft Power Platform OAuth connections (SharePoint, Excel Online, Outlook, Teams, Word Online), configured inside Power Automate Studio itself, not in files in this repo. There is deliberately no `.env.example` here — see D-05 in `changelog/DECISIONS.md`.
>
> What *does* matter for this project is a small set of stable **environment facts** — site URLs, item IDs, connection ownership — that every fix depends on getting right. This file documents those instead.

Last updated: 2026-09-16

---

## Required environment facts

| Fact | Value | Where it's used | Notes |
|---|---|---|---|
| SharePoint site | `https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO` | Every flow's SharePoint/Excel connector `dataset` parameter | The team site all master-list templates and student/company lists live on |
| Master-list template folder | `/Shared Documents/Power Automate Documents/[UTP_CSD_CDO_AppointmentLetter]/Template/` | Flows #2, #7, #12, #13 (see `flow_inventory.md`) | Contains `Host Company MasterList Template.xlsx`, `HC Supervisor MasterList Template.xlsx`, `Control Template.xlsx`, `FinalizedHeader.xlsx` — **must be cleared in place, never replaced** (D-03) |
| Letter drop folder (deprecated trigger) | `/Shared Documents/Power Automate Documents/[UTP_CSD_CDO_AppointmentLetter]/Drop File` | Flow #2's trigger | Target of the deprecated "file created" trigger being replaced in P3 |
| Student list drop folder (deprecated trigger) | `/Shared Documents/Power Automate Documents/UTP_CSD_CDO_Report Duty Process/StudentList_DropFile` | Flow #14's trigger | Same — target of the P3 trigger replacement |
| Host Company MasterList drive-item ID | `01QW2RL4GFFAT2NQYTXFEZ45YLOE4VKNIH` (as of 2026-09-16 export) | Flow #13's `Run_script` / `Get_file_content_using_path` actions | **This is exactly the kind of hard-coded ID D-03 targets for removal.** Will change if the file is ever replaced — if it does, every flow referencing it needs updating until P3's path-based lookup fix lands |
| Host Company MasterList Office Script ID | `ms-officescript://onedrive_business_itemlink/01HL57H3NEOVQVGZ3N75FIXLGLMLEIQ7IG` (as of 2026-09-16 export) | Flow #13's `Run_script` action | Tied to the file above; same fragility |
| Current flow connection owner | `kamalazreel.k@utp.edu.my` | All 14 flows | Target of the M6 ownership migration (P4) |
| "Control Template" config item | SharePoint list, table `be7f2b53-cc4e-42b1-a043-a7d6a849ba42`, item `id: 1` | Every flow's `Get_item` action. Confirmed by `refdocs/context-2023-2024-admin-user-guide.pdf` (pages 4, 31) this is the PowerApp's "Control Template" screen — an admin-edited-each-semester record with fields `Current Semester`, `PIC Approval Teams`, `PIC Email To`, `PIC Email CC`, `Teams Notification 1`, registration cut-off date | Shared across all 14 flows — same fragility class as the drive-item IDs above, just lower severity (a list item survives edits; it only breaks if the item itself is deleted). **Do not delete this item or rename its columns** — every flow's Teams notifications (success and, once issue 1 lands, failure), approval routing, and status emails all break at once. This record is already the *correct* pattern D-03 wants applied elsewhere: edited in place each semester, never replaced. See `refdocs/issues/2026-09-16-01-no-failure-notifications.md` and `refdocs/guides/previous_system_guide_notes.md` |

## Optional / not yet confirmed

| Fact | Default if unset | What it changes |
|---|---|---|
| Shared CDO mailbox address (for M6's Outlook migration) | None exists yet, per PRD Open Question #6 | Where the M6 execution doc sends outbound student/company emails from once written |
| New flow owner account (for M4) | Not yet decided | Who the 14 flows' connections get re-authenticated as in P4 |

---

## Setup

There is no build/install step — this is a documentation and flow-export repo, not a runnable codebase.

```bash
# To inspect a flow's current live definition:
unzip -o -q "flows/<flow name>.zip" -d /tmp/<scratch-dir>
cat "/tmp/<scratch-dir>/Microsoft.Flow/flows/<guid>/definition.json"
```

To re-import a fixed flow into Power Automate, use Studio's "Import Package" on the corresponding `.zip` in `flows/` — this repo's `.zip` files are meant to stay in the standard exportable format, so don't commit an extracted/unzipped copy of a flow (the `.gitignore` blocks `flows/*/` for exactly this reason).

---

## Rules

- **Never commit a real value that isn't already public inside these flow exports.** The IDs above are already visible in the `.zip` files tracked in this repo, so recording them here isn't a new exposure — but if a future fix ever introduces a genuine secret (an API key for a custom Azure Function under D-04, for instance), it goes in a real `.env` file, gitignored, documented here by name only, never by value.
- **A hard-coded ID changing without warning is this project's actual failure mode** (D-03) — if any flow starts failing right after a template file was touched, check this table first.

## When an environment fact changes

If the SharePoint site, a folder path, a drive-item ID, or the connection owner changes, update: this file, `guides/flow_inventory.md`, and a changelog entry — in the same session. Miss one and the next debugging session re-derives a fact that was already known.
